from flask_testing import TestCase

from app import app
from rcg.src.db import db_query


class TestFolio(TestCase):
    def create_app(self):
        return app

    def test_home_route(self):
        response = self.client.get("/")
        self.assert200(response)


def test_sql():
    q = """
        select artist_name
        from artist
        where spotify_id="0du5cEVh5yTK9QJze8zA0C";
        """
    result = db_query(q)
    assert result[0][0] == "Bruno Mars"
