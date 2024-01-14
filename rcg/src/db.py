# db init
import os
from typing import Any, Union

from pymysql import connect
from pymysql.connections import Connection
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine


def make_sql_connection() -> Connection[Any]:
    if "MYSQL_PW" in os.environ:
        conn = connect(
            user=os.environ["MYSQL_USER"],
            password=os.environ["MYSQL_PW"],
            host=os.environ["MYSQL_URL"],
            database=os.environ["MYSQL_DB"],
            port=3306
        )
    else:
        conn = connect(
            user=os.environ["MYSQL_USER"],
            host=os.environ["MYSQL_URL"],
            database=os.environ["MYSQL_DB"],
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
    conn: Union[Connection[Any], None] = None,
    commit: bool = False,
    close: bool = True
) -> Any:
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
