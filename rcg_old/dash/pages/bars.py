from dash import html, register_page
from rcg.dash.dash_code import bar_grapher_generator

register_page(__name__)

bg = bar_grapher_generator()
layout = html.Div(
    html.H1("LOADING..."),
    className="holder-holder",
    id="holder-holder")