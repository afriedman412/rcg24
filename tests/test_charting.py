import json
import logging
import os

from rcg.src import load_chart, load_spotipy, parse_spotify_chart
from rcg.src.adding import add_chart_to_db
from rcg.src.dates import get_most_recent_chart_date
from rcg.src.db import db_query
from rcg.src.gender import lookup_gender
from rcg.src.track import Chart


def test_gender():
    logging.info("TESTING GENDER")
    assert lookup_gender("Nicki Minaj") == ('f', 'f', 'f')
    assert lookup_gender("Yeat") == ("m", "m", "m")


def test_spotipy():
    logging.info("TESTING SPOTIPY")
    sp = load_spotipy()
    drake = sp.artist('spotify:artist:3TVXtAsR1Inumwj472S9r4')
    assert drake['name'] == "Drake"


def test_parse_spotify_chart(pretest):
    test_rc = json.load(open(os.path.join(pretest, "test_chart.json")))
    test_chart: Chart = parse_spotify_chart("2023-01-01", raw_chart=test_rc)
    assert test_chart.chart_date == "2023-01-01"
    assert len(test_chart.appearances()) == 94


def test_group_artists():
    assert db_query(
        """select artist_name, artist_spotify_id
        from group_table
        where group_spotify_id='5Rzqmz1zAszembFHGZQuAt'"""
    ) == (
        ('Tajai', '3C3HtG0MPpmkY87mctxgSk'),
        ('A-Plus', '5WwguN1D1fTYBZL1rEBkM7'),
        ('Phesto', '2tgyOPAmFNLotTv5yiQ9Ip'),
        ('Opio', '1dpAIrpTGOrblTYJHpE8ao')
    )


def test_load_chart():
    chart = load_chart("2022-12-31")
    assert len(chart.appearances()) == 86


def test_update_chart(pretest):
    test_rc = json.load(open(os.path.join(pretest, "test_chart.json")))
    test_chart: Chart = parse_spotify_chart("2023-01-01", raw_chart=test_rc)
    assert len([a for a in test_chart.artists() if a.name is None]) == 0
    assert get_most_recent_chart_date().strftime("%Y-%m-%d") == "2022-12-31"
    logging.info("most recent chart date pre-update is correct")
    add_chart_to_db(test_chart)
    assert get_most_recent_chart_date().strftime("%Y-%m-%d") == "2023-01-01"
    logging.info("most recent chart date post-update is correct")
    new_chart = load_chart("2023-01-01")
    assert test_chart == new_chart

    assert set(db_query(
        "select distinct(song_name) from chart where primary_artist_name='Drake'"
    )) == set((
        ('Jimmy Cooks (feat. 21 Savage)',),
        ('Pussy & Millions (feat. Travis Scott)',),
        ('Rich Flex',),
        ('Major Distribution',),
        ('Privileged Rappers',),
        ('First Person Shooter (feat. J. Cole)',),
        ('You Broke My Heart',),
        ('IDGAF (feat. Yeat)',)
    ))


def test_artist_added():
    spotify_id = db_query(
        "SELECT spotify_id from artist where artist_name='Doja Cat'"
    )
    assert spotify_id[0][0] == '5cj0lLjcoR7YOSnhnX0Po5'
