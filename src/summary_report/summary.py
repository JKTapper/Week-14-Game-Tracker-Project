"""This module assembles key game metrics and charts into a HTML report using weekly data."""

from datetime import datetime
from visuals import count_releases_by_day, most_common_genres, price_distribution_histogram, \
    find_mean_price, find_new_release_count, find_free_count, DAY_RANGE


def create_summary_html() -> str:
    mean_price = find_mean_price()
    releases_week = find_new_release_count(DAY_RANGE)
    free_games_count = find_free_count()
    report_date = datetime.now().strftime("%d-%m-%Y")

    count_releases_by_day()
    most_common_genres()
    price_distribution_histogram()

    html_content = f"""
    <html>
        <body>
            <h1>New Game Tracker Weekly Report</h1>
            <p><i>Date: {report_date}</i></p>

            <h2>This Week's Key Stats</h2>
            <ul>
                <li><b>New Releases:</b> {releases_week}</li>
                <li><b>Average Price (Paid Games):</b> {mean_price}</li>
                <li><b>Total Free Games:</b> {free_games_count}</li>
            </ul>

            <h2>Recent Release Activity</h2>
            <img src="cid:release_count_graph" alt="Releases by day line graph">

            <h2>Most Common Genres</h2>
            <img src="cid:genre_bar_chart" alt="Top 5 most common genres graph">

            <h2>Price Distribution of Paid Games</h2>
            <img src="cid:hist_chart" alt="Price distribution histogram">
        </body>
    </html>
    """
    return html_content
