# pylint: disable=import-error
'''Module importing big function and containing lambda handler'''
from transform_and_load_to_rds import main


def handler(event, context):
    '''Lambda handler that runs the transform and load'''
    try:
        main()
        print(f'{event}: Lambda time remaining in MS:',
              context.get_remaining_time_in_millis())
        return {'statusCode': 200}
    except (TypeError, ValueError, IndexError) as e:
        return {'statusCode': 500, 'error': str(e)}
