"""
Inconsistant implementation of local/remote db control. Sometimes you can control it and sometimes you can't. That's probably fine, because the default is "LOCAL" environmental variable. But it's bad form.
"""
import os
import click
from rcg.db import db_commit, db_query
from dotenv import load_dotenv
from rcg import app
from rcg.code.track_code import Track
from rcg.code.code import (
    get_date, 
    get_counts, 
    get_chart_from_db,
    most_recent_chart_date, 
    load_rap_caviar,
    load_one_song,
    update_chart
    )

@click.group()
@click.option("-l", "--local", is_flag=True)
@click.pass_context
def tools(ctx, local):
    ctx.ensure_object(dict)
    print(f"** Tools USING {'LOCAL' if local else 'REMOTE'} **")
    ctx.obj['LOCAL'] = "True" if local else "False"
    load_dotenv()
    os.environ['LOCAL'] = "True" if local else "False"
    pass

@tools.command()
def current():
    chart = get_chart_from_db()
    click.echo(chart)
    return

@tools.command()
def count():
    """
    Returns gender counts for current chart.
    """
    with app.app_context():
        c = get_counts()
        click.echo(c)
    return

@tools.command()
def current_rc():
    """
    Returns the rap caviar chart from Spotify.
    """
    chart = load_rap_caviar()
    for c in chart:
        click.echo(c)
    return

@tools.command()
@click.pass_context
def xday(ctx):
    """
    Deletes the chart for the current day.
    """
    chart_date = get_date()
    q = f"""
        DELETE FROM chart
        WHERE chart_date='{chart_date}'
        """
    db_commit(q, ctx.obj['LOCAL'])
    print("max date:", most_recent_chart_date())
    click.echo(f"{chart_date} data deleted")
    return

@tools.command()
@click.pass_context
def update(ctx):
    """adds new rcg data if it exists"""
    output = update_chart(ctx.obj['LOCAL'])
    if output:
        click.echo('db updated')
    return output

@tools.command()
@click.option("-s", "--song_spotify_id")
def add_artists(song_spotify_id: str):
    """
    Adds all artists for a song_spotify_id to the db.
    """
    track_info = load_one_song(song_spotify_id)
    t = Track(track_info)
    t.update_chart(False)
    return

@tools.command()
@click.option("-a", "--artist")
@click.option("-g", "--gender")
@click.pass_context
def gender(ctx, artist, gender):
    """
    Sets artist's gender.
    """
    q = f"""
    UPDATE artist
    SET gender="{gender}"
    WHERE artist_name="{artist}";
    """
    db_commit(q, ctx.obj["LOCAL"])
    click.echo(f'{artist} gender is now {gender}')
    return

@tools.command()
@click.pass_context
def reload(ctx):
    """
    xday and update combined
    """
    old_max_date = most_recent_chart_date(ctx.obj['LOCAL'])
    click.echo(f"deleting chart date: {old_max_date}")
    q = f"""
        DELETE FROM chart
        WHERE chart_date="{old_max_date}"
        """
    db_commit(q, ctx.obj['LOCAL'])
    new_max_date = most_recent_chart_date(ctx.obj['LOCAL'])
    click.echo(f"new max date: {new_max_date}")
    output = update_chart(ctx.obj['LOCAL'])
    if output:
        click.echo('db updated')
    return

@tools.command()
@click.pass_context
def reload(ctx):
    """
    xday and update combined
    """
    old_max_date = most_recent_chart_date(ctx.obj['LOCAL'])
    click.echo(f"deleting chart date: {old_max_date}")
    q = f"""
        DELETE FROM chart
        WHERE chart_date="{old_max_date}"
        """
    db_commit(q, ctx.obj['LOCAL'])
    new_max_date = most_recent_chart_date(ctx.obj['LOCAL'])
    click.echo(f"new max date: {new_max_date}")
    output = update_chart(ctx.obj['LOCAL'])
    if output:
        click.echo('db updated')
    return

@tools.command()
@click.pass_context
def set_group_genders(ctx):
    q = """UPDATE artist 
            SET gender = "g"
            WHERE spotify_id in (SELECT group_spotify_id FROM group_table)
        """
    db_commit(q, ctx.obj["LOCAL"])
    click.echo(f'group genders updated')
    return
    
@tools.command()
@click.pass_context
def max_date(ctx):
    q = "select max(chart_date) from chart"
    print(db_query(q, ctx.obj["LOCAL"])[0][0])
    return

if __name__=="__main__":
    tools()
    
        
