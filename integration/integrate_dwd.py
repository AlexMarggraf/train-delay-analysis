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

print(f"Loading german_weatherstation.csv into table german_weatherstation...")

with open("processed/dwd/german_weatherstation.csv", "r", encoding="utf-8") as f:
    cur.copy_expert(
        f"""
        COPY {"german_weatherstation"}
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

for csv_file in glob.glob(r"processed/dwd/air_temp/*csv"):
    print(f"Loading {csv_file} into table german_air_temp...")

    with open(csv_file, "r", encoding="utf-8") as f:
        cur.copy_expert(
            f"""
            COPY {"german_temp"}
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

for csv_file in glob.glob(r"processed/dwd/precipitation/*csv"):
    print(f"Loading {csv_file} into table german_precipitation...")

    with open(csv_file, "r", encoding="utf-8") as f:
        cur.copy_expert(
            f"""
            COPY {"german_prec"}
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

for csv_file in glob.glob(r"processed/dwd/pressure/*csv"):
    print(f"Loading {csv_file} into table german_pressure...")

    with open(csv_file, "r", encoding="utf-8") as f:
        cur.copy_expert(
            f"""
            COPY {"german_pres"}
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

for csv_file in glob.glob(r"processed/dwd/wind/*csv"):
    print(f"Loading {csv_file} into table german_wind...")

    with open(csv_file, "r", encoding="utf-8") as f:
        cur.copy_expert(
            f"""
            COPY {"german_wind"}
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
