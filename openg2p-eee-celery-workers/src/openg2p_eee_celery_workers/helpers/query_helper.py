import json

from sqlalchemy import text


def construct_intersect_query(sql_query_json):
    """Convert stored JSON SQL queries into a single SQL query using INTERSECT."""
    try:
        queries = json.loads(sql_query_json)
        if not queries or not isinstance(queries, list):
            return None

        intersect_query = " INTERSECT ".join(queries)
        return text(intersect_query)
    except json.JSONDecodeError:
        return None
