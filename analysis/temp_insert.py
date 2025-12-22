import psycopg2

if __name__ == "__main__":
    # Connection settings
    conn = psycopg2.connect(
        dbname="group-05",
        user="postgres",
        password="dbsys2025",
        host="localhost",
        port=5432
    )

    cur = conn.cursor()
    
    with open("trainstation_weatherstation.csv", "r", encoding="utf-8") as f:
        cur.copy_expert(
            f"""
            COPY {"trainstation_weatherstation"}
            FROM STDIN
            WITH (
                FORMAT csv,
                HEADER true,
                DELIMITER ','
            )
            """,
            f
        )
    print("loaded data into database")
    
    conn.commit()
    conn.close()