import datetime
import re

from dateutil.parser import parse


def get_current_datetime_string():
    """
    Get the datetime string which is used to indicate date.
    """
    return datetime.datetime.now().isoformat()[:-7]


def get_current_filename():
    """
    Get the name for the most recent capture.
    """
    return 'capture-{0}.jpg'.format(get_current_datetime_string())


def get_datetime_from_name(filename):
    """
    Extract datetime object from filename.
    Returns None if name is invalid.
    """

    try:
        regex = '^.+?-{1}(.+)\.jpg'
        matches = re.search(regex, filename, re.IGNORECASE)

        if matches is None:
            return None

        date_string = matches.group(1)
        dt = parse(date_string)
        return dt

    except Exception as err:
        print('Exception while parsing filename {0}: {1}'.format(filename, err))

    return None
