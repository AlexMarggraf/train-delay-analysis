import psycopg2
from psycopg2.extras import RealDictCursor

# Before using the bat update the fields host, port, dbname, user and password accordingly

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="gruppe5",
        user="postgres",
        password="1234",
        cursor_factory=RealDictCursor
    )
