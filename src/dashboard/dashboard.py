"""
This module produces a Streamlit dashboard for tracking new game releases, displaying metrics
and charts
"""

import streamlit as st
import asyncio
from visuals import count_releases_by_day, most_common_genres, price_distribution_histogram, \
    find_mean_price, find_new_release_count, find_free_count, best_weekday, \
    average_price_by_platform, player_counts_graph
from database import fetch_game_data

LOGO = "https://github.com/JKTapper/Week-14-Game-Tracker-Project/blob/main/assets/logo.png?raw=true"
TITLE = "https://raw.githubusercontent.com/JKTapper/Week-14-Game-Tracker-Project/a2fa5228b3b646783a95318f214fec7e47981919/assets/final_title.png"

st.set_page_config(page_title="Game Tracker Dashboard",
                   page_icon="🎮", initial_sidebar_state="expanded")


st.image(TITLE)
st.write("")
stores = fetch_game_data("SELECT store_name FROM store")['store_name'].unique()
genres = fetch_game_data(
    """SELECT genre_name FROM game
    JOIN genre_assignment USING(game_id)
    JOIN genre USING(genre_id)"""
).value_counts(
    'genre_name').index


with st.sidebar:

    st.logo(LOGO, size="large")
    # st.image(LOGO)
    st.title("Filters:")
    with st.expander("Stores", True):
        store_options = st.multiselect(
            "Stores",
            stores,
            stores
        )

    with st.expander("Genres", True):
        genre_options = st.multiselect(
            "Genres",
            ['all'] + list(genres)[:15],
            ['all']
        )

GENRE_SELECTION = f"""AND genre_name IN('{"', '".join(genre_options)}')""" if 'all' not in genre_options else ''

FILTER_STATEMENT = f"""
WITH filtered_games AS (SELECT game_name,game_id,price,currency,store_id,release_date
FROM game JOIN store USING(store_id) LEFT JOIN genre_assignment USING(game_id)
LEFT JOIN genre USING(genre_id)
WHERE store_name IN ('{"','".join(store_options)}')
""" + GENRE_SELECTION + """
GROUP BY game_name,game_id,price,currency,store_id,release_date)"""

player_count_info = asyncio.run(player_counts_graph())
st.write(player_count_info)
col1, col2 = st.columns(2)
with col1:
    game_count_week = find_new_release_count(7, FILTER_STATEMENT)
    st.metric("New releases this week:", game_count_week)
    avg_price = find_mean_price(FILTER_STATEMENT)
    st.metric("💰 Average price:", avg_price)
with col2:
    game_count_month = find_new_release_count(30, FILTER_STATEMENT)
    st.metric("New releases (Last 30 days):", game_count_month)
    free_pct = find_free_count(FILTER_STATEMENT)
    st.metric("Free games released (Last 30 days):", free_pct)


st.subheader("Recent Release Activity")
count_releases_by_day(FILTER_STATEMENT)

st.subheader("Most Common Genres")
most_common_genres(FILTER_STATEMENT)

st.subheader("Price Distribution of Paid Games")
price_distribution_histogram(FILTER_STATEMENT)

st.subheader("Releases by Weekday")
best_weekday(FILTER_STATEMENT)

# st.subheader("Releases by Store")
# releases_by_store()

st.subheader("Average price by Store")
average_price_by_platform(FILTER_STATEMENT)

# st.subheader("Genre Combinations")
# genre_combinations()
