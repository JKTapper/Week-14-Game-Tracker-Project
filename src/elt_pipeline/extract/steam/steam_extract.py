'''Scrapes the steam website for the most recently released
PC games and stores all scraped games in a json list.
Takes json list of newly scraped games, requests data from API
and adds supplementary data to the json list.'''
import json
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import pandas as pd
import awswrangler as wr

BUCKET = 'c18-game-tracker-s3'
S3_PATH = f"s3://{BUCKET}/input/"
STEAM_URL = "https://store.steampowered.com/search/?sort_by=Released_DESC&supportedlang=english"


def get_existing_games(path) -> pd.DataFrame:
    '''Reads the entire dataset from S3 (partitioned by year/month/day).
    Returns a DataFrame containing existing games' app IDs'''
    try:
        df = wr.s3.read_parquet(path, dataset=True, columns=['app_id'])
        return df
    except Exception as e:
        print("No existing data found in S3:", e)
        return pd.DataFrame()


def get_html(url):
    """
    Gets the html content of the webpage at a given url
    """
    with urlopen(url) as page:
        html_bytes = page.read()
        html = html_bytes.decode("utf_8")
    return html


def parse_games_bs(html):
    """
    Extracts the games from the steam website
    """
    games = []
    soup = BeautifulSoup(html, "html.parser")
    a_tags = soup.find_all('a')
    for a_tag in a_tags:
        link = a_tag.get('href')
        if 'https://store.steampowered.com/app' in link:
            title = a_tag.find('span').get_text()
            release_date = a_tag.find(
                'div', class_='col search_released responsive_secondrow').get_text().strip()
            game = {
                'url': link,
                'title': title,
                'release': release_date
            }
            games.append(game)
    return games


if __name__ == "__main__":
    existing_games = get_existing_games(S3_PATH)

    steam_html = get_html(STEAM_URL)
    scraped_games = parse_games_bs(steam_html)[0:5]  # first 5 only
    new_games = [
        new_game for new_game in scraped_games if str(new_game.get("id")) not in existing_games]
    print(new_games)
