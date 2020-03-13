"""
Retrieve data from EIA Form 860 spreadsheets for analysis.

This modules pulls data from EIA's published Excel spreadsheets.

This code is for use analyzing EIA Form 860 data.
"""

import logging

import pandas as pd

import pudl.constants as pc
import pudl.extract.excel as excel

logger = logging.getLogger(__name__)


class Extractor(excel.GenericExtractor):
    DATASET = 'eia860'

    PAGE_GLOBS = {
        'boiler_generator_assn': '*EnviroAssoc*',
        'utility': '*Utility*',
        'plant': '*Plant*',
        'generator_existing': '*Generat*',
        'generator_proposed': '*Generat*',
        'generator_retired': '*Generat*',
        'ownership': '*Owner*',
    }

    def file_basename_glob(self, year, page):
        return self.PAGE_GLOBS[page]

    def process_raw(self, year, page, df):
        if 'report_year' not in df.columns:
            df['report_year'] = year
        return df

    def dtypes(self, year, page):
        dt = {'plant_id_eia': pd.Int64Dtype()}
        if 'zip_code' in self._metadata.all_columns(page):
            dt['zip_code'] = pc.column_dtypes['eia']['zip_code']
        return dt
