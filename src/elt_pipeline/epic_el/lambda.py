# pylint: disable=logging-fstring-interpolation, import-error
'''Runs EL pipeline from Epic to S3 bucket'''
import logging
from datetime import datetime
from extract import (
    S3_PATH,
    get_existing_games,
    get_session,
    get_epic_game_summaries,
    iterate_through_scraped_games
)
from load import add_time_partitioning, upload_to_s3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def run_pipeline():
    '''Runs pipeline that extracts epic data and loads data into S3'''
    # Connect to S3 and get existing 'app_id's
    pipeline_session = get_session()
    existing_games = get_existing_games(S3_PATH, pipeline_session)
    logging.info(f'Found {len(existing_games)} games on S3 bucket')

    # Scraping
    scraped_games = get_epic_game_summaries()
    logging.info(f'Scraped {len(scraped_games)} games from Epic Games Store')
    # can limit number that are used
    new_games = [
        new_game for new_game in scraped_games
        if str(new_game.get("app_id")) not in existing_games
    ]
    logging.info(f'{len(new_games)} new games not already in S3')

    if not new_games:
        return None

    # Add data from API with release date
    release_cutoff = datetime.today().date()
    full_game_data = iterate_through_scraped_games(new_games, release_cutoff)

    if not full_game_data:
        logging.info("No full game data to process, exiting.")
        return None

    logging.info(f'Added data from API for {len(full_game_data)} games')

    # Turn into dataframe and load into S3
    df = add_time_partitioning(full_game_data)
    upload_to_s3(df, pipeline_session)
    logging.info(f"Uploaded {len(df)} games to {S3_PATH}")


def handler(event, context):
    '''Handler function for lambda function'''
    try:
        run_pipeline()
        print(f'{event}: Lambda time remaining in MS:',
              context.get_remaining_time_in_millis())
        return {'statusCode': 200}
    except (TypeError, ValueError, IndexError) as e:
        return {'statusCode': 500, 'error': str(e)}


if __name__ == "__main__":
    run_pipeline()
