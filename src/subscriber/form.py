"""
Flask app to run form for user subscriptions
"""
import os
import logging
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
from flask import Flask, render_template, request, Response

from typing import List, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def connect_to_rds() -> Engine:
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


def insert_sub_genre_assignment(conn: Connection, subscriber_id: int, genres_sub: List[str]) -> None:
    """
    Insert genre assignments for a subscriber.
    """
    for genre in genres_sub:
        genre_id = conn.execute(
            text("SELECT genre_id FROM genre WHERE genre_name = :genre"),
            {"genre": genre}
        ).fetchone()[0]

        conn.execute(
            text("""INSERT INTO subscriber_genre_assignment (genre_id, subscriber_id)
                    VALUES (:genre_id, :subscriber_id)"""),
            {"genre_id": genre_id, "subscriber_id": subscriber_id}
        )
        logger.info(f"Assigned genre '{genre}' (id: {genre_id}) to subscriber {subscriber_id}")


@app.route("/", methods=["GET", "POST"])
def form() -> Union[str, Response]:
    """
    Display or process the subscription form.
    """
    connection = connect_to_rds()

    with connection.begin() as conn:
        genres = pd.read_sql("SELECT * FROM genre;", conn)["genre_name"]

    if request.method == "POST":
        email = request.form["email"]
        genres_sub = request.form.getlist("genre")
        email_notifications = request.form.get("notifications", False)
        summary = request.form.get("summary", False)

        try:
            with connection.begin() as conn:
                result = conn.execute(
                    text("""INSERT INTO subscriber (subscriber_email, email_notifications, summary)
                            VALUES (:email, :email_notifications, :summary)
                            RETURNING subscriber_id"""),
                    {
                        "email": email,
                        "email_notifications": email_notifications,
                        "summary": summary,
                    }
                )
                subscriber_id = result.fetchone()[0]
                logger.info(f"Inserted subscriber {subscriber_id} with email {email}")

                if genres_sub:
                    insert_sub_genre_assignment(conn, subscriber_id, genres_sub)

                return f"Thank you! We'll contact you at {email}."

        except Exception as e:
            logger.error(f"Error inserting subscriber: {e}")
            return "Email already registered use another one"

    return render_template("form.html", genres=genres)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
