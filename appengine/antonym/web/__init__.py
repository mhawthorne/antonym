import urllib

import simplejson as json

from katapult.core import Hashes


def unicode_hash(hash):
    unicode_hash = {}
    for k, v in hash.iteritems():
        unicode_hash[k.encode("utf-8")] = v
    return unicode_hash

def read_json_fields(helper, *fields, **kw):
    logger = kw.get("logger", None)
    success = False

    json_body = helper.request().body
    if not json_body:
        helper.error(400, "body required")
        return success, tuple()

    decoded_body = urllib.unquote(json_body)
    try:
        field_hash = json.loads(decoded_body)
    except json.JSONDecodeError, e:
        msg = "malformed json: %s" % decoded_body
        helper.error(400, msg)
        if logger:
            logger.warn(msg)
        return success, tuple()

    # de-unicodes keys
    decoded_hash = unicode_hash(field_hash)

    result = Hashes.fetch_fields(decoded_hash, fields)
    if result.missing_fields:
        success = False
        msg = "missing fields: %s" % result.missing_fields
        helper.error(400, msg)
        if logger:
            logger.info(msg)
    else:
        success = True
    # returning a (success, values) tuple is a bit weird,
    # but they seem to do it in erlang a lot
    return success, result.values

def opensearch_wrapper(results, query, total_results=0, items_per_page=0, start_index=0):
    """ wraps results with opensearch variables """
    total_results = 0
    items_per_page = 0
    start_index = 0
    wrapper = { "totalResults": total_results,
        "startIndex": start_index,
        "itemsPerPage": items_per_page,
        "query": query, 
        "results": results }
    return wrapper