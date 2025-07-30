# pylint: disable=logging-fstring-interpolation
'''Runs EL pipeline from Steam to S3 bucket'''
import logging
from extract import (STEAM_URL, get_existing_games, get_html,
                     parse_games_bs, iterate_through_scraped_games)
from load import S3_PATH, get_session, add_time_partitioning, upload_to_s3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def run_pipeline():
    '''Runs pipeline that extracts steam data and loads data into S3'''
    # Connect to S3 and get existing 'app_id's
    pipeline_session = get_session()
    existing_games = get_existing_games(S3_PATH, pipeline_session)
    logging.info(f'Found {len(existing_games)} games on S3 bucket')

    # Scraping
    steam_html = get_html(STEAM_URL)
    # can limit number that are used
    scraped_games = parse_games_bs(steam_html)
    new_games = [
        new_game for new_game in scraped_games if str(new_game.get("app_id")) not in existing_games]
    logging.info(f'Scraped {len(new_games)} new games')

    # Add data from API
    full_game_data = iterate_through_scraped_games(new_games)
    logging.info(f'Added data from API for {len(full_game_data)} games')

    # Turn into dataframe and load into S3
    df = add_time_partitioning(full_game_data)
    upload_to_s3(df, pipeline_session)
    logging.info(f"Uploaded to {S3_PATH}")


def handler(event, context):
    '''Handler function for lambda function'''
    try:
        run_pipeline()
        print(f'{event}: Lambda time remaining in MS:',
              context.get_remaining_time_in_millis())
        return {'statusCode': 200}
    except (TypeError, ValueError, IndexError) as e:
        return {'statusCode': 500, 'error': str(e)}
