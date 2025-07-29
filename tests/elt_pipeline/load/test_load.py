# pylint: skip-file
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.elt_pipeline.load.load import get_session, add_time_partitioning, upload_to_s3

# Sample input data
SAMPLE_DATA = [
    {"url": "url1", "title": "title1", "release": "28 Jul, 2025"},
    {"url": "url2", "title": "title2", "release": "29 Jul, 2025"},
]


def test_get_session_valid(monkeypatch):
    '''Test that get_session returns a boto3 Session object when valid AWS credentials are available.
    Uses monkeypatch to mock boto3.Session and its credentials.'''
    # Mock credentials
    class DummyCreds:
        def get_frozen_credentials(self):
            return self

    class DummySession:
        def get_credentials(self):
            return DummyCreds()

    monkeypatch.setattr("boto3.Session", lambda: DummySession())
    session = get_session()
    assert session is not None


def test_get_session_error(monkeypatch):
    '''Test that get_session raises a RuntimeError when no AWS credentials are found.
    Mocks boto3.Session to simulate missing credentials.'''
    class DummySession:
        def get_credentials(self):
            return None

    monkeypatch.setattr("boto3.Session", lambda: DummySession())
    with pytest.raises(RuntimeError, match="AWS credentials not found"):
        get_session()


def test_add_time_partitioning():
    '''Tests that add_time_partitioning correctly converts input JSON list to a DataFrame
    and adds year, month, and day columns extracted from the 'release' column.'''
    df = add_time_partitioning(SAMPLE_DATA)
    print(df)
    assert isinstance(df, pd.DataFrame)
    assert "year" in df.columns
    assert "month" in df.columns
    assert "day" in df.columns
    assert df["year"].iloc[0] == 2025
    assert df["month"].iloc[0] == 7
    assert df["day"].iloc[0] == 28


@patch("src.elt_pipeline.load.load.wr.s3.to_parquet")
def test_upload_to_s3_calls_wrangler(mock_to_parquet):
    '''Test that upload_to_s3 calls awswrangler's to_parquet method with correct parameters.
    Uses patch to mock the S3 upload call, avoiding actual S3 interaction.'''
    df = add_time_partitioning(SAMPLE_DATA)
    upload_to_s3(df)

    mock_to_parquet.assert_called_once()
    args, kwargs = mock_to_parquet.call_args

    assert kwargs["dataset"] is True
    assert kwargs["mode"] == "append"
    assert "day" in kwargs["partition_cols"]
