'''Scrapes the gog website for the most recently released
PC games and stores all scraped games in a json list.
Takes json list of newly scraped games, requests data from API
and adds supplementary data to the json list.'''
import logging
import re
from datetime import datetime
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import awswrangler as wr
import boto3

GOG_URL = "https://www.gog.com/en/games/new"
S3_PATH = "s3://c18-game-tracker-s3/input/gog/"


def get_session() -> boto3.Session:
    '''Creates session with credentials in environment'''
    session = boto3.Session()
    creds = session.get_credentials()
    if creds is None:
        raise RuntimeError("Error: AWS credentials not found.")
    return session


def get_existing_games(path: str, session) -> list[str]:
    '''Reads the entire dataset from S3 (partitioned by year/month/day).
    Returns a DataFrame containing existing games' app IDs'''
    try:
        df = wr.s3.read_parquet(path, dataset=True, columns=[
            'app_id'], boto3_session=session)
        return df['app_id'].astype(str).tolist()
    except Exception as e:
        logging.error(f"No existing data found in S3: {e}")
        return []


def get_html(url):
    """
    Gets the html content of the webpage at a given url
    """
    with urlopen(url) as page:
        html_bytes = page.read()
        html = html_bytes.decode("utf_8")
    return html


def extract_game_details(game_page: BeautifulSoup) -> dict[str:str]:
    game_details_list = game_page.find(
        'div', class_="details")
    game_details_rows = game_details_list.find_all(
        'div', recursive=False, class_='table__row')
    details_dict = {}
    for row in game_details_rows[:7]:
        elements = [row.find(class_='details__category'), row.find(
            class_='details__content')]
        row = row.find_all()[:2]
        label, content = [re.sub(r'\s+', ' ', element.get_text()).strip()
                          for element in elements][:2]
        details_dict[label] = content
    return details_dict


def parse_games_bs(html):
    """
    Extracts the games from the gog website
    """
    total = 0
    games = []
    recent_releases_soup = BeautifulSoup(html, "html.parser")
    # only first 12 games have their images load correctly
    for game_tile in recent_releases_soup.find_all('product-tile')[:12]:
        total += 1
        site_game = game_tile.find('a')
        link = site_game.get('href')
        app_id = site_game.get('data-product-id')
        image_block = site_game.find('picture')
        if link and app_id and image_block:
            image_string = image_block.find('source').get('srcset')
            image_url = re.search(
                r'https[^ ,]+?2x\.webp', image_string).group()
            game = {
                'url': link,
                'app_id': app_id,
                'image': image_url
            }
            games.append(game)
        else:
            logging.warning("Game %s not stored", app_id)
    return games


def get_gog_game_details(url: str) -> dict[str]:
    '''Takes the gog store url for a game
    and scrapes taht page for useful data
    Returns dict of useful data'''
    this_game_soup = BeautifulSoup(get_html(url), "html.parser")

    title = this_game_soup.find(
        'h1', class_='productcard-basics__title').get_text().strip()
    price = this_game_soup.find(
        'span', class_='product-actions-price__final-amount').get_text()
    description = this_game_soup.find(
        'div', class_='description')

    game_details = extract_game_details(this_game_soup)
    makers = game_details.get('Company:')
    requirements = game_details.get('Size:')
    release = game_details.get('Release date:')

    release = re.search(r'\d\d\d\d-\d\d-\d\d', release).group()
    release = datetime.strptime(release, '%Y-%m-%d').date()

    if ' / ' in makers:
        developer, publisher = makers.split(' / ')
    else:
        developer, publisher = makers, makers

    price = int(price.replace('.', ''))

    description = re.search(
        r'<p>(\n\w[\s\S]+?)<\/p>', str(description)) or re.search(
        r'<div class="description">([\s\S]+?)<br\/>', str(description))
    description = description.group()
    description = re.sub(r'<.*?>', '', description).replace('\n', '')

    return {
        'publishers': [publisher],
        'developers': [developer],
        'description': description,
        'requirements': requirements,
        'is_free': price == 0,
        'price': price,
        'currency': 'GBP',
        'genres': game_details['Genre:'].split(' - '),
        'title': title,
        'release': release
    }


def iterate_through_scraped_games(json_data: list[dict[str]]):
    '''
    Iterates through list of games and adds on supplementary data into each dict
    '''
    games_full_data = []
    for item in json_data:
        link = item['url']
        if link:
            details = get_gog_game_details(link)
            full_data = item | details
            games_full_data.append(full_data)
    return games_full_data


if __name__ == "__main__":
    main_session = get_session()
    existing_games = get_existing_games(S3_PATH, main_session)

    gog_html = get_html(GOG_URL)
    scraped_games = parse_games_bs(gog_html)
    new_games = [
        new_game for new_game in scraped_games if str(new_game.get("app_id")) not in existing_games]

    full_game_data = iterate_through_scraped_games(new_games)
