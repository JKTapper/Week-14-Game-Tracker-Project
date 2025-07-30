"""
Transforms the data stored in the S3 to
be in the right format to be loaded into the RDS
"""
from os import environ
from datetime import datetime, date
import re
import pandas as pd
import awswrangler as wr
from dotenv import load_dotenv
from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor


BUCKET = 'c18-game-tracker-s3'
S3_PATH = f"s3://{BUCKET}/input/"


def get_db_connection() -> connection:
    """Returns a live connection from the database"""
    load_dotenv()
    conn = connect(
        user=environ["DATABASE_USERNAME"],
        password=environ["DATABASE_PASSWORD"],
        host=environ["DATABASE_IP"],
        port=environ["DATABASE_PORT"],
        database=environ["DATABASE_NAME"],
        cursor_factory=RealDictCursor
    )
    return conn


def read_db_table_into_df(table_name: str) -> pd.DataFrame:
    """Returns the data in an RDS table as a dataframe"""
    conn = None
    try:
        conn = get_db_connection()
        return pd.read_sql(f"SELECT * FROM {table_name}", conn)
    finally:
        if conn is not None:
            conn.close()


def get_reference_data(raw_data: pd.DataFrame,
                       existing_data: pd.DataFrame,
                       table_name: str) -> pd.DataFrame:
    """
    Combines incoming data with old data to create up to date
    dataframe representing secondary tables like genre or developer
    """

    valid_lists = raw_data[table_name +
                           's'].apply(lambda x: isinstance(x, list))
    cleaned_column = raw_data.loc[valid_lists, table_name + 's']
    cleaned_column = sum(cleaned_column, [])

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
                      reference_table: pd.DataFrame,
                      main_table_name: str,
                      reference_table_name: str):
    """
    Returns a pandas dataframe representing the
    assigment table mediating a many to many relationship
    """
    assignment_table_rows = []
    for row in iterrows_dict(main_table):
        for item in row[reference_table_name + 's']:
            assignment_table_rows.append(
                {
                    main_table_name + '_id': row[main_table_name + '_id'],
                    reference_table_name + '_name': item
                }
            )
    assignment_table = pd.DataFrame(assignment_table_rows)
    assignment_table = pd.merge(
        assignment_table,
        reference_table,
        how='inner',
        on=reference_table_name+'_name'
    )
    return assignment_table.drop([reference_table_name + '_name'], axis=1)


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
    return new_dataframe


def extract_memory_requirements(requirements: dict) -> str:
    """
    Extracts the memory requirements from the
    requirements dictionary returned by the API
    """
    if not isinstance(requirements, dict):
        return None
    try:
        match = re.search(
            r'(?<=<strong>Storage:<\\\/strong> ).+?(?= available space)',
            requirements['minimum']
        ).group()
        if match:
            return match
        else:
            return None
    except Exception:
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


STEAM_STORE_ID = 1

GAME_DATA_TRANSLATION = [
    {'old_name': 'release', 'new_name': 'release_date',
        'translation': interpret_release_date},
    {'name': 'description',
        'translation': lambda x: x},
    {'old_name': 'requirements', 'new_name': 'storage_requirements',
        'translation': extract_memory_requirements},
    {'name': 'price',
        'translation': lambda x: int(100*x) if pd.notna(x) else 0},
    {'old_name': 'title', 'new_name': 'game_name',
        'translation': lambda x: x},
    {'name': 'app_id',
        'translation': lambda x: x},
    {'name': 'store_id',
        'value': STEAM_STORE_ID}
]


def transform_s3_steam_data():
    """
    Reads data in the S3, discards any data already in the RDS and
    transforms it into the correct format to be uploaded to the RDS
    """
    raw_df = wr.s3.read_parquet(S3_PATH)
    existing_data = read_db_table_into_df('game')
    new_data = raw_df[~raw_df['app_id'].isin(existing_data['app_id'])]
    game_data = process_data(new_data, GAME_DATA_TRANSLATION)
    game_data["game_id"] = list(range(
        existing_data["game_id"].max() + 1 if not existing_data.empty else 1,
        existing_data["game_id"].max(
        ) + 1 + len(game_data) if not existing_data.empty else 1 + len(game_data)
    ))
    new_data = new_data.copy()
    new_data["game_id"] = game_data["game_id"]

    genres = get_reference_data(
        new_data, read_db_table_into_df('genre'), 'genre')
    publishers = get_reference_data(
        new_data, read_db_table_into_df('publisher'), 'publisher')
    developers = get_reference_data(
        new_data, read_db_table_into_df('developer'), 'developer')

    print("new_data columns:", new_data.columns)

    return {
        'genre': genres['new'],
        'publisher': publishers['new'],
        'developer': developers['new'],
        'genre_assignment': get_assignment_df(new_data, genres['all'], 'game', 'genre'),
        'publisher_assignment': get_assignment_df(new_data, publishers['all'], 'game', 'publisher'),
        'developer_assignment': get_assignment_df(new_data, developers['all'], 'game', 'developer'),
        'game': game_data
    }
