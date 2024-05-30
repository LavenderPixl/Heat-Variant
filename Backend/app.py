import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()
app = FastAPI()

token = os.getenv("INFLUXDB_TOKEN")
org = "heat_variant"
bucket = "variants"
url = "http://10.0.0.2:8086"

client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)


@app.get("/test")
async def test():
    return {"Hello World": "Testing, again.!"}


@app.get("/get-air-data")
async def get_air_data(apt_number: str):
    return {f""}


@app.get("/get-temperature")
async def get_temperature(temp: str):
    return {f"temperature": temp}


@app.get("/get-pressure")
async def get_pressure(pressure: str):
    return {f"pressure": pressure}


@app.get("/get-humidity")
async def get_humidity(humidity: str):
    return {f"humidity": humidity}


@app.get("/get-gas")
async def get_gas(gas: str):
    return {f"gas": gas}


# Temperature = 27.08 *C
# Pressure = 1004.68 hPa
# Humidity = 49.33 %
# Gas = 148.23 KOhms
# Approx. Altitude = 71.60 m

print("Connected.")

# for value in range(5):
#     point = (
#         Point("measurement1")
#         .tag("tagname1", "tagvalue1")
#         .field("field1", value)
#     )
#     write_api.write(bucket=bucket, org=org, record=point)
#     time.sleep(1)  # separate points by 1 second
