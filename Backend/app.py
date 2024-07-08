import http
import asyncio
import datetime
import string
import random
import influxdb_client, os, time
import uvicorn
import asyncio
from _datetime import datetime
import mysql.connector
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
from typing import Optional

load_dotenv()
app = FastAPI()

msdb = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
)

ms = msdb.cursor()

token = os.getenv("DOCKER_INFLUXDB_INIT_ADMIN_TOKEN")
org = "heat_variant"
bucket = "air-data"
influx_url = "http://172.0.0.2:8086"

client = influxdb_client.InfluxDBClient(url=influx_url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)


@app.post("/create-tables")
async def create_tables():
    ms.execute("USE HeatVariant")
    ms.execute(
        "CREATE TABLE IF NOT EXISTS Apartments (Apartment_id INT PRIMARY KEY AUTO_INCREMENT, Floor INT NOT NULL, "
        "Apt_number VARCHAR(32) NOT NULL, UNIQUE INDEX unique_apt (apt_number, floor))")
    ms.execute(
        "CREATE TABLE IF NOT EXISTS Residents (Resident_id INT PRIMARY KEY AUTO_INCREMENT, "
        "first_name VARCHAR(32) NOT NULL, last_name VARCHAR(32) NOT NULL, Apartment_id INT, "
        "Moved_in DATETIME, Moved_out DATETIME, FOREIGN KEY (Apartment_id) REFERENCES Apartments(Apartment_id))")
    ms.execute(
        "CREATE TABLE IF NOT EXISTS  Microcontrollers (Mc_id INT PRIMARY KEY AUTO_INCREMENT, Mac_address VARCHAR(32), "
        "Apartment_id INT, FOREIGN KEY (Apartment_id) REFERENCES Apartments(Apartment_id))")
    ms.execute(
        "CREATE TABLE IF NOT EXISTS Users (User_id INT PRIMARY KEY AUTO_INCREMENT, Email VARCHAR(32) NOT NULL, "
        "Phone_number VARCHAR(32) NOT NULL, Password VARCHAR(225) NOT NULL, Apartment_id INT, Admin BOOL, Active BOOL, "
        "FOREIGN KEY (Apartment_id) REFERENCES Apartments(Apartment_id))")

    # ms.execute(
    #     "DROP PROCEDURE IF EXISTS cleanOldData;"
    #     "DELIMITER &&"
    #     "CREATE STORED PROCEDURE cleanOldData IF NOT EXISTS AS"
    #     "BEGIN"
    #     "INSERT INTO Apartments(FLOOR, Apt_number) VALUES (100, unix_timestamp())"
    #     "END && "
    # )
    ms.execute("SHOW TABLES")
    tables = ms.fetchall()
    return tables


async def startup():
    try:
        ms.execute("CREATE DATABASE IF NOT EXISTS HeatVariant")
        print("DB HeatVariant created successfully.")
        print(await create_tables())
        await seed_apartments()
        await create_admin()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))


# region Classes
class Apartment(BaseModel):
    apartment_id: Optional[int] = None
    floor: int
    apt_number: str


class Microcontrollers(BaseModel):
    mc_id: int
    mac_address: str
    apartment_id: int


class Residents(BaseModel):
    resident_id: Optional[int] = None
    first_name: str
    last_name: str
    apartment_id: int
    moved_in: datetime
    moved_out: Optional[datetime] = None


class Users(BaseModel):
    user_id: Optional[int] = None
    apartment_id: Optional[int] = None
    email: str
    phone_number: str
    password: str
    admin: bool
    active: bool


class AirData(BaseModel):
    mc_id: str
    temperature: float = 0
    pressure: float = 0
    humidity: float = 0
    air_quality: float = 0


class Billing(BaseModel):
    apt_id: int
    billing_id: Optional[int] = None
    amount: float = 0.00
    date_issued: str | None = None
    date_paid: str | None = None
    paid: bool


# endregion

# region InfluxDB
@app.post("/air/get-air-data")
async def get_air_data(data: AirData):
    print(f"Received temperature: {data.temperature}, Pressure: {data.pressure}, Humidity: {data.humidity}, "
          f"Air Quality/Gas: {data.air_quality}, Mc_ID: {data.mc_id}")
    await deliver_data(data)
    return True


async def deliver_data(data: AirData):
    p = (
        Point("Air")
        .tag("micro controller", data.mc_id)
        .field("temperature", data.temperature)
        .field("pressure", data.pressure)
        .field("humidity", data.humidity)
        .field("air_quality", data.air_quality)
    )
    try:
        write_api.write(bucket, org, p)
    except HTTPException as e:
        print(f"Bucket cannot be found. Error: {e}")
    time.sleep(1)


# endregion

# region MySQL
@app.get("/apartments/")
@app.post("/apartments/insert-apartment")
async def insert_apartment(apt: Apartment):
    try:
        ms.execute("SELECT floor, apt_number, COUNT(*) FROM Apartments WHERE floor = %s AND apt_number = %s",
                   (apt.floor, apt.apt_number))
        msg = ms.fetchone()
        if msg[2] == 0:
            try:
                ms.execute(f"INSERT INTO Apartments(floor, apt_number) VALUES (%s, %s)",
                           [apt.floor, apt.apt_number])
                msdb.commit()
            except mysql.connector.Error as err:
                print(f"Database Error: {err}")
        else:
            print(f"Error: Already exists apartment: {apt.floor}, {apt.apt_number}")
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")


async def seed_apartments():
    try:
        ms.execute("USE HeatVariant")
        ms.executemany(
            "INSERT IGNORE INTO Apartments (floor, apt_number) VALUES (%s, %s)",
            [(1, 1), (1, 2), (1, 3), (1, 4), (1, 5)]
        )
        msdb.commit()
        print("Tables created successfully.")
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")


