# pylint: disable=line-too-long
"""Script to take transformed data and stores into our RDS Postgres Database"""
import os
import logging
from datetime import datetime, date
import re
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text, Engine
import awswrangler as wr
from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
import numpy as np

BUCKET = 'c18-game-tracker-s3'
S3_PATH = f"s3://{BUCKET}/input/"

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_db_connection() -> connection:
    """Returns a live connection from the database"""
    load_dotenv()
    conn = connect(
        user=os.environ["DATABASE_USERNAME"],
        password=os.environ["DATABASE_PASSWORD"],
        host=os.environ["DATABASE_IP"],
        port=os.environ["DATABASE_PORT"],
        database=os.environ["DATABASE_NAME"],
        cursor_factory=RealDictCursor
    )
    return conn


def read_db_table_into_df(table_name: str, conn) -> pd.DataFrame:
    """Returns the data in an RDS table as a dataframe"""
    return pd.read_sql(f"SELECT * FROM {table_name}", conn)


def get_reference_data(raw_data: pd.DataFrame,
                       existing_data: pd.DataFrame,
                       table_name: str) -> pd.DataFrame:
    """
    Combines incoming data with old data to create up to date
    dataframe representing secondary tables like genre or developer
    """
    id_col = f"{table_name}_id"

    if id_col in existing_data.columns:
        existing_data[id_col] = (
            pd.to_numeric(existing_data[id_col], errors='coerce')
              .fillna(0)
              .astype(int)
        )
    else:
        existing_data[id_col] = pd.Series(dtype=int)

    valid_lists = raw_data[table_name +
                           's'].apply(lambda x: isinstance(x, (list, np.ndarray)))
    cleaned_column = raw_data.loc[valid_lists, table_name + 's']
    cleaned_column = [
        item for sublist in cleaned_column for item in sublist]

    new_data = list(set(cleaned_column))

    added_data = list(
        filter(lambda x: not x in existing_data[table_name + '_name'].unique(), new_data))
    highest_existing_id = max(existing_data[table_name + '_id'], default=0)
    data_to_add_to_rds = pd.DataFrame({
        table_name + '_name': added_data,
        table_name + '_id': list(range(
            highest_existing_id + 1,
            highest_existing_id + len(added_data) + 1
        ))
    })

    return {
        'new': data_to_add_to_rds,
        'all': pd.concat([existing_data, data_to_add_to_rds])
    }


def iterrows_dict(df: pd.DataFrame) -> dict:
    """
    Allows you to iterate through the rows of a
    pandas dataframe and get each row as a dictionary
    """
    columns = list(df.columns)
    for row in df.itertuples(index=False):
        yield {columns[i]: row[i] for i in range(len(columns))}


def get_assignment_df(main_table: pd.DataFrame,
                      main_table_name: str,
                      reference_table_name: str,
                      conn):
    """
    Returns a pandas dataframe representing the
    assigment table mediating a many to many relationship
    """
    assignment_table_rows = []
    for row in iterrows_dict(main_table):
        for item in row[reference_table_name + 's']:
            reference_id = get_or_create_id(
                conn,
                table=reference_table_name,
                name_col=f"{reference_table_name}_name",
                name_val=item,
                id_col=f"{reference_table_name}_id"
            )
            assignment_table_rows.append(
                {
                    main_table_name + '_id': row[main_table_name + '_id'],
                    reference_table_name + '_id': reference_id
                }
            )
    if not assignment_table_rows:
        return pd.DataFrame({
            main_table_name + '_id': [],
            reference_table_name + '_id': []
        })
    return pd.DataFrame(assignment_table_rows)


def process_data(old_dataframe: pd.DataFrame,
                 columns: list[dict],) -> pd.DataFrame:
    """Returns a dataframe with the specified columns"""
    new_dataframe = pd.DataFrame()
    for column in columns:
        if 'name' in column:
            name = column['name']
            column['old_name'], column['new_name'] = name, name
        if 'translation' in column:
            new_dataframe[column['new_name']] = old_dataframe[column['old_name']].apply(
                column['translation'])
        elif 'value' in column:
            new_dataframe[column['new_name']] = column['value']
        logging.info("%s collumn transformed", column['new_name'])
    return new_dataframe


def extract_memory_requirements(requirements: dict) -> str:
    """
    Extracts the memory requirements from the
    requirements dictionary returned by the API
    """
    if not isinstance(requirements, dict):
        return None
    try:
        requirements_string = requirements['minimum']
        match = re.search(
            r'(?<=<strong>Storage:<\/strong> ).+?(?= available space)', requirements_string).group()
        if match:
            return match
        return None
    except Exception as e:
        logging.error(e)
        return None


