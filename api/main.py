from datetime import datetime

from fastapi import FastAPI

from mask import GermanPrecMask
from database import get_connection

# to start use this: python -m uvicorn main:app --reload or the bat file
# after you can go to http://127.0.0.1:8000/docs to test all the functions

app = FastAPI()


@app.get("/precipitation/{station_id}")
def get_german_prec_by_station_limit_100(station_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM german_prec WHERE station_id = %s LIMIT 100",
        (station_id,)
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


@app.post("/precipitation")
def insert_into_german_prec(data: GermanPrecMask):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        Insert INTO german_prec(
            station_id, 
            station_timestamp, 
            qn_8, 
            precipitation_mm,
            precipitation_t_or_f, 
            precipitation_type, 
            eor)

        Values (%s, %s, %s, %s, %s, %s, %s)
        """,
        (data.station_id,
         data.station_timestamp,
         data.qn_8,
         data.precipitation_mm,
         data.precipitation_t_or_f,
         data.precipitation_type,
         data.eor)
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "new tupel created"}

@app.put("/precipitation/{station_id}/{station_timestamp}")
def update_prec_with_station_id_and_timestamp(station_id: int, station_timestamp: datetime, data: GermanPrecMask):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE german_prec
        SET 
            qn_8 = %s, 
            precipitation_mm = %s,
            precipitation_t_or_f = %s, 
            precipitation_type = %s, 
            eor = %s
            
        WHERE station_id = %s
        AND station_timestamp = %s
        """,

        (data.qn_8,
         data.precipitation_mm,
         data.precipitation_t_or_f,
         data.precipitation_type,
         data.eor,

         station_id,
         station_timestamp
         )
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"message": "updated"}


@app.delete("/precipitation/{station_id}/{station_timestamp}")
def delete_prec_with_station_id_and_timestamp(station_id: int, station_timestamp: datetime):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM german_prec
        WHERE station_id = %s
            AND station_timestamp = %s
        """,
        (station_id,
         station_timestamp
         )
    )
    conn.commit()
    cur.close()
    conn.close()

    return {"message": "deleted"}