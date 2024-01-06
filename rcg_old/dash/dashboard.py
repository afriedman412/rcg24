from dash import Dash, html, page_container
from dash.dcc import Location
from dash.dependencies import Input, Output
from .dash_code import bar_grapher_generator

def init_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = Dash(
        use_pages=True,
        server=server,
        pages_folder="./dash/pages",
        routes_pathname_prefix='/dashapp/',
        external_stylesheets=[
            '/static/styles/stylesheet.css',
        ]
    )
    dash_app.layout = html.Div([
        Location(id='url', refresh=True),
        page_container
    ])
    init_callbacks(dash_app)

    return dash_app.server

def init_callbacks(dash_app):
    """
    Adds provided callbacks to dash_app.
    """
    @dash_app.callback(
    Output("holder-holder", 'children'),
    Input("url", "search")
    )
    def reload_graphs(date_):
        print(date_)
        if date_:
            date_ = date_.split("?")[-1]
            bg_ = bar_grapher_generator(date_)
        else:
            bg_ = bar_grapher_generator()
        return bg_.bar_charts




