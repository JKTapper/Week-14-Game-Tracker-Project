"""Script to take transformed data and stores into our RDS Postgres Database"""

import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, Engine, text, Connection

from elt_pipeline.transform.transform import transform_s3_steam_data


load_dotenv()
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = int(os.getenv("DB_PORT"))
# DB_SCHEMA = os.getenv("DB_SCHEMA")


def get_engine() -> Engine:
    """Connects to RDS Postgres instance"""
    url = (
        f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine = create_engine(url, future=True)

    return engine


def load_data_into_database(games_df: pd.DataFrame,
                            publisher_df: pd.DataFrame,
                            developer_df: pd.DataFrame,
                            genre_df: pd.DataFrame,
                            genre_assignment_df: pd.DataFrame,
                            developer_assignment_df: pd.DataFrame,
                            publisher_assignment_df: pd.DataFrame,) -> None:
    """Takes data and loads it into each table"""
    engine = get_engine()

    if "store_name" in games_df.columns:
        stores_df = games_df[["store_name"]].dropna(
        ).drop_duplicates().reset_index(drop=True)
    else:
        stores_df = pd.DataFrame(columns=["store_name"])

    with engine.begin() as conn:
        store_cache = upload_stores(conn, stores_df)
        publisher_cache = upload_references_to_games(
            conn, publisher_df, "publisher_name", "publisher", "publisher_id")
        dev_cache = upload_references_to_games(
            conn, developer_df, "developer_name", "developer", "developer_id")
        genre_cache = upload_references_to_games(
            conn, genre_df,     "genre_name",     "genre",     "genre_id")
        games_cache = games_upload(conn, store_cache, games_df)

        for _, row in genre_assignment_df.iterrows():
            conn.execute(
                text("""
                INSERT INTO genre_assignment (genre_id, game_id)
                VALUES (:g_id, :gm_id)
                ON CONFLICT DO NOTHING
                """),
                {"g_id": genre_cache[row["genre_name"]],
                 "gm_id": games_cache[row["app_id"]]},
            )
        for _, row in developer_assignment_df.iterrows():
            conn.execute(
                text("""
                INSERT INTO developer_assignment (developer_id, game_id)
                VALUES (:d_id, :gm_id)
                ON CONFLICT DO NOTHING
                """),
                {"d_id": dev_cache[row["developer_name"]],
                 "gm_id": games_cache[row["app_id"]]},
            )
        for _, row in publisher_assignment_df.iterrows():
            conn.execute(
                text("""
                INSERT INTO publisher_assignment (publisher_id, game_id)
                VALUES (:p_id, :gm_id)
                ON CONFLICT DO NOTHING
                """),
                {"p_id": publisher_cache[row["publisher_name"]],
                 "gm_id": games_cache[row["app_id"]]},
            )


def upload_stores(conn: Connection, stores_df: pd.DataFrame) -> dict:
    """Inserts into store table and returns cache of ids and names"""
    for store in stores_df["store_name"]:
        conn.execute(
            text("""
                    INSERT INTO store (store_name)
                    VALUES (:name)
                    ON CONFLICT (store_name) DO NOTHING
                    """),
            {"name": store}
        )

    store_cache = {
        row.store_name: row.store_id
        for row in conn.execute(text("SELECT store_id, store_name FROM store"))
    }

    return store_cache


def upload_references_to_games(conn: Connection, df: pd.DataFrame, col: str, table_name: str, pk_name: str) -> dict:
    """Helps with loading into publisher, developer and genre tables"""

    for name in df[col]:
        conn.execute(text(
            f"""
                INSERT INTO {table_name} ({col}_name)
                VALUES (:name)
                ON CONFLICT ({col}_name) DO NOTHING
            """
        ),
            {"name": name}
        )

    rows = conn.execute(text(
        f"SELECT {col}, {pk_name} FROM {table_name}"
    ))

    return {row[col + "_name"]: getattr(row, pk_name) for row in rows}


def games_upload(conn: Connection, store_cache: dict, games_df: pd.DataFrame) -> dict:
    """Uploads games to games tables and returns game_id cache"""
    for _, row in games_df.iterrows():
        store_name = row.get(
            "store_name") if "store_name" in games_df.columns else None
        store_id = store_cache.get(store_name) if store_name else None
        conn.execute(
            text("""
                INSERT INTO game
                  (game_name, app_id, store_id, release_date,
                   game_description, recent_reviews_summary,
                   os_requirements, storage_requirements, price)
                VALUES
                  (:name, :app, :store, :rel, :desc, :rev, :os, :stor, :price)
                ON CONFLICT (app_id) DO NOTHING
                """),
            {
                "name": row["game_name"],
                "app":  row["app_id"],
                "store": 1,
                "rel":   row.get("release_date"),
                "desc":  row.get("game_description"),
                "rev":   row.get("recent_reviews_summary"),
                "os":    row.get("os_requirements"),
                "stor":  row.get("storage_requirements"),
                "price": row.get("price"),
            },
        )
    rows = conn.execute(text("SELECT app_id, game_id FROM game"))

    return {row.app_id: row.game_id for row in rows}


def main() -> None:
    """Main to run other functions"""

    data = transform_s3_steam_data()

    games_df = data["game"]
    publisher_df = data["publisher"]
    developer_df = data["developer"]
    genre_df = data["genre"]
    genre_assignment_df = data["genre_assignment"]
    developer_assignment_df = data["developer_assignment"]
    publisher_assignment_df = data["publisher_assignment"]

    print("Publishers DF:", publisher_df.head())
    print("Developers DF:", developer_df.head())
    print("Genres DF:", genre_df.head())
    print("Genre Assignment DF:", genre_assignment_df.head())
    print("Developer Assignment DF:", developer_assignment_df.head())
    print("Publisher Assignment DF:", publisher_assignment_df.head())

    load_data_into_database(games_df,
                            publisher_df,
                            developer_df,
                            genre_df,
                            genre_assignment_df,
                            developer_assignment_df,
                            publisher_assignment_df)


if __name__ == "__main__":
    main()
