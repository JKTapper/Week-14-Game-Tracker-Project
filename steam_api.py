'''Takes json file of newly scraped games, requests data from API
and adds supplementary data to the json file'''
import requests
import re
import json


def read_json_file(filename: str):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data


def save_json_file(filename: str, data: list[dict[str]]):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def extract_app_id(url):
    match = re.search(r'/app/(\d+)/', url)  # /app/{ID}/
    return int(match.group(1)) if match else None  # first group in brackets


def get_steam_game_details(app_id):
    url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if data[str(app_id)]['success']:
            game_data = data[str(app_id)]['data']
            return {
                'app_id': app_id,
                'name': game_data.get('name'),
                'genres': [genre['description'] for genre in game_data.get('genres', [])],
                'developers': game_data.get('developers', []),
                'publishers': game_data.get('publishers', []),
                'release_date': game_data.get('release_date', {}).get('date'),
                'is_free': game_data.get('is_free', False),
            }
        else:
            return {'app_id': app_id, 'error': 'Data not found'}
    except Exception as e:
        return {'app_id': app_id, 'error': str(e)}


def iterate_through_scraped_games(json_data):
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
    data = read_json_file('steamgames.json')

    full_data = iterate_through_scraped_games(data)

    save_json_file('steamgames.json', full_data)
