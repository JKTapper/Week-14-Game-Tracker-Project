import os
from dotenv import load_dotenv
import psycopg2
import pandas as pd
from reportlab.pdfgen import canvas
from pathlib import Path
from pypdf import PdfWriter
from visuals import count_releases_by_day, most_common_genres


def connect_to_rds():
    """
    Connection to aws rds
    """
    load_dotenv()
    print(os.getenv("DB_HOST"), os.getenv("DB_USERNAME"),
          os.getenv("DB_PASSWORD"), os.getenv("DB_NAME"))
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=5432,
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        dbname="postgres"

    )


def query_rds(conn, query):
    return pd.read_sql(query, conn)


CONTENTS = [
    "Contents:",
    "1. Contents",
    "2. Bar chart of release vs genre"
]

if __name__ == "__main__":
    current_directory = Path.cwd()
    for path in current_directory.glob("*.pdf"):
        os.remove(path)
    connection = connect_to_rds()
    data = query_rds(connection, "select * from game;")
    summary = canvas.Canvas("0.pdf")
    for line_numer, line in enumerate(CONTENTS):
        summary.drawString(100, 500-15*line_numer, line)
    summary.showPage()
    summary.save()
    chart = most_common_genres()
    chart.show()
    chart.save('1.pdf')
    print(data)
    pdf_merger = PdfWriter()
    for path in current_directory.glob("*.pdf"):
        print(path, type(path))
        pdf_merger.append(path)
    pdf_merger.write("Summary.pdf")
    pdf_merger.close()
