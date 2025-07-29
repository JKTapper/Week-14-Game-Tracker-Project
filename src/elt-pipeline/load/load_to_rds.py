"""Script to take transformed data and stores into our RDS Postgres Database"""
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text, engine

load_dotenv()
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = int(os.getenv("DB_PORT"))
DB_SCHEMA = os.getenv("DB_SCHEMA")


def get_engine() -> engine:
    """Connects to RDS Postgres instance"""
    url = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine = create_engine(url, future=True)

    return engine


def load_data_into_database():
    ...


def main() -> None:
    #  Load dataframes from transform script
    #  Pass them to load_data_to_database()

    ...


if __name__ == "__main__":
    main()
#  Data coming in will be a pandas dataframe
