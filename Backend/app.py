import datetime
import http
import asyncio
import influxdb_client, os, time
import uvicorn
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()
app = FastAPI()

token = os.getenv("INFLUXDB_TOKEN")
org = "heat_variant"
bucket = "Air Data"
influx_url = "http://10.0.0.2:8086"

client = influxdb_client.InfluxDBClient(url=influx_url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)


class Apartment(BaseModel):
    apt_id: int
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


@app.post("/apt_info")
async def test(apartment: Apartment):
    try:
        print(f"Method used. Apartment: {apartment}")
        return {"apartment": apartment.dict()}
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/get-air-data")
async def get_temperature(data: AirData):
    print(f"Received temperature: {data.temperature}, Pressure: {data.pressure}, humidity: {data.humidity}, "
          f"air quality: {data.air_quality}, mc_id: {data.mc_id}")
    await deliver_data(data)
    return {"mc_id": data.mc_id, "temperature": data.temperature, "pressure": data.pressure, "humidity": data.humidity,
            "air_quality": data.air_quality}


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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

# for value in range(5):
#     point = (
#         Point("measurement1")
#         .tag("tagname1", "tagvalue1")
#         .field("field1", value)
#     )
#     write_api.write(bucket=bucket, org=org, record=point)
#     time.sleep(1)  # separate points by 1 second
