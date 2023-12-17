from flask import redirect, session, url_for

from functools import wraps

import re

# TODO: Create decorator function for Spotify connection -- can that & the
# login decorator work together?


# Decorator function for routes that require user to be logged in
def is_logged_in(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if "jammer_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)

    return decorator


# Check that password is 8-30 chars with at least 1 capital, 1 lowercase, 1 num,
# & 1 non-alphanumeric/whitespace symbol
def is_valid_password(password):
    pw_re = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^A-Za-z\d\s]).{8,30}$")
    if not pw_re.match(password):
        return False
    return True


# Exception class for business logic issues
class AppError(Exception):
    pass


def clear_spotify_session():
    session.pop("access_token", None)
    session.pop("refresh_token", None)
    session.pop("spotify_auth_state", None)


def clear_user_data():
    session.pop("has_loaded_page", None)
    session.pop("jammer_id", None)
    session.pop("email", None)
    session.pop("username", None)
    session.pop("is_timing_started", None)
