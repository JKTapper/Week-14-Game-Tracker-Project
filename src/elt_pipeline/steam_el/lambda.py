'''Runs EL pipeline from Steam to S3 bucket'''
from extract import *
from load import *


def run_pipeline():
    # Connect to S3 and get existing 'app_id's
    pipeline_session = get_session()
    existing_games = get_existing_games(S3_PATH, pipeline_session)
    print(existing_games)

    # Scraping
    steam_html = get_html(STEAM_URL)
    # can limit number that are used
    scraped_games = parse_games_bs(steam_html)
    new_games = [
        new_game for new_game in scraped_games if str(new_game.get("app_id")) not in existing_games]
    print(new_games, '\n')

    # Add data from API
    full_game_data = iterate_through_scraped_games(new_games)
    print(full_game_data)

    # Turn into dataframe and load into S3
    df = add_time_partitioning(full_game_data)
    upload_to_s3(df, pipeline_session)


def handler(event, context):
    '''Handler function for lambda function'''
    try:
        run_pipeline()
        print(f'{event}: Lambda time remaining in MS:',
              context.get_remaining_time_in_millis())
        return {'statusCode': 200}
    except (TypeError, ValueError, IndexError) as e:
        return {'statusCode': 500, 'error': str(e)}
