import os
import csv

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
    "data/raw/population_2025.csv",
    "r",
    encoding="utf-8"
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        neighborhood_name = row["neighborhood"]
        year = int(row["year"])
        population = int(row["population"])

        query = """
            INSERT INTO population_stats (
                neighborhood_id,
                year,
                population,
                source
            )

            SELECT
                id,
                %s,
                %s,
                %s

            FROM neighborhoods

            WHERE name = %s

            ON CONFLICT (neighborhood_id, year)

            DO UPDATE SET
                population = EXCLUDED.population,
                source = EXCLUDED.source;
        """

        cursor.execute(
            query,
            (
                year,
                population,
                "TUIK ADNKS 2025",
                neighborhood_name
            )
        )


conn.commit()

print("Nüfus verileri başarıyla PostgreSQL'e aktarıldı.")

cursor.close()
conn.close()