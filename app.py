import os
from flask import jsonify
from rcg.app_prep import app
from rcg.db.routes import db_routes
from rcg.src import load_chart, chart_w_features

app.register_blueprint(db_routes)


@app.route("/")
def testo():
    return " • ".join(["divorth???", os.getenv("LOCAL", "xxx")])


@app.route("/chart")
def chart():
    full_chart, date = load_chart()
    # return chart.to_json()
    # return count_data(full_chart).to_json()
    return jsonify(chart_w_features(full_chart))


if __name__ == "__main__":
    app.run()
