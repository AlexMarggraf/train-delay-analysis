import psycopg2
import os
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

with open(r"processed/sbb/swiss_trainstation.csv", "r", encoding='utf-8') as f:
    cur.copy_expert(
                f"""
                COPY {"swiss_trainstation"}
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

with open(r"processed/sbb/swiss_operator.csv", "r", encoding='utf-8') as f:
    cur.copy_expert(
                f"""
                COPY {"swiss_operator"}
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

for csv_file in glob.glob(r"processed/sbb/**/*csv"):
    table = os.path.splitext(os.path.basename(csv_file))[0].split("-")[0]
    
    if table == "line":
        with open(csv_file, "r", encoding="utf-8") as f:
            cur.copy_expert(
                f"""
                COPY {"swiss_trainline"}
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

for csv_file in glob.glob(r"processed/sbb/**/*csv"):
    table = os.path.splitext(os.path.basename(csv_file))[0].split("-")[0]

    print(f"Loading {csv_file} into table {table}...")

    if table == "stop":
        with open(csv_file, "r", encoding="utf-8") as f:
            cur.copy_expert(
                f"""
                COPY {"swiss_trainstop"}
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
