# pylint: skip-file
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

import src.elt_pipeline.epic_el.extract as scraper


def test_get_session_valid_credentials():
    with patch("src.elt_pipeline.epic_el.extract.boto3.Session") as mock_session:
        mock_session.return_value.get_credentials.return_value = True
        session = scraper.get_session()
        assert session is not None


def test_get_session_missing_credentials():
    with patch("src.elt_pipeline.epic_el.extract.boto3.Session") as mock_session:
        mock_session.return_value.get_credentials.return_value = None
        with pytest.raises(RuntimeError):
            scraper.get_session()


def test_get_existing_games_returns_list():
    mock_df = MagicMock()
    mock_df.__getitem__.return_value.astype.return_value.tolist.return_value = [
        'game1', 'game2']
    with patch("src.elt_pipeline.epic_el.extract.wr.s3.read_parquet", return_value=mock_df):
        result = scraper.get_existing_games("dummy-path", MagicMock())
        assert result == ['game1', 'game2']


def test_get_existing_games_handles_error():
    with patch("src.elt_pipeline.epic_el.extract.wr.s3.read_parquet", side_effect=Exception("error")):
        result = scraper.get_existing_games("dummy-path", MagicMock())
        assert result == []


def test_fetch_game_with_release_check_valid_date():
    fake_item = {
        'app_id': 'abc123',
        'url': 'https://store.epicgames.com/en-US/p/fake-game'
    }
    fake_product_map = {'namespace1': 'fake-game'}
    release_date = datetime(2024, 3, 20).isoformat()

    with patch("src.elt_pipeline.epic_el.extract.get_epic_game_details", return_value={
        'app_id': 'abc123',
        'release': release_date,
        'publishers': [],
        'developers': [],
        'description': '',
        'requirements': {'minimum': None},
        'is_free': False,
        'price': 999,
        'currency': 'USD',
        'genres': [],
        'image': ''
    }):
        result = scraper.fetch_game_with_release_check(
            fake_item, fake_product_map, datetime(2024, 3, 20).date())
        assert result is not None
        assert result['app_id'] == 'abc123'


def test_fetch_game_with_release_check_invalid_date():
    fake_item = {
        'app_id': 'abc123',
        'url': 'https://store.epicgames.com/en-US/p/fake-game'
    }
    fake_product_map = {'namespace1': 'fake-game'}

    with patch("src.elt_pipeline.epic_el.extract.get_epic_game_details", return_value={'release': '2022-01-01T00:00:00.000Z', 'app_id': 'abc123'}):
        result = scraper.fetch_game_with_release_check(
            fake_item, fake_product_map, datetime(2024, 3, 20).date())
        assert result is None
