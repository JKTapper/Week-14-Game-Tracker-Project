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


def load_data_into_database(full_df: pd.DataFrame, drop_table: bool = False) -> None:
    engine = get_engine()
    if drop_table:
        exists = "replace"
    else:
        exists = "append"

    publisher_df = full_df[["publisher"]].dropna().drop_duplicates()
    developer_df = full_df[["developer"]].dropna().drop_duplicates()
    genre_df = full_df[["genre"]].dropna().drop_duplicates()
    stores_df = full_df[["store_name"]].dropna().drop_duplicates()
    games_df = full_df[
        [
            "game_name", "app_id", "store_name", "release_date",
            "game_description", "recent_reviews_summary",
            "os_requirements", "storage_requirements", "price"
        ]
    ].drop_duplicates(subset=["app_id"])

    assign_genres = (
        full_df[["game_name", "genre"]]
        .dropna()
        .drop_duplicates()
        .reset_index(drop=True)
    )

    assign_developers = (
        full_df[["game_name", "developer"]]
        .dropna()
        .drop_duplicates()
        .reset_index(drop=True)
    )

    assign_publishers = (
        full_df[["game_name", "publisher"]]
        .dropna()
        .drop_duplicates()
        .reset_index(drop=True)
    )


def main() -> None:
    #  Load dataframes from transform script
    #  Pass them to load_data_to_database()

    data = ...  #  From transform script

    full_df = pd.DataFrame.from_records(data)

    load_data_into_database(full_df)


if __name__ == "__main__":
    main()
#  Data coming in will be a pandas dataframe


"""
return {
        'genre': genres['new'],
        'publisher': publishers['new'],
        'developer': developers['new']
    }
"""
