"""Script to take transformed data and stores into our RDS Postgres Database"""

import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, Engine, text, Connection

from src.elt_pipeline.transform.transform import transform_s3_steam_data


load_dotenv()
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = int(os.getenv("DB_PORT"))


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
                            genre_df: pd.DataFrame) -> None:
    """Takes data and loads it into each table"""

    if "store_name" in games_df.columns:
        stores_df = games_df[["store_name"]].dropna(
        ).drop_duplicates().reset_index(drop=True)
    else:
        stores_df = pd.DataFrame(columns=["store_name"])

    engine = get_engine()

    with engine.begin() as conn:

        store_cache = upload_stores(conn, stores_df)

        publisher_cache = upload_references_to_games(
            conn, publisher_df, "publisher_name", "publisher", "publisher_id")
        developer_cache = upload_references_to_games(
            conn, developer_df, "developer_name", "developer", "developer_id")
        genre_cache = upload_genres(conn, genre_df)
        game_cache = games_upload(conn, store_cache, games_df)

        genre_links = []
        developer_links = []
        publisher_links = []

        for _, row in games_df.iterrows():
            game_id = game_cache[row["app_id"]]

            for genre in row.get("genres", []):
                genre_id = genre_cache.get(genre)
                if genre_id is not None:
                    genre_links.append((genre_id, game_id))

            for dev in row.get("developers", []):
                dev_id = developer_cache.get(dev)
                if dev_id is not None:
                    developer_links.append((dev_id, game_id))

            for pub in row.get("publishers", []):
                pub_id = publisher_cache.get(pub)
                if pub_id is not None:
                    publisher_links.append((pub_id, game_id))

        upload_links(
            conn, "genre_assignment", "genre_id", "game_id", genre_links)
        upload_links(conn, "developer_assignment",
                     "developer_id", "game_id", developer_links)
        upload_links(conn, "publisher_assignment",
                     "publisher_id", "game_id", publisher_links)


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


def upload_references_to_games(conn: Connection,
                               df: pd.DataFrame,
                               col: str,
                               table_name: str,
                               pk_name: str) -> dict:
    """Helps with loading into publisher, developer tables"""

    for _, row in df.iterrows():
        conn.execute(text(f"""
            INSERT INTO {table_name} ({col})
            VALUES (:name)
            ON CONFLICT ({col}) DO NOTHING
            """), {
            "name": row[col]
        }
        )

    rows = conn.execute(text(f"""
        SELECT {col}, {pk_name}
          FROM {table_name}
    """)).mappings()

    return {r[col]: r[pk_name] for r in rows}


def games_upload(conn: Connection, store_cache: dict, games_df: pd.DataFrame) -> dict:
    """Uploads games to games tables and returns game_id cache"""
    for _, row in games_df.iterrows():

        default_store_id = store_cache["steam"]

        store_name = row.get(
            "store_name") if "store_name" in games_df.columns else None
        store_id = store_cache.get(store_name, default_store_id)

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
                "store": store_id,
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


def upload_genres(conn: Connection, genre_df: pd.DataFrame) -> dict:
    """Insert genres and return genre  cache."""
    for _, row in genre_df.iterrows():
        conn.execute(text("""
            INSERT INTO genre (genre_name)
            VALUES (:name)
            ON CONFLICT (genre_name) DO NOTHING
        """), {"name": row["genre_name"]})

    rows = conn.execute(
        text("SELECT genre_name, genre_id FROM genre")).mappings()
    return {row["genre_name"]: row["genre_id"] for row in rows}


def upload_links(conn: Connection,
                 table_name: str,
                 left_col: str,
                 right_col: str,
                 data: list[tuple]) -> None:
    """Insert pairs into the joint tables"""

    for left_id, right_id in data:
        conn.execute(text(f"""
            INSERT INTO {table_name} ({left_col}, {right_col})
            VALUES (:left, :right)
            ON CONFLICT DO NOTHING
        """), {"left": left_id, "right": right_id})


def main() -> None:
    """Main to run other functions"""

    data = transform_s3_steam_data()

    games_df = data["game"]
    games_df["app_id"] = games_df["app_id"].astype(int)
    games_df["price"] = games_df["price"].astype(float)

    publisher_df = data["publisher"]
    developer_df = data["developer"]
    genre_df = data["genre"]

    load_data_into_database(games_df,
                            publisher_df,
                            developer_df,
                            genre_df)


if __name__ == "__main__":
    main()
