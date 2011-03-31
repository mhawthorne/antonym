import logging
import traceback


def sanitize_encoding(string):
    # attempting to avoid "ordinal not in range" errors
    
    # not sure exactly what's going on here:
    # 1) does the logging module convert strings to ascii
    # 2) is sys.getdefaultencoding() relevent?
    
    # return string if type(string) is unicode else unicode(string, "utf-8", "replace")
    if not isinstance(string, unicode):
        try:
            string = _unicode(string, "utf8", "replace")
        except TypeError, e:
            logging.error("'%s' (%s)\n%s" % (string, type(string), traceback.format_exc()))
            raise e
    # return string.encode("ascii", "replace") 
    return string.encode("ascii", "ignore") 

def _unicode(*args):
    """ mock enabler """
    return unicode(*args)