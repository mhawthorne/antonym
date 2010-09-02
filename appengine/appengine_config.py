import logging


def webapp_add_wsgi_middleware(app):
    logging.basicConfig(level=logging.DEBUG)
    
    from google.appengine.ext.appstats import recording
    # disabling to debug django issue
    app = recording.appstats_wsgi_middleware(app)
    return app