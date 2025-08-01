"""
This module produces a Streamlit dashboard for tracking new game releases, displaying metrics
and charts
"""

import streamlit as st
from visuals import count_releases_by_day, most_common_genres, price_distribution_histogram, \
    find_mean_price, find_new_release_count, find_free_count


st.set_page_config(page_title="Game Tracker Dashboard",
                   page_icon="🎮")
st.title("🎮 New Games Tracker")

col1, col2 = st.columns(2)

with col1:
    game_count_week = find_new_release_count(7)
    st.metric("New releases this week:", game_count_week)
    avg_price = find_mean_price()
    st.metric("💰 Average price:", avg_price)
with col2:
    game_count_month = find_new_release_count(30)
    st.metric("New releases (Last 30 days):", game_count_month)
    free_pct = find_free_count()
    st.metric("Free games released (Last 30 days):", free_pct)


st.subheader("Recent Release Activity")
count_releases_by_day()

st.subheader("Most Common Genres")
most_common_genres()

st.subheader("Price Distribution of Paid Games")
price_distribution_histogram()
