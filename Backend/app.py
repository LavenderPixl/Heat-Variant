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
        "CREATE TABLE IF NOT EXISTS Apartments (Apartment_id INT PRIMARY KEY AUTO_INCREMENT, Mc_id VARCHAR(32), "
        "Floor INT NOT NULL, Apt_number VARCHAR(32) NOT NULL)")
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
async def insert_seed_apartments():
    try:
        ms.execute("USE HeatVariant")
        sql = "INSERT INTO Apartments (mc_id, floor, apt_number, email, phone_number) VALUES (%s, %s, %s, %s, %s)"
        val = [
            ("08:3A:F2:A8:C5:9C", 1, 2, "email@email.com", "22548032"),
            ("NULL", 1, 3, "email2@email.com", "34194673"),
            ("NULL", 1, 4, "email3@email.com", "34567843"),
            ("NULL", 1, 5, "email4@email.com", "34198653")
        ]
        ms.executemany(sql, val)
        msdb.commit()
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

# @app.post("/apt_info")
# async def test(apartment: Apartment):
#     try:
#         print(f"Method used. Apartment: {apartment}")
#         return {"apartment": apartment.dict()}
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")

# endregion

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
asyncio.run(startup())