@app.post("/mysql/seed-data")
async def seed_data():
    try:
        ms.execute("USE HeatVariant")
        ms.executemany(
            "INSERT IGNORE INTO Apartments (floor, apt_number) VALUES (%s, %s)",
            [
                (1, 2), (1, 3), (1, 4), (1, 5)
            ])
        print("Apartments Seeded.")
        ms.executemany(
            "INSERT IGNORE INTO Microcontrollers (mac_address, apartment_id) VALUES (%s, %s)",
            [
                ("08:3A:F2:A8:C5:9C", 1),
                ("Tester", 2)
            ])
        print("Microcontrollers Seeded.")
        ms.executemany(
            "INSERT IGNORE INTO Residents (first_name, last_name, apartment_id, moved_in, moved_out) VALUES "
            "(%s, %s, %s, %s, %s)",
            [
                ("John", "Doe", 1, datetime.now(), None),
                ("Jane", "Doe", 1, datetime.now(), None),
                ("Jenny", "Doe", 1, datetime.now(), None),
                ("Benny", "Johnson", 2, datetime.now(), None)
            ])
        print("Residents Seeded.")
        ms.executemany("INSERT IGNORE INTO Users "
                       "(email, phone_number, password, apartment_id, admin, active)"
                       "VALUES (%s, %s, %s, %s, %s, %s)", [
                           ("john@email.com", "22314332", "password123", 1, True, True),
                           ("jane@email.com", "22314332", "password123", 1, False, True),
                           ("benny@email.com", "22314332", "password123", 2, False, True),
                       ])
        print("Users Seeded.")
        msdb.commit()
        return "Seeded."
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")


@app.post("/mysql/reset-tables")
async def reset_tables():
    try:
        ms.execute("USE HeatVariant")
        ms.execute("DROP TABLE IF EXISTS Apartments, Microcontrollers, Residents, Users")
        print("Resetting..")
        print(await create_tables())
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")


# endregion

# region UserMethods
async def create_admin():
    try:
        print("Creating admin...")
        ms.execute("SELECT email, phone_number, COUNT(*) FROM Users WHERE email = %s AND phone_number = %s",
                   ("admin", "admin"))
        msg = ms.fetchone()
        if msg[2] == 0:
            try:
                ms.execute(
                    "INSERT INTO Users (email, phone_number, password, admin, active) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    ("admin", "admin", "admin", True, True))
                print("New Admin created.")
                msdb.commit()
                return "New Admin account created."
            except mysql.connector.Error as err:
                print(f"Database Error: {err}")
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")


@app.post("/create-user")
async def create_user(new_user: Users):
    try:
        ms.execute("SELECT email, phone_number, COUNT(*) FROM Users WHERE email = %s AND phone_number = %s",
                   (new_user.email, new_user.phone_number))
        msg = ms.fetchone()
        if msg[2] == 0:
            print(msg[2])
            try:
                ms.execute("INSERT INTO Users (apartment_id, email, phone_number, password, admin, active) "
                           "VALUES (%s, %s, %s, %s, %s, %s)",
                           (new_user.apartment_id, new_user.email,
                            new_user.phone_number, new_user.password, new_user.admin, False))
                print(f"New user: {new_user}")
                msdb.commit()
                return f"New user created: {new_user}"
            except mysql.connector.Error as err:
                return f"Database Error: {err}"
        else:
            return "User already exists."
    except mysql.connector.Error as err:
        return "Database Error: {err}"


@app.get("/residents")
async def all_residents():
    ms.execute(f"SELECT * FROM Residents")
    return ms.fetchall()


@app.get("/residents/{apartment-id}")
async def get_residents(apartment_id: int):
    ms.execute(f"SELECT * FROM Residents WHERE Apartment_id = {apartment_id}")
    return ms.fetchall()


@app.put("/user/deactivate")
async def deactivate(apartment_id: int):
    try:
        now = datetime.now()
        print(f"new time: {now}")
        ms.execute(f"UPDATE Residents SET moved_out = current_date WHERE Apartment_id = {apartment_id}")
        ms.execute(f"UPDATE Users SET active = FALSE WHERE apartment_id = {apartment_id}")
        residents = await get_residents(apartment_id)
        msdb.commit()
        print(f"Users deactivated: {residents}")
        print(f"Residents now moved out: {residents}")
        return residents
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")


@app.put("/user/reset-login")
async def reset_login(email: str = Body(..., embed=True)):
    if email is None:
        raise HTTPException(status_code=422, detail="Email is required")
    new_pass = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(9))
    try:
        ms.execute("UPDATE Users SET password = %s WHERE email = %s",
                   (new_pass, email))
        msdb.commit()
        return "New password: " + new_pass
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")


@app.get("/users")
async def get_active_users():
    ms.execute("SELECT * FROM Users WHERE active = TRUE")
    return ms.fetchall()


@app.get("/users/inactive")
async def get_users():
    ms.execute("SELECT * FROM Users WHERE active = FALSE")
    return ms.fetchall()


@app.get("/users/{apartment-id}")
async def apartment_users(apartment_id: int):
    try:
        ms.execute(f"SELECT * FROM Users WHERE Apartment_id = {apartment_id}")
        return ms.fetchall()
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")


@app.get("/users/{userid}")
async def get_user(userid: int):
    try:
        ms.execute(f"SELECT 1 FROM Users WHERE User_id = {userid}")
        return ms.fetchone()
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")


# async def login(user: Users) deactivate
# MAKE SURE TO CHECK IF USER IS ACTIVE !! INACTIVE = NOT ABLE TO LOG IN!!!
# LOGIN SETS ACTIVE = TRUE
# endregion


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
asyncio.run(startup())
