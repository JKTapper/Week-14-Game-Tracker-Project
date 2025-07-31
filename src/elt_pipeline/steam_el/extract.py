'''Scrapes the steam website for the most recently released
PC games and stores all scraped games in a json list.
Takes json list of newly scraped games, requests data from API
and adds supplementary data to the json list.'''
import logging
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import awswrangler as wr
import boto3

STEAM_URL = "https://store.steampowered.com/search/?sort_by=Released_DESC&supportedlang=english"
S3_PATH = "s3://c18-game-tracker-s3/input/"


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
            app_id = a_tag.get("data-ds-appid")
            title = a_tag.find('span').get_text()
            release_date = a_tag.find(
                'div', class_='col search_released responsive_secondrow').get_text().strip()
            game = {
                'url': link,
                'app_id': app_id,
                'title': title,
                'release': release_date
            }
            games.append(game)
    return games


def get_steam_game_details(app_id: int) -> dict[str]:
    '''Takes Steam store app ID and requests data through the API
    Returns dict of useful data'''
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()

            if data.get(str(app_id), {}).get('success'):
                game_data = data[str(app_id)]['data']
                return {
                    'app_id': app_id,
                    'publishers': game_data.get('publishers', []),
                    'developers': game_data.get('developers', []),
                    'description': game_data.get('short_description'),
                    'requirements': game_data.get('pc_requirements'),
                    'is_free': game_data.get('is_free', False),
                    'price': game_data.get('price_overview', {}).get('final'),
                    'currency': game_data.get('price_overview', {}).get('currency'),
                    'genres': [genre['description'] for genre in game_data.get('genres', [])],
                    'image': game_data.get('header_image')
                }
            return {'app_id': app_id, 'error': 'Data not found or incomplete'}
        return {'app_id': app_id,
                'error': f"HTTP error {response.status_code}: {response.reason}"}
    except requests.RequestException as e:
        return {'app_id': app_id, 'error': f'Request failed: {str(e)}'}


def iterate_through_scraped_games(json_data: list[dict[str]]):
    '''
    Iterates through list of games and adds on supplementary data into each dict
    '''
    games_full_data = []
    for item in json_data:
        app_id = item['app_id']
        if app_id:
            details = get_steam_game_details(app_id)
            if 'requirements' not in details or not isinstance(details['requirements'], dict) or 'minimum' not in details['requirements']:
                details['requirements'] = {'minimum': None}
            details['price'] = int(details['price']) if details['price'] else 0
            # Merge original data with extra info
            full_data = item | details
            games_full_data.append(full_data)
    return games_full_data


if __name__ == "__main__":
    main_session = get_session()
    existing_games = get_existing_games(S3_PATH, main_session)

    steam_html = get_html(STEAM_URL)
    scraped_games = parse_games_bs(steam_html)
    new_games = [
        new_game for new_game in scraped_games if str(new_game.get("app_id")) not in existing_games]

    full_game_data = iterate_through_scraped_games(new_games)
