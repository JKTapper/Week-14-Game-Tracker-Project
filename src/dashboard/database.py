"""
This module contains functions for connection and data fetching for an RDS.

"""

import os
import logging
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import streamlit as st

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Establish connection to RDS PostgreSQL database."""
    load_dotenv()
    try:
        conn = psycopg2.connect(
            port="5432",
            database="postgres",
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        logger.info("Successfully connected to database.")
        return conn
    except Exception as e:
        logger.error("Error connecting to database: %s", e)
        raise


@st.cache_data(ttl=60, show_spinner="Fetching latest data...")
def fetch_game_data(query) -> pd.DataFrame:
    """Fetch game data from RDS and return as pandas DataFrame."""
    with get_db_connection() as conn:
        df = pd.read_sql(query, conn)
        logger.info("Fetched %s rows from database.", len(df))
    return df
