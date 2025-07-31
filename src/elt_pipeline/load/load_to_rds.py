"""Script to take transformed data and stores into our RDS Postgres Database"""
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text, Engine

from src.elt_pipeline.steam_tl.transform import transform_s3_steam_data

load_dotenv()

DB_URL = (
    f"postgresql+psycopg2://{os.getenv('DB_USERNAME')}"
    f":{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}"
    f":{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME')}"
)


def get_engine() -> Engine:
    """Connects and returns engine to function"""

    return create_engine(DB_URL, future=True)


def upload_table(conn, df: pd.DataFrame, table: str, col: str, pk: str) -> None:
    """Insert each value of df to database"""

    sql = text(f"""
        INSERT INTO {table} ({pk}, {col})
        VALUES (:id, :name)
        ON CONFLICT ({pk}) DO NOTHING
    """)

    for _, row in df.iterrows():
        conn.execute(sql, {
            "id":   int(row[pk]),
            "name": row[col],
        })


def upload_games(conn, games_df: pd.DataFrame) -> None:
    """INSERT games to games table"""

    sql = text("""
        INSERT INTO game (
          game_id, game_name, app_id, store_id, release_date,
          game_description, recent_reviews_summary,
          os_requirements, storage_requirements, price
        ) VALUES (
          :game_id, :game_name, :app_id, :store_id, :release_date,
          :game_description, :recent_reviews_summary,
          :os_requirements, :storage_requirements, :price
        )
        ON CONFLICT (app_id) DO NOTHING
    """)

    for _, row in games_df.iterrows():
        conn.execute(sql, {
            "game_id": row["game_id"],
            "game_name": row["game_name"],
            "app_id": row["app_id"],
            "store_id": 1,
            # This hardcodes for steam currently
            "release_date": row["release_date"],
            "game_description": row["description"],
            "recent_reviews_summary": None,
            "os_requirements": None,
            "storage_requirements": None,
            "price": row["price"],
        })


def upload_assignments(conn, df: pd.DataFrame, table: str, left_foreign_key: str, right_foreign_key: str) -> None:
    """Generic function to help with genre, publisher and developer assignment"""
    sql = text(f"""
        INSERT INTO {table} ({left_foreign_key}, {right_foreign_key})
        VALUES (:l, :r)
        ON CONFLICT DO NOTHING
    """)

    for _, row in df.iterrows():
        conn.execute(
            sql, {"l": int(row[left_foreign_key]), "r": int(row[right_foreign_key])})


def get_existing_game_ids(conn) -> set[int]:
    """Gets set of all existing game ids"""
    result = conn.execute(text("SELECT game_id FROM game"))
    return set(row[0] for row in result.fetchall())


def load_data_into_database(games_df: pd.DataFrame,
                            publisher_df: pd.DataFrame,
                            developer_df: pd.DataFrame,
                            genre_df: pd.DataFrame,
                            genre_assignment_df,
                            developer_assignment_df,
                            publisher_assignment_df) -> None:
    """Loads all data into our database"""

    games_df["app_id"] = games_df["app_id"].astype(int)
    games_df["price"] = games_df["price"].astype(int)

    engine = get_engine()

    with engine.begin() as conn:
        upload_table(conn, publisher_df, "publisher",
                     "publisher_name", "publisher_id")
        upload_table(conn, developer_df, "developer",
                     "developer_name", "developer_id")
        upload_table(conn, genre_df, "genre", "genre_name", "genre_id")

        upload_games(conn, games_df)

        existing_game_ids = get_existing_game_ids(conn)

        genre_assignment_df = genre_assignment_df[
            genre_assignment_df["game_id"].isin(existing_game_ids)
        ]
        developer_assignment_df = developer_assignment_df[
            developer_assignment_df["game_id"].isin(existing_game_ids)
        ]
        publisher_assignment_df = publisher_assignment_df[
            publisher_assignment_df["game_id"].isin(existing_game_ids)
        ]

        upload_assignments(conn, genre_assignment_df,
                           "genre_assignment",     "genre_id",     "game_id")
        upload_assignments(conn, developer_assignment_df,
                           "developer_assignment", "developer_id", "game_id")
        upload_assignments(conn, publisher_assignment_df,
                           "publisher_assignment", "publisher_id", "game_id")


def main():
    """Main to run other functions"""
    data = transform_s3_steam_data()
    games_df = data["game"]
    publisher_df = data["publisher"]
    developer_df = data["developer"]
    genre_df = data["genre"]
    genre_assignment_df = data["genre_assignment"]
    developer_assignment_df = data["developer_assignment"]
    publisher_assignment_df = data["publisher_assignment"]
    load_data_into_database(games_df, publisher_df, developer_df, genre_df,
                            genre_assignment_df, developer_assignment_df, publisher_assignment_df)


if __name__ == "__main__":
    main()
