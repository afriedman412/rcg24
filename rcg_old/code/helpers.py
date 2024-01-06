"""
Outloading non-dependant functions here to prevent circular imports!
"""
import os
from ..db import db_query, db_commit
from pytz import timezone
from datetime import datetime as dt
from datetime import timedelta

def local_check():
    return os.environ.get('LOCAL') in ("True", "true", 1)

def most_recent_chart_date() -> str:
    """
    Gets the most recent chart date.
    """
    checker = db_query("select max(chart_date) from chart")
    return checker[0][0]

def get_date(delta=0) -> str:
    """
    Gets today for the Eastern time zone and turns it into a string.

    If delta, returns delta days ago. (delta=1 is yesterday)
    """
    day = timezone('US/Eastern').localize(dt.now())
    if delta:
        day = day - timedelta(delta)
    return day.strftime("%Y-%m-%d")

def query_w_date(q: str, date_: str=None, local: bool=False):
    """
    Easier to make this a function than to do the date logic every time.
    """
    if not date_:
        date_ = get_date()
    return db_query(q.format(date_), local)