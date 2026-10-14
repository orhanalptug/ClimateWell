import os
import json

import psycopg2
from dotenv import load_dotenv


load_dotenv()


conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

cursor = conn.cursor()


with open(
    "data/raw/cankaya_neighborhoods.geojson",
    "r",
    encoding="utf-8"
) as file:
    data = json.load(file)


for feature in data["features"]:

    properties = feature["properties"]
    geometry = feature["geometry"]

    object_id = properties["OBJECTID"]
    name = properties["AD"]
    identity_no = properties["KIMLIKNO"]
    district_id = properties["ILCEID"]

    geometry_json = json.dumps(geometry)

    query = """
        INSERT INTO neighborhoods (
            object_id,
            name,
            identity_no,
            district_id,
            geometry
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            ST_SetSRID(
                ST_GeomFromGeoJSON(%s),
                4326
            )
        );
    """

    cursor.execute(
        query,
        (
            object_id,
            name,
            identity_no,
            district_id,
            geometry_json
        )
    )


conn.commit()

print("Mahalle verileri başarıyla PostgreSQL'e aktarıldı.")

cursor.close()
conn.close()