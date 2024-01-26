import os

from dash import html, register_page

from rcg.dash.dashboard import bar_grapher_generator

register_page(__name__)

bg = bar_grapher_generator(os.getenv("LATEST_CHART_DATE", "2022-12-10"))
layout = html.Div(
    html.H1("LOADING..."),
    className="holder-holder",
    id="holder-holder")
