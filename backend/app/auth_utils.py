from functools import wraps

from flask import jsonify, session


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("staff_id"):
            return jsonify({"error": "authentication required"}), 401
        return view_func(*args, **kwargs)

    return wrapped
