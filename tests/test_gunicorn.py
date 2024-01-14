import os

import pytest
import requests


@pytest.fixture
def gunicorn_server():
    import subprocess
    import time

    command = [
        "gunicorn",
        "--config",
        "gunicorn_config.py",
        "--env",
        "FLASK_ENV=test",
        "app:app",
    ]
    process = subprocess.Popen(command)

    time.sleep(2)

    yield process
    process.terminate()
    process.wait()


def test_guni_env(gunicorn_server):
    assert os.environ.get("FLASK_ENV") == "test"


def test_guni(gunicorn_server):
    response = requests.get("http://127.0.0.1:5000/")
    assert response.status_code == 200
    assert "Gender Tracker" in response.text
