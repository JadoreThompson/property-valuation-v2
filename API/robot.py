from typing import Tuple, List


def get_existing_user(cur, email, table="users", field='1'):
    cur.execute(f"""\
        SELECT {field}\
        FROM {table}\
        WHERE email = %s;
    """, (email, ))
    return cur.fetchone()


def get_insert_data(data: dict) -> Tuple[List, str, List]:
    cols = [key for key in data if data[key] is None]
    placeholders = ", ".join(["%s"] * len(cols))
    values = [(data[key]) for key in cols]
    return cols, placeholders, values