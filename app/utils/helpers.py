from flask import request


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
