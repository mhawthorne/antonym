import logging
import traceback

from google.appengine.api import users
from google.appengine.api.users import User
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import login_required, run_wsgi_app

from katapult.requests import RequestHelper

from antonym.accessors import ConfigurationAccessor
from antonym.web.tweeter import TwitterConnector


class OAuthHandler(webapp.RequestHandler):
    
    _rtoken_key_cookie = "oauth-rtoken-key"
    _rtoken_secret_cookie = "oauth-rtoken-secret"
    
    @login_required
    def get(self):
        helper = RequestHelper(self)
        try:
            if not users.is_current_user_admin():
                helper.error(403, "admin required")
                return
            
            oauth_token = self.request.get("oauth_token")
            if not oauth_token:
                # initial request, I store the request token key/secret as cookies and redirect to twitter's auth page
                request_token, auth_url = TwitterConnector.get_request_token_and_auth_url()
                logging.debug("request token key:%s, secret:%s" % (request_token.key, request_token.secret))
                
                helper.set_cookie("%s=%s; path=/" % (self._rtoken_key_cookie, request_token.key))
                helper.set_cookie("%s=%s; path=/" % (self._rtoken_secret_cookie, request_token.secret))
                helper.write_text("redirecting request token %s to %s" % (request_token.to_string(), auth_url))
                self.redirect(auth_url)
            else:
                # post verification request
                key = self.request.cookies.get(self._rtoken_key_cookie, None)
                secret = self.request.cookies.get(self._rtoken_secret_cookie, None)
                if not (key and secret):
                    helper.error(400, "key and secret not stored as cookies")
                    return
                access_token = TwitterConnector.get_access_token(key, secret)
                token_string = access_token.to_string()
                ConfigurationAccessor.update(twitter_access_token=token_string)
                helper.write_text("saved access token %s" % token_string)
        except Exception, e:
            msg = traceback.print_exc()
            helper.error(500, msg)


application = webapp.WSGIApplication([
    ('/-/oauth', OAuthHandler)])

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    main()