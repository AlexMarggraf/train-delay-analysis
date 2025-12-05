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

print(f"Loading german_trainstation.csv into table german_stop...")

with open("processed/db/german_trainstation.csv", "r", encoding="utf-8") as f:
    cur.copy_expert(
        f"""
        COPY {"german_trainstation"}
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

print(f"Loading german_line.csv into table german_stop...")

with open("processed/db/german_line.csv", "r", encoding="utf-8") as f:
    cur.copy_expert(
        f"""
        COPY {"german_trainline"}
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

for csv_file in glob.glob(r"processed/db/processed/*csv"):

    print(f"Loading {csv_file} into table german_stop...")

    with open(csv_file, "r", encoding="utf-8") as f:
        cur.copy_expert(
            f"""
            COPY {"german_trainstop"}
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
