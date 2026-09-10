import datetime
from datetime import datetime as dat
from datetime import timedelta, timezone

import pytz


def has_expired(expiry: int) -> bool:
    """
    Checks if the given expiry timestamp has already passed.

    Args:
        expiry (int): The expiry timestamp to check.

    Returns:
        bool: True if the expiry timestamp has already passed, False otherwise.
    """
    return expiry <= get_current_timestamp()


def get_current_timestamp() -> int:
    """
    Returns the current Unix timestamp in milliseconds.

    Returns:
        An integer representing the current Unix timestamp in milliseconds.
    """
    # Get the current timezone-aware datetime object in UTC
    current_time = datetime.datetime.now(timezone.utc)

    # Get the Unix epoch timestamp in seconds
    timestamp_seconds = current_time.timestamp()

    return int(timestamp_seconds * 1000)


def get_timestamp(expires_delta: timedelta = timedelta(hours=1)) -> int:
    """
    Generates a Unix epoch timestamp in milliseconds, given an optional time delta.

    Args:
        expires_delta: A timedelta object representing the time delta to add to the current time. Defaults to 1 hour.

    Returns:
        An integer representing the Unix epoch timestamp in milliseconds.
    """
    # Get the current timezone-aware datetime object in UTC
    current_time = datetime.datetime.now(timezone.utc)
    current_time = current_time + expires_delta

    # Get the Unix epoch timestamp in seconds
    timestamp_seconds = current_time.timestamp()

    return int(timestamp_seconds * 1000)


def get_current_date_time() -> datetime.datetime:
    """
    Returns the current date and time in UTC timezone.

    Returns:
        datetime.datetime: A datetime object representing the current date and time in UTC timezone.
    """
    return datetime.datetime.now(timezone.utc)


def get_n_previous_day_timestamp(days) -> int:
    """
    Returns the UNIX timestamp in milliseconds of `days` number of days ago at midnight UTC.
    Args:
        days (int): The number of days ago to retrieve the timestamp for.
    Returns:
        float: The timestamp in milliseconds.
    """
    prev_time = datetime.datetime.now(timezone.utc) - datetime.timedelta(days=days)
    midnight_prev_time = datetime.datetime.combine(prev_time, datetime.time.min)
    return int(midnight_prev_time.timestamp() * 1000)


def get_today_midnight_time() -> int:
    """
    Returns the Unix timestamp in milliseconds for midnight of the current day in UTC timezone.
    Returns a float representing the Unix timestamp in milliseconds for midnight of the current day in UTC timezone.
    """
    now = datetime.datetime.now(tz=timezone.utc)
    midnight_date = datetime.datetime(now.year, now.month, now.day, tzinfo=timezone.utc)  # Midnight
    return int(midnight_date.timestamp() * 1000)


def get_local_date_and_time_by_timezone(date: int, timezone_data: str):
    local_timezone = pytz.timezone(timezone_data)
    date_time = dat.fromtimestamp(date / 1000, tz=pytz.utc)
    date_time = date_time.astimezone(local_timezone)
    current_date = date_time.strftime('%B %d, %Y')
    current_time = date_time.strftime('%I:%M %p')
    return current_date, current_time


def date_to_milliseconds(date_string: str, date_format: str = '%d-%m-%Y') -> int:
    # Create a datetime object from the date string
    date_object = datetime.datetime.strptime(date_string, date_format).replace(tzinfo=timezone.utc)

    # Get the Unix epoch timestamp in seconds
    timestamp_seconds = date_object.timestamp()

    return int(timestamp_seconds * 1000)


def get_midnight_epoch_based_on_timezones(epoch_ms, timezone_data='Asia/Kolkata'):
    """
    Returns the midnight time of the local timezone in epoch milliseconds.

    Args:
        epoch_ms (int): Epoch time in milliseconds.
        timezone_data (str, optional): Timezone data. Defaults to 'Asia/Kolkata'.

    Returns:
        int: Midnight time of the local timezone in epoch milliseconds.
    """
    time_zone = pytz.timezone(timezone_data)
    dt = datetime.datetime.fromtimestamp(epoch_ms / 1000, time_zone)
    midnight_dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(midnight_dt.timestamp() * 1000)


def get_midnight_epoch_gmt(epoch_ms):
    """
    Returns the midnight (12:00 AM) time in GMT (UTC) for the given epoch in milliseconds.

    Args:
        epoch_ms (int): Epoch time in milliseconds.

    Returns:
        int: Midnight time in GMT (UTC) in epoch milliseconds.
    """
    utc = pytz.UTC
    dt = datetime.datetime.fromtimestamp(epoch_ms / 1000, utc)  # convert to datetime in UTC
    midnight_utc = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return int(midnight_utc.timestamp() * 1000)


def get_date_range_time(month, year) -> int:
    midnight_date = datetime.datetime(year, month, 1, tzinfo=timezone.utc)  # Midnight
    return int(midnight_date.timestamp() * 1000)


def get_previous_timerange():
    current_time = datetime.datetime.now(timezone.utc)

    # Add the specified number of minutes
    future_time = current_time - timedelta(minutes=10)

    # Get the Unix epoch timestamp in seconds
    timestamp_seconds = future_time.replace(second=0, microsecond=0).timestamp()
    start_time_ms = int(timestamp_seconds * 1000)
    return start_time_ms


def timestamp_to_epoch_ms(timestamp: str) -> int:
    """
    Converts a given timestamp in seconds to epoch milliseconds.

    Args:
        timestamp (str): The ISO 8601 timestamp.

    Returns:
        int: The equivalent epoch time in milliseconds.
    """
    try:
        if not timestamp:
            raise ValueError('timestamp is missing or empty')

        # Parse ISO 8601 string - fromisoformat handles 'Z' suffix since Python 3.11
        # For older Python versions, we keep the replace for compatibility
        if timestamp.endswith('Z'):
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = datetime.datetime.fromisoformat(timestamp)

        # Convert to epoch in milliseconds
        return int(dt.timestamp() * 1000)

    except (ValueError, TypeError, AttributeError) as e:
        raise ValueError(f'Invalid timestamp format: {e}') from e
