"""
Script to query subscribers and the genres they are assigned to.
Sends email updates using AWS SES when new games are released.
"""

import os
import logging
import time
import pandas as pd
import json
import boto3
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

SOURCE_EMAIL = "gametrackerc18@gmail.com"


def connect_to_rds()-> Engine:
    """
    Connect to AWS RDS using environment variables.
    """
    load_dotenv()
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USERNAME")
    db_password = os.getenv("DB_PASSWORD")
    db_name = "postgres"
    db_port = 5432

    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(db_url)


def get_sub_notifications() -> pd.DataFrame:
    """
    Query RDS for subscribers and the genres they want email notifications for.
    """
    connection = connect_to_rds()
    with connection.begin() as conn:
        return pd.read_sql("""
            SELECT g.genre_name, game_name, release_date, subscriber_email 
            FROM game
            JOIN genre_assignment ga ON ga.game_id = game.game_id
            JOIN subscriber_genre_assignment sga ON sga.genre_id = ga.genre_id 
            JOIN subscriber s ON s.subscriber_id = sga.subscriber_id
            JOIN genre g ON g.genre_id = ga.genre_id
            WHERE s.email_notifications = true
            AND release_date >= NOW() - INTERVAL '1 days';
        """, conn)



def make_html(df:pd.DataFrame) -> str:
    """
    Parses an html string
    """
    return f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        color: #333;
                        padding: 20px;
                    }}
                    h2 {{
                        color: #ff6600;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        background-color: #fff;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #ff6600;
                        color: white;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                </style>
            </head>
            <body>
                <h2>🎮 New Game Releases in Your Favourite Genres</h2>
                {df.to_html(index=False, escape=False)}
                <p>Thanks for subscribing to Game Tracker!</p>
            </body>
            </html>
        """





def handler(event, context):
    """
    Lambda handler which sends email to all subscribers
    """
    client = boto3.client('ses', region_name='eu-west-2')

    data = get_sub_notifications()
    emails = data['subscriber_email'].unique()

    for email in emails:
        email_df = data[data['subscriber_email'] == email]
        
        # Group by genre so that result is in form {genre1:[game1, game2, game3]}
        grouped = email_df.groupby('genre_name')['game_name'].apply(list).to_dict()

        # Get list with the most elements to determine size of df/table 
        max_len = max(len(games) for games in grouped.values())
        formatted_data = {
            genre: games + [''] * (max_len - len(games))
            for genre, games in grouped.items()
        }
        # df now in form (col=genres, row=games)
        pivot_df = pd.DataFrame(formatted_data)

        html_content = make_html(pivot_df)
        try:
            client.send_email(
                Destination={'ToAddresses': [email]},
                Message={
                    'Body': {
                        'Html': {
                            'Charset': 'UTF-8',
                            'Data': html_content,
                        }
                    },
                    'Subject': {
                        'Charset': 'UTF-8',
                        'Data': '🆕 New Games Added - Game Tracker Update',
                    },
                },
                Source=SOURCE_EMAIL
            )

            logger.info(f"Email notification sent to {email}")
            time.sleep(1)

        except Exception as e:
            logger.error(f"Failed to send email to {email}: {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps("Emails Sent Successfully")
    }


