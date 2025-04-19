from datetime import datetime

def get_time_now() -> datetime:
    """Gets the current datetime.

    Returns:
        datetime: The current datetime object.

    Examples:
        >>> current_time = get_time_now()
        >>> print(current_time)
        2024-01-01 12:34:56.789012
    """
    return datetime.now()