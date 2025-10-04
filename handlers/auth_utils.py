from functools import wraps
from flask import g, redirect, url_for, abort


def require_role(role: str):
    """Decorator to require a specific role on a view.

    If the user isn't logged in, redirect to login. If logged in but role
    mismatches, return 403 Forbidden.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            current = getattr(g, 'current_user_role', None)
            if not current:
                return redirect(url_for('auth.login'))
            if current != role:
                return abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator


def require_any_role(*roles):
    """Decorator to require any of the provided roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            current = getattr(g, 'current_user_role', None)
            if not current:
                return redirect(url_for('auth.login'))
            if current not in roles:
                return abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator
