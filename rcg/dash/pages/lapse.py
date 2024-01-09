import pandas as pd
import plotly.graph_objs as go
from dash import html, register_page
from dash.dcc import Graph

from rcg.db import db_query

register_page(__name__)

start_date = "2022-12-15"
end_date = "2022-12-30"

q = f"""
    SELECT chart_date, gender, count(gender) FROM chart
    LEFT JOIN song ON song.song_spotify_id=chart.song_spotify_id
    LEFT JOIN artist ON song.artist_spotify_id=artist.spotify_id
    WHERE chart_date >= '{start_date}'
    AND chart_date < '{end_date}'
    GROUP BY chart_date, gender
    """

output = db_query(q)
df = pd.DataFrame(output, columns=['chart_date', 'gender', 'count'])

data = [go.Bar(
    x=df.query(f"gender=='{g}'")['chart_date'],
    y=df.query(f"gender=='{g}'")['count'],
    name=g
) for g in ['m', 'f', 'n']]
layout = go.Layout(
    barmode='stack',
    xaxis=dict(tickvals=df['chart_date'])
)

fig = go.Figure(data=data, layout=layout)

layout = html.Div(Graph(id="lapser", figure=fig))
