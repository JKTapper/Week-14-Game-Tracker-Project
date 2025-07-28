import json
from urllib.request import urlopen
from bs4 import BeautifulSoup


def get_html(url):
    with urlopen(url) as page:
        html_bytes = page.read()
        html = html_bytes.decode("utf_8")
    return html


def parse_games_bs(html):
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


if __name__ == "__main__":
    with open("steamgames.json", 'r') as game_file:
        existing_games = json.load(game_file)
    steam_url = "https://store.steampowered.com/search/?sort_by=Released_DESC&supportedlang=english"
    steam_html = get_html(steam_url)
    scraped_games = parse_games_bs(steam_html)[0:5]
    new_games = [
        game for game in scraped_games if game not in existing_games]
    games = existing_games + new_games
    print(games)
    with open("steamgames.json", 'w') as game_file:
        json.dump(games, game_file)
