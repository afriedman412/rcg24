# db init
from pymysql import connect
import os

def make_sql_connection(local: bool=None):
    if local is None:
        local = True if os.environ.get('LOCAL') in ("True", "true", "1") else False
        print('using env to localize:', "local" if local else "remote")

    if local:
        mysql_conn = connect(
            user=os.environ.get('LOCAL_MYSQL_USER'),
            password=os.environ.get('LOCAL_MYSQL_PW'),
            host=os.environ.get('LOCAL_MYSQL_URL'),
            port=3306,
            db=os.environ.get('LOCAL_MYSQL_DB')
        )

    else:
        mysql_conn = connect(
            user=os.environ.get('MYSQL_USER'),
            password=os.environ.get('MYSQL_PW'),
            host=os.environ.get('MYSQL_URL'),
            port=3306,
            db=os.environ.get('MYSQL_DB')
        )
    
    return mysql_conn

def db_commit(q, local: bool=None):
    conn = make_sql_connection(local)
    with conn.cursor() as cur:
        cur.execute(q)
        conn.commit()
    conn.close()
    return

def db_query(q, local: bool=None):
    conn = make_sql_connection(local)
    with conn.cursor() as cur:
        cur.execute(q)
    data = cur.fetchall()
    conn.close()
    return data



