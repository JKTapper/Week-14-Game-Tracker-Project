import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import awswrangler as wr
import boto3
from epicstore_api import EpicGamesStoreAPI, OfferData

S3_PATH = "s3://c18-game-tracker-s3/input/epic/"
api = EpicGamesStoreAPI()


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


def get_epic_game_summaries() -> list:
    '''Fetches newly listed Epic games '''
    summaries = []
    product_map = api.get_product_mapping()

    for i, (namespace, slug) in enumerate(product_map.items()):
        try:
            product = api.get_product(slug)
            if not product:
                logging.warning(
                    f"Skipping game '{slug}' because product is None.")
                continue

            for page in product.get('pages', []):
                if 'offer' in page and 'id' in page['offer']:
                    offer = page.get('offer', {})
                    offer_id = offer.get('id')
                if offer_id:
                    summaries.append({
                        'app_id': offer_id,
                        'url': f"https://store.epicgames.com/en-US/p/{slug}"
                    })

        except Exception as e:
            logging.warning(f"Error getting data for {slug}: {e}")
            continue

    return summaries


def get_epic_game_details(offer_id: str, namespace: str = '') -> dict:
    '''Fetches detailed data for a store listing'''
    try:
        offer_data = api.get_offers_data(OfferData(namespace, offer_id))

        catalog = offer_data[0]['data']['Catalog']['catalogOffer']
        if not catalog:
            raise ValueError(f"No catalogOffer data for {offer_id}")

        dev_name = ''
        for attr in catalog.get('customAttributes', []):
            if attr['key'] == 'developerName':
                dev_name = attr['value']

        release_date = catalog.get(
            'releaseDate') or catalog.get('effectiveDate') or ''

        return {
            'app_id': catalog['id'],
            'publishers': catalog.get('publisherName', []),
            'developers': [dev_name] if dev_name else [],
            'description': catalog.get('description', ''),
            'requirements': {'minimum': None},
            'is_free': catalog.get('price', {}).get('totalPrice', {}).get('discountPrice', 1) == 0,
            'price': catalog.get('price', {}).get('totalPrice', {}).get('discountPrice', 0),
            'currency': catalog.get('price', {}).get('totalPrice', {}).get('currencyCode', 'USD'),
            'genres': [tag.get('name') for tag in catalog.get('tags', []) if tag.get('name')],
            'image': catalog.get('keyImages', [{}])[0].get('url', ''),
            'release': release_date
        }
    except Exception as e:
        logging.warning(f"Error fetching details for {offer_id}: {e}")
        return {
            'app_id': offer_id,
            'publishers': [],
            'developers': [],
            'description': '',
            'requirements': {'minimum': None},
            'is_free': True,
            'price': 0,
            'currency': 'USD',
            'genres': [],
            'image': ''
        }


def iterate_through_scraped_games(json_data: list[dict], release_cutoff: datetime.date) -> list:
    '''Adds relevant data to existing data'''
    games_full_data = []
    product_map = api.get_product_mapping()

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(fetch_game_with_release_check,
                            item, product_map, release_cutoff)
            for item in json_data
        ]
        for f in futures:
            result = f.result()
            if result:
                games_full_data.append(result)

    return games_full_data


def fetch_game_with_release_check(item, product_map, release_cutoff) -> dict | None:
    """Checks if game just came out"""
    app_id = item['app_id']
    slug = item['url'].split('/')[-1]
    namespace = next((ns for ns, s in product_map.items() if s == slug), '')
    if not app_id:
        return None

    details = get_epic_game_details(app_id, namespace)
    release_str = details.get('release')

    try:
        if release_str:
            release_dt = datetime.fromisoformat(release_str.replace('Z', ''))
            if release_dt.date() == release_cutoff:
                return {**item, **details}
    except Exception as e:
        logging.warning(f"Error parsing release date for {app_id}: {e}")

    return None


def main() -> list[dict]:
    """Main to run other functions"""
    main_session = get_session()
    existing_games = get_existing_games(S3_PATH, main_session)

    scraped_games = get_epic_game_summaries()
    new_games = [
        game for game in scraped_games if str(game.get("app_id")) not in existing_games
    ]
    print(f"Scraped {len(new_games)} new game(s) not already in S3.")

    release_cutoff = datetime.today().date()

    # release_cutoff = datetime.strptime("20/03/2024", "%d/%m/%Y").date()

    full_game_data = iterate_through_scraped_games(new_games, release_cutoff)
    print(json.dumps(full_game_data, indent=2))

    return full_game_data


if __name__ == "__main__":
    main()
