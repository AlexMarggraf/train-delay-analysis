import psycopg2
import glob

# Connection settings
conn = psycopg2.connect(
    dbname="group-05",
    user="postgres",
    password="dbsys2025",
    host="localhost",
    port=5432
)

cur = conn.cursor()

print(f"Loading swiss_weatherstation.csv into table swiss_weatherstation...")

with open(r"processed/meteoSwiss\ogd-smn_meta_stations.csv", "r", encoding="latin1") as f:
    cur.copy_expert(
        f"""
        COPY {"swiss_weatherstation"}
        FROM STDIN
        WITH (
            FORMAT csv,
            HEADER true,
            DELIMITER ';'
        )
        """,
        f
    )

conn.commit()

for csv_file in glob.glob(r"processed/meteoSwiss/processed/*csv"):
    print(f"Loading {csv_file} into table swiss_weather_measurement...")

    with open(csv_file, "r", encoding="utf-8") as f:
        cur.copy_expert(
            f"""
            COPY {"swiss_measurement"}
            FROM STDIN
            WITH (
                FORMAT csv,
                HEADER true,
                DELIMITER ','
            )
            """,
            f
        )

    conn.commit()

cur.close()
conn.close()

print("Done.")
