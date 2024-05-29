import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("INFLUXDB_TOKEN")
org = "Heat-Variant-ORG"
url = "http://localhost:8086"
# url = "http://0.0.0.0:8086"
client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)


bucket = "Heat-Variant"

write_api = client.write_api(write_options=SYNCHRONOUS)

for value in range(5):
    point = (
        Point("measurement1")
        .tag("tagname1", "tagvalue1")
        .field("field1", value)
    )
    write_api.write(bucket=bucket, org="Heat-Variant-ORG", record=point)
    time.sleep(1)  # separate points by 1 second
