import os
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=DeprecationWarning)
    import connexion
from flask import Flask
from dotenv import find_dotenv, load_dotenv
from .src.dates import get_date


def init_app() -> Flask:
    """
    Construct core Flask application with embedded Dash app.
    """
    load_dotenv()
    env = ".env.local" if os.getenv("LOCAL", False) else ".env.remote"
    env_file = find_dotenv(env)
    load_dotenv(env_file, override=True)
    dir_ = os.path.abspath(os.path.dirname(__file__))
    connex_app = connexion.App(__name__, specification_dir=dir_)
    app = connex_app.app
    os.environ['TODAY'] = get_date()
    os.environ['LATEST_CHART_DATE'] = get_date(default_is_today=False)
    return app


def augment_app(app: Flask) -> Flask:
    with app.app_context():
        from .dash.dashboard import init_dashboard
        app = init_dashboard(app)
        return app


app = init_app()
app = augment_app(app)
