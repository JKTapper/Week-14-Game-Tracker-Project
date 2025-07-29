"""
Transofrms the data stored in the S3 to
be in the right form to beloaded into the RDS
"""
from os import environ
import pandas as pd
import awswrangler as wr
from dotenv import load_dotenv
from psycopg2 import connect
from psycopg2.errors import SyntaxError
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor


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
    try:
        conn = get_db_connection()
        return pd.read_sql(f"SELECT * FROM {table_name}", conn)
    except Exception as e:
        print(e)
    finally:
        conn.close()


def get_reference_data(raw_data: pd.DataFrame, table_name: str) -> pd.DataFrame:
    existing_data = read_db_table_into_df(table_name)
    new_data = list(set(sum(raw_data[table_name])))
    added_data = [
        datum for datum in new_data if datum not in existing_data['table_name'].apply(lambda x: x+'_name')]
    highest_existing_id = max(existing_data[table_name + '_id'])
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


def transform_s3_steam_data():
    raw_df = wr.s3.read_parquet()
    genres = get_reference_data('genre')
    publishers = get_reference_data('publisher')
    developers = get_reference_data('developer')
    return {
        'genre': genres['new'],
        'publisher': publishers['new'],
        'developer': developers['new']
    }
