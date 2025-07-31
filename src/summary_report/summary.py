import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

def connect_to_rds():
    """
    Connection to aws rds
    """
    load_dotenv()
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USERNAME")
    db_password = os.getenv("DB_PASSWORD")
    db_name = "postgres"  
    db_port = 5432

    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(db_url)


if __name__ =="__main__":
    connection = connect_to_rds()
    weekly_games = pd.read_sql("select game_name,release_date from game where release_date >= CURRENT_DATE - INTERVAL '7 days';", connection)
    print(weekly_games)
    