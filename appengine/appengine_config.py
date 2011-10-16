import logging
import os

from google.appengine.ext.appstats import recording

# the "f" is to avoid favico.ico requests
apptrace_URL_PATTERNS  = ['^/[^f_-].*$']

# TODO: dynamically load all module names?
# apptrace_TRACE_MODULES = [ 'antonym.mixer', 'antonym.accessors', 'antonym.model' ]


def is_prod():
    return not os.environ.get('SERVER_SOFTWARE', '').startswith('Development')
    
def webapp_add_wsgi_middleware(app):
    logging.basicConfig(level=logging.DEBUG)

    # disabling appstats until log noise is fixed
    # app = recording.appstats_wsgi_middleware(app)
    
    # adds apptrace profiling if running locally
    # if not is_prod():
    #     from apptrace.middleware import apptrace_middleware
    #     app = apptrace_middleware(app)
    
    return app