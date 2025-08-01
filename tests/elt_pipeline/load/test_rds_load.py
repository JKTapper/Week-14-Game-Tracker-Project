# pylint: skip-file

from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from unittest.mock import MagicMock, patch
import src.elt_pipeline.steam_tl.transform_and_load_to_rds as loader


games_df = pd.DataFrame({
    "game_id": [1],
    "game_name": ["Game A"],
    "app_id": [123],
    "store_id": 1,
    'storage_requirements': 'idk',
    "release_date": ["2023-01-01"],
    "description": ["Description A"],
    "price": [1999],
    "currency": "GDP",
})

publisher_df = pd.DataFrame({
    "publisher_id": [1],
    "publisher_name": ["Publisher A"]
})

developer_df = pd.DataFrame({
    "developer_id": [1],
    "developer_name": ["Developer A"]
})

genre_df = pd.DataFrame({
    "genre_id": [1],
    "genre_name": ["Genre A"]
})

genre_assignment_df = pd.DataFrame({
    "genre_id": [1],
    "game_id": [123]
})

developer_assignment_df = pd.DataFrame({
    "developer_id": [1],
    "game_id": [123]
})

publisher_assignment_df = pd.DataFrame({
    "publisher_id": [1],
    "game_id": [123]
})

assignment_df = pd.DataFrame({
    "genre_id": [1],
    "game_id": [123]
})


def test_upload_table_calls_execute_with_correct_sql():
    conn = MagicMock()
    df = pd.DataFrame({"publisher_id": [1], "publisher_name": ["Pub1"]})
    loader.upload_table(conn, df, "publisher",
                        "publisher_name", "publisher_id")

    assert conn.execute.call_count == len(df)
    args, kwargs = conn.execute.call_args
    params = args[1]
    assert "INSERT INTO publisher" in str(args[0])
    assert params["id"] == 1
    assert params["name"] == "Pub1"


def test_upload_games_executes_correctly():
    conn = MagicMock()
    loader.upload_games(conn, games_df)

    assert conn.execute.call_count == len(games_df)
    args, kwargs = conn.execute.call_args
    params = args[1]
    assert "INSERT INTO game" in str(args[0])
    assert params["game_name"] == "Game A"
    assert params["app_id"] == 123
    assert params["price"] == 1999


def test_upload_assignments_executes_correctly():
    conn = MagicMock()
    loader.upload_assignments(conn, assignment_df,
                              "genre_assignment", "genre_id", "game_id")

    assert conn.execute.call_count == len(assignment_df)
    args, kwargs = conn.execute.call_args
    params = args[1]
    assert "INSERT INTO genre_assignment" in str(args[0])
    assert params["l"] == 1
    assert params["r"] == 123


@patch("src.elt_pipeline.steam_tl.transform_and_load_to_rds.get_engine")
@patch("src.elt_pipeline.steam_tl.transform_and_load_to_rds.transform_s3_steam_data")
def test_load_data_into_database_calls_all_uploads(mock_transform, mock_get_engine):
    mock_transform.return_value = {
        "genre_assignment": genre_assignment_df,
        "developer_assignment": developer_assignment_df,
        "publisher_assignment": publisher_assignment_df,
    }

    mock_conn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.begin.return_value.__enter__.return_value = mock_conn
    mock_get_engine.return_value = mock_engine

    loader.load_data_into_database(
        games_df, publisher_df, developer_df, genre_df, genre_assignment_df, developer_assignment_df, publisher_assignment_df)

    assert mock_conn.execute.call_count > 0


def test_get_engine_returns_engine_instance():
    engine = loader.get_engine()

    from sqlalchemy.engine import Engine

    assert isinstance(engine, Engine)
