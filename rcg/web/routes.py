import os

from flask import Blueprint, jsonify, render_template

from ..src import (get_chart_delta, get_count_data, get_daily_gender_counts,
                   get_gender_counts_keys, get_gender_counts_prep, load_chart,
                   make_chart_w_features, make_tally, make_chart, format_count_data)
from ..src.dates import get_date

web_routes = Blueprint("web_routes", __name__)


@web_routes.route("/chart")
def chart():
    full_chart, date = load_chart()
    return jsonify(make_chart_w_features(full_chart))


@web_routes.route("/testo")
def testo():
    return " • ".join(["divorth???", os.getenv("LOCAL", "xxx")])


@web_routes.route("/new-chart-test")
def new_chart():
    tally = make_tally()
    chart = make_chart()
    count_data = format_count_data()
    return render_template(
        "home2.html",
        count_data=count_data,
        tally=tally,
        chart_w_features=chart
    )


@web_routes.route("/")
@web_routes.route("/<chart_date>")
@web_routes.route("/web/<chart_date>")
def home_with_date(chart_date: str = None):
    full_chart, chart_date = load_chart(chart_date)
    chart_w_features = make_chart_w_features(full_chart)
    return render_template(
        "home.html",
        chart_w_features=chart_w_features,
        chart_date=chart_date,
        gender_counts_full=get_gender_counts_prep(full_chart, return_dict=True),
        gender_count_data=get_count_data(full_chart),
        gender_counts_keys=get_gender_counts_keys
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


@web_routes.route("/report")
def report():
    """
    Shows the differences between today and yesterday and any unknowns.
    """
    today_chart, today_date = load_chart()
    yesterday_chart, yesterday_date = load_chart(get_date(1))

    not_in_yesterday, not_in_today = get_chart_delta(today_chart, yesterday_chart)

    counts = get_daily_gender_counts()

    return render_template(
        "report.html",
        counts=counts,
        new_chart_date=today_date,
        old_chart_date=yesterday_date,
        added_to_chart=not_in_yesterday,
        removed_from_chart=not_in_today
        )

# @web_routes.route("/")
# @web_routes.route("/<chart_date>")
# @web_routes.route("/web/<chart_date>")
# def home_with_date(chart_date: str=None):
#     full_chart, chart_date = load_chart(chart_date)
#     chart = Chart(full_chart, chart_date)
#     return render_template("home.html", chart=chart)
