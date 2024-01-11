import os
from flask import url_for
from rcg.app_prep import app
from rcg.web.routes import web_routes

@app.route("/favicon.ico")
def favicon():
    return url_for('static', filename='data:,')

app.register_blueprint(web_routes)

if __name__ == "__main__":
    app.run()
