from datetime import datetime
import re

_default_seperator = "."

def day_seconds(days):
    return days * hour_seconds(24)

def hour_seconds(hours):
    return hours * minute_seconds(60)

def minute_seconds(minutes):
    return minutes * 60

def format(dtime, separator=_default_seperator):
    # injects "fake" underscores into string to be replaced by real separator
    return re.sub("_", separator, dtime.strftime("%Y_%m_%d_%H_%M_%S"))

def timestamp(separator=_default_seperator):
    return format(datetime.now(), separator=separator)

def http_timestamp():
    return format_date_time(time.mktime(datetime.now().timetuple()))

def http_timestamp_future(**kw):
    """
    builds a http timestamp
    
    keywords:
        passed directly to timedelta constructor
    """
    expiration = datetime.now() + timedelta(**kw)
    return format_date_time(time.mktime(expiration.timetuple()))