import os
from typing import Any, Union

from flask import Blueprint, render_template

from ..src import get_chart_stats, load_chart, load_spotify_chart, make_tally
from ..src.adding import add_chart_to_db
from ..src.dates import get_date, verify_date

web_routes = Blueprint("web_routes", __name__)


@web_routes.route("/testo")
def testo():
    return " • ".join([
        os.getenv(v, v) for v in [
            'DIVORTH??', 'LOCAL', 'MYSQL_DB', 'TODAY', 'LATEST_CHART_DATE'
            ]
        ])


@web_routes.route("/dpt")
@web_routes.route("/dpt/<chart_date>")
def date_picker_test(chart_date: Union[str, None] = None) -> str:
    if chart_date is None:
        chart_date = os.environ["LATEST_CHART_DATE"]
    verify_date(chart_date)
    return render_template(
        "date-picker-test.html",
        )


@web_routes.route("/update/XXYYXX", methods=["GET"])
def update() -> dict[Any, Any]:
    new_chart = load_spotify_chart()
    add_chart_to_db(new_chart)
    return get_chart_delta(new_chart.chart_date, True)


@web_routes.route("/")
@web_routes.route("/<chart_date>")
def make_latest_chart(chart_date: Union[str, None] = None) -> str:
    if chart_date is None:
        chart_date = os.environ["LATEST_CHART_DATE"]
    verify_date(chart_date)
    tally = make_tally(chart_date)
    assert tally, f"no chart date for {chart_date}"
    chart = load_chart(chart_date)
    count_data = get_chart_stats(chart_date)
    return render_template(
        "home.html",
        chart_date=chart_date,
        count_data=count_data,
        tally=tally,
        chart_w_features=[t._todict() for t in chart]
    )


@web_routes.route("/report")
@web_routes.route("/report/<chart_date>")
def get_chart_delta(chart_date: Union[str, None] = None, updated: bool = False) -> str:
    if chart_date is None:
        chart_date = os.getenv("LATEST_CHART_DATE")
    verify_date(chart_date)
    yesterday_date = get_date(chart_date, 1)
    today_chart, yesterday_chart = (load_chart(d) for d in [chart_date, yesterday_date])
    if yesterday_chart.tracks:
        added_to_chart = today_chart.tracks - yesterday_chart.tracks
        removed_from_chart = yesterday_chart.tracks - today_chart.tracks

    else:
        yesterday_date += " **NO CHART IN DB**"
        added_to_chart = None
        removed_from_chart = None
    return render_template(
        "report.html",
        new_chart_date=chart_date,
        old_chart_date=yesterday_date,
        added_to_chart=added_to_chart,
        removed_from_chart=removed_from_chart,
        updated=updated
    )
