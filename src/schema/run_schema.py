import os
from dotenv import load_dotenv
import psycopg2


def connect_to_rds():
    """
    Connection to aws rds
    """
    load_dotenv()
    print(os.getenv("DB_HOST"), os.getenv("DB_USERNAME"),
          os.getenv("DB_PASSWORD"), os.getenv("DB_NAME"))
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=5432,
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        dbname="postgres"

    )


def run_schema(conn):
    """
    Run all required functions to extract data
    """
    cur = conn.cursor()

    with open("src/schema/schema.sql", "r", encoding='utf-8') as f:
        cur.execute(f.read())

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    conn = connect_to_rds()
    run_schema(conn)
