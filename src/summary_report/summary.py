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


if __name__ == "__main__":
    connection = connect_to_rds()
    data = query_rds(connection, "select * from game;")
    summary = canvas.Canvas("0.pdf")
    summary.drawString(100, 100, str(data))
    summary.showPage()
    summary.save()
    chart = most_common_genres()
    chart.show()
    chart.save('1.pdf')
    print(data)
    pdf_merger = PdfWriter()
    for path in Path.cwd().glob("*.pdf"):
        pdf_merger.append(path)
    pdf_merger.write("Summary.pdf")
