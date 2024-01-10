import os
from itertools import zip_longest
from typing import Dict, List, Tuple, Union

import spotipy

from ..db import db_query
from ..db.queries import chart_q, chart_w_features_q, gender_count_q, tally_q
from .dates import get_date, get_most_recent_chart_date, verify_date
from .track import Artist, Track, add_artist, parse_chart, parse_track


@verify_date
def make_tally(chart_date: Union[str, None] = None):
    tally = db_query(tally_q.format(chart_date))
    tally_formatted = [_ for _ in zip_longest(
        [t for t in tally if t[1] == 'm'],
        [t for t in tally if t[1] == 'f'],
        [t for t in tally if t[1] == 'n']
    )]
    return tally_formatted


@verify_date
def make_chart_w_features(chart_date: Union[str, None] = None):
    chart = db_query(chart_w_features_q.format(chart_date))
    chart = [
        [
            t[0],
            t[1],
            t[2].replace(",", ", ") if t[2] else ""
        ]
        for t in chart
    ]
    return chart


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
def get_parsed_chart(chart_date: Union[str, None] = None) -> List[Track]:
    """
    Presumes group artists are already queried!
    """
    chart = db_query(chart_q.format(chart_date))
    unique_ids = set([t[1] for t in chart])
    parsed_chart = []
    for i in unique_ids:
        song_name = next(
            t[0] for t in chart if t[1] == i
        )
        primary_artist_info = next(
            (t[2], t[3]) for t in chart
            if t[1] == i and t[-1][0].lower() == 't'
        )
        artists = (
            Artist(t[2], t[3]) for t in chart
            if t[1] == i and t[-1][0].lower() == 'f'
        )
        track = Track._make(
            [
                song_name,
                i,
                artists,
                primary_artist_info[0],
                primary_artist_info[1]
            ]
        )
        parsed_chart.append(track)
    return parsed_chart


@verify_date
def update_chart(
    chart_date: Union[str, None] = None,
    chart: Union[list[Track], None] = None,
) -> List[Track]:
    """
    Updates chart for current date.

    INPUTS:
        chart (List[Track]): chart to be added to db. Uses latest rap caviar if none provided.
        chart_date (str): date of chart to be added. Uses today via get_date() if none provided.

    OUTPUT:
        new_chart (List[Track]): chart for `chart_date`, which should be `chart`

    """
    live_chart = chart if chart else load_rap_caviar()
    latest_chart_in_db = get_parsed_chart()
    if set(tuple(live_chart)) == set(tuple(latest_chart_in_db)):
        print(f"no updates, chart date {chart_date}")
        return
    else:
        print(f"updating chart for {chart_date}")
        q = make_charting_query(live_chart, chart_date)
        db_query(q, commit=True)
        print(f"chart date updated for {chart_date}")

        all_ids = [a[0] for a in db_query("select spotify_id from artist")]

        new_artists = {
            a
            for t in live_chart
            for a in t.artists
            if a.spotify_id not in all_ids
        }

        for a in new_artists:
            add_artist(a.name, a.spotify_id)

        q = f"""
            SELECT * FROM chart WHERE chart_date = "{chart_date}"
            """
        new_chart = db_query(q)
        new_chart = parse_chart(new_chart)
        return new_chart


def make_charting_query(chart: list[Track], chart_date: str) -> str:
    q = """
            INSERT INTO
            chart (song_name, song_spotify_id, primary_artist_name,
            primary_artist_spotify_id, chart_date)
            VALUES """

    q += ",\n".join(
        [
            "(" + ", ".join(
                f'"{p}"' for p in
                [
                    track.song_name,
                    track.song_spotify_id,
                    track.primary_artist_name,
                    track.primary_artist_spotify_id,
                    chart_date
                ]) + ")"
            for track in chart
        ]
    )
    return q


def new_chart_check(latest_chart, current_chart) -> bool:
    return {t[2] for t in latest_chart} == {t[1] for t in current_chart} \
        and get_date() == get_most_recent_chart_date()


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


def load_rap_caviar() -> list[Track]:
    """
    Loads the current rap caviar playlist from Spotify.
    """
    sp = load_spotipy()
    rc = sp.playlist('spotify:playlist:37i9dQZF1DX0XUsuxWHRQd')
    current_chart = [parse_track(t['track']) for t in rc['tracks']['items']]
    return current_chart


def load_one_song(song_spotify_id: str) -> Track:
    sp = load_spotipy()
    track = sp.track(song_spotify_id)
    track = parse_track(track)
    return track


@verify_date
def get_chart_from_db(chart_date: str = None) -> Tuple[str, List[Track]]:
    q = f"""
        SELECT song_name, primary_artist_name FROM chart WHERE chart_date = '{chart_date}'
        """
    raw_chart = db_query(q)
    assert raw_chart, f"No chart found for {chart_date}"
    chart = parse_chart(raw_chart)
    return chart_date, chart
