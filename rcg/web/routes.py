import os
import re
from typing import Union

from flask import Blueprint, jsonify, render_template

from ..src import (format_count_data, get_parsed_chart, make_chart_w_features,
                   make_tally)
from ..src.dates import get_date, verify_date

web_routes = Blueprint("web_routes", __name__)


@web_routes.route("/chart")
def chart():
    full_chart = make_chart_w_features("2022-12-31")
    return jsonify(full_chart)


@web_routes.route("/testo")
def testo():
    return " • ".join(["divorth???", os.getenv("LOCAL", "xxx")])

@web_routes.route("/")
@web_routes.route("/<chart_date>")
@verify_date
def new_chart(chart_date: Union[str, None] = None):
    tally = make_tally(chart_date)
    assert tally, f"no chart date for {chart_date}"
    chart = make_chart_w_features(chart_date)
    count_data = format_count_data(chart_date)
    return render_template(
        "home.html",
        chart_date=chart_date,
        count_data=count_data,
        tally=tally,
        chart_w_features=chart
    )

@web_routes.route("/report/")
@web_routes.route("/report/<chart_date>")
def get_chart_delta(chart_date: Union[str, None] = None):
    if not chart_date:
        chart_date = get_date()
    today_chart = get_parsed_chart(chart_date)
    yesterday_date = get_date(chart_date, 1)
    yesterday_chart = get_parsed_chart(yesterday_date)
    assert yesterday_chart, f"no chart for {yesterday_date}"
    added_to_chart = [
        (
            s.song_name,
            s.primary_artist_name,
            ', '.join([a.name for a in s.artists]) if s.artists else ""
        ) for s in today_chart if s not in yesterday_chart
    ]
    removed_from_chart = [
        (
            s.song_name,
            s.primary_artist_name,
            ', '.join([a.name for a in s.artists]) if s.artists else ""
        ) for s in yesterday_chart if s not in today_chart
    ]
    return render_template(
        "report.html",
        new_chart_date=chart_date,
        old_chart_date=yesterday_date,
        added_to_chart=added_to_chart,
        removed_from_chart=removed_from_chart
    )


# @web_routes.route("/update")
# def update():
#     """
#     - Loads the latest chart in the db
#     - Updates the db with the current chart
#     - Loads the latest chart again
#     - Renders a comparison of the two charts
#     """
#     old_chart, old_chart_date = load_chart()
#     old_chart = Chart(old_chart, old_chart_date)
#     print("OLD DATE:", old_chart_date)

#     update_chart()

#     new_chart, new_chart_date = load_chart()
#     new_chart = Chart(new_chart, new_chart_date)
#     print("NEW DATE:", new_chart_date)

#     added_to_chart, removed_from_chart = chart_delta(new_chart, old_chart)
#     return render_template(
#         "update.html",
#         new_chart_date=new_chart_date,
#         old_chart_date=old_chart_date,
#         added_to_chart=added_to_chart,
#         removed_from_chart=removed_from_chart
#         )
