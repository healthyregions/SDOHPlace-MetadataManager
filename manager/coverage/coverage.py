#!/usr/bin/env python3
import os
import argparse
from enum import Enum

import pandas as pd
import geopandas as gpd

# Map "spatial_resolution" above with the prefix to use
spatial_resolution_prefix_map = {
    'state': {
        'prefix': '040US',
        'shp_url': 'https://herop-geodata.s3.us-east-2.amazonaws.com/oeps/state-2018-500k-shp.zip',
        'id_length': 2,
    },
    'county': {
        'prefix': '050US',
        'shp_url': 'https://herop-geodata.s3.us-east-2.amazonaws.com/oeps/county-2018-500k-shp.zip',
        'id_length': 5,
    },
    'tract': {
        'prefix': '140US',
        'shp_url': 'https://herop-geodata.s3.us-east-2.amazonaws.com/oeps/tract-2018-500k-shp.zip',
        'id_length': 11,
    },
    'bg': {
        'prefix': '150US',
        'shp_url': 'https://herop-geodata.s3.us-east-2.amazonaws.com/oeps/bg-2018-500k-shp.zip',
        'id_length': 12,
    },
    'zcta': {
        'prefix': '860US',
        'shp_url': 'https://herop-geodata.s3.us-east-2.amazonaws.com/oeps/zcta-2018-500k-shp.zip',
        'id_length': 5,
    },
}

# Enum for spatial_reolution
class SpatialResolution(str, Enum):
    state = 'state'
    county = 'county'
    tract = 'tract'
    blockgroup = 'blockgroup'
    zcta = 'zcta'

    def __str__(self) -> str:
        return self.value

    # Constant prefixes based on spatial resolution
    def to_prefix(self):
        return spatial_resolution_prefix_map[self.value]['prefix']

    def get_geodataframe(self):
        return gpd.read_file(spatial_resolution_prefix_map[self.value]['shp_url'])

    def id_length(self):
        return spatial_resolution_prefix_map[self.value]['id_length']


STUDY_DATASET_DIRECTORY = os.getenv('STUDY_DATASET_DIRECTORY', 'manager/data/test')
MASTER_GEOGRAPHY_DIRECTORY = os.getenv('MASTER_GEOGRAPHY_DIRECTORY', 'manager/data/master')

# Mapping of dataset to verify -> master file used for verification
# TODO:  Map all files from Box?
file_map = {
    'SVI_2010_US.csv': {
        'mgeo': '2010-tract.csv',
        'spatial_resolution': 'tract'
    },

    'SVI_2010_US_county.csv': {
        'mgeo': '2010-county.csv',
        'spatial_resolution': 'county'
    },
}

# Store coverage results in a new dictionary
coverage = {}

def check_coverage(file_path, geography, id_field=None):
    print('Checking coverage...')

    geog_lookup = SpatialResolution(geography)
    study_df, use_id = read_csv(file_path, id_field)
    study_df[use_id] = study_df[use_id].astype(str).str.zfill(geog_lookup.id_length())
    print(study_df[use_id])

    # Read master geography file
    gdf = geog_lookup.get_geodataframe()
    herop_id_col = 'HEROP_ID'  # Column in df2 that should match col1 + '140US'
    gdf[herop_id_col] = gdf[herop_id_col].astype(str)
    print(gdf[herop_id_col])

    # Use a predicate to compare FIPS to HEROP_ID
    mask = ~(gdf[herop_id_col]).isin(geog_lookup.to_prefix() + study_df[use_id])
    missing_df = gdf[mask]

    print(f'{len(gdf)} HEROP_IDs are present in master geography file.')
    print(f'{len(missing_df)} are missing from the input dataset ({file_path}).')
    print("generating highlight_ids list...")

    highlight_ids = []
    if missing_df.shape[0] == 0:
        highlight_ids = [f"{geog_lookup.to_prefix()}*"]
    else:
        # if less than half the total ids are missing, then use missing ids with negative filter
        if missing_df.shape[0] < gdf.shape[0] / 2:
            highlight_ids = [f"-{i}" for i in missing_df[herop_id_col]]
        # otherwise, use matching ids with positive filter
        else:
            mask = (gdf[herop_id_col]).isin(geog_lookup.to_prefix() + study_df[use_id])
            matching_df = gdf[mask]
            highlight_ids = [i["HEROP_ID"] for i in matching_df]

    print('Done checking!')

    # Generate the proper entry for highlight_ids
    return highlight_ids

def report_coverage():
    print('Reporting coverage')
    for check, missing in coverage.items():
        mgeo_path = file_map[check]['mgeo']
        print(f'The following HEROP_IDs are present in master geography file ({mgeo_path}),\n')
        print(f'but no matching FIPS was found in the dataset ({check}):\n')
        print(missing['HEROP_ID'])

        # TODO: Write to CSV file?

    print('Done reporting!')

def read_csv(filepath, id_field):
    print(f'Reading {filepath}...')
    df = pd.read_csv(filepath, dtype=str)

    use_id = None

    if 'FIPS' in df.columns:
        print(f'This file has FIPS column: {len(df.index)} rows found')
        use_id = "FIPS"
    elif id_field in df.columns:
        print(f'This file has {id_field} column: {len(df.index)} rows found')
        use_id = id_field
    else:
        print(f'WARNING! Neither FIPS, HEROP_ID, nor the provided id field were found. Available columns: {str(df.columns)}')
        exit()
    return (df, use_id)

def main():
    print('Running coverage checker...')
    check_coverage()
    report_coverage()

if __name__=="__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="path to input file")
    parser.add_argument("geography",
        help="name of geography to check against. 2018 US Census files will be used.",
        choices=[
            "state",
            "county",
            "tract",
            "blockgroup",
            "zcta",
        ],
    )
    parser.add_argument("-i", "--id_field",
        help="name of field in input file that has FIPS, GEOID, or HEROPID in it",
    )
    parser.add_argument("-o", "--output",
        help="file to write a list of ids to",
    )
    args = parser.parse_args()

    highlight_ids = check_coverage(args.input_file, args.geography, args.id_field)

    if args.output:
        with open(args.output, "w") as o:
            o.write("\n".join(highlight_ids))
