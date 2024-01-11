"""
Inconsistant implementation of local/remote db control. Sometimes you can control it and sometimes you can't.

That's probably fine, because the default is "LOCAL" environmental variable. But it's bad form.

None of these endpoints are really in use either!
"""

from typing import Literal

from flask import Blueprint, jsonify

from ..src import get_date, update_chart
from . import db_query

db_routes = Blueprint("db_routes", __name__)


@db_routes.route("/update/XXYYXX", methods=["GET"])
def update():
    output = update_chart()
    return jsonify(output, 200)


@db_routes.route("/rcg/chart/", methods=["GET"])
def get_recent_chart():
    date_ = get_date()
    q = f"""
        SELECT song_name, primary_artist_name, chart_date
        FROM chart
        WHERE chart_date = "{date_}"
        """
    return jsonify(db_query(q), 200)
