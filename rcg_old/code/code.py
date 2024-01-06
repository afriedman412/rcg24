from datetime import datetime as dt
import pandas as pd
from pandas import DataFrame
import os
from typing import Tuple
import spotipy
from .track_code import Track
from ..db import db_query
from .helpers import (
    local_check, get_date, most_recent_chart_date, query_w_date
)

def update_chart(local: bool=False):
    """
    Updates chart for current date. 
    """
    os.environ['LOCAL'] = "true" if local else "false"
    print("update:", "local" if local_check() else "remote")
    current_chart = load_rap_caviar()
    latest_chart = get_chart_from_db()
    chart_date = get_date()

    if new_chart_check(latest_chart, current_chart):
            print(f"no updates, chart date {chart_date}")
            return False
    else:
        print(f"updating chart for {chart_date}")
        
        for t in current_chart:
            t = Track(t, chart_date) # parse_track is in load_rap_caviar
            t.update_chart()

        print(f"chart date updated for {chart_date}")

        q = f"""
            SELECT * FROM chart WHERE chart_date = "{chart_date}"
            """
        return db_query(q)

def new_chart_check(latest_chart, current_chart):

    return {t[2] for t in latest_chart} == {t[1] for t in current_chart} \
        and get_date() == most_recent_chart_date()

def parse_track(t):
    """
    Unpacks track metadata from a Spotify track.
    """
    song_name, song_spotify_id, artists = (t['name'], t['id'], [(a['name'], a['id']) for a in t['artists']])
    primary_artist_name, primary_artist_spotify_id = (artists[0])
    return song_name, song_spotify_id, artists, primary_artist_name, primary_artist_spotify_id

def load_spotipy():
    """
    Instantiates Spotipy object w credentials.
    """
    spotify_cred_manager = spotipy.oauth2.SpotifyClientCredentials(
        os.environ['SPOTIFY_ID'], 
        os.environ['SPOTIFY_SECRET']
        )
    sp = spotipy.Spotify(client_credentials_manager=spotify_cred_manager)
    return sp

def load_rap_caviar():
    """
    Loads the current rap caviar playlist from Spotify.
    """
    sp = load_spotipy()
    rc = sp.playlist('spotify:user:spotify:playlist:37i9dQZF1DX0XUsuxWHRQd')
    current_chart = [parse_track(t['track']) for t in rc['tracks']['items']]
    return current_chart

def load_one_song(song_spotify_id: str):
    sp = load_spotipy()
    track_info = sp.track(song_spotify_id)
    track_info = parse_track(track_info)
    return track_info

def get_chart_from_db(date_: str=None):
    q = """
        SELECT * FROM chart WHERE chart_date = "{}"
        """
    return query_w_date(q, date_)

def get_counts(date_: str=None):
    q = """
        SELECT gender, count(*)
        FROM chart
        LEFT JOIN song on chart.song_spotify_id=song.song_spotify_id
        LEFT JOIN artist on song.artist_spotify_id = artist.spotify_id
        WHERE chart_date = "{}"
        GROUP BY gender;
        """
    return query_w_date(q, date_)


def load_chart(chart_date: str=None, local: bool=False) -> Tuple[DataFrame, str]:
    """
    Loads the chart from chart_date, defaulting to the latest chart in the db.
    
    Returns it as a DataFrame, formatted for Flask HTML processing.

    TODO: Does it have to be pandas?
    """
    os.environ['LOCAL'] = "true" if local else "false"
    print("load:", "local" if local_check() else "remote")
    chart_date = most_recent_chart_date() if not chart_date else chart_date
    print("loading chart date:", chart_date)
    chart_date = dt.strptime(chart_date, "%Y-%m-%d").strftime("%Y-%m-%d")

    q = f"""
        SELECT chart.song_name, chart.primary_artist_name, chart_date, artist.artist_name, gender
        FROM chart
        INNER JOIN song ON chart.song_spotify_id=song.song_spotify_id
        LEFT JOIN artist ON song.artist_spotify_id=artist.spotify_id
        WHERE chart_date="{chart_date}"
        """

    full_chart = pd.DataFrame(
        db_query(q), 
        columns=['song_name', 'primary_artist_name', 'chart_date', 'artist_name', 'gender'])
    full_chart['gender'] = full_chart['gender'].map({"m": "Male", "f": "Female", "n": "Non-Binary"})
    if not chart_date:
        chart_date = full_chart['chart_date'][0]
    formatted_chart_date = dt.strptime(chart_date, "%Y-%m-%d").strftime("%B %-d, %Y")
    return full_chart, formatted_chart_date