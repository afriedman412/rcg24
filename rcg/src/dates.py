"""
Outloading non-dependant functions here to prevent circular imports!
"""
from datetime import datetime as dt
from datetime import timedelta
from typing import Union
from pytz import timezone
import re

from ..db import db_query


def get_most_recent_chart_date() -> str:
    """
    Gets the most recent chart date.
    """
    most_recent_chart_date = db_query("select max(chart_date) from chart")
    most_recent_chart_date = most_recent_chart_date[0][0]
    return most_recent_chart_date


def get_date(date: Union[str, dt, None] = None, offset: int = 0) -> str:
    """
    If no date is provided, date is today for the Eastern time zone.    

    If offset, returns offset days ago. (offset=1 is yesterday)
    """
    if isinstance(date, str):
        assert re.match(r"\d{4}-\d{2}-\d{2}", date), "chart_date format must be YYYY-MM-DD"
        date = dt.strptime(date, "%Y-%m-%d")
    else:
        date = date if date else timezone('US/Eastern').localize(dt.now())
    if offset:
        date = date - timedelta(offset)
    date = date.strftime("%Y-%m-%d")
    return date


def query_w_date(q: str, date_: str = None):
    """
    Easier to make this a function than to do the date logic every time.
    """
    if not date_:
        date_ = get_date()
    return db_query(q.format(date_))


def verify_date(func):
    def wrapper(chart_date: Union[str, None] = None, *args, **kwargs):
        if not chart_date:
            chart_date = get_date()
        assert re.match(r"\d{4}-\d{2}-\d{2}", chart_date), "chart_date format must be YYYY-MM-DD"
        return func(chart_date, *args, **kwargs)
    return wrapper

