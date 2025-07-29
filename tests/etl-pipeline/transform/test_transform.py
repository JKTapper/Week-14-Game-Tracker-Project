import pandas as pd
import pytest
from src.elt_pipeline.transform.transform import get_assignment_df

get_assignment_df_test_data = [(
    pd.DataFrame({
        'friend_id': [1, 2],
        'friend_name': ['Hugo', 'Susan'],
        'clubs': [['Tennis', 'Chess'], ['Chess', 'Knitting']]
    }),
    pd.DataFrame({
        'club_name': ['Tennis', 'Chess', 'Knitting'],
        'club_id': [1, 2, 3]
    }),
    'friend',
    'club',
    pd.DataFrame({
        'friend_id': [1, 1, 2, 2],
        'club_id': [1, 2, 2, 3]
    })
)]


@pytest.mark.parametrize('main_df,reference_df,main_df_name,reference_df_name,assignment_df', get_assignment_df_test_data)
def test_get_assignment_df(main_df, reference_df, main_df_name, reference_df_name, assignment_df):
    assert get_assignment_df(main_df, reference_df,
                             main_df_name, reference_df_name).equals(assignment_df)
