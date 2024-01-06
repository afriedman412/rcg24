import os
from ..db import db_commit, db_query
from .gender_code import full_gender_lookup


class Track:
    """
    input: track info from spotipy (formatted by parse_track)
    """
    def __init__(self, t, chart_date: str=None):
        from .code import get_date
        self.local = True if os.environ.get('LOCAL') in ("True", "true", "1") else False
        self.chart_date = chart_date if chart_date else get_date()
        self.parse_track(t)
        print(self.song_name, self.primary_artist_name, self.artists)
        self.get_group_artists()
        return

    def update_chart(self, add_to_chart: bool=True):
        if add_to_chart and not self.chart_song_check():
            self.chart_song()
        self.add_all_songs_and_artists()
        return

    def parse_track(self, t):
        self.song_name, self.song_spotify_id, self.artists, self.primary_artist_name, self.primary_artist_spotify_id = (t)
        return

    def get_group_artists(self):
        """
        If artists is a group, get group artists.
        """
        for artist_info in self.artists:
            print(artist_info)
            artist_name, artist_spotify_id = (artist_info)
            group_artists = db_query(
                f'SELECT artist_name,artist_spotify_id from group_table where group_spotify_id="{artist_spotify_id}"', self.local)
            if group_artists:
                self.artists += group_artists
        return

    def chart_song_check(self):
        """
        Is the song song_spotify_id by artist_spotify_id already in the current chart?
        """
        return db_query(
                    f"""
                    SELECT * FROM chart 
                    WHERE song_spotify_id="{self.song_spotify_id}"
                    AND primary_artist_spotify_id="{self.primary_artist_spotify_id}"
                    AND chart_date="{self.chart_date}";
                    """,
                self.local
                )
    
    def chart_song(self):
        q = """
            INSERT INTO
            chart (song_name, song_spotify_id, primary_artist_name, 
            primary_artist_spotify_id, chart_date)
            VALUES (""" + ", ".join(
            f'"{p}"' for p in 
            [
                self.song_name, 
                self.song_spotify_id, 
                self.primary_artist_name, 
                self.primary_artist_spotify_id, 
                self.chart_date
            ]) + ");"

        db_commit(q, self.local)
        return

    def artist_check(self, artist_name, artist_spotify_id):
        """
        Is artist_spotify_id in the db?
        """
        return db_query(f'SELECT * from artist where spotify_id="{artist_spotify_id}"', self.local)

    def add_artist(self, artist_name, artist_spotify_id):
        print(f"adding {artist_name} to artists")
        lfm_gender, wikipedia_gender, gender = full_gender_lookup(artist_name)
        q = """
            INSERT INTO 
            artist (spotify_id, artist_name, last_fm_gender, 
            wikipedia_gender, gender)
            VALUES (""" + ", ".join(
            f'"{p}"' for p in 
            [artist_spotify_id, artist_name, lfm_gender, wikipedia_gender, gender]) + ");"
        db_commit(q, self.local)
        return

    def song_check(self, artist_name, artist_spotify_id):
        """
        Is the song song_spotify_id featuring artist_spotify_id in the db?
        """
        return db_query(
                    f"""
                    SELECT * FROM song 
                    WHERE song_spotify_id="{self.song_spotify_id}"
                    AND artist_spotify_id="{artist_spotify_id}"; 
                    """,
                    self.local
                )

    def add_song_feature(self, artist_name, artist_spotify_id, primary: bool=False):
        """
        Add song feature.
        """
        q = f"""
            INSERT INTO 
            song (song_name, song_spotify_id, artist_name, artist_spotify_id, `primary`)
            VALUES (""" + ", ".join(
            f'"{p}"' for p in 
            [self.song_name, self.song_spotify_id, artist_name, artist_spotify_id, primary]) + ");"
        db_commit(q, self.local)
        return

    def add_all_songs_and_artists(self):
        """
        Add all song features that aren't already in the db.
        """
        primary = True # only first artist is primary
        for artist_info in self.artists:
            artist_name, artist_spotify_id = (artist_info)
            if not self.song_check(artist_name, artist_spotify_id):
                self.add_song_feature(artist_name, artist_spotify_id, primary)

            if not self.artist_check(artist_name, artist_spotify_id):
                self.add_artist(artist_name, artist_spotify_id)
            primary = False
        return

    

    