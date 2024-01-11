from collections import namedtuple
from typing import Any, Dict, Iterable, List, Tuple, Union

from sqlalchemy.engine.cursor import CursorResult

from .dates import verify_date
from .db import db_query
from .gender import lookup_gender

Artist: tuple[str] = namedtuple(
    "Artist", [
        "name",
        "spotify_id",
        "primary"
    ]
)


def create_artist(name: str, spotify_id: str, primary: Union[str, bool] = False) -> Artist:
    if isinstance(primary, str) and primary in [True, 'True', 't']:
        primary = True
    return Artist(name, spotify_id, primary)


class Track:
    def __init__(
            self,
            song_name: str,
            song_spotify_id: str,
            artists: Tuple[Tuple[Artist]],
            primary_artist: Artist = None
    ):
        self.song_name = song_name
        self.song_spotify_id = song_spotify_id
        self.artists = artists
        if not primary_artist:
            try:
                primary_artist = next(a for a in artists if a.primary in ['T', 't', 'True', True])
            except StopIteration:
                raise StopIteration(f"no primary artists for {song_name}, (artists found: {artists})")
        self.primary_artist_name = primary_artist.name
        self.primary_artist_id = primary_artist.spotify_id
        return

    def __hash__(self):
        return hash(self.song_spotify_id)

    def __eq__(self, other):
        return isinstance(other, Track) and self.song_spotify_id == other.song_spotify_id

    def __repr__(self):
        return ", ".join([
            self.song_name,
            self.primary_artist_name,
            self.features
        ])

    @property
    def features(self):
        featured = [a.name for a in self.artists if a.primary != True]
        return ", ".join(featured) if featured else ""

    def _todict(self):
        """For Jinja, because getattr() doesn't work in Jinja"""
        return {k: self.__getattribute__(k) for k in ['primary_artist_name', 'song_name', 'features']}


class Chart:
    def __init__(
            self,
            chart_date: str,
            tracks: Iterable[Track]
    ):
        self.chart_date = chart_date
        self.tracks = set(tracks)
        return

    def __iter__(self):
        return iter(self.tracks)

    def __repr__(self):
        return (t for t in self.tracks)

    def __hash__(self):
        return hash(self.tracks)

    def __eq__(self, other):
        return isinstance(other, Chart) and self.tracks == other.tracks

    def make_charting_query(self) -> str:
        """
        Constructs a single query string for adding all tracks to the database.

        OUTPUT:
            q (str): mysql query string
        """
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
                        track.primary_artist_id,
                        self.chart_date
                    ]) + ")"
                for track in self.tracks
            ]
        )
        return q


def parse_spotify_track(track: Dict[Any, Any]) -> Track:
    """
    Input:
        track (dict) - spotify track from chart

    Output:
        track_output (Track) - input track parsed into Track class
    """
    artists = [create_artist(a['name'], a['id'], i==0) for i, a in enumerate(track['track']['artists'])]
    artists += get_group_artists(artists)
    return Track(
        track['track']['name'],
        track['track']['id'],
        artists
    )


@verify_date
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
        group_artists = db_query(
            f'''
            SELECT artist_name,artist_spotify_id
            FROM group_table
            WHERE group_spotify_id="{a.spotify_id}"
            ''')
        if group_artists:
            new_artists.append([create_artist(a[0], a[1]) for a in group_artists])
    return new_artists


def chart_song_check(
        song_spotify_id: str,
        primary_artist_spotify_id: str,
        chart_date: str
) -> Union[Tuple[Any], None]:
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


def artist_check(artist_spotify_id: str) -> Union[Tuple[Any], None]:
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


def feature_check(song_spotify_id: str, artist_spotify_id: str) -> Union[Tuple[Any], None]:
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
        if not artist_check(a.spotify_id):
            add_artist(a.name, a.spotify_id)
        primary = False
    return
