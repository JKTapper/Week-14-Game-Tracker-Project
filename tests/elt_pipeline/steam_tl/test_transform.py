# pylint: skip-file
"""Test suite for the functions in the transformation code"""
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch
from src.elt_pipeline.steam_tl.transform_and_load_to_rds import get_assignment_df, process_data, extract_memory_requirements, get_reference_data

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


@patch('src.elt_pipeline.steam_tl.transform_and_load_to_rds.get_or_create_id')
@pytest.mark.parametrize(
    'main_df,reference_df,main_df_name,reference_df_name,assignment_df',
    get_assignment_df_test_data
)
def test_get_assignment_df(mock_get_or_create_id, main_df, reference_df, main_df_name, reference_df_name, assignment_df):
    """Tests whether get_assignment_df correctly generates an assignment table"""
    name_to_id = {'Tennis': 1, 'Chess': 2, 'Knitting': 3}
    mock_get_or_create_id.side_effect = lambda conn, table, name_col, name_val, id_col: name_to_id[
        name_val]
    conn = MagicMock()
    result = get_assignment_df(
        main_df, main_df_name, reference_df_name, conn)

    assert result.equals(assignment_df)


process_data_test_data = [
    (pd.DataFrame({
        "Test": [1, 2, 3],
        "Unwanted": [4, 5, 6],
        "keeps": [7, 8, 9]
    }), [
        {'old_name': 'Test', 'new_name': 'test', 'translation': lambda x: 2*x},
        {'name': 'keeps', 'translation': str},
        {'name': 'ten', 'value': 10}
    ],
        pd.DataFrame({
            "test": [2, 4, 6],
            "keeps": ['7', '8', '9'],
            "ten": [10, 10, 10]
        }))

]


@pytest.mark.parametrize(
    "unprocessed_info,config,processed_info",
    process_data_test_data
)
def test_process_data(unprocessed_info, config, processed_info):
    """Tests whether process_data correctly generates an processed table"""
    assert process_data(unprocessed_info, config).equals(processed_info)


extract_memory_requirements_test_data = [
    (
        {"minimum": r"""<strong>Minimum:</strong><br><ul class=\"bb_ul\">
         <li><strong>OS:</strong> Windows 10/11<br></li>
         <li><strong>Processor:</strong> 1.8+ GHz or better<br></li>
         <li><strong>Memory:</strong> 1 GB RAM<br></li>
         <li><strong>Graphics:</strong> Intel UHD Graphics 620 or better<br></li>
         <li><strong>Storage:</strong> 1 GB available space</li></ul>"""},
        '1 GB'
    )

]


@pytest.mark.parametrize(
    "requirements,memory_requirements",
    extract_memory_requirements_test_data
)
def test_extract_memory_requirements(requirements, memory_requirements):
    """Tests whether extract_memory_requirements correctly reads memory requirements"""
    assert extract_memory_requirements(
        requirements) == memory_requirements


get_reference_data_test_data = [(
    pd.DataFrame({
        'friend_id': [1, 2],
        'friend_name': ['Hugo', 'Susan'],
        'clubs': [['Tennis', 'Chess'], ['Chess', 'Knitting']]
    }),
    pd.DataFrame({
        'club_name': ['Tennis'],
        'club_id': [1]
    }),
    'club'
)]


@pytest.mark.parametrize(
    'main_df,reference_df,reference_df_name',
    get_reference_data_test_data
)
def test_get_reference_data(main_df, reference_df, reference_df_name):
    """Tests whether get_reference_data correctly generates a secondary table"""
    reference_table = get_reference_data(main_df, reference_df,
                                         reference_df_name)
    assert set(reference_table['all']['club_name']) == {
        'Tennis', 'Chess', 'Knitting'}
    assert set(reference_table['all']['club_id']) == {
        1, 2, 3}
    assert set(reference_table['new']['club_name']) == {
        'Chess', 'Knitting'}
    assert set(reference_table['new']['club_id']) == {
        2, 3}
