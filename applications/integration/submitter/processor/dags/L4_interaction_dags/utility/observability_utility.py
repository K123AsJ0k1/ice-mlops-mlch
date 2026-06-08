# Check imports and inputs
def observability_utility_table_path(
    source_type: str,
    case_name: str, 
    start_times: list,
    end_times: list,
    debug_prints: bool
) -> str:
    try:
        from datetime import datetime, timezone
        from icebreaker.storage.management import set_object_path
    except ImportError as e:
        raise ImportError("L4_interaction_dags/utility/observability_utility failed to import", e)

    table_object_path = None
    if 0 < len(start_times) or 0 < len(end_times):
        # These are in UTC+0
        oldest_time = min(start_times)
        newest_time = max(end_times)

        oldest_dt_object = datetime.fromtimestamp(oldest_time, tz = timezone.utc)
        newest_dt_object = datetime.fromtimestamp(newest_time, tz = timezone.utc)
        
        oldest_year = oldest_dt_object.strftime('year-%Y')
        oldest_month = oldest_dt_object.strftime('month-%m')
        oldest_day = oldest_dt_object.strftime('day-%d')

        oldest_hour = oldest_dt_object.strftime('%H')
        oldest_minute = oldest_dt_object.strftime('%M')
        oldest_second = oldest_dt_object.strftime('%S')

        newest_hour = newest_dt_object.strftime('%H')
        newest_minute = newest_dt_object.strftime('%M')
        newest_second = newest_dt_object.strftime('%S')

        object_name = 'table' 
        object_name += '-' + oldest_hour 
        object_name += '-' + oldest_minute 
        object_name += '-' + oldest_second 
        object_name += '-range'
        object_name += '-' + newest_hour
        object_name += '-' + newest_minute
        object_name += '-' + newest_second
        object_name += '.parquet'

        table_object_path = set_object_path(
            object_name = 'metr',
            path_replacers = {
                'name': source_type
            },
            path_names = [
                case_name,
                oldest_year,
                oldest_month,
                oldest_day,
                object_name
            ],
            debug_prints = debug_prints
        )
    return table_object_path
# Check imports and inputs
def observability_utility_table_timerange(
    object_name: str
) -> any:
    try:
        import re
        from datetime import time
    except ImportError as e:
        raise ImportError("interaction_dags/local_func/observability failed to import", e)

    time_match = re.search(r'(\d{2}-\d{2}-\d{2})-range-(\d{2}-\d{2}-\d{2})', object_name)
    timerange = None
    if time_match:
        start_str, end_str = time_match.groups()
        start_t = time(*map(int, start_str.split('-')))
        end_t = time(*map(int, end_str.split('-')))
        timerange = (start_t, end_t)
    return timerange
# Check imports and inputs
def observability_utility_range_check(
    existing_paths: list, 
    object_path: str
) -> bool:
    object_path_split = object_path.split('.')[0].split('/')

    folder_prefix = '/'.join(object_path_split[:-1])
    new_timerange = observability_utility_table_timerange(
        object_name = object_path_split[-1]
    ) 
    
    relevant_matches = [p for p in existing_paths if p.startswith(folder_prefix)]
    path_exists = False 
    
    if 0 < len(relevant_matches):
        for existing_path in relevant_matches:
            existing_path_split = existing_path.split('.')[0].split('/')
            
            old_timerange = observability_utility_table_timerange(
                object_name = existing_path_split[-1]
            )
            
            new_start, new_end = new_timerange
            old_start, old_end = old_timerange
            if (new_start < old_end) and (old_start < new_end):
                path_exists = True
                
    return path_exists
# Check imports and inputs
def observability_utility_table_timestamp(
    source_type: str,
    case_name: str,
    timestamp: int,
    table_name: str,
    debug_prints: bool
) -> str:
    try:
        from datetime import datetime, timezone
        from icebreaker.storage.management import set_object_path
    except ImportError as e:
        raise ImportError("interaction_dags/local_func/observability failed to import", e)

    table_object_path = None
    if 0 < timestamp:
        timestamp_dt_object = datetime.fromtimestamp(timestamp, tz = timezone.utc)
        
        oldest_year = timestamp_dt_object.strftime('year-%Y')
        oldest_month = timestamp_dt_object.strftime('month-%m')
        oldest_day = timestamp_dt_object.strftime('day-%d')

        oldest_hour = timestamp_dt_object.strftime('%H')
        oldest_minute = timestamp_dt_object.strftime('%M')
        oldest_second = timestamp_dt_object.strftime('%S')
        oldest_microsecond = timestamp_dt_object.strftime('%f')

        object_name = 'table-' + table_name
        object_name += '-' + oldest_hour 
        object_name += '-' + oldest_minute 
        object_name += '-' + oldest_second 
        object_name += '-' + oldest_microsecond
        object_name += '.parquet'

        table_object_path = set_object_path(
            object_name = 'metr',
            path_replacers = {
                'name': source_type
            },
            path_names = [
                case_name,
                oldest_year,
                oldest_month,
                oldest_day,
                object_name
            ],
            debug_prints = debug_prints
        )
    return table_object_path