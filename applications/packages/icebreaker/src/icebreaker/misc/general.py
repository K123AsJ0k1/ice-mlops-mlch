
def set_formatted_user(
    user: str   
) -> any:
    try:
        import re
    except ImportError as e:
        raise ImportError("Failed to import", e)
    return re.sub(r'[^a-z0-9]+', '-', user)

def set_indexed_placeholders(
    text: str, 
    values: list
) -> str :
    try:
        import re
    except ImportError as e:
        raise ImportError("Failed to import", e)

    pattern = r'\{(\d+)\}'
    
    def replacer(match):
        index = int(match.group(1))
        return str(values[index]) if index < len(values) else match.group(0)

    return re.sub(pattern, replacer, text)

def unit_converter(
    value: str,
    bytes: bool
) -> any:
    units = {
        'K': {
            'normal': 1000,
            'bytes': 1024
        },
        'M': {
            'normal': 1000**2,
            'bytes': 1024**2
        },
        'G': {
            'normal': 1000**3,
            'bytes': 1024**3
        },
        'T': {
            'normal': 1000**4,
            'bytes': 1024**4
        },
        'P': {
            'normal': 1000**5,
            'bytes': 1024**5
        }
    }
    
    converted_value = 0
    unit_letter = ''

    character_index = 0
    for character in value:
        if character.isalpha():
            unit_letter = character
            break
        character_index += 1
    
    if 0 < len(unit_letter):
        if not bytes:
            converted_value = int(float(value[:character_index]) * units[unit_letter]['normal'])
        else:
            converted_value = int(float(value[:character_index]) * units[unit_letter]['bytes'])
    else:
        converted_value = value
    return converted_value

def convert_into_seconds(
    given_time: str
) -> int:
    try:
        from datetime import timedelta
    except ImportError as e:
        raise ImportError("Failed to import", e)

    days = 0
    hours = 0
    minutes = 0
    seconds = 0
    milliseconds = 0

    day_split = given_time.split('-')
    if '-' in given_time:
        days = int(day_split[0])

    millisecond_split = day_split[-1].split('.')
    if '.' in given_time:
        milliseconds = int(millisecond_split[1])
    
    hour_minute_second_split = millisecond_split[0].split(':')

    if len(hour_minute_second_split) == 3:
        hours = int(hour_minute_second_split[0])
        minutes = int(hour_minute_second_split[1])
        seconds = int(hour_minute_second_split[2])
    else:
        minutes = int(hour_minute_second_split[0])
        seconds = int(hour_minute_second_split[1])
    
    result = timedelta(
        days = days,
        hours = hours,
        minutes = minutes,
        seconds = seconds,
        milliseconds = milliseconds
    ).total_seconds()
    return result

def test_url(
    target_url: str,
    timeout: int
) -> bool:
    try:
        import requests
    except ImportError as e:
        raise ImportError("Failed to import", e)

    try:
        response = requests.head(
            url = target_url, 
            timeout = timeout
        )
        if response.status_code == 200:
            return True
        return False
    except requests.ConnectionError:
        return False
    
def get_unix_time(
    time: str,
    separator: str,
    largest_first: bool
) -> int:
    try:
        from datetime import datetime, timezone
    except ImportError as e:
        raise ImportError("Failed to import", e)

    time_split = list(map(int,time.split(separator)))
    if largest_first:
        time_split.reverse()
    time = datetime(
        year = time_split[6],
        month = time_split[5],
        day = time_split[4],
        hour = time_split[3],
        minute = time_split[2],
        second = time_split[1],
        microsecond = time_split[0],
        tzinfo = timezone.utc
    ).timestamp()
    return time 