def interpret_release_date(release_date: str) -> date:
    """
    Interprets the release date as a date object
    """
    if isinstance(release_date, (datetime, pd.Timestamp)):
        return release_date.date()
    try:
        return datetime.strptime(release_date, '%d %b, %Y').date()
    except ValueError:
        return None


GAME_DATA_TRANSLATION_BASE = [
    {'old_name': 'release', 'new_name': 'release_date',
        'translation': interpret_release_date},
    {'name': 'description',
        'translation': lambda x: x},
    {'name': 'price',
        'translation': lambda x: x if pd.notna(x) else 0},
    {'old_name': 'title', 'new_name': 'game_name',
        'translation': lambda x: x},
    {'name': 'app_id',
        'translation': lambda x: x},
    {'name': 'currency',
        'translation': lambda x: 'GBP' if pd.isna(x) else x},
    {'old_name': 'image', 'new_name': 'image_url',
        'translation': lambda x: x}
]


def get_game_id(count: int) -> list[int]:
    """Gets current game ids from database to help merge assignment tables"""
    conn = get_db_connection()

    try:
        cur = conn.cursor(cursor_factory=None)
        cur.execute(f"""
            SELECT nextval(pg_get_serial_sequence('game','game_id'))
            FROM generate_series(1, %s)
        """, (count,))

        rows = cur.fetchall(
        )

        new_ids = [row["nextval"] for row in rows]
    finally:
        conn.close()

    return new_ids


def transform_s3_steam_data(conn, store: dict[str]) -> dict[str:pd.DataFrame]:
    """
    Reads data in the S3, discards any data already in the RDS and
    transforms it into the correct format to be uploaded to the RDS
    """
    try:
        raw_df = wr.s3.read_parquet(S3_PATH + store['store_name'])
    except Exception as e:
        logging.error('Error reading S3 path %s: %s',
                      S3_PATH + store['store_name'], e)
        return {
            'genre': pd.DataFrame(),
            'publisher': pd.DataFrame(),
            'developer': pd.DataFrame(),
            'genre_assignment': pd.DataFrame(),
            'publisher_assignment': pd.DataFrame(),
            'developer_assignment': pd.DataFrame(),
            'game': pd.DataFrame()
        }
    raw_df['app_id'] = raw_df['app_id'].apply(store['app_id_method'])
    logging.info("Data about %s %s games downloaded from S3",
                 len(raw_df), store['store_name'])

    existing_data = read_db_table_into_df('game', conn)
    existing_data['game_id'] = pd.to_numeric(
        existing_data['game_id'], errors='coerce').fillna(0).astype(int)
    logging.info("Data about %s games downloaded from RDS", len(existing_data))
    new_data = raw_df[~raw_df['app_id'].isin(existing_data['app_id'])].copy()
    logging.info("%s new games identified", len(new_data))

    store_translation = [
        {'old_name': 'requirements', 'new_name': 'storage_requirements',
         'translation': store['requirments_method']},
        {'name': 'store_id',
         'value': store['store_id']}
    ] + GAME_DATA_TRANSLATION_BASE

    game_data = process_data(new_data, store_translation)
    logging.info("Game data transformed")

    new_ids = get_game_id(len(new_data))
    new_data["game_id"] = new_ids

    game_data["game_id"] = new_ids

    genres = get_reference_data(
        new_data, read_db_table_into_df('genre', conn), 'genre')
    logging.info("Genre table generated")
    publishers = get_reference_data(
        new_data, read_db_table_into_df('publisher', conn), 'publisher')
    logging.info("Publisher table generated")
    developers = get_reference_data(
        new_data, read_db_table_into_df('developer', conn), 'developer')
    logging.info("Developer table generated")

    genre_assignment_df = get_assignment_df(
        new_data, 'game', 'genre', conn)
    logging.info("Genre asssignment table generated")
    publisher_assignment_df = get_assignment_df(
        new_data, 'game', 'publisher', conn)
    logging.info("Publisher asssignment table generated")
    developer_assignment_df = get_assignment_df(
        new_data, 'game', 'developer', conn)
    logging.info("Developer asssignment table generated")

    return {
        'genre': genres['new'],
        'publisher': publishers['new'],
        'developer': developers['new'],
        'genre_assignment': genre_assignment_df,
        'publisher_assignment': publisher_assignment_df,
        'developer_assignment': developer_assignment_df,
        'game': game_data
    }


load_dotenv()

DB_URL = (
    f"postgresql+psycopg2://{os.getenv('DATABASE_USERNAME')}"
    f":{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_IP')}"
    f":{os.getenv('DATABASE_PORT', 5432)}/{os.getenv('DATABASE_NAME')}"
)


