from fastapi import FastAPI
from database import get_connection

# to start use this: python -m uvicorn main:app --reload or the bat file
# after you can go to http://127.0.0.1:8000/docs to test all the functions

app = FastAPI()

@app.get("/precipitation/{station_id}")
def get_prec_by_station_limit_100(station_id: int):
    limit = 100
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM german_prec WHERE station_id = %s LIMIT %s",
        (station_id,limit)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows