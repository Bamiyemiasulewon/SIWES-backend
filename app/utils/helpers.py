from functools import wraps

from flask import jsonify, request
from flask_jwt_extended import current_user


def json_error(status_code, error, message, details=None):
    payload = {"error": error, "message": message, "status_code": status_code}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status_code


def paginate_query(query, page=None, per_page=None):
    page = int(page or request.args.get("page", 1))
    per_page = int(per_page or request.args.get("per_page", 10))
    per_page = min(max(per_page, 1), 100)

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return paginated


def parse_bool(value):
    if value is None:
        return None
    return str(value).lower() in {"1", "true", "yes", "y"}


def require_roles(*allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user or current_user.role not in allowed_roles:
                return json_error(403, "forbidden", "Access denied")
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user or current_user.role != "admin":
            return json_error(403, "forbidden", "Admin access required")
        return fn(*args, **kwargs)
    return wrapper
