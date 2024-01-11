import json
import os

import pytest

from rcg.src.db import db_query
from rcg.src import load_spotipy, update_chart
from rcg.src.dates import get_most_recent_chart_date
from rcg.src.gender import lookup_gender
from rcg.src.track import parse_spotify_chart
from tests.pretest_setup import pretest_setup


@pytest.fixture(scope='session')
def pretest():
    test_dir = pretest_setup()
    return test_dir


def test_gender():
    assert lookup_gender("Nicki Minaj") == ('f', 'f', 'f')
    assert lookup_gender("Yeat") == ("m", "m", "m")


def test_spotipy():
    sp = load_spotipy()
    drake = sp.artist('spotify:artist:3TVXtAsR1Inumwj472S9r4')
    assert drake['name'] == "Drake"


def test_chart(pretest):
    test_dir = pretest
    test_rc = json.load(open(os.path.join(test_dir, "test_chart.json")))
    test_chart = parse_spotify_chart(raw_chart=test_rc)
    assert get_most_recent_chart_date().strftime("%Y-%m-%d") == "2022-12-31"
    charted_output = update_chart("2024-01-01", test_chart)
    assert test_chart == charted_output

    assert db_query(
        "select distinct(song_name) from chart where primary_artist_name='Drake'"
    ) == (
        ('Jimmy Cooks (feat. 21 Savage)',),
        ('Pussy & Millions (feat. Travis Scott)',),
        ('Rich Flex',),
        ('Major Distribution',),
        ('Privileged Rappers',),
        ('First Person Shooter (feat. J. Cole)',),
        ('You Broke My Heart',),
        ('IDGAF (feat. Yeat)',)
    )


def test_artist_added():
    spotify_id = db_query(
        "SELECT spotify_id from artist where artist_name='Doja Cat'"
    )
    assert spotify_id[0][0] == '5cj0lLjcoR7YOSnhnX0Po5'
