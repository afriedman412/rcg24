from flask import Blueprint, render_template
from ..code.code import load_chart, update_chart, get_date, get_counts
from ..code.chart_code import Chart, chart_delta

web_routes = Blueprint("web_routes", __name__)

# @web_routes.route("/favicon.ico")
# def load_favicon():
#     return

@web_routes.route("/update")
def update():
    """
    - Loads the latest chart in the db
    - Updates the db with the current chart
    - Loads the latest chart again
    - Renders a comparison of the two charts
    """
    old_chart, old_chart_date = load_chart()
    old_chart = Chart(old_chart, old_chart_date)
    print("OLD DATE:", old_chart_date)

    update_chart()

    new_chart, new_chart_date = load_chart()
    new_chart = Chart(new_chart, new_chart_date)
    print("NEW DATE:", new_chart_date)

    added_to_chart, removed_from_chart = chart_delta(new_chart, old_chart)
    return render_template(
        "update.html", 
        new_chart_date=new_chart_date, 
        old_chart_date=old_chart_date,
        added_to_chart=added_to_chart,
        removed_from_chart=removed_from_chart
        )

@web_routes.route("/report")
def report():
    """
    Shows the differences between today and yesterday and any unknowns.
    """
    today_chart, today_date = load_chart()
    today_chart = Chart(today_chart, today_date)

    yesterday_chart, yesterday_date = load_chart(get_date(1))
    yesterday_chart = Chart(yesterday_chart, yesterday_date)

    not_in_yesterday, not_in_today = chart_delta(today_chart, yesterday_chart)

    counts = get_counts()

    return render_template(
        "report.html", 
        counts=counts,
        new_chart_date=today_date, 
        old_chart_date=yesterday_date,
        added_to_chart=not_in_yesterday,
        removed_from_chart=not_in_today
        )
    

@web_routes.route("/")
@web_routes.route("/<chart_date>")
@web_routes.route("/web/<chart_date>")
def home_with_date(chart_date: str=None):
    full_chart, chart_date = load_chart(chart_date)
    chart = Chart(full_chart, chart_date)
    return render_template("home.html", chart=chart)