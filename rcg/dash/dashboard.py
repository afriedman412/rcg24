import os
import re
from typing import Dict, Union

from dash import Dash, html, page_container
from dash.dcc import Graph, Location
from dash.dependencies import Input, Output
from flask import Flask
from plotly.graph_objects import Bar, Figure

from rcg.src import format_count_data
from rcg.src.dates import verify_date

from ..config.config import COLORS


def init_dashboard(server) -> Flask:
    """Create a Plotly Dash dashboard."""
    dash_app = Dash(
        use_pages=True,
        server=server,
        pages_folder="dash/pages",
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

    def reload_graphs(chart_date: Union[str, None]):
        if chart_date is None:
            chart_date = os.getenv("LATEST_CHART_DATE", "BAD DATE")
        chart_date = re.sub(r"^\?", "", chart_date)
        try:
            verify_date(chart_date)
        except AssertionError:
            chart_date = os.getenv("LATEST_CHART_DATE", "BAD DATE")
        return bar_grapher_generator(chart_date)


def bar_grapher_generator(chart_date: Union[str, None] = None):
    # transposing the count_data was easier than rewriting the code for getting count_data
    
    count_data = format_count_data(chart_date)
    count_data = {
        i: {g: count_data[g][i] for g in count_data.keys()}
        for i in ['Total', 'Normalized']
    }
    total = make_bar_graph(count_data['Total'], False, chart_date)
    normalized = make_bar_graph(count_data['Normalized'], True, chart_date)
    return [
            html.Div(
                [total, normalized],
                className="bar-chart-container"
            )
            ]


def make_bar_graph(
        count_data: Dict[str, Dict[str, float]],
        normalize: bool,
        chart_date: Union[str, None] = None
        ):
    title_text = "% of Artist Credits<br>({})" if normalize else "Total Artist Credits<br>({})"
    fig = Figure(
            Bar(
                x=list(count_data.keys()),
                y=list(count_data.values()),
                marker_color=list(COLORS.values()),
                text=list(count_data.values()),
                textposition='outside',
                textfont_color="white"
            )
        )
    fig.update_layout(
            title={
                'text': title_text.format(chart_date),
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'bottom',
                'font': {
                    'color': 'white',
                    'family': 'Arial'
                    },
            },
            yaxis_range=[0, 110] if normalize else [
                0, max(count_data.values())*1.2],
            margin=dict(t=70, r=20, l=20, b=30),
            paper_bgcolor="black",
            plot_bgcolor="black",
            autosize=True,
            yaxis=dict(color='white', ticksuffix="  "),
            xaxis=dict(color='white')
            )
    if normalize:
        fig.update_traces(texttemplate='%{y:.1f}%')
    class_name = 'bar-chart r' if normalize else 'bar-chart r'
    div = html.Div(Graph(
            id="normalized" if normalize else "total",
            figure=fig,
            config={
                'staticPlot': True,
                'format': 'svg',
                'displayModeBar': False
                }
            ), className=class_name)
    return div
