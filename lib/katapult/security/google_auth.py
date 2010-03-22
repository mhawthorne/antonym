from google.appengine.api import users

from katapult.requests import RequestHelper


class Messages:
    
    LOGIN_REQUIRED = "login-required"


def require_user(error_header, *emails):
    """ decorator that requires specified user to be logged in """
    def function_call(f):
        def args_call(*args, **kw):
            handler = args[0]
            helper = RequestHelper(handler)
            user = users.get_current_user()
            if not user:
                helper.header(error_header, Messages.LOGIN_REQUIRED)
                helper.error(403)
            elif not emails or (not user.email() in emails):
                helper.header(Headers.APP_ERROR, "unauthorized-user")
                helper.error(403)
            else:
                f(*args, **kw)
        return args_call
    return function_call

def require_login(error_header):
    def function_call(f):
        """ decorator that requires admin login to proceed """
        def args_call(*args, **kw):
            handler = args[0]
            helper = RequestHelper(handler)
            if not users.get_current_user():
                helper.header(error_header, Messages.LOGIN_REQUIRED)
                helper.error(403)
            else:
                f(*args, **kw)
        return args_call
    return function_call

def require_admin(error_header):
    def function_call(f):
        """ decorator that requires admin login to proceed """
        def args_call(*args, **kw):
            handler = args[0]
            helper = RequestHelper(handler)
            if not users.is_current_user_admin():
                helper.header(error_header, "admin-required")
                helper.error(403)
            else:
                f(*args, **kw)
        return args_call
    return function_call