"""AWS Lambda handler for the weekly game report."""

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from botocore.exceptions import ClientError
from summary import create_summary_html
from database import fetch_game_data
import pandas as pd
import boto3
import logging
import json
import os

SOURCE_EMAIL = "gametrackerc18@gmail.com"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_sub_notifications() -> pd.DataFrame:
    """
    Query RDS for subscribers who want to receive the weekly summary.
    """
    logger.info("Fetching subscriber list for weekly summary.")
    query = "SELECT subscriber_email FROM subscriber WHERE summary = true;"
    summary_subs_df = fetch_game_data(query)
    logger.info("Found %d subscribers for the summary.", len(summary_subs_df))
    return summary_subs_df


def send_report_email(ses_client, recipient_email: str, html_content: str):
    """
    Constructs and sends a single multipart email with embedded images.

    Args:
        ses_client: An initialized boto3 SES client.
        recipient_email: The email address of the recipient.
        html_content: The HTML body of the email.
    """
    msg = MIMEMultipart('related')
    msg['Subject'] = '🎮 New Games Tracker - Your Weekly Report!'
    msg['From'] = SOURCE_EMAIL
    msg['To'] = recipient_email

    # Attach the HTML body
    msg.attach(MIMEText(html_content, 'html'))

    images = [
        ('release_count_line_graph.png', 'release_count_graph'),
        ('genre_bar_chart.png', 'genre_bar_chart'),
        ('hist_chart.png', 'hist_chart')
    ]

    for filename, cid in images:
        img_path = os.path.join('/tmp', filename)
        try:
            with open(img_path, 'rb') as img:
                mime_img = MIMEImage(img.read())
                mime_img.add_header('Content-ID', f'<{cid}>')
                msg.attach(mime_img)
            logger.info("Successfully attached image %s", filename)
        except FileNotFoundError:
            logger.error(
                "Image file not found at path: %s", img_path)
            return False
        except Exception as e:
            logger.error("Error attaching image %s: %s", filename, e)
            return False

    # Send the email using SES
    try:
        ses_client.send_raw_email(
            Source=SOURCE_EMAIL,
            Destinations=[recipient_email],
            RawMessage={'Data': msg.as_string()}
        )
        logger.info("Successfully sent report to %s", recipient_email)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'MessageRejected':
            logger.error(
                "Message rejected for %s. Recipient may need to verify their email.", recipient_email)
            return False
        else:
            logger.error("Failed to send email to %s: [%s] %s",
                         recipient_email, error_code, e.response['Error']['Message'])
            return False


def handler(event, context):  # pylint: disable=unused-argument
    """
    Lambda handler to generate and send a weekly game report to all subscribers.
    """
    ses_client = boto3.client('ses', 'eu-west-2')

    try:
        # Generate the report email content.
        html_content = create_summary_html()
    except Exception as e:
        logger.error(
            "Failed to generate HTML report content. Error: %s", e)
        return {'statusCode': 500, 'body': json.dumps({"error": "Failed to generate report"})}

    try:
        # Fetch the list of subscribers
        sub_data = get_sub_notifications()
        if sub_data.empty:
            logger.info("No subscribers found.")
            return {'statusCode': 200, 'body': json.dumps({"message": "No subscribers found."})}

        emails = sub_data['subscriber_email'].unique()
    except Exception as e:
        logger.error(
            "Failed to fetch subscriber data. Error: %s", e)
        return {'statusCode': 500, 'body': json.dumps({"error": "Failed to fetch subscriber data"})}

    success_count = 0
    failure_count = 0
    for email in emails:
        try:
            check_success = send_report_email(ses_client, email, html_content)
            if check_success:
                success_count += 1
            else:
                failure_count += 1
        except Exception:
            failure_count += 1

    final_message = f"Email sending complete. Success: {success_count}, Failures: {failure_count}."
    logger.info(final_message)

    return {
        'statusCode': 200,
        'body': json.dumps({"message": final_message})
    }
