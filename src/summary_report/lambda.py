"""AWS Lambda handler for the weekly game report."""

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from summary import create_summary_html
from database import fetch_game_data
import pandas as pd
import boto3
import logging
import time
import json

SOURCE_EMAIL = "gametrackerc18@gmail.com"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_sub_notifications() -> pd.DataFrame:
    """
    Query RDS for subscribers and the genres they want email notifications for.
    """
    query = """
            SELECT subscriber_email, summary 
            FROM subscriber
            WHERE summary = true;
            """
    summary_subs_df = fetch_game_data(query)
    return summary_subs_df


def handler(event, context):  # pylint: disable=unused-argument
    """
    Handles Lambda event to generate and return a weekly game report for subscribers.
    """

    client = boto3.client('ses', region_name='eu-west-2')

    data = get_sub_notifications()
    emails = data['subscriber_email'].unique()

    html_content = create_summary_html()

    for email in emails:
        msg = MIMEMultipart('related')
        msg['Subject'] = '🎮 New Games Tracker Weekly Report'
        msg['From'] = SOURCE_EMAIL
        msg['To'] = email

        msg.attach(MIMEText(html_content, 'html'))

        images = [
            ('/tmp/release_count_line_graph.png', 'myimage1'),
            ('/tmp/genre_bar_chart.png', 'myimage2'),
            ('/tmp/hist_chart.png', 'myimage3')
        ]

        for img_path, cid in images:
            with open(img_path, 'rb') as img:
                mime_img = MIMEImage(img.read())
                mime_img.add_header('Content-ID', f'<{cid}>')
                mime_img.add_header('Content-Disposition',
                                    'inline', filename=img_path)
                msg.attach(mime_img)

        try:
            client.send_raw_email(
                Source=SOURCE_EMAIL,
                Destinations=[email],
                RawMessage={'Data': msg.as_string()}
            )
            print(f"Email sent to {email}")
            time.sleep(1)
        except Exception as e:
            print(f"Failed to send email to {email}: {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps("Emails Sent Successfully")
    }
