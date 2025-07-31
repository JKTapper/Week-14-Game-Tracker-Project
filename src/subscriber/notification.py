from app import connect_to_rds
import pandas as pd


def get_sub_notifications():
    connection = connect_to_rds()
    with connection.begin() as conn:
        print(pd.read_sql("select * from subscriber_genre_assignment", conn))



if __name__ == "__main__":
    get_sub_notifications()