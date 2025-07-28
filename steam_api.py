'''Takes json file of newly scraped games, requests data from API
and adds supplementary data to the json file'''
import re
import json
import requests


def read_json_file(filename: str) -> list[dict[str]]:
    '''Reads json file and returns list of dicts'''
    with open(filename, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    return json_data


def save_json_file(filename: str, json_data: list[dict[str]]):
    '''Saves data into json file'''
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)


def extract_app_id(url: str) -> int:
    '''Uses regex to search Steam URL for app ID and returns it'''
    match = re.search(r'/app/(\d+)/', url)  # /app/{ID}/
    return int(match.group(1)) if match else None  # first group in brackets


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
                    'name': game_data.get('name'),
                    'genres': [genre['description'] for genre in game_data.get('genres', [])],
                    'developers': game_data.get('developers', []),
                    'publishers': game_data.get('publishers', []),
                    'release_date': game_data.get('release_date', {}).get('date'),
                    'is_free': game_data.get('is_free', False)}
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
        app_id = extract_app_id(item['url'])
        if app_id:
            details = get_steam_game_details(app_id)
            # Merge original data with extra info
            full_data = item | details
            print(full_data)
            games_full_data.append(full_data)
    return games_full_data


if __name__ == "__main__":
    scraped_data = read_json_file('steamgames.json')

    full_game_data = iterate_through_scraped_games(scraped_data)

    save_json_file('steamgames.json', full_game_data)
