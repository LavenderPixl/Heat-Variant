import datetime
import http
import asyncio
import influxdb_client, os, time
import uvicorn
import asyncio
import mysql.connector
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()
app = FastAPI()

msdb = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
)

ms = msdb.cursor()

token = os.getenv("INFLUXDB_TOKEN")
org = "heat_variant"
bucket = "Air Data"
influx_url = "http://172.0.0.2:8086"

client = influxdb_client.InfluxDBClient(url=influx_url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)


@app.post("/create_tables")
async def create_tables():
    ms.execute("USE HeatVariant")
    ms.execute(
        "CREATE TABLE IF NOT EXISTS Apartments (Apartment_id INT PRIMARY KEY AUTO_INCREMENT, Floor INT NOT NULL, "
        "Apt_number VARCHAR(32) NOT NULL)")
    ms.execute(
        "CREATE TABLE IF NOT EXISTS Residents (Resident_id INT PRIMARY KEY AUTO_INCREMENT, "
        "first_name VARCHAR(32) NOT NULL, last_name VARCHAR(32) NOT NULL, Apartment_id INT, "
        "FOREIGN KEY (Apartment_id) REFERENCES Apartments(Apartment_id))")
    ms.execute(
        "CREATE TABLE IF NOT EXISTS Microcontrollers (Mc_id INT PRIMARY KEY AUTO_INCREMENT, Mac_address VARCHAR(32), "
        "Apartment_id INT, FOREIGN KEY (Apartment_id) REFERENCES Apartments(Apartment_id))")
    ms.execute(
        "CREATE TABLE IF NOT EXISTS Users (User_id INT PRIMARY KEY AUTO_INCREMENT, Email VARCHAR(32) NOT NULL, "
        "Phone_number VARCHAR(32) NOT NULL, Apartment_id INT, "
        "FOREIGN KEY (Apartment_id) REFERENCES Apartments(Apartment_id))")
    ms.execute("SHOW TABLES")
    tables = ms.fetchall()
    return tables


async def startup():
    try:
        ms.execute("CREATE DATABASE IF NOT EXISTS HeatVariant")
        print("DB HeatVariant created successfully.")
        print("Tables created successfully.")
        print(await create_tables())
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))


# region Classes
class Apartment(BaseModel):
    id: int
    mc_id: str | None = None
    floor: int
    apt_number: str
    email: str
    phone_number: str


class AirData(BaseModel):
    mc_id: str
    temperature: float = 0
    pressure: float = 0
    humidity: float = 0
    air_quality: float = 0


class Billing(BaseModel):
    apt_id: int
    billing_id: int
    amount: float = 0.00
    date_issued: str | None = None
    date_paid: str | None = None
    paid: bool


# endregion

# region InfluxDB
@app.post("/get-air-data")
async def get_temperature(data: AirData):
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
# @app.post("/insert_new_apartment")
@app.post("/insert_seed_apartments")
async def seed_data():
    try:
        ms.execute("USE HeatVariant")
        ms.executemany(
            "INSERT INTO Apartments (floor, apt_number) VALUES (%s, %s)",
            [
                (1, 2), (1, 3), (1, 4), (1, 5)
            ])
        ms.executemany(
            "INSERT INTO Microcontrollers (mac_address, apartment_id) VALUES (%s, %s)", [
                ("08:3A:F2:A8:C5:9C", 1), ("Tester", 2)
            ]
        )
        ms.executemany(
            "INSERT INTO Residents (first_name, last_name, apartment_id) VALUES (%s, %s, %s)", [
                ("John", "Doe", 1),
                ("Jane", "Doe", 1),
                ("Jenny", "Doe", 1),
                ("Benny", "Johnson", 2)
            ]
        )
        ms.executemany("INSERT INTO Users (email, phone_number, apartment_id) VALUES (%s, %s, %s)", [
            ("john@email.com", "22314332", 1),
            ("jane@email.com", "22314332", 1),
            ("benny@email.com", "22314332", 2),
        ])
        msdb.commit()
        return "Seeded."
    except mysql.connector.Error as err:
        print(f"Error: {err}")


@app.post("/reset_tables")
async def reset_tables():
    try:
        ms.execute("USE HeatVariant")
        ms.execute("DROP TABLE IF EXISTS Apartments, Microcontrollers, Residents, Users")
        print(await create_tables())
    except mysql.connector.Error as err:
        print(f"Error: {err}")


# endregion

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
asyncio.run(startup())
