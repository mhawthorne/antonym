def sanitize_encoding(cls, string):
    # attempting to avoid "ordinal not in range" errors
    return unicode(string).encode("utf-8")
