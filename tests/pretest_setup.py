from rcg.db import make_sql_engine, db_query
import pandas as pd
import os


def pretest_setup():
    test_dir = os.path.join(os.getcwd(), "tests/test_data")
    engine = make_sql_engine()
    for t in ['artist', 'group_table', 'chart', 'song']:
        print(t)
        df = pd.read_csv(os.path.join(test_dir, f'{t}_df.csv'))
        df.to_sql(t, con=engine, if_exists='replace', index=False)
    print('db setup!')
    assert db_query('select artist_name from artist where spotify_id="4kYSro6naA4h99UJvo89HB"'
                    ) == (('Cardi B',),)
    assert db_query(
        "select max(chart_date) from chart;"
        ) == (('2022-12-31',),)
    assert db_query(
        "select distinct(song_name) from chart where primary_artist_name='Drake'"
        ) == (
            ('Jimmy Cooks (feat. 21 Savage)',),
            ('Pussy & Millions (feat. Travis Scott)',),
            ('Rich Flex',),
            ('Major Distribution',),
            ('Privileged Rappers',))
    return test_dir
