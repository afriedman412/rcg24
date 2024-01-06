import pandas as pd
from pandas import DataFrame
from typing import Tuple, Literal, List
import regex as re
from .code import get_date
from ..config.config import COLORS, GENDERS # TODO: also this, better

from io import BytesIO
import base64
import logging # TODO: add logging


class Chart:
    """
    Preps chart data for flask template rendering.

    Moved "load_chart" to "code" section.

    TODO: consolidate the load chart protocol with the dash code
    """
    def __init__(self, full_chart: DataFrame, chart_date: str=None):
        self.full_chart = full_chart.fillna("")
        self.chart_date = chart_date if chart_date else get_date()
        return
    
    def count_data(self) -> DataFrame:
        count_data = pd.DataFrame(
                [
                self.full_chart['gender'].value_counts().astype(int),
                self.full_chart['gender'].value_counts(normalize=True).map(lambda n: n*100).round(1)
                ],
                ["Total", "Percentage"]
            )

        return count_data

    def gender_count_data(self, g: Literal["m", "f", "n", "x"]):
        return self.count_data().to_dict().get(g, None)

    def chart_w_features(self) -> DataFrame:
        """
        Adds "Features" column to the full chart.
        """
        features = self.full_chart.query("primary_artist_name != artist_name").groupby("song_name")['artist_name'].apply(lambda a: ", ".join(a))
        main_chart = self.full_chart.query("primary_artist_name == artist_name").set_index("song_name")
        chart_w_features = main_chart.drop(
            ['chart_date', 'artist_name', 'gender'],axis=1).join(features).reset_index().rename(columns={'artist_name':'features'}).fillna("")

        chart_w_features.columns = ['Song', 'Primary Artist', 'Features']
        chart_w_features['Song'] = chart_w_features['Song'].map(self.remove_features_from_title)
        return chart_w_features.to_dict('records')

    def remove_features_from_title(self, t):
        return re.sub(r"\s[\(\[](feat\.|with).+[\)\]]", "", t)

    def total_chart_dict(self) -> dict:
        """
        Extracts gender data and converts to one dict.
        """
        total_df = self.full_chart['gender'].value_counts().rename_axis('gender').reset_index(name='count') # gender count
        pct_df = self.full_chart['gender'].value_counts(normalize=True).rename_axis('gender').reset_index(name='pct') # gender pct
        pct_df['pct'] = pct_df['pct'].map(lambda c: c*100).round(2) # formatted gender pct
        total_df=total_df.set_index('gender').join(pct_df.set_index("gender")).reset_index() # join counts and pct
        total_chart_dict = total_df.to_dict("records") # convert to dict
        for k in set(GENDERS).difference(set([d['gender'] for d in total_chart_dict])):
            total_chart_dict.append({"gender":k, "count":0, "pct":0}) # add any missing genders
        return total_chart_dict

    @property
    def gender_counts_prep(self) -> DataFrame:
        """
        Formats artist-wise gender counts for "Tally". Done this way for annoying formatting reasons.
        """
        gender_counts = {
            c:self.full_chart.query(
                f"gender=='{c}'")['artist_name'].value_counts().reset_index().rename(
                    columns={"index": f"artist_name_{c[0].lower()}", "artist_name":f"count_{c[0].lower()}"})for c in GENDERS
        }

        gender_counts_full = gender_counts['Male'].join(
            gender_counts['Female']).join(
            gender_counts['Non-Binary']
        )

        gender_counts_full.fillna("", inplace=True)
        
        for c in gender_counts_full.columns:
            if 'count' in c:
                gender_counts_full[c] = gender_counts_full[c].map(lambda c: int(c) if isinstance(c, float) else c)

        return gender_counts_full.fillna("")

    def gender_counts_keys(self) -> Tuple:
        """
        Formatting things here I can't figure out how to format in Jinja
        """
        return [(f"artist_name_{g}", f"count_{g}") for g in "mfn"]

    def gender_counts_full(self) -> DataFrame:
        return self.gender_counts_prep.to_dict('records')

    def gender_indexes(self):
        return list(zip(self.gender_counts_prep.columns[::2], self.gender_counts_prep.columns[1::2]))

def chart_delta(new_chart: Chart, old_chart: Chart) -> Tuple[List]:
    """
    Returns a list of tracks in the new chart and not in the old chart, and a list of tracks in the old chart but not in the new chart.
    """
    not_in_old = [s for s in new_chart.chart_w_features() if s not in old_chart.chart_w_features()]
    not_in_new = [s for s in old_chart.chart_w_features() if s not in new_chart.chart_w_features()]
    return not_in_old, not_in_new