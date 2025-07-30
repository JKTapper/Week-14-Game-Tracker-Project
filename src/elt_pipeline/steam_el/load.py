'''Receiving json and upload to S3, time-partitioning by day'''
import boto3
import pandas as pd
import awswrangler as wr

BUCKET = 'c18-game-tracker-s3'
S3_PATH = f"s3://{BUCKET}/input/"


def get_session() -> boto3.Session:
    '''Creates session with credentials in environment'''
    session = boto3.Session()
    creds = session.get_credentials()
    if creds is None:
        raise RuntimeError("Error: AWS credentials not found.")
    return session


def add_time_partitioning(data: list[dict[str]]) -> pd.DataFrame:
    '''Converts json to dataframe and adds Y/M/D columns'''
    df = pd.DataFrame(data)
    df['release'] = pd.to_datetime(df['release'])

    df['year'] = df['release'].dt.year
    df['month'] = df['release'].dt.month
    df['day'] = df['release'].dt.day
    return df


def upload_to_s3(df: pd.DataFrame):
    '''Uses awswrangler to upload dataframe as a parquet file to S3 bucket'''
    wr.s3.to_parquet(
        df=df,
        path=S3_PATH,
        dataset=True,
        mode="append",
        partition_cols=["year", "month", "day"]
    )
    print(f"Uploaded to {S3_PATH}")
