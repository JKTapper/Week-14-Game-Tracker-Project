import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from flask import Flask, render_template, request

app = Flask(__name__)

def connect_to_rds():
    """
    Connection to aws rds
    """
    load_dotenv()
    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USERNAME")
    db_password = os.getenv("DB_PASSWORD")
    db_name = "postgres"  
    db_port = 5432

    db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(db_url)



def insert_sub_genre_assignment(conn, subscriber_id, genres_sub):
    for genre in genres_sub:
        genre_id = conn.execute(text("select genre_id from genre where genre_name = :genre"), {"genre":genre}).fetchone()[0]
        conn.execute(text("""insert into subscriber_genre_assignment (genre_id, subscriber_id)
                        values (:genre_id, :subscriber_id)"""), {"genre_id":genre_id, "subscriber_id":subscriber_id})


@app.route("/", methods=["GET", "POST"])
def form():

    connection = connect_to_rds()
    #Get list of current genres in RDS
    with connection.begin() as conn:
        genres = pd.read_sql("select * from genre;", conn)["genre_name"]
    
    if request.method == "POST":
        email = request.form["email"]
        genres_sub = request.form.getlist('genre')
        email_notifications = request.form.get("notifications", False)
        summary = request.form.get("summary", False)
        
        try:
            with connection.begin() as conn:
                sub_id = conn.execute(
                text("""INSERT INTO subscriber (subscriber_email, email_notifications, summary) 
                    VALUES (:email, :email_notifications, :summary) returning subscriber_id"""),
                {"email": email, "email_notifications":email_notifications, "summary":summary}).fetchone()[0]
                insert_sub_genre_assignment(conn, sub_id, genres_sub)
                return f"Thank you! You selected {genres_sub}. We'll contact you at {email}."
                
        except:  
            return ("Email already registered use another one")


    return render_template("form.html", genres=genres)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