def get_engine() -> Engine:
    """Connects and returns engine to function"""

    return create_engine(DB_URL, future=True)


def upload_table(conn, df: pd.DataFrame, table: str, col: str) -> None:
    """Insert each value of df to database"""

    sql = text(f"""
        INSERT INTO {table} ({col})
        VALUES (:name)
        ON CONFLICT ({col}) DO NOTHING
    """)

    for _, row in df.iterrows():
        conn.execute(sql, {
            "name": row[col],
        })
    logging.info("%s table uploaded", table)


def upload_games(conn, games_df: pd.DataFrame) -> None:
    """INSERT games to games table"""

    sql = text("""
        INSERT INTO game (
          game_id, game_name, app_id, store_id, release_date, image_url, 
          game_description, storage_requirements, price, currency
        ) VALUES (
          :game_id, :game_name, :app_id, :store_id, :release_date, :image_url, 
          :game_description, :storage_requirements, :price, :currency
        )
        ON CONFLICT (app_id) DO NOTHING
    """)

    for _, row in games_df.iterrows():
        conn.execute(sql, {
            "game_id": row["game_id"],
            "game_name": row["game_name"],
            "app_id": row["app_id"],
            "store_id": row["store_id"],
            "release_date": row["release_date"],
            "image_url": row["image_url"],
            "game_description": row["description"],
            "storage_requirements": row["storage_requirements"],
            "price": row["price"],
            "currency": row["currency"],
        })


def upload_assignments(conn, df: pd.DataFrame,
                       table: str,
                       left_foreign_key: str,
                       right_foreign_key: str) -> None:
    """Generic function to help with genre, publisher and developer assignment"""
    sql = text(f"""
        INSERT INTO {table} ({left_foreign_key}, {right_foreign_key})
        VALUES (:l, :r)
        ON CONFLICT DO NOTHING
    """)

    for _, row in df.iterrows():
        conn.execute(
            sql, {"l": int(row[left_foreign_key]), "r": int(row[right_foreign_key])})
    logging.info("%s table uploaded", table)


def get_existing_game_ids(conn) -> set[int]:
    """Gets set of all existing game ids"""
    result = conn.execute(text("SELECT game_id FROM game"))
    return set(row[0] for row in result.fetchall())


def get_or_create_id(conn, table: str, name_col: str, name_val: str, id_col: str) -> int:
    """Insert a name into a lookup table if it doesn't exist, then return its ID."""
    insert_sql = text(f"""
        INSERT INTO {table} ({name_col})
        VALUES (:name_val)
        ON CONFLICT ({name_col}) DO NOTHING;
    """)
    conn.execute(insert_sql, {"name_val": name_val})

    select_sql = text(f"""
        SELECT {id_col}
        FROM {table}
        WHERE {name_col} = :name_val;
    """)
    result = conn.execute(select_sql, {"name_val": name_val}).fetchone()

    return result[0]


def load_data_into_database(conn, games_df: pd.DataFrame,
                            publisher_df: pd.DataFrame,
                            developer_df: pd.DataFrame,
                            genre_df: pd.DataFrame,
                            genre_assignment_df,
                            developer_assignment_df,
                            publisher_assignment_df) -> None:
    """Loads all data into our database"""

    games_df["app_id"] = games_df["app_id"].astype(int)
    games_df["price"] = games_df["price"].astype(int)

    upload_table(conn, publisher_df, "publisher",
                 "publisher_name")
    upload_table(conn, developer_df, "developer",
                 "developer_name")
    upload_table(conn, genre_df, "genre", "genre_name")

    upload_games(conn, games_df)
    logging.info("game table uploaded")

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


stores = [
    {
        'store_name': 'steam',
        'store_id': 1,
        'app_id_method': int,
        'requirments_method': extract_memory_requirements
    },
    {
        'store_name': 'epic',
        'store_id': 2,
        'app_id_method': lambda x: int(x, 16),
        'requirments_method': lambda x: x
    },
    {
        'store_name': 'gog',
        'store_id': 3,
        'app_id_method': int,
        'requirments_method': lambda x: x
    }
]


def main():
    """Main to run other functions"""
    engine = get_engine()
    for store in stores:
        with engine.connect() as conn:
            with conn.begin():
                data = transform_s3_steam_data(conn, store)
                if data['game'].empty:
                    logging.warning(
                        "No new game data for %s, skipping upload.", store)
                    continue
                load_data_into_database(
                    conn, data["game"], data["publisher"],
                    data["developer"], data["genre"],
                    data["genre_assignment"],
                    data["developer_assignment"],
                    data["publisher_assignment"]
                )


if __name__ == "__main__":
    main()
