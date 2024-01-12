import os
from itertools import zip_longest
from typing import Any, Dict, List, Tuple, Union

import spotipy

from .dates import verify_date
from .db import db_query
from .queries import features_q, gender_count_q, tally_q
from .track import (Chart, Track, add_artist_to_db, create_artist,
                    parse_spotify_chart, parse_spotify_track, add_song_feature)


@verify_date
def make_tally(chart_date: Union[str, None] = None) -> List[List[Tuple[Any]]]:
    tally = db_query(tally_q.format(chart_date))
    tally_formatted = [_ for _ in zip_longest(
        [t for t in tally if t[1] == 'm'],
        [t for t in tally if t[1] == 'f'],
        [t for t in tally if t[1] == 'n']
    )]
    return tally_formatted


@verify_date
def load_chart(chart_date: Union[str, None] = None) -> Chart:
    """
    Loads a chart from the db and parses it into a Chart object.
    """
    features = db_query(features_q.format(chart_date))
    unique_ids = set([t[1] for t in features])
    chart_tracks = []
    for i in unique_ids:
        song_features = [t for t in features if t[1] == i]
        artists = [create_artist(*t[2:]) for t in song_features]
        chart_tracks.append(Track(song_features[0][0], i, artists))
    return Chart(chart_date, chart_tracks)


@verify_date
def format_count_data(chart_date: Union[str, None] = None) -> Dict[str, Dict[str, float]]:
    count_data = db_query(gender_count_q.format(chart_date))
    count_dict = {
        g.lower()[0]: {
            'Total': next(d for d in count_data if d[0] == g.lower()[0])[1],
            'Normalized': round(
                float(
                    next(d for d in count_data if d[0] == g.lower()[0])[2]
                ), 3)
        } for g in ['Male', 'Female', 'Non-Binary']
    }
    return count_dict


@verify_date
def update_chart(
    chart_date: Union[str, None],
    live_rc_chart: Chart
) -> Chart:
    """
    Updates chart for current date.

    INPUTS:
        chart (Chart): chart to be added to db. Uses latest rap caviar if none provided.
        chart_date (str): date of chart to be added. Uses today via get_date() if none provided.

    OUTPUT:
        new_chart (Chart]): chart for `chart_date`, which should be `chart`.
            Returns latest chart in db if no changes.

    """
    latest_chart_in_db = load_chart()
    if live_rc_chart.tracks != latest_chart_in_db.tracks:
        print(f"updating chart for {chart_date}")
        q = live_rc_chart.make_charting_query()
        db_query(q, commit=True)
        print(f"chart date updated for {chart_date}")
        new_chart = load_chart()
        assert new_chart.tracks == live_rc_chart.tracks, str([len(new_chart.tracks), len(live_rc_chart.tracks)])

        appearances_in_db = db_query(f"""
            SELECT distinct
                chart.song_spotify_id,
                artist.spotify_id
            FROM chart
            INNER JOIN song ON chart.song_spotify_id=song.song_spotify_id
            LEFT JOIN artist ON song.artist_spotify_id=artist.spotify_id
            WHERE chart_date='{chart_date}'
            """)

        new_appearances = [
            a for a in new_chart.appearances
            if (a.song_spotify_id, a.artist_spotify_id)
            not in appearances_in_db
        ]

        for a in new_appearances:
            add_song_feature(
                a.song_name,
                a.song_spotify_id,
                a.name,
                a.id,
                a.primary
                )

        new_artist_ids = db_query(f"""
            SELECT song.artist_spotify_id
            FROM chart
            INNER JOIN song ON chart.song_spotify_id=song.song_spotify_id
            WHERE chart_date='{chart_date}' AND song.spotify_id not in (
                               SELECT spotify_id FROM artist
            )
            """)

        for a in [
            a for a in new_chart.appearances
            if a.artist_spotify_id in new_artist_ids
        ]:
            add_artist_to_db(a.name, a.spotify_id)
        return new_chart
    else:
        print(f"no updates, chart date {chart_date}")
        return latest_chart_in_db


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
    chart = parse_spotify_chart(rc)
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
