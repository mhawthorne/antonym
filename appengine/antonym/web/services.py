from katapult.security.google_auth import require_user
from katapult.security.biggie import require_login
from katapult.security import digest

from antonym.web import service_users


_digest_users = service_users.digest_map()


def require_service_user():
    """ decorator to ensure service methods are invoked only by the mastermind. """
    return require_user(Services.ERROR_HEADER, Services.API_USER)


def require_biggie_user():
    return require_login(Services.ERROR_HEADER)


def require_digest_login():
    return digest.require_login('antonym', _digest_users, Services.ERROR_HEADER, Messages.LOGIN_REQUIRED)


class Services:

    ERROR_HEADER = "X-Antonym-Error"
    
    API_USER = "meh.subterfusion@gmail.com"


class Messages:
    """ error messages """
    
    LOGIN_REQUIRED = 'login-required'