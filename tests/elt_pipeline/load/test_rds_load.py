# pylint: skip-file

from pathlib import Path
import pytest
import pandas as pd
from sqlalchemy import create_engine, text
import src.elt_pipeline.load.load_to_rds as loader


@pytest.fixture
def temp_engine():
    engine = create_engine("sqlite:///:memory:")

    schema_path_sql = Path("src/schema/test_schema.sql").read_text()

    conn = engine.raw_connection()
    with conn:
        conn.executescript(schema_path_sql)

    return engine


def fake_data():
    games_df = pd.DataFrame([{
        "game_name": "Test Game",
        "app_id": 42,
        "store_name": "steam",
        "release_date": "2025-07-30",
        "game_description": "A test",
        "recent_reviews_summary": "Mostly positive",
        "os_requirements": "Any",
        "storage_requirements": "5GB",
        "price": 12.34,
        "genres": ["Indie"],
        "developers": ["Developer Company"],
        "publishers": ["Publisher Company"],
    }])

    publisher_df = pd.DataFrame([{"publisher_name": "Publisher Company"}])
    developer_df = pd.DataFrame([{"developer_name": "Developer Company"}])
    genre_df = pd.DataFrame([{"genre_name": "Indie"}])

    return games_df, publisher_df, developer_df, genre_df


def test_load_data_into_database(monkeypatch, temp_engine):
    monkeypatch.setattr(loader, "get_engine", lambda: temp_engine)

    games_df, publisher_df, developer_df, genre_df = fake_data()

    loader.load_data_into_database(
        games_df, publisher_df, developer_df, genre_df)

    with temp_engine.connect() as conn:
        expected_counts = {
            "store": 1,
            "publisher": 1,
            "developer": 1,
            "genre": 1,
            "game": 1,
            "genre_assignment": 1,
            "developer_assignment": 1,
            "publisher_assignment": 1,
        }

        for table, expected in expected_counts.items():
            count = conn.execute(
                text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            assert count == expected, f"Expected {expected} row(s) in {table}, found {count}"
