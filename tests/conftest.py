import json
import logging
import os
from logging.handlers import RotatingFileHandler

import pytest
from pretest_setup import pretest_setup

from rcg.src import parse_spotify_chart
from rcg.src.track import Chart


@pytest.fixture(scope='session', autouse=True)
def configure_logging():
    log_file_path = "testing.log"
    file_handler = RotatingFileHandler(log_file_path, maxBytes=10240, backupCount=5)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)
    return file_handler


@pytest.fixture(scope='session')
def pretest():
    test_dir = pretest_setup()
    return test_dir


@pytest.fixture(scope='session')
def test_chart(pretest):
    test_rc = json.load(open(os.path.join(pretest, "test_chart.json")))
    test_chart: Chart = parse_spotify_chart("2023-01-01", raw_chart=test_rc)
    return test_chart
