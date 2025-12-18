import psycopg2

# Update the fields host, port, dbname, user and password accordingly

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="group-05",
        user="postgres",
        password="1234"
    )
