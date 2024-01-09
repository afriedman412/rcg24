import os
import re
from datetime import datetime as dt
from typing import List, Literal, Tuple, Union, Dict

import pandas as pd
import spotipy
from pandas import DataFrame
from itertools import zip_longest

from ..config.config import GENDERS  # TODO: move colors to CSS
from ..db import db_query
from ..db.queries import chart_q, gender_count_q, tally_q
from .dates import get_date, get_most_recent_chart_date, query_w_date
from .track import Track, add_artist, parse_chart, parse_track


def make_tally(chart_date: Union[str, None] = None):
    if not chart_date:
        chart_date = get_date()
    tally = db_query(tally_q.format(chart_date))
    tally_formatted = [_ for _ in zip_longest(
        [t for t in tally if t[1] =='m'],
        [t for t in tally if t[1] =='f'],
        [t for t in tally if t[1] =='n']
    )]
    return tally_formatted
    

def make_chart(chart_date: Union[str, None] = None):
    if not chart_date:
        chart_date = get_date()
    chart = db_query(chart_q.format(chart_date))
    return chart


def format_count_data(chart_date: Union[str, None] = None) -> Dict[str, Dict[str, float]]:
    if not chart_date:
        chart_date = get_date()
    count_data = db_query(gender_count_q.format(chart_date))

    count_dict = {
        g.lower()[0]: {
            'Total': next(d for d in count_data if d[0] == g.lower()[0])[1],
            'Percentage': round(
                float(
                    next(d for d in count_data if d[0] == g.lower()[0])[2]
                ), 3)
        } for g in ['Male', 'Female', 'Non-Binary']
    }
    return count_dict


def get_count_data(full_chart: List[Track]) -> DataFrame:
    """
    Gets count and normalized count from full chart.
    """
    full_chart = pd.DataFrame(full_chart)
    count_data = pd.DataFrame(
        [
            full_chart['gender'].value_counts().astype(int),
            full_chart['gender'].value_counts(normalize=True).map(lambda n: n*100).round(1)
        ],
        ["Total", "Percentage"]
    )
    return count_data


def get_gender_count_data(
        count_data: DataFrame,
        g: Literal["m", "f", "n", "x"]
        ) -> Union[str, None]:
    """Used in Jinja"""
    return count_data.to_dict().get(g, None)


def make_chart_w_features(full_chart: DataFrame) -> DataFrame:
    """
    Adds "Features" column to the full chart.
    """
    features = full_chart.query(
        "primary_artist_name != artist_name"
    ).groupby("song_name")['artist_name'].apply(
        lambda a: ", ".join(a)
    )

    main_chart = full_chart.query(
        "primary_artist_name == artist_name"
    ).set_index("song_name")

    chart_w_features = main_chart.drop(
        ['chart_date', 'artist_name', 'gender'], axis=1
    ).join(features).reset_index(
    ).rename(columns={'artist_name': 'features'}).fillna("")

    chart_w_features.columns = ['Song', 'Primary Artist', 'Features']
    chart_w_features['Song'] = chart_w_features['Song'].map(
        lambda t: re.sub(r"\s[\(\[](feat\.|with).+[\)\]]", "", t)
    )
    return chart_w_features.drop_duplicates()


def make_total_chart_dict(full_chart: DataFrame) -> Dict[str, Dict[str, Union[str, int]]]:
    """
    Extracts gender data and converts to one dict.
    """
    total_df = full_chart['gender'].value_counts().rename_axis(
        'gender'
    ).reset_index(name='count')  # gender count
    pct_df = full_chart['gender'].value_counts(
        normalize=True
    ).rename_axis('gender').reset_index(name='pct')  # gender pct
    pct_df['pct'] = pct_df['pct'].map(
        lambda c: c*100
    ).round(2)  # formatted gender pct
    total_df = total_df.set_index('gender').join(
        pct_df.set_index("gender")
    ).reset_index()  # join counts and pct
    total_chart_dict = total_df.to_dict("records")  # convert to dict
    for k in set(GENDERS).difference(
        set([d['gender'] for d in total_chart_dict])
    ):
        total_chart_dict.append(
            {"gender": k, "count": 0, "pct": 0}
        )  # add any missing genders
    return total_chart_dict


