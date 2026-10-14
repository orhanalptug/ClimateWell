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
    "data/raw/cankaya_parks.geojson",
    "r",
    encoding="utf-8"
) as file:
    data = json.load(file)


for feature in data["features"]:

    properties = feature["properties"]
    geometry = feature["geometry"]

    osm_id = properties["osm_id"]
    osm_type = properties["osm_type"]
    name = properties["name"]

    geometry_json = json.dumps(geometry)

    query = """
        INSERT INTO parks (
            osm_id,
            osm_type,
            name,
            geometry
        )
        VALUES (
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
            osm_id,
            osm_type,
            name,
            geometry_json
        )
    )


conn.commit()

print("Park verileri başarıyla PostgreSQL'e aktarıldı.")

cursor.close()
conn.close()