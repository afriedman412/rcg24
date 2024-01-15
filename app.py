from flask import url_for, request
from rcg.app_prep import app
from rcg.web.routes import web_routes
from rcg.src.dates import get_date
import os

DATES_SET = True

@app.route("/favicon.ico")
def favicon():
    return url_for('static', filename='data:,')

app.register_blueprint(web_routes)

@app.before_request
def set_dates():
    global DATES_SET

    if not DATES_SET:
        os.environ['TODAY'] = get_date()
        os.environ['LATEST_CHART_DATE'] = get_date(default_is_today=False)

        DATES_SET = True

if __name__ == "__main__":
    app.run()
