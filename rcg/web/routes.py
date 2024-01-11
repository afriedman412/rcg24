import os
from typing import Union

from flask import Blueprint, jsonify, render_template

from ..src import format_count_data, load_chart, make_tally, update_chart
from ..src.dates import get_date, verify_date

web_routes = Blueprint("web_routes", __name__)


@web_routes.route("/testo")
def testo():
    return " • ".join(["divorth???", os.getenv("LOCAL", "xxx")])


@web_routes.route("/update/XXYYXX", methods=["GET"])
def update():
    output = update_chart()
    return jsonify(output, 200)


@web_routes.route("/")
@web_routes.route("/<chart_date>")
@verify_date
def new_chart(chart_date: Union[str, None] = None):
    tally = make_tally(chart_date)
    assert tally, f"no chart date for {chart_date}"
    chart = load_chart(chart_date)
    count_data = format_count_data(chart_date)
    return render_template(
        "home.html",
        chart_date=chart_date,
        count_data=count_data,
        tally=tally,
        chart_w_features=[t._todict() for t in chart]
    )


@web_routes.route("/report/")
@web_routes.route("/report/<chart_date>")
def get_chart_delta(chart_date: Union[str, None] = None):
    if not chart_date:
        chart_date = get_date()
    yesterday_date = get_date(chart_date, 1)
    today_chart, yesterday_chart = (load_chart(d) for d in [chart_date, yesterday_date])
    assert yesterday_chart.tracks, f"no chart for {yesterday_date}"

    added_to_chart = today_chart.tracks - yesterday_chart.tracks
    removed_from_chart = yesterday_chart.tracks - today_chart.tracks
    return render_template(
        "report.html",
        new_chart_date=chart_date,
        old_chart_date=yesterday_date,
        added_to_chart=added_to_chart,
        removed_from_chart=removed_from_chart
    )

