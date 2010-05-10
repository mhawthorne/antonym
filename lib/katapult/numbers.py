def safe_int(raw_int, default=0):
    """
    returns:
        an integer, or default if raw_int is not a valid integer
    """
    try:
        return int(raw_int)
    except ValueError, e:
        return default