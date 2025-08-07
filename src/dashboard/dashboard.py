"""
This module produces a Streamlit dashboard for tracking new game releases, displaying metrics
and charts
"""

import streamlit as st
from visuals import count_releases_by_day, most_common_genres, price_distribution_histogram, \
    find_mean_price, find_new_release_count, find_free_count, best_weekday, releases_by_store, \
    average_price_by_platform, genre_combinations
from database import fetch_game_data


st.set_page_config(page_title="Game Tracker Dashboard",
                   page_icon="🎮")
st.title("🎮 New Games Tracker")

stores = fetch_game_data("SELECT store_name FROM store")['store_name'].unique()
genres = fetch_game_data("SELECT genre_name FROM genre")['genre_name'].unique()

store_options = st.multiselect(
    "Stores",
    stores,
    stores
)

genre_options = st.multiselect(
    "Genres",
    genres,
    genres
)

filter_statement = f"""
WITH filtered_games AS (SELECT game_name,game_id,price,currency,store_id,release_date
FROM game JOIN store USING(store_id) JOIN genre_assignment USING(game_id)
JOIN genre USING(genre_id)
WHERE store_name IN ('{"','".join(store_options)}')
AND genre_name IN ('{"','".join(genre_options)}')
GROUP BY game_name,game_id,price,currency,store_id,release_date)"""

col1, col2 = st.columns(2)

with col1:
    game_count_week = find_new_release_count(7, filter_statement)
    st.metric("New releases this week:", game_count_week)
    avg_price = find_mean_price(filter_statement)
    st.metric("💰 Average price:", avg_price)
with col2:
    game_count_month = find_new_release_count(30, filter_statement)
    st.metric("New releases (Last 30 days):", game_count_month)
    free_pct = find_free_count(filter_statement)
    st.metric("Free games released (Last 30 days):", free_pct)


st.subheader("Recent Release Activity")
count_releases_by_day(filter_statement)

st.subheader("Most Common Genres")
most_common_genres(filter_statement)

st.subheader("Price Distribution of Paid Games")
price_distribution_histogram(filter_statement)

st.subheader("Releases by Weekday")
best_weekday(filter_statement)

# st.subheader("Releases by Store")
# releases_by_store()

st.subheader("Average price by Store")
average_price_by_platform(filter_statement)

# st.subheader("Genre Combinations")
# genre_combinations()
