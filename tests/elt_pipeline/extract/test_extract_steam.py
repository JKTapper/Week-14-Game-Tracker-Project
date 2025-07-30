# pylint: skip-file
"""
This module tests functions used during the extraction of steam data via scraping and the api
"""

from src.elt_pipeline.steam_el.extract import get_existing_games, get_steam_game_details, parse_games_bs, iterate_through_scraped_games
from unittest.mock import patch
import requests_mock
import pandas as pd
import awswrangler as wr
import requests as req


@patch('awswrangler.s3.read_parquet')
def test_get_existing_games_success(mock_read_parquet):
    """
    Tests get_existing_games returns correct dataframe on success.
    """
    mock_df = pd.DataFrame({'app_id': [100, 101]})
    mock_read_parquet.return_value = mock_df
    expected_list = ['100', '101']

    result = get_existing_games("s3://fake-bucket/input/", None)

    assert result == expected_list
    mock_read_parquet.assert_called_once()


@patch('awswrangler.s3.read_parquet')
def test_get_existing_games_failure(mock_read_parquet):
    """
    Tests get_existing_games returns empty dataframe on failure.
    """
    mock_read_parquet.side_effect = Exception("No files found")

    result = get_existing_games("s3://fake-bucket/input/", None)

    assert result == []
    mock_read_parquet.assert_called_once()


def test_parse_games_bs_valid_data(example_two_games_html):
    """
    Tests parse_games_bs returns games correctly in a list of dictionaries with correct keys.
    """
    games = parse_games_bs(example_two_games_html)

    assert len(games) == 2

    game1 = games[0]

    assert game1['app_id'] == '10'
    assert game1['title'] == 'Counter-Strike'
    assert game1['release'] == 'Nov 1, 2000'
    assert game1['url'] == 'https://store.steampowered.com/app/10/CounterStrike/'

    game2 = games[1]
    assert game2['app_id'] == '730'
    assert game2['title'] == 'Counter-Strike 2'
    assert game2['release'] == 'Aug 21, 2012'
    assert game2['url'] == 'https://store.steampowered.com/app/730/CS2/'


def test_parse_games_bs_empty_html():
    """
    Tests parse_games_bs returns an empty list when passed an empty html.
    """
    games = parse_games_bs("")

    assert games == []


def test_get_steam_game_details_success(requests_mock, example_steam_api):
    """
    Tests get_steam_game_details returns the correct dict when given valid data.
    """
    app_id = 10
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"

    requests_mock.get(url, json=example_steam_api, status_code=200)

    result = get_steam_game_details(app_id)

    assert result['app_id'] == 10
    assert result['publishers'] == ['Valve']
    assert result['developers'] == ['Valve']
    assert result['description'] == "Play the world's number 1 online action game. Engage in an incredibly realistic brand of terrorist warfare in this wildly popular team-based game. Ally with teammates to complete strategic missions. Take out enemy sites. Rescue hostages. Your role affects your team's success. Your team's success affects your role."
    assert result['requirements'] == {"minimum": "\n\t\t\t\u003Cp\u003E\u003Cstrong\u003EMinimum:\u003C/strong\u003E 500 mhz processor, 96mb ram, 16mb video card, Windows XP, Mouse, Keyboard, Internet Connection\u003Cbr /\u003E\u003C/p\u003E\n\t\t\t\u003Cp\u003E\u003Cstrong\u003ERecommended:\u003C/strong\u003E 800 mhz processor, 128mb ram, 32mb+ video card, Windows XP, Mouse, Keyboard, Internet Connection\u003Cbr /\u003E\u003C/p\u003E\n\t\t\t"}
    assert result['image'] == 'https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/10/header.jpg?t=1745368572'
    assert result['is_free'] == False
    assert result['price'] == 719
    assert result['genres'] == ['Action']


def test_get_steam_game_details_not_found(example_failure_html):
    """
    Tests get_steam_game_details function returns correct error
    """
    with requests_mock.Mocker() as mocker:
        mocker.get("https://store.steampowered.com/api/appdetails?appids=1",
                   json=example_failure_html, status_code=200)
        data = get_steam_game_details(1)
        assert data == {'app_id': 1,
                        'error': 'Data not found or incomplete'}


def test_get_steam_game_details_network_error(requests_mock):
    """
    Tests get_steam_game_details returns the expected error when a network exception occurs.
    """
    app_id = 10
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"

    requests_mock.get(url, exc=req.RequestException("Connection Error"))

    result = get_steam_game_details(app_id)

    assert result == {
        'app_id': 10,
        'error': 'Request failed: Connection Error'
    }


@patch('src.elt_pipeline.steam_el.extract.get_steam_game_details')
def test_iterate_through_scraped_games_success(mock_get_details):
    """
    Tests iterate_through_scraped_games returns the required list of dicts when passed valid data.
    """
    game_list = [
        {'app_id': 10, 'title': 'Game 1', 'release': '2025-01-01'},
        {'app_id': 20, 'title': 'Game 2', 'release': '2025-01-02'}
    ]

    api_details = {
        'publishers': ['Fake Publisher'],
        'description': 'A great game!',
        'is_free': False
    }

    mock_get_details.return_value = api_details

    result = iterate_through_scraped_games(game_list)

    assert mock_get_details.call_count == 2
    mock_get_details.assert_any_call(10)  # Was it called with app_id 10?
    mock_get_details.assert_any_call(20)  # Was it called with app_id 20?

    full_data_game_1 = result[0]
    assert full_data_game_1['app_id'] == 10
    assert full_data_game_1['title'] == 'Game 1'
    assert full_data_game_1['description'] == 'A great game!'
    assert full_data_game_1['release'] == '2025-01-01'
    assert full_data_game_1['publishers'] == ['Fake Publisher']
    assert full_data_game_1['is_free'] == False

    full_data_game_2 = result[1]
    assert full_data_game_2['app_id'] == 20
    assert full_data_game_2['title'] == 'Game 2'
    assert full_data_game_2['description'] == 'A great game!'
    assert full_data_game_2['release'] == '2025-01-02'
    assert full_data_game_2['publishers'] == ['Fake Publisher']
    assert full_data_game_2['is_free'] == False


def test_iterate_through_scraped_games_empty_list():
    """
    Tests iterate_through_scraped_games returns an empty input list when passed an empty list.
    """
    result = iterate_through_scraped_games([])

    assert result == []


@patch('src.elt_pipeline.steam_el.extract.get_steam_game_details')
def test_iterate_skips_items_no_app_id(mock_get_details):
    """
    Tests iterate_through_scraped_games correctly skips items missing an app_id.
    """
    data_with_missing_id = [
        {'app_id': 10, 'title': 'Game A'},
        {'app_id': None, 'title': 'Game with no app_id'}
    ]

    result = iterate_through_scraped_games(data_with_missing_id)

    assert mock_get_details.call_count == 1
    mock_get_details.assert_any_call(10)

    assert len(result) == 1
