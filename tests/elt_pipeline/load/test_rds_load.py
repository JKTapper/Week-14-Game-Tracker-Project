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
    }])

    publisher_df = pd.DataFrame([{"publisher_name": "Publisher Company"}])
    developer_df = pd.DataFrame([{"developer_name": "Developer Company"}])
    genre_df = pd.DataFrame([{"genre_name": "Indie"}])

    genre_assignment_df = pd.DataFrame([{
        "genre_name": "Indie",
        "app_id": 42
    }])
    developer_assignment_df = pd.DataFrame([{
        "developer_name": "Developer Company",
        "app_id": 42
    }])
    publisher_assignment_df = pd.DataFrame([{
        "publisher_name": "Publisher Company",
        "app_id": 42
    }])

    return (
        games_df,
        publisher_df,
        developer_df,
        genre_df,
        genre_assignment_df,
        developer_assignment_df,
        publisher_assignment_df,
    )


def test_load_data_into_database(monkeypatch, temp_engine):
    monkeypatch.setattr(loader, "get_engine", lambda: temp_engine)

    data = fake_data()

    loader.load_data_into_database(*data)

    with temp_engine.connect() as conn:
        for table in [
            "store",
            "publisher",
            "developer",
            "genre",
            "game",
            "genre_assignment",
            "developer_assignment",
            "publisher_assignment",
        ]:
            count = conn.execute(
                text(f"SELECT COUNT(*) FROM {table}")).scalar_one()

            assert count == 1, f"Expected 1 row in {table}, found {count}"
