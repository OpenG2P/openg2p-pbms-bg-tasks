from sqlalchemy import TextClause, text


def construct_intersect_query(sql_queries: list) -> TextClause:
    """Convert list of SQL queries into a single SQL query using INTERSECT"""
    try:
        if not sql_queries or not isinstance(sql_queries, list):
            return None

        intersect_query = " INTERSECT ".join(sql_queries)
        return text(intersect_query)
    except Exception as _:
        return None
