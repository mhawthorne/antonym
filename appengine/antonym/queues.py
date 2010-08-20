from katapult.caching import Cache, MemcacheQueue
from katapult.dates import day_seconds

def get_activity_queue():
    # bumped expiration time from 1 to 2 days to study effect.
    # it's currently only caching ~4 hours of activity
    return MemcacheQueue("activity", time=day_seconds(2))