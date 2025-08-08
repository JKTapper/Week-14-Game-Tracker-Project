"""
This module contains visualisation and metric functions for the Game Tracker Dashboard
"""
import pandas as pd
import streamlit as st
import altair as alt
from database import fetch_game_data


def find_mean_price(filter_with_statement: str) -> str:
    """Finds and returns the mean price of all games in the entire database"""
    query = filter_with_statement + """
            ,converted_prices AS (SELECT game_id,
            CASE
                WHEN currency = 'GBP' THEN price
                WHEN currency = 'USD' THEN price*0.75
            END AS corrected_price FROM filtered_games
            WHERE price > 0 AND (currency = 'GBP' OR currency = 'USD')
                )
            SELECT
            AVG(corrected_price) as avg_price FROM filtered_games
            JOIN converted_prices USING(game_id)
            """
    with st.spinner("Fetching game data..."):
        price_df = fetch_game_data(query)

    avg_price_value = price_df['avg_price'].iloc[0]

    if avg_price_value is not None:
        average_price = f"£{avg_price_value / 100:.2f}"
    else:
        average_price = "N/A"

    return average_price


def find_new_release_count(day_range, filter_with_statement: str):
    """
    Finds the number of games released in either the last 7 days or last 30 days

    Parameters:
        day_range: A number indicating how many days worth of releases should be counted

    Returns:
        A number representing the total number of games released in this time day_range
    """
    query = filter_with_statement + f"""
            SELECT count(game_name) as game_count
            FROM filtered_games
            WHERE release_date >= NOW() - INTERVAL '{day_range} days'
            AND release_date <= CURRENT_DATE
            """
    with st.spinner("Fetching game data..."):
        price_df = fetch_game_data(query)

    game_count = price_df['game_count'].iloc[0]

    return game_count


def find_free_count(filter_with_statement: str):
    """Finds and returns the number of free games in the entire database"""
    query = filter_with_statement + """
            SELECT count(price) as free_count
            FROM filtered_games
            WHERE price = 0
            """
    with st.spinner("Fetching game data..."):
        price_df = fetch_game_data(query)

    free_count = price_df['free_count']

    return free_count


def count_releases_by_day(filter_with_statement: str):
    """Creates a line chart showing the number of releases per day by querying the the database"""
    query = filter_with_statement + """
            SELECT
            release_date, store_name
            FROM filtered_games JOIN store USING(store_id)
            WHERE release_date >= '2025-07-31'
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


def most_common_genres(filter_with_statement: str):
    """Creates a bar chart showing the 5 most common genres by querying the the database"""
    query = filter_with_statement + """
            SELECT
            genre.genre_name, store_name
            FROM filtered_games
            JOIN genre_assignment using (game_id)
            JOIN genre using (genre_id)
            JOIN store USING(store_id)
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


PRICE_BUCKET_STARTS = [0, 3, 5, 10, 20, 30, 40]


def convert_price_cutoffs_to_buckets(price_cutoffs: list) -> list:
    length = len(price_cutoffs)
    return ['£' + str(price) + (
        '+' if index == length else '-£' +
        str(price_cutoffs[index])) for index, price in enumerate(
            price_cutoffs, 1)]


def convert_to_price_bucket(price: float, price_buckets: list):
    """Takes a price and returns the bucket that price falls into"""
    for index, num in enumerate(PRICE_BUCKET_STARTS, 1):
        if num < price and (index == len(PRICE_BUCKET_STARTS)
                            or price < PRICE_BUCKET_STARTS[index]):
            return price_buckets[index-1]
    return None


def price_distribution_histogram(filter_with_statement: str):
    """Creates a histogram showing the price of paid games by querying the the database"""
    query = filter_with_statement + """
            SELECT store_name,
            CASE
                WHEN currency = 'GBP' THEN price
                WHEN currency = 'USD' THEN price*0.75
            END AS price
            FROM filtered_games JOIN store USING(store_id)
            WHERE price > 0 AND (currency = 'GBP' OR currency = 'USD')
            """
    with st.spinner("Fetching game data..."):
        game_df = fetch_game_data(query)

    price_df = game_df.dropna(subset=['price'])
    price_df['price'] = pd.to_numeric(price_df['price']/100, errors='coerce')
    price_buckets = convert_price_cutoffs_to_buckets(PRICE_BUCKET_STARTS)
    price_df['price_bucket'] = price_df['price'].apply(
        lambda x: convert_to_price_bucket(x, price_buckets))
    price_df = price_df.value_counts(['price_bucket']).reset_index()
    total_games = price_df['count'].sum()
    price_df['count'] = price_df['count'].apply(
        lambda x: 100*x/total_games)
    hist_chart = alt.Chart(price_df).mark_bar().encode(
        x=alt.X('price_bucket', title='Price (£)', sort=price_buckets),
        y=alt.Y('count', title='Number of Games (%)'),
        tooltip=[
            alt.Tooltip('count', title='Number of games (%)'),
            alt.Tooltip('price_bucket', title='Price range')
        ]
    ).interactive()

    st.altair_chart(hist_chart, use_container_width=True)


def best_weekday(filter_with_statement: str):
    """Creates a bar chart showing the number of games released on each weekday"""
    query = filter_with_statement + """
            SELECT
            release_date FROM filtered_games
            """
    with st.spinner("Fetching game data..."):
        game_df = fetch_game_data(query)

    game_df['day_of_week'] = pd.to_datetime(
        game_df['release_date']).dt.day_name()

    day_order = ['Monday', 'Tuesday', 'Wednesday',
                 'Thursday', 'Friday', 'Saturday', 'Sunday']

    day_release_counts = game_df.groupby(
        game_df['day_of_week']
    ).size().reset_index(name='count')

    bar_chart = alt.Chart(day_release_counts).mark_bar().encode(
        x=alt.X('day_of_week:O', title='Day of the Week', sort=day_order),
        y=alt.Y('count:Q', title='Number of Releases'),
        color=alt.Color('count:N', scale=alt.Scale(
            scheme='magma', reverse=True), legend=None),
        tooltip=['day_of_week', 'count']
    ).properties(
        width=600,
        height=300
    ).interactive()

    st.altair_chart(bar_chart, use_container_width=True)


def releases_by_store(filter_with_statement):
    '''Creates a pie chart showing the number of games released by each store recently'''
    query = filter_with_statement + """
            SELECT game.store_id, store.store_name
            FROM filtered_games
            JOIN store USING (store_id)
            """
    with st.spinner("Fetching game data..."):
        game_df = fetch_game_data(query)

    store_count = game_df.groupby(
        game_df['store_name']
    ).size().reset_index(name='count')
    store_count['Store'] = store_count['store_name']

    pie_chart = alt.Chart(store_count).mark_arc().encode(
        theta="count",
        color="Store"
    )
    st.altair_chart(pie_chart, use_container_width=True)


def average_price_by_platform(filter_with_statement: str):
    """Creates a bar chart showing the average price of games released on each platform"""
    query = filter_with_statement + """
            ,converted_prices AS (SELECT game_id,
            CASE
                WHEN currency = 'GBP' THEN price
                WHEN currency = 'USD' THEN price*0.75
            END AS corrected_price FROM filtered_games
            WHERE price > 0 AND (currency = 'GBP' OR currency = 'USD')
                )
            SELECT
            AVG(corrected_price) as average, store_name AS "Store" FROM filtered_games
            JOIN store USING(store_id) JOIN converted_prices USING(game_id)
            GROUP BY store_name
            """
    with st.spinner("Fetching game data..."):
        avg_price_df = fetch_game_data(query)
    avg_price_df['Average price (£)'] = avg_price_df['average'].apply(
        lambda x: float(x)/100)

    bar_chart = alt.Chart(avg_price_df).mark_bar().encode(
        x=alt.X('Store', title='Store', sort=avg_price_df['average']),
        y=alt.Y('Average price (£)', title='Average price (£)'),
        color=alt.Color('Average price (£)', legend=None)
    ).properties(
        width=600,
        height=300
    ).interactive()

    st.altair_chart(bar_chart, use_container_width=True)

# genre combinations


def genre_combinations(filter_with_statement):
    """Creates a heatmap showing which genres conincide with each other"""
    query = filter_with_statement + """
            SELECT
            game_id ,genre_name AS "Genre"
            FROM filtered_games
            JOIN genre_assignment USING(game_id)
            JOIN genre USING(genre_id)
            ORDER BY game_id,COUNT(*) OVER (PARTITION BY genre_id) desc, genre_name
            """
    with st.spinner("Fetching game data..."):
        avg_price_df = fetch_game_data(query)
    genres = avg_price_df['Genre'].value_counts()[:11]

    current_game_id = 0
    current_games_genres = []
    genre_combination_frequencies = {}

    for row in avg_price_df.iterrows():
        game_id, genre = row[1][:2]
        if game_id != current_game_id:
            current_games_genres = []
            current_game_id = game_id
        if genre in genres:
            for present_genre in current_games_genres:
                genre_combination_frequencies[(
                    present_genre,
                    genre
                )] = genre_combination_frequencies.get(
                    (present_genre, genre), 0) + 1
            current_games_genres.append(genre)

    source = pd.DataFrame({
        'Genres - x': [genre_pair[0] for genre_pair in genre_combination_frequencies],
        'Genres - y': [genre_pair[1] for genre_pair in genre_combination_frequencies],
        'frequency': genre_combination_frequencies.values()
    })

    heatmap = alt.Chart(source).mark_rect().encode(
        x=alt.X('Genres - x', sort=genres.index),
        y=alt.Y('Genres - y', sort=genres.index),
        color='frequency'
    )

    st.altair_chart(heatmap)
