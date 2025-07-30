"""Script to take transformed data and stores into our RDS Postgres Database"""
import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, engine, Engine, text, Connection

load_dotenv()
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = int(os.getenv("DB_PORT"))
# DB_SCHEMA = os.getenv("DB_SCHEMA")


def get_engine() -> engine:
    """Connects to RDS Postgres instance"""
    url = (
        f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine = create_engine(url, future=True)

    return engine


def load_data_into_database(full_df: pd.DataFrame, drop_table: bool = False) -> None:
    """Takes data and loads it into each table"""
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
    )

    assign_developers = (
        full_df[["game_name", "developer"]]
        .dropna()
        .drop_duplicates()
    )

    assign_publishers = (
        full_df[["game_name", "publisher"]]
        .dropna()
        .drop_duplicates()
    )

    with engine.begin() as conn:
        store_cache = upload_stores(conn, stores_df)
        publisher_cache = upload_references_to_games(
            conn, publisher_df, "publisher", "publisher", "publisher_id")
        dev_cache = upload_references_to_games(
            conn, developer_df, "developer", "developer", "developer_id")
        genre_cache = upload_references_to_games(
            conn, genre_df,     "genre",     "genre",     "genre_id")
        games_cache = games_upload(conn, games_df, store_cache)

        for _, row in assign_genres.iterrows():
            conn.execute(
                text("""
                INSERT INTO genre_assignment (genre_id, game_id)
                VALUES (:g_id, :gm_id)
                ON CONFLICT DO NOTHING
                """),
                {"g_id": genre_cache[row["genre"]],
                 "gm_id": games_cache[row["app_id"]]},
            )
        for _, row in assign_developers.iterrows():
            conn.execute(
                text("""
                INSERT INTO developer_assignment (developer_id, game_id)
                VALUES (:d_id, :gm_id)
                ON CONFLICT DO NOTHING
                """),
                {"d_id": dev_cache[row["developer"]],
                 "gm_id": games_cache[row["app_id"]]},
            )
        for _, row in assign_publishers.iterrows():
            conn.execute(
                text("""
                INSERT INTO publisher_assignment (publisher_id, game_id)
                VALUES (:p_id, :gm_id)
                ON CONFLICT DO NOTHING
                """),
                {"p_id": publisher_cache[row["publisher"]],
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
        f"SELECT {col}_name, {pk_name} FROM {table_name}"
    ))

    return {row[col + "_name"]: getattr(row, pk_name) for row in rows}


def games_upload(conn: Connection, store_cache: dict, games_df: pd.DataFrame) -> dict:
    """Uploads games to games tables and returns game_id cache"""
    for _, row in games_df.iterrows():
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
                "store": store_cache[row["store_name"]],
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
    fake = pd.DataFrame([
        {
            "game_name": "Test Game A",
            "app_id": 111, "store_name": "steam",
            "release_date": "2025-01-01",
            "game_description": "…", "recent_reviews_summary": "…",
            "os_requirements": "…", "storage_requirements": "…",
            "price": 9.99, "genre": "Indie",
            "developer": "DevCo", "publisher": "PubCo"
        },
        {
            "game_name": "Test Game B",
            "app_id": 222, "store_name": "gog",
            "genre": "RPG", "developer": "DevCo",
            "publisher": "PubCo"
        },
    ])

    # data = ...  #  From transform script

    full_df = pd.DataFrame.from_records(fake)

    load_data_into_database(full_df)


if __name__ == "__main__":
    main()
