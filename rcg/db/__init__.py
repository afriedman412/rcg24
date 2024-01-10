# db init
import os
from typing import Tuple, Union

from pymysql import connect
from pymysql.connections import Connection
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine


def make_sql_connection() -> Connection:
    conn = connect(
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PW"),
        host=os.getenv("MYSQL_URL"),
        database=os.getenv("MYSQL_DB"),
        port=3306
    )
    return conn


def make_sql_engine() -> Engine:
    """
    For using pandas .to_sql() -- INSERT wasn't working otherwise
    """
    if os.getenv("MYSQL_PW"):
        connection_string = "mysql://{}:{}@{}/{}".format(
            *[os.getenv(var) for var in [
                'MYSQL_USER',
                'MYSQL_PW',
                'MYSQL_URL',
                'MYSQL_DB']]
                )
    else:
        connection_string = "mysql://{}@{}/{}".format(
            *[os.getenv(var) for var in [
                'MYSQL_USER',
                'MYSQL_URL',
                'MYSQL_DB']]
                )
    return create_engine(connection_string)


def db_query(
    q: str,
    conn: Union[Connection, None] = None,
    commit: bool = False,
    close: bool = True
) -> Tuple[Tuple]:
    if not conn:
        conn = make_sql_connection()
    with conn.cursor() as cur:
        cur.execute(q)
        if commit:
            conn.commit()
    data = cur.fetchall()
    if close:
        conn.close()
    return data


# def db_query(q: str) -> Union[CursorResult, None]:
#     """
#     INPUTS:
#         q (str): sql query string

#     OUPUT:
#         data (CursorResult): output of running q
#     """
#     engine = make_sql_engine()
#     with engine.connect() as conn:
#         result = conn.execute(text(q))
#     return result
