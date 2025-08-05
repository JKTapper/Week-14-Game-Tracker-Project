from summary import create_summary_html


def handler(event, context):
    """
    Handles Lambda event to generate and return a weekly game report.
    """
    html_content = create_summary_html()
    if html_content:
        return {
            'statusCode': 200,
            'body': html_content
        }
    else:
        return {
            'statusCode': 404,
            'body': "Error retrieving last week's data"
        }
