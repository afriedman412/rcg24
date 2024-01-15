import os
from itertools import zip_longest
from typing import Any, Dict, List, Tuple

import spotipy

from .adding import parse_spotify_chart, parse_spotify_track
from .db import db_query
from .track import Appearance, Chart, Track, make_track_from_appearances
from .dates import verify_date


def make_tally(chart_date: str) -> List[List[Tuple[Any]]]:
    verify_date(chart_date)
    q = """
    SELECT
    artist.artist_name,
    artist.gender,
    COUNT(chart.song_spotify_id) AS appearances
    FROM chart
    INNER JOIN
        song ON chart.song_spotify_id = song.song_spotify_id
    INNER JOIN
        artist ON song.artist_spotify_id = artist.spotify_id
    WHERE chart.chart_date = '{}'
    GROUP BY
        artist.artist_name,
        artist.gender,
        artist.spotify_id;
    """.format(chart_date)
    tally = db_query(q)
    tally_formatted = [_ for _ in zip_longest(
        [t for t in tally if t[1] == 'm'],
        [t for t in tally if t[1] == 'f'],
        [t for t in tally if t[1] == 'n']
    )]
    return tally_formatted


def load_chart(chart_date: str) -> Chart:
    """
    Loads a chart from the db and parses it into a Chart object.
    """
    verify_date(chart_date)
    q = """
    SELECT
        chart.song_spotify_id,
        chart.song_name,
        artist.spotify_id,
        artist.artist_name,
        song.primary
    FROM chart
    INNER JOIN song ON chart.song_spotify_id=song.song_spotify_id
    LEFT JOIN artist ON song.artist_spotify_id=artist.spotify_id
    WHERE chart_date="{}"
    """.format(chart_date)
    q = db_query(q)
    appearances = [Appearance._make(result) for result in q]
    chart_tracks = []
    for i in set([a.song_spotify_id for a in appearances]):
        track = make_track_from_appearances([a for a in appearances if a.song_spotify_id == i])
        chart_tracks.append(track)
    return Chart(chart_date, chart_tracks)


def format_count_data(chart_date: str) -> Dict[str, Dict[str, float]]:
    verify_date(chart_date)
    q = """
        SELECT
            gender,
            COUNT(*) AS total,
            COUNT(*) / SUM(COUNT(*)) OVER () * 100 AS percentage
        FROM chart
        INNER JOIN song ON chart.song_spotify_id=song.song_spotify_id
        LEFT JOIN artist ON song.artist_spotify_id=artist.spotify_id
        WHERE chart_date="{}"
        GROUP BY gender
        """.format(chart_date)
    count_data = db_query(q)
    count_dict = {
        g.lower()[0]: {
            'Total': next(d for d in count_data if d[0] == g.lower()[0])[1],
            'Normalized': round(
                float(
                    next(d for d in count_data if d[0] == g.lower()[0])[2]
                ), 1)
        } for g in ['Male', 'Female', 'Non-Binary']
    }
    return count_dict


def load_spotipy() -> spotipy.Spotify:
    """
    Instantiates Spotipy object w credentials.
    """
    spotify_cred_manager = spotipy.oauth2.SpotifyClientCredentials(
        os.environ['SPOTIFY_ID'],
        os.environ['SPOTIFY_SECRET']
    )
    sp = spotipy.Spotify(client_credentials_manager=spotify_cred_manager)
    return sp


def load_spotify_chart(chart_id: str = 'spotify:playlist:37i9dQZF1DX0XUsuxWHRQd') -> Chart:
    """
    Loads playlist from Spotify at the proivded chart_id. Defaut is for Rap Caviar.

    INPUTS:
        chart_id (str)

    OUTPUT:
        chart (Chart)
    """
    sp = load_spotipy()
    rc = sp.playlist(chart_id)
    chart = parse_spotify_chart(None, rc)
    return chart


def load_one_song(song_spotify_id: str) -> Track:
    """
    Utility function, not actually in use.

    INPUT:
        song_spotify_id (str)

    OUTPUT:
        track (Track)
    """
    sp = load_spotipy()
    track = sp.track(song_spotify_id)
    track = parse_spotify_track(track)
    return track
