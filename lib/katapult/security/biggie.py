import base64
import hashlib
import hmac

from google.appengine.api import users

from katapult.requests import RequestHelper


def require_login(error_header, error_message):
    def function_call(f):
        """ decorator that requires admin login to proceed """
        def args_call(*args, **kw):
            handler = args[0]
            helper = RequestHelper(handler)
            if not Authenticator.is_authenticated(handler.request.path, handler.request.method, helper):
                helper.header(error_header, error_message)
                helper.error(403)
            else:
                f(*args, **kw)
        return args_call
    return function_call


class Authenticator:

    HTTP_AUTH_HEADER = "Authorization"

    AUTH_SCHEME = "biggie"

    # returns:
    #   Authentication instance
    @classmethod
    def is_authenticated(cls, path, method, helper):
        logger = self.__logger()

        headers = helper.headers()

        # decode path
        logger.debug("path:'%s', headers:%s" % (path, headers))

        # TODO: return proper challenge in response
        if not self.HTTP_AUTH_HEADER in headers:
            helper.error(401, "unauthorized.")
            return Authentication(False)

        auth = headers[self.HTTP_AUTH_HEADER]
        auth_parts = auth.split(" ")

        if len(auth_parts) != 2:
            helper.error(401, "malformed auth header.")
            return Authentication(False)

        scheme, credentials = auth_parts

        if scheme != self.AUTH_SCHEME:
            helper.error(401, "unrecognized auth scheme.")
            return Authentication(False)

        # credentials format = api_key:signature
        credential_parts = credentials.split(":")

        if len(credential_parts) != 2:
            helper.error(401, "malformed credentials.")
            return Authentication(False)

        key, provided_signature = credential_parts
        accessor = Accessor.find_by_api_key(key)
        if not accessor:
            helper.error(403, "invalid API key")
            return Authentication(False)

        username = accessor.username
        secret = accessor.secret
        
        string_to_hash = u"%s:%s" % (method, path)
        hasher = hmac.new(secret, string_to_hash, hashlib.sha1)
        calculated_signature = base64.b64encode(hasher.digest())

        if provided_signature != calculated_signature:
            logger.warn("signature mismatch -> provided:%s calculated:%s)" % (provided_signature, calculated_signature))
            helper.error(403, "invalid signature.")
            return Authentication(False, accessor)

        return AuthResult(True, accessor)    
