"""
Outloading non-dependant functions here to prevent circular imports!
"""
from datetime import datetime as dt
from datetime import timedelta

from pytz import timezone

from ..db import db_query


def get_most_recent_chart_date() -> str:
    """
    Gets the most recent chart date.
    """
    most_recent_chart_date = db_query("select max(chart_date) from chart")
    most_recent_chart_date = most_recent_chart_date[0][0]
    return most_recent_chart_date


def get_date(delta: int = 0) -> str:
    """
    Gets today for the Eastern time zone and turns it into a string.

    If delta, returns delta days ago. (delta=1 is yesterday)
    """
    day = timezone('US/Eastern').localize(dt.now())
    if delta:
        day = day - timedelta(delta)
    day = day.strftime("%Y-%m-%d")
    return day


def query_w_date(q: str, date_: str = None):
    """
    Easier to make this a function than to do the date logic every time.
    """
    if not date_:
        date_ = get_date()
    return db_query(q.format(date_))
