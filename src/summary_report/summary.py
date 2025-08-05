from datetime import datetime
from visuals import count_releases_by_day, most_common_genres, price_distribution_histogram, \
    find_mean_price, find_new_release_count, find_free_count


def create_summary_html() -> str:
    """
    Gathers metrics and charts and creates a HTML weekly report summary.

    Returns:
        A string containing the HTML for the report.
    """
    mean_price = find_mean_price()
    releases_week = find_new_release_count(7)
    free_games_count = find_free_count()
    report_date = datetime.now().strftime("%d-%m-%Y")

    releases_chart_obj = count_releases_by_day()
    genres_chart_obj = most_common_genres()
    price_hist_obj = price_distribution_histogram()

    html_content = f"""
    <html>
        <head>
            <title>New Games Tracker Report</title>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega@5"></script>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-lite@5.20.1"></script>
            <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
        </head> 
        <body style="font-family: sans-serif;">
            <h1>New Games Tracker Weekly Report</h1>
            <p><i>Date: {report_date}</i></p>

            <h2>This Week's Key Stats</h2>
            <ul>
                <li><b>New Releases:</b> {releases_week}</li>
                <li><b>Average Price (Paid Games):</b> {mean_price}</li>
                <li><b>Total Free Games:</b> {free_games_count}</li>
            </ul>

            <h2>Recent Release Activity</h2>
            <div id="releases-chart"></div>
            
            <h2>Most Common Genres</h2>
            <div id="genres-chart"></div>

            <h2>Price Distribution of Paid Games</h2>
            <div id="price-distribution-chart"></div>

            <script>
                vegaEmbed("#releases-chart", {releases_chart_obj.to_json()});
                vegaEmbed("#genres-chart", {genres_chart_obj.to_json()});
                vegaEmbed("#price-distribution-chart", {price_hist_obj.to_json()});
            </script>
        </body>
    </html>
    """
    return html_content
