"""Code for adding charts to the database."""
from typing import Any, Dict, List

from .db import db_query
from .gender import lookup_gender
from .track import (Appearance, Artist, Chart, Track, create_artist)


# for reading from spotipy
def parse_spotify_track(track: Dict[Any, Any]) -> Track:
    """
    Creates [Artist] for every artist.
    Adds any group artists in the db.

    Input:
        track (dict): spotify track from chart

    Output:
        track_output (Track): input track parsed into Track class
    """
    assert 'track' in track and 'artists' in track['track']
    artists = [create_artist(a['name'], a['id'], i == 0) for i, a in enumerate(track['track']['artists'])]
    artists = get_group_artists(artists)
    return Track(
        track['track']['name'],
        track['track']['id'],
        artists
    )


def parse_spotify_chart(chart_date: str, raw_chart: Dict[Any, Any]) -> Chart:
    """
    Converts a spotify chart (dict) into a Chart.

    INPUTS:
        chart_date (str) - should be current date, but leaving it variable for qc and testing.
            (load_rap_caviar() automatically uses current date)
        raw_chart (dict) - spotify chart

    OUTPUT:
        parsed_chart (Chart)
    """
    assert 'tracks' in raw_chart
    tracks = [parse_spotify_track(t) for t in raw_chart['tracks']['items']]
    parsed_chart = Chart(chart_date, tracks)
    return parsed_chart


def get_group_artists(artists: List[Artist]) -> List[Artist]:
    """
    If artists is a group, get group artists.

    INPUT:
        artists (list) - list of artists from a Track -- can be a tuple?

    OUTPUT:
        artists (tuple) - same list of artists with any group members added
    """
    new_artists = []
    for a in artists:
        new_artists.append(a)
        group_artists = db_query(
            f'''
            SELECT artist_name,artist_spotify_id
            FROM group_table
            WHERE group_spotify_id='{a.spotify_id}'
            ''')
        if group_artists:
            new_artists += ([create_artist(a[0], a[1]) for a in group_artists])
    return new_artists


def add_chart_to_db(chart: Chart) -> None:
    # verify chart does not already exist
    verification = db_query(f"SELECT count(*) FROM chart WHERE chart_date='{chart.chart_date}'")[0][0]
    assert verification == 0, f"Chart at date {chart.chart_date} already contains {str(verification)} items."
    charting_query = chart.make_charting_query()
    db_query(charting_query, commit=True)
    for data_type in ['artists', 'appearances']:
        verify_data(chart, data_type)

    verify = db_query(f"SELECT count(*) FROM chart WHERE chart_date='{chart.chart_date}'")[0][0]
    assert verify == len(chart.tracks), str(verify)
    return


def verify_data(
        chart: Chart,
        data_type: str
) -> None:
    assert data_type in ['artists', 'appearances']
    missing = globals()[f"find_missing_{data_type}"](chart)
    if missing:
        globals()[f'add_multiple_{data_type}'](missing)
    missing_check = globals()[f"find_missing_{data_type}"](chart)
    assert len(missing_check) == 0, missing_check
    return


def find_missing_artists(chart: Chart) -> List[Artist]:
    """
    INPUT:
        chart (Chart)
    OUTPUT:
        missing_artists (List[Artist])
    """
    all_artist_ids = db_query("""
        SELECT DISTINCT spotify_id from artist
        """)

    return [
        a for a in chart.artists() if a.spotify_id not in
        [i[0] for i in all_artist_ids]
    ]


def make_artist_query(artist: Artist) -> str:
    """
    INPUT:
        artist (Artist)

    OUTPUT:
        query (str): partial sql string for adding artist to db
    """
    print(f"adding {artist.name} to artists")
    lfm_gender, wikipedia_gender, gender = lookup_gender(artist.name)
    query = '(' + ", ".join(
            f'"{p}"' for p in
            [
                artist.spotify_id,
                artist.name, lfm_gender,
                wikipedia_gender,
                gender]
    ) + ")"
    return query


def add_multiple_artists(artists: List[Artist]) -> None:
    """
    Creates a full query to add multiple artists to the database.
    Checks all artist ids in db against artists to add to verify all have been added.

    INPUT:
        artists (List[Artist])
    """
    query = """
        INSERT INTO
            artist (
                spotify_id,
                artist_name,
                last_fm_gender,
                wikipedia_gender,
                gender
            )
        VALUES """
    artist_queries = ",\n\t".join(set([make_artist_query(a) for a in artists]))
    query = query + artist_queries + ";"
    db_query(query, commit=True)
    return


def find_missing_appearances(chart: Chart) -> List[Appearance]:
    """
    INPUT:
        chart (Chart)
    OUTPUT:
        missing_appearances (List[Appearance])
    """
    all_appearances = db_query("""
        SELECT DISTINCT song.song_spotify_id, song.artist_spotify_id
        FROM song
    """)
    return [
        a for a in chart.appearances()
        if (a.song_spotify_id, a.artist_spotify_id) not in all_appearances
    ]


def make_appearance_query(appearance: Appearance) -> str:
    """
    INPUT:
        appearance (Appearance)

    OUTPUT:
        query (str): partial sql string for adding appearance to song table
    """
    print(f"adding {appearance.song_name}, {appearance.artist_name} to song table")
    query = '(' + ", ".join(
            f'"{appearance.__getattribute__(p)}"'
            for p in
            [
                "song_spotify_id",
                "song_name",
                "artist_spotfy_id",
                "artist_name",
                "primary"
            ]) + ")"
    return query


def add_multiple_appearances(appearances: List[Appearance]) -> None:
    """
    Creates a full query to add multiple appearances to the database.
    Checks song table to verify all have been added.

    INPUT:
        appearances (List[Appearance])
    """
    query = """
        INSERT INTO
            song (
                song_spotify_id,
                song_name,
                artist_spotify_id,
                artist_name,
                primary
            )
        VALUES """
    appearance_queries = ",\n\t".join([make_appearance_query(a) for a in appearances])
    query = query + appearance_queries + ";"
    db_query(query, commit=True)
    return
