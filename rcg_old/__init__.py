import connexion
from dotenv import load_dotenv
from datetime import datetime as dt
import os

def init_app():
    """
    Construct core Flask application with embedded Dash app.
    """
    load_dotenv()
    dir_ = os.path.abspath(os.path.dirname(__file__))
    connex_app = connexion.App(__name__, specification_dir=dir_)
    app = connex_app.app
    app.config.from_pyfile('config/config.py')
    return app

def augment_app(app):
    
    with app.app_context():
        from .dash.dashboard import init_dashboard
        app = init_dashboard(app)
        return app

app = init_app()
app = augment_app(app)