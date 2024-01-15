import re
from datetime import datetime as dt
from datetime import timedelta
from typing import Callable, Union, Any

from pytz import timezone

from .db import db_query

date_str = "%Y-%m-%d"


def get_date(date: Union[str, dt, None] = None, offset: int = 0) -> str:
    """
    If no date is provided, date is today for the Eastern time zone.

    If offset, returns offset days ago. (offset=1 is yesterday)
    """
    if not date:
        date = dt.now()
    elif isinstance(date, str):
        assert re.match(r"\d{4}-\d{2}-\d{2}", date), f"chart_date ({date}) format is not YYYY-MM-DD"
        date = dt.strptime(date, date_str)
    date = timezone('US/Eastern').localize(date)
    if offset:
        date = date - timedelta(offset)
    date = date.strftime(date_str)
    return date


def revert_to_most_recent_chart_date(chart_date: str) -> str:
    most_recent_chart_date = get_most_recent_chart_date().strftime(date_str)
    return most_recent_chart_date if most_recent_chart_date > chart_date else chart_date


def get_most_recent_chart_date() -> dt:
    """
    Gets the most recent chart date.
    """
    most_recent_chart_date = db_query("select max(chart_date) from chart")[0][0]
    assert re.match(
        r"\d{4}-\d{2}-\d{2}", most_recent_chart_date
    ), "chart_date format must be YYYY-MM-DD"
    return timezone('US/Eastern').localize(dt.strptime(most_recent_chart_date, date_str))


def verify_date(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """
    To be used as a decorator for functions that need a chart date.
    """
    def wrapper(chart_date: Union[str, None] = None, *args, **kwargs) -> Callable[[Any], Any]:
        if not chart_date:
            chart_date = get_date()
        assert re.match(r"\d{4}-\d{2}-\d{2}", chart_date), "chart_date format must be YYYY-MM-DD"
        return func(chart_date, *args, **kwargs)
    return wrapper
