"""
Scrapes the steam website for the 5 most recently released
PC games and stores all scraped games in a json
"""
import json
from urllib.request import urlopen
from bs4 import BeautifulSoup


def get_existing_games(filename: str):
    '''Returns list of games currently in json file'''
    try:
        with open(filename, 'r', encoding='utf-8') as game_file:
            try:
                existing_games = json.load(game_file)
            except json.JSONDecodeError:  # empty file
                print("Warning: file empty. Creating empty list.")
                existing_games = []
    except FileNotFoundError:
        print(f"{filename} not found. Creating empty list.")
        existing_games = []
    return existing_games


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
            text = a_tag.find('span').get_text()
            release_date = a_tag.find(
                'div', class_='col search_released responsive_secondrow').get_text().strip()
            game = {
                'url': link,
                'title': text,
                'release': release_date
            }
            games.append(game)
    return games


STEAM_URL = "https://store.steampowered.com/search/?sort_by=Released_DESC&supportedlang=english"


if __name__ == "__main__":
    existing_games = get_existing_games('steamgames.json')

    steam_html = get_html(STEAM_URL)
    scraped_games = parse_games_bs(steam_html)[0:5]
    new_games = [
        new_game for new_game in scraped_games if new_game not in existing_games]
    all_games = existing_games + new_games
    print(all_games)
    with open("steamgames.json", 'w', encoding='utf-8') as game_file:
        json.dump(all_games, game_file)
