# pylint: skip-file
"""
This module tests functions used during the extraction of gog data via scraping and the api
"""

from src.elt_pipeline.gog_el.extract import get_gog_game_details, parse_games_bs, iterate_through_scraped_games
from unittest.mock import patch
from datetime import date
import requests_mock
import pandas as pd
import awswrangler as wr
import requests as req


def test_gog_parse_games_bs_valid_data(example_gog_new_releases):
    """
    Tests parse_games_bs returns games correctly in a list of dictionaries with correct keys.
    """
    games = parse_games_bs(example_gog_new_releases)

    assert len(games) == 2

    game1, game2 = games

    assert game1['url'] == 'https://www.gog.com/en/game/days_gone_broken_road_dlc'
    assert game1['app_id'] == '1183726056'
    assert game1['image'] == 'https://images.gog-statics.com/43bb2cd8e4dfbe59cba48ec2b98b634cf77a508b4e5d307383f471cf458e554d_product_tile_extended_432x243_2x.webp'

    assert game2['url'] == 'https://www.gog.com/en/game/sengoku_dynasty'
    assert game2['app_id'] == '1414368460'
    assert game2['image'] == 'https://images.gog-statics.com/e2cc56a5c5d0530eaf702cd86133dd1898d0cca4abb18fb8274afc9fdf19ee8f_product_tile_extended_432x243_2x.webp'


def test_gog_parse_games_bs_empty_html():
    """
    Tests parse_games_bs returns an empty list when passed an empty html.
    """
    games = parse_games_bs("")

    assert games == []


def test_get_gog_game_details_success(example_gog_game_page):
    """
    Tests get_steam_game_details returns the correct dict when given valid data.
    """

    result = get_gog_game_details(example_gog_game_page)

    assert result['publishers'] == ['Toplitz Productions']
    assert result['developers'] == ['Superkami']
    assert result['description'] == "Build a life, cultivate your community and start a dynasty in a region once devastated by famine and war. Play solo or in co-op multiplayer and explore a beautiful open world. Gather resources, craft, hunt and build, then automate your village production to survive and grow."
    assert result['requirements'] == '12.7 GB'
    assert result['is_free'] == False
    assert result['price'] == 1750
    assert result['genres'] == ['Adventure', 'Simulation', 'Exploration']
    assert result['title'] == 'Sengoku Dynasty'
    assert result['release'] == date(2024, 11, 7)
