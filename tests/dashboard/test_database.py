# pylint: skip-file
from unittest.mock import patch, MagicMock
import pandas as pd
from src.dashboard.database import get_db_connection, fetch_game_data


@patch('src.dashboard.database.psycopg2.connect')
def test_get_db_connection_success(mock_connect):
    """Test that get_db_connection returns a connection when environment is set."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    conn = get_db_connection()

    assert conn == mock_conn


@patch('src.dashboard.database.psycopg2.connect')
def test_get_db_connection_failure(mock_connect):
    """Test get_db_connection raises exception on failed connection."""
    mock_connect.side_effect = Exception("Connection failed")

    try:
        get_db_connection()
    except Exception as e:
        assert str(e) == "Connection failed"


@patch('src.dashboard.database.get_db_connection')
@patch('src.dashboard.database.pd.read_sql')
def test_fetch_game_data_success(mock_read_sql, mock_get_conn):
    """Test that fetch_game_data returns a DataFrame with expected data."""
    mock_conn = MagicMock()
    mock_get_conn.return_value.__enter__.return_value = mock_conn

    fake_df = pd.DataFrame({"game_id": [1], "title": ["Test Game"]})
    mock_read_sql.return_value = fake_df

    result = fetch_game_data("SELECT * FROM games")

    pd.testing.assert_frame_equal(result, fake_df)
    mock_get_conn.assert_called_once()


@patch('src.dashboard.database.get_db_connection')
@patch('src.dashboard.database.pd.read_sql')
def test_fetch_game_data_empty(mock_read_sql, mock_get_conn):
    """Test that fetch_game_data handles empty result."""
    mock_conn = MagicMock()
    mock_get_conn.return_value.__enter__.return_value = mock_conn

    empty_df = pd.DataFrame()
    mock_read_sql.return_value = empty_df

    result = fetch_game_data("SELECT * FROM games WHERE 1=0")

    assert result.empty
