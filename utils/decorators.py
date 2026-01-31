from flask import session, redirect
from functools import wraps


def login_required(f):

    loginEnabled = True
    # For debug testing
    
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For debug
        if loginEnabled and session.get("user_id") == "Insert ID":
            session["user_id"] = None
        elif not loginEnabled and session.get("user_id") is None:
            session["user_id"] = "Insert ID"

        if session.get("user_id") is None: #or session.get("username") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function
