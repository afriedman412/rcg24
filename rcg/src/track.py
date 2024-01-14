from collections import namedtuple
from typing import List, Union, Any, Dict, Iterable

Artist: tuple[str] = namedtuple(
    "Artist", [
        "name",
        "spotify_id",
        "primary"
    ]
)

Appearance: tuple[str, str, str, str, bool] = namedtuple(
    "Appearance", [
        "song_spotify_id",
        "song_name",
        "artist_spotify_id",
        "artist_name",
        "primary"
    ]
)


class Track:
    """
    INPUTS:
        song_name (str)
        song_spotify_id (str)
        artists (Tuple[Artist])
        primary_artist (Artist): if no primary artist is provided, uses the first artist where .primary is True
    """

    def __init__(
            self,
            song_name: str,
            song_spotify_id: str,
            artists: List[Artist],
            primary_artist: Union[Artist, None] = None
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
        assert self.primary_artist_name is not None, \
            f"bad formatting for primary artist, {song_name}, (artists found: {artists})"
        return

    def __hash__(self) -> int:
        return hash(self.song_spotify_id + self.primary_artist_id)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Track) and self.song_spotify_id == other.song_spotify_id

    @property
    def features(self) -> str:
        featured = [str(a.name) for a in self.artists if a.primary is not True]
        if len(featured) < 1:
            return ""
        return ", ".join(featured)

    def format_for_charting(self, chart_date: str) -> str:
        return "(" + ", ".join(
            f'"{p}"' for p in
            [
                self.song_name,
                self.song_spotify_id,
                self.primary_artist_name,
                self.primary_artist_id,
                chart_date
            ]) + ")"

    def appearances(self) -> list[Appearance]:
        """
        For adding to songs table.

        song_spotify_id, song_name, artist_spotify_id, artist_name, primary
        """
        return [
            Appearance(self.song_spotify_id, self.song_name, a.spotify_id, a.name, a.primary) for a in self.artists
        ]

    def _todict(self) -> Dict[str, str]:
        """For Jinja, because getattr() doesn't work in Jinja"""
        return {k: self.__getattribute__(k) for k in ['primary_artist_name', 'song_name', 'features']}


class Chart:
    def __init__(
            self,
            chart_date: str,
            tracks: List[Track]
    ):
        self.chart_date = chart_date
        self.tracks = set(tracks)
        return

    def __iter__(self) -> Iterable[Track]:
        return iter(self.tracks)

    def __hash__(self) -> int:
        return hash(self.tracks)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Chart) and self.tracks == other.tracks

    def appearances(self) -> list[Appearance]:
        return [
            a for t in self.tracks
            for a in t.appearances()
        ]

    def artists(self) -> set[Artist]:
        return set([
            a for t in self.tracks
            for a in t.artists
        ])

    def make_charting_query(self) -> str:
        """
        Constructs a single query string for adding all tracks to the database.

        OUTPUT:
            q (str): mysql query string
        """
        q = """
                INSERT INTO
                chart (
                    song_name,
                    song_spotify_id,
                    primary_artist_name,
                    primary_artist_spotify_id,
                    chart_date
                )
                VALUES """

        q += ",\n\t".join([t.format_for_charting(self.chart_date) for t in self.tracks]) + ";"
        return q


def create_artist(name: str, spotify_id: str, primary: Union[str, bool] = False) -> Artist:
    if isinstance(primary, str) and primary in ['True', 't']:
        primary = True
    return Artist(name, spotify_id, primary)


def make_track_from_appearances(appearances: List[Appearance]) -> Track:
    return Track(
        song_name=appearances[0].song_name,
        song_spotify_id=appearances[0].song_spotify_id,
        artists=[Artist(a.artist_name, a.artist_spotify_id, a.primary) for a in appearances]
    )
