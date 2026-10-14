import os

import requests
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


query = """
    SELECT
        id,
        name,
        ST_Y(ST_Centroid(geometry)) AS latitude,
        ST_X(ST_Centroid(geometry)) AS longitude
    FROM neighborhoods
    ORDER BY id;
"""

cursor.execute(query)

neighborhoods = cursor.fetchall()


API_URL = "https://archive-api.open-meteo.com/v1/archive"

START_DATE = "2025-06-01"
END_DATE = "2025-08-31"


for neighborhood in neighborhoods:

    neighborhood_id = neighborhood[0]
    neighborhood_name = neighborhood[1]
    latitude = neighborhood[2]
    longitude = neighborhood[3]

    print()
    print("----------------------------------")
    print("Mahalle:", neighborhood_name)
    print("Latitude:", latitude)
    print("Longitude:", longitude)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min"
        ),
        "timezone": "Europe/Istanbul"
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    dates = data["daily"]["time"]

    max_temperatures = (
        data["daily"]["temperature_2m_max"]
    )

    min_temperatures = (
        data["daily"]["temperature_2m_min"]
    )

    for date, max_temp, min_temp in zip(
        dates,
        max_temperatures,
        min_temperatures
    ):

        insert_query = """
            INSERT INTO temperature_records (
                neighborhood_id,
                recorded_date,
                max_temperature_c,
                min_temperature_c,
                source
            )

            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s
            )

            ON CONFLICT (
                neighborhood_id,
                recorded_date
            )

            DO UPDATE SET
                max_temperature_c =
                    EXCLUDED.max_temperature_c,

                min_temperature_c =
                    EXCLUDED.min_temperature_c,

                source =
                    EXCLUDED.source;
        """

        cursor.execute(
            insert_query,
            (
                neighborhood_id,
                date,
                max_temp,
                min_temp,
                "Open-Meteo Historical API"
            )
        )

    conn.commit()

    print(
        len(dates),
        "günlük sıcaklık kaydı eklendi."
    )


cursor.close()
conn.close()

print()
print("===================================")
print("Tüm sıcaklık verileri başarıyla aktarıldı.")
print("===================================")