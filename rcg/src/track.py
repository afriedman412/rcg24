from collections import namedtuple
from typing import List, Tuple, Union, Iterable, Any

from sqlalchemy.engine.cursor import CursorResult

from ..db import db_query
from .gender import lookup_gender

Artist: tuple[str] = namedtuple(
    "Artist", [
        "name",
        "spotify_id",
    ]
)

Track: tuple[str, str, Tuple[Artist], str, str] = namedtuple(
    "Track", [
        "song_name",
        "song_spotify_id",
        "artists",
        "primary_artist_name",
        "primary_artist_spotify_id"
    ]
)


def parse_chart(chart: Union[Tuple[Any], CursorResult]) -> List[Track]:
    """
    Turns a chart queried from the db into a list of Tracks.
    """
    return [Track._make(t[2:]) for t in chart]


def parse_track(track: dict) -> Track:
    """
    Input:
        track (dict) - spotify track from chart

    Output:
        track_output (Track) - input track parsed into Track namedtuple
    """
    artists = tuple(Artist._make([a['name'], a['id']]) for a in track['artists'])
    artists = get_group_artists(artists)
    track_output = Track._make(
        [
            track['name'],
            track['id'],
            artists,
            artists[0].name,
            artists[0].spotify_id
        ]
    )
    return track_output


def get_group_artists(artists: Iterable[Artist]) -> Iterable[Artist]:
    """
    If artists is a group, get group artists.

    INPUT:
        artists (list) - list of artists from a Track

    OUTPUT:
        artists (list) - same list of artists with any group members added
    """
    for a in artists:
        group_artists = db_query(
            f'SELECT artist_name,artist_spotify_id from group_table where group_spotify_id="{a.spotify_id}"')
        if group_artists:
            artists += [Artist._make(a) for a in group_artists]
    return artists


def chart_song_check(
        song_spotify_id: str,
        primary_artist_spotify_id: str,
        chart_date: str
) -> Union[Tuple, None]:
    """
    Is the song song_spotify_id by artist_spotify_id already in the current chart?

    INPUT:
        song_spotify_id (str)
        primary_artist_spotify_id (str)
        chart_date (str)

    OUTPUT:
        query result, if it exists
    """
    return db_query(
        f"""
        SELECT * FROM chart
        WHERE song_spotify_id="{song_spotify_id}"
        AND primary_artist_spotify_id="{primary_artist_spotify_id}"
        AND chart_date="{chart_date}";
        """
    )


def artist_check(artist_spotify_id: str) -> Union[Tuple, None]:
    """
    Is artist_spotify_id in the db?
    """
    return db_query(
        f'SELECT * from artist where spotify_id="{artist_spotify_id}"'
    )


def add_artist(artist_name: str, artist_spotify_id: str) -> None:
    """
    INPUTS:
        artist_name (str)
        artist_spotify_id (str)
    """
    print(f"adding {artist_name} to artists")
    lfm_gender, wikipedia_gender, gender = lookup_gender(artist_name)
    q = """
        INSERT INTO
        artist (spotify_id, artist_name, last_fm_gender,
        wikipedia_gender, gender)
        VALUES (""" + ", ".join(
        f'"{p}"' for p in
        [artist_spotify_id, artist_name, lfm_gender, wikipedia_gender, gender]) + ");"
    db_query(q, commit=True)
    return


def feature_check(song_spotify_id: str, artist_spotify_id: str) -> Union[Tuple, None]:
    """
    Is artist_spotify_id's contribution to song_spotify_id in the db?
    """
    return db_query(
        f"""
        SELECT * FROM song
        WHERE song_spotify_id="{song_spotify_id}"
        AND artist_spotify_id="{artist_spotify_id}";
        """
    )


def add_song_feature(
        track: Track,
        artist_name: str,
        artist_spotify_id: str,
        primary: bool = False) -> None:
    """
    Add song feature.

    INPUTS:
        track (Track)
        artist_name (str)
        artist_spotify_id (str)
        primary (bool) - is the artist the primary artist?
    """
    q = """
        INSERT INTO
        song (song_name, song_spotify_id, artist_name, artist_spotify_id, `primary`)
        VALUES (""" + ", ".join(
        f'"{p}"' for p in
        [
            track.song_name,
            track.song_spotify_id,
            artist_name,
            artist_spotify_id,
            primary]) + ");"
    db_query(q)
    return


def add_all_songs_and_artists(track: Track) -> None:
    """
    Add all song features that aren't already in the db.
    """
    primary = True  # only first artist is primary
    for a in track.artists:
        if not feature_check(track.song_spotify_id, a.spotify_id):
            add_song_feature(track, a.name, a.spotify_id, primary)
        if not artist_check(a.name, a.spotify_id):
            add_artist(a.name, a.spotify_id)
        primary = False
    return
