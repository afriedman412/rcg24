import re
from datetime import datetime as dt
from datetime import timedelta
from typing import Callable, Union, Any

from pytz import timezone

from .db import db_query

DATE_FORMAT = "%Y-%m-%d"


def get_date(
        date: Union[str, dt, None] = None, 
        offset: int = 0,
        default_is_today: bool = True
    ) -> str:
    """
    If no date is provided, date is today for the Eastern time zone.

    If offset, returns offset days ago. (offset=1 is yesterday)
    """
    if not date:
        if default_is_today:
            date = dt.now()
        else:
            date = get_most_recent_chart_date()
    elif isinstance(date, str):
        date = dt.strptime(date, DATE_FORMAT)
    if date.tzinfo is None:
        date = timezone('US/Eastern').localize(date)
    if offset:
        date = date - timedelta(offset)
    date = date.strftime(DATE_FORMAT)
    return date


def get_most_recent_chart_date() -> dt:
    """
    Gets the most recent chart date.
    """
    most_recent_chart_date = db_query("select max(chart_date) from chart")[0][0]
    verify_date(most_recent_chart_date)
    return timezone('US/Eastern').localize(dt.strptime(most_recent_chart_date, DATE_FORMAT))


def verify_date(chart_date: str):
    """
    Assures correct date formatting, prevents SQL injections.
    """
    assert chart_date is not None, "No date provided (or date is None)"
    assert re.match(r"\d{4}-\d{2}-\d{2}", chart_date), f"chart_date ({chart_date}) format is not YYYY-MM-DD"


# def preload_today(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
#     """
#     To be used as a decorator for functions that needs a chart_date defaulting to today.
#     """
#     def preload_today_wrapper(chart_date: Union[str, None] = None, *args, **kwargs) -> Callable[[Any], Any]:
#         chart_date = get_date(chart_date)
#         verify_date(chart_date)
#         return func(chart_date, *args, **kwargs)
#     return preload_today_wrapper


# def preload_latest_chart_date(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
#     """
#     To be used as a decorator for functions that needs a chart_date defaulting to most recent date in data.
#     """
#     def preload_latest_wrapper(chart_date: Union[str, None] = None, *args, **kwargs) -> Callable[[Any], Any]:
#         chart_date = get_date(chart_date, default_is_today=False)
#         verify_date(chart_date)
#         return func(chart_date, *args, **kwargs)
#     return preload_latest_wrapper
