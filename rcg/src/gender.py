import os
from collections import Counter
from typing import Any, Tuple

import pylast
import wikipedia


def lookup_gender(artist_name: str) -> Tuple[str, str, str]:
    """
    Gets the gender from last.fm and wikipedia, then determines the "official" gender.

    Returns all three.
    """
    lfm_gender = get_lastfm_gender(artist_name)
    wikipedia_gender = get_wikipedia_gender(artist_name)
    gender = parse_genders(lfm_gender, wikipedia_gender)
    return lfm_gender, wikipedia_gender, gender


def access_lfm() -> Any:
    """
    Instantiates a lastfm network object w credentials.
    """
    return pylast.LastFMNetwork(
        api_key=os.environ['LAST_FM_ID'],
        api_secret=os.environ['LAST_FM_SECRET'],
        username=os.environ['LAST_FM_USER'],
        password_hash=pylast.md5(os.environ['LAST_FM_PW'])
    )


def get_lastfm_gender(artist: str) -> str:
    """
    Loads the LastFM bio for an artists for gender processing.
    """
    lastfm_network = access_lfm()
    try:
        bio = pylast.Artist(artist, lastfm_network).get_bio_content(language="en")
    except pylast.WSError:
        return "l"  # artist not found in last fm
    if (not bio) or (bio.startswith('<a href="https://www.last.fm/music/')):
        return "x"  # no last fm bio
    return gender_count(bio)


def get_wikipedia_gender(artist: str) -> str:
    """
    Loads the wikipedia bio for an artists for gender processing.
    """
    try:
        bio = wikipedia.page(artist, auto_suggest=False, redirect=True).content
    except wikipedia.DisambiguationError as e:
        try:
            artist_ = next(o for o in e.options if 'rapper' in o)
            bio = wikipedia.page(artist_, auto_suggest=False, redirect=True).content
        except StopIteration:
            return "d"  # disambiguation error
    except wikipedia.PageError:
        return "p"  # page error
    return gender_count(bio)


def gender_count(bio: str) -> str:
    """
    Guesses gender based on pronouns in bio.
    """
    pronoun_count = Counter(bio.lower().split())
    data = [
        ('m', ['he', 'him', 'his']),
        ('f', ['she', 'her', 'hers']),
        ('n', ['they', 'them', 'theirs'])
    ]
    counts = {
        d[0]: sum(
            [pronoun_count[p] for p in d[1]]
        ) for d in data
    }
    return max(counts, key=counts.get)


def parse_genders(last_fm_gender: str, wikipedia_gender: str) -> str:
    """
    Logic to decide which gender to return (m, f, n, or x)

    'm' or 'f' if either is present at all, 'n' if either is 'n', otherwise 'x'.
    """
    try:
        return next(
            iter({last_fm_gender, wikipedia_gender}.intersection('mf'))
        )
    except StopIteration:
        if last_fm_gender == 'n' or wikipedia_gender == 'n':
            return 'n'
        else:
            return 'x'
