import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine


def connect_to_rds():
    """
    Connection to aws rds
    """
    load_dotenv()
    print(os.getenv("DB_HOST"),os.getenv("DB_USERNAME"),os.getenv("DB_PASSWORD"),os.getenv("DB_NAME"))
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=5432,
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        dbname="postgres"

    )



def query_rds(conn, query):
    return pd.read_sql(query,conn)


if __name__ == "__main__":
    connection = connect_to_rds()
    data = query_rds(connection,"select * from game;")
    print(data)