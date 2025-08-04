"""
For now script queries subscribers and the genres they are assigned to
To be used to send emails when SES is set up
"""
import pandas as pd
from form import connect_to_rds


def get_sub_notifications():
    """
    Query RDS subcribers and the genres they want email notifications
    """
    connection = connect_to_rds()
    with connection.begin() as conn:
        print(pd.read_sql("""select * from subscriber_genre_assignment
        where email_notifications = true""", conn))



if __name__ == "__main__":
    get_sub_notifications()
