"""
This module contains visualisation and metric functions for the Game Tracker Dashboard
"""
import pandas as pd
import streamlit as st
import altair as alt
from database import fetch_game_data


def find_mean_price() -> str:
    """Finds and returns the mean price of all games in the entire database"""
    query = """
            SELECT AVG(price) as avg_price
            FROM game
            where price > 0
            AND currency = 'GBP'
            """
    with st.spinner("Fetching game data..."):
        price_df = fetch_game_data(query)

    avg_price_value = price_df['avg_price'].iloc[0]

    if avg_price_value is not None:
        average_price = f"£{avg_price_value / 100:.2f}"
    else:
        average_price = "N/A"

    return average_price


def find_new_release_count(day_range):
    """
    Finds the number of games released in either the last 7 days or last 30 days

    Parameters:
        day_range: A number indicating how many days worth of releases should be counted

    Returns:
        A number representing the total number of games released in this time day_range
    """
    query = f"""
            SELECT count(game_name) as game_count
            FROM game
            WHERE release_date >= NOW() - INTERVAL '{day_range} days'
            AND release_date <= CURRENT_DATE
            """
    with st.spinner("Fetching game data..."):
        price_df = fetch_game_data(query)

    game_count = price_df['game_count'].iloc[0]

    return game_count


def find_free_count():
    """Finds and returns the number of free games in the entire database"""
    query = """
            SELECT count(price) as free_count
            FROM game
            WHERE price = 0
            """
    with st.spinner("Fetching game data..."):
        price_df = fetch_game_data(query)

    free_count = price_df['free_count']

    return free_count


def count_releases_by_day():
    """Creates a line chart showing the number of releases per day by querying the the database"""
    query = """
            SELECT
            release_date
            FROM game
            WHERE EXTRACT(YEAR FROM release_date) >= 2025
            AND release_date <= CURRENT_DATE
            """
    with st.spinner("Fetching game data..."):
        game_df = fetch_game_data(query)

    game_df['release_date'] = pd.to_datetime(game_df['release_date'])

    daily_release_counts = game_df.groupby(
        game_df['release_date'].dt.date
    ).size().reset_index(name='count')

    line_chart = alt.Chart(daily_release_counts).mark_line(point=True).encode(
        x=alt.X('release_date:T', title='Release Date'),
        y=alt.Y('count:Q', title='Number of Releases'),
        tooltip=['release_date:T', 'count']
    ).interactive()

    st.altair_chart(line_chart, use_container_width=True)


def most_common_genres():
    """Creates a bar chart showing the 5 most common genres by querying the the database"""
    query = """
            SELECT
            genre.genre_name
            FROM game
            JOIN genre_assignment using (game_id)
            JOIN genre using (genre_id)
            """
    with st.spinner("Fetching game data..."):
        game_df = fetch_game_data(query)

    genre_counts = game_df['genre_name'].value_counts().head(
        5).reset_index(name='count')
    genre_counts.columns = ['genre_name', 'count']
    bar_chart = alt.Chart(genre_counts).mark_bar().encode(
        x=alt.X('genre_name:O', title='Genre', sort='-y'),
        y=alt.Y('count:Q', title='Number of Releases'),
        color=alt.Color('genre_name:N', legend=None),
        tooltip=['genre_name', 'count']
    ).properties(
        width=600,
        height=300
    ).interactive()

    st.altair_chart(bar_chart, use_container_width=True)


def price_distribution_histogram():
    """Creates a histogram showing the price of paid games by querying the the database"""
    query = """
            SELECT price
            FROM game
            WHERE price > 0
            AND currency = 'GBP'
            """
    with st.spinner("Fetching game data..."):
        game_df = fetch_game_data(query)

    price_df = game_df.dropna(subset=['price'])
    price_df['price'] = pd.to_numeric(price_df['price']/100, errors='coerce')
    hist_chart = alt.Chart(price_df).mark_bar().encode(
        x=alt.X('price:Q', bin=alt.Bin(maxbins=10), title='Price (£)'),
        y=alt.Y('count()', title='Number of Games'),
        tooltip=[
            alt.Tooltip('count()', title='Number of games'),
            alt.Tooltip('price:Q', bin=True, title='Price range')
        ]
    ).interactive()

    st.altair_chart(hist_chart, use_container_width=True)


def best_weekday():
    """Creates a bar chart showing the number of games released on each weekday"""
    query = """
            SELECT
            TO_CHAR(release_date, 'Day') AS day_of_week
            FROM game
            """
    with st.spinner("Fetching game data..."):
        game_df = fetch_game_data(query)

    day_release_counts = game_df.groupby(
        game_df['day_of_week']
    ).size().reset_index(name='count')

    bar_chart = alt.Chart(day_release_counts).mark_bar().encode(
        x=alt.X('day_of_week:O', title='Day of the Week', sort='-y'),
        y=alt.Y('count:Q', title='Number of Releases'),
        color=alt.Color('count:N', scale=alt.Scale(
            scheme='magma', reverse=True), legend=None),
        tooltip=['day_of_week', 'count']
    ).properties(
        width=600,
        height=300
    ).interactive()

    st.altair_chart(bar_chart, use_container_width=True)


def releases_by_store():
    '''Creates a pie chart showing the number of games released by each store recently'''
    query = """
            SELECT game.store_id, store.store_name
            FROM game
            JOIN store USING (store_id)
            """
    with st.spinner("Fetching game data..."):
        game_df = fetch_game_data(query)

    store_count = game_df.groupby(
        game_df['store_name']
    ).size().reset_index(name='count')

    pie_chart = alt.Chart(store_count).mark_arc().encode(
        theta="count",
        color="store_name"
    )
    st.altair_chart(pie_chart, use_container_width=True)
