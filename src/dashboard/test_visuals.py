# pylint: skip-file
import pandas as pd
from unittest.mock import patch
from src.dashboard.visuals import find_mean_price, find_new_release_count, find_free_count


@patch("src.dashboard.visuals.fetch_game_data")
def test_find_mean_price(mock_fetch):
    """Test price formatting is correct from database"""
    mock_fetch.return_value = pd.DataFrame({"avg_price": [799]})

    result = find_mean_price('')

    assert result == "£7.99"
    mock_fetch.assert_called_once()


@patch("src.dashboard.visuals.fetch_game_data")
def test_find_mean_price_none(mock_fetch):
    """Test mean price returns 'N/A' if no result"""
    mock_fetch.return_value = pd.DataFrame({"avg_price": [None]})

    result = find_mean_price('')

    assert result == "N/A"
    mock_fetch.assert_called_once()


@patch("src.dashboard.visuals.fetch_game_data")
def test_find_new_release_count(mock_fetch):
    """Test new release count query with a range of days"""
    mock_fetch.return_value = pd.DataFrame({"game_count": [5]})

    result = find_new_release_count(30, '')

    assert result == 5
    # Check query includes correct interval
    assert "30 days" in mock_fetch.call_args[0][0]
    mock_fetch.assert_called_once()


@patch("src.dashboard.visuals.fetch_game_data")
def test_find_free_count(mock_fetch):
    """Test counting free games"""
    mock_fetch.return_value = pd.DataFrame({"free_count": [12]})

    result = find_free_count('')

    pd.testing.assert_series_equal(result, pd.Series([12], name="free_count"))
    mock_fetch.assert_called_once()