def get_gender_counts_prep(
        full_chart: DataFrame,
        return_dict: bool = False,
        return_indexes: bool = False,
) -> Union[DataFrame, dict, list]:
    """
    Formats artist-wise gender counts for "Tally".
    Done this way for annoying formatting reasons.
    """
    gender_counts = {
        c: full_chart.query(
            f"gender=='{c}'")['artist_name'].value_counts().reset_index().rename(
                columns={
                    "artist_name": f"artist_name_{c[0].lower()}",
                    "count": f"count_{c[0].lower()}"
                }
        ) for c in GENDERS
    }
    gender_counts_full = gender_counts['Male'].join(
        gender_counts['Female']).join(
        gender_counts['Non-Binary']
    )
    gender_counts_full.fillna("", inplace=True)
    for c in gender_counts_full.columns:
        if 'count' in c:
            gender_counts_full[c] = gender_counts_full[c].map(lambda c: int(c) if isinstance(c, float) else c)

    # not sure why this happens twice...
    gender_counts_full.fillna("", inplace=True)
    if return_dict:
        return gender_counts_full.to_dict('records')
    if return_indexes:
        return list(
            zip(
                gender_counts_full.columns[::2],
                gender_counts_full.columns[1::2]
            )
        )
    return gender_counts_full


def get_gender_counts_keys() -> List[Tuple[str]]:
    """
    Formatting things here I can't figure out how to format in Jinja!
    """
    return [(f"artist_name_{g}", f"count_{g}") for g in "mfn"]


def get_chart_delta(
        new_chart: List[Track],
        old_chart: List[Track]
) -> Tuple[List[Track], List[Track]]:
    """
    Returns a list of tracks in the new chart and not in the old chart...
    and a list of tracks in the old chart but not in the new chart.

    Probably an easier way to do this!
    """
    not_in_old = [s for s in new_chart if s not in old_chart]
    not_in_new = [s for s in old_chart if s not in new_chart]
    return not_in_old, not_in_new


def update_chart(
        chart: Union[list[Track], None] = None,
        chart_date: Union[str, None] = None
) -> List[Track]:
    """
    Updates chart for current date.

    INPUTS:
        chart (List[Track]): chart to be added to db. Uses latest rap caviar if none provided.
        chart_date (str): date of chart to be added. Uses today via get_date() if none provided.

    OUTPUT:
        new_chart (List[Track]): chart for `chart_date`, which should be `chart`

    """
    if chart_date:
        assert re.match(r"\d{4}-\d{2}-\d{2}", chart_date), "chart_date format must be YYYY-MM-DD"
    else:
        chart_date = get_date()
    live_chart = chart if chart else load_rap_caviar()
    latest_chart_in_db = get_chart_from_db()

    if new_chart_check(latest_chart_in_db, live_chart):
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


def get_chart_from_db(chart_date: str = None) -> Tuple[str, List[Track]]:
    if not chart_date:
        chart_date = db_query("select max(chart_date) from chart")[0][0]
    q = f"""
        SELECT song_name, primary_artist_name FROM chart WHERE chart_date = '{chart_date}'
        """
    raw_chart = db_query(q)
    assert raw_chart, f"No chart found for {chart_date}"
    chart = parse_chart(raw_chart)
    return chart_date, chart


def get_daily_gender_counts(date_: str = None):
    q = """
        SELECT gender, count(*)
        FROM chart
        LEFT JOIN song on chart.song_spotify_id=song.song_spotify_id
        LEFT JOIN artist on song.artist_spotify_id = artist.spotify_id
        WHERE chart_date = "{}"
        GROUP BY gender;
        """
    return query_w_date(q, date_)


def load_chart(chart_date: str = None) -> Tuple[DataFrame, str]:
    """
    Loads the chart from chart_date, defaulting to the latest chart in the db.

    Returns it as a DataFrame, formatted for Flask HTML processing.

    TODO: Does it have to be pandas?
    """
    chart_date = get_most_recent_chart_date() if not chart_date else chart_date
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
    formatted_chart_date = dt.strptime(chart_date, "%Y-%m-%d").strftime("%B %-d, %Y")
    return full_chart, formatted_chart_date
