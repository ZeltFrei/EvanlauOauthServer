from datetime import datetime


def parse_datetime(datetime_string: str) -> datetime:
    """
    Parse datetime string to datetime object
    The string format should be "%Y-%m-%dT%H:%M:%S.%fZ"
    :param datetime_string: datetime string
    :return: datetime object
    """
    return datetime.strptime(datetime_string, "%Y-%m-%dT%H:%M:%S.%fZ")
