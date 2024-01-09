# gender counts
gender_count_q = """
    SELECT
        gender,
        COUNT(*) AS total,
        COUNT(*) / SUM(COUNT(*)) OVER () * 100 AS percentage
    FROM chart
    INNER JOIN song ON chart.song_spotify_id=song.song_spotify_id
    LEFT JOIN artist ON song.artist_spotify_id=artist.spotify_id
    WHERE chart_date="{}"
    GROUP BY gender
    """

# chart
chart_q = """
    SELECT
        chart.song_name,
        chart.song_spotify_id,
        artist.artist_name,
        artist.spotify_id,
        song.primary
    FROM chart
    INNER JOIN song ON chart.song_spotify_id=song.song_spotify_id
    LEFT JOIN artist ON song.artist_spotify_id=artist.spotify_id
    WHERE chart_date="{}"
    """

# chart w features
chart_w_features_q = """
    SELECT
        chart.song_name,
        MAX(CASE WHEN (
            song.primary = 'True' or song.primary = 't'
            ) THEN artist.artist_name END) AS primary_artist_name,
        GROUP_CONCAT(CASE WHEN (
            song.primary = 'False' or song.primary = 'f'
            ) THEN artist.artist_name END) AS features_artist_names
    FROM
        chart
    INNER JOIN
        song ON chart.song_spotify_id = song.song_spotify_id
    LEFT JOIN
        artist ON song.artist_spotify_id = artist.spotify_id
    WHERE
        chart.chart_date = '{}'
    GROUP BY
    chart.song_spotify_id, chart.song_name;
    """

# tally
tally_q = """
    SELECT
    artist.artist_name,
    artist.gender,
    COUNT(chart.song_spotify_id) AS appearances
    FROM chart
    INNER JOIN
        song ON chart.song_spotify_id = song.song_spotify_id
    INNER JOIN
        artist ON song.artist_spotify_id = artist.spotify_id
    WHERE chart.chart_date = '{}'
    GROUP BY
        artist.artist_name,
        artist.gender,
        artist.spotify_id;
    """
