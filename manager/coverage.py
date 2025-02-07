#!/usr/bin/env python3
import os
import logging
import pandas as pd
from utils import SpatialResolution

STUDY_DATASET_DIRECTORY = os.getenv('STUDY_DATASET_DIRECTORY', './data/test/')
MASTER_GEOGRAPHY_DIRECTORY = os.getenv('MASTER_GEOGRAPHY_DIRECTORY', './data/master/')

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

def check_coverage():
    print('Checking coverage...')
    for check, master in file_map.items():
        # Read study CSV
        study_df = read_csv(STUDY_DATASET_DIRECTORY + '/' + check)
        fips_col = 'FIPS'  # Column in df1
        study_df[fips_col] = study_df[fips_col].astype(str)
        print(study_df[fips_col])

        # Read master geography CSV
        mgeo_df = read_csv(MASTER_GEOGRAPHY_DIRECTORY + '/' + master['mgeo'])
        herop_id_col = 'HEROP_ID'  # Column in df2 that should match col1 + '140US'
        mgeo_df[herop_id_col] = mgeo_df[herop_id_col].astype(str)
        print(mgeo_df[herop_id_col])

        # TODO: Null-checking, handle NaN, etc

        # Determine prefix for HEROP_ID
        prefix = SpatialResolution(master['spatial_resolution']).to_prefix()

        # Use a predicate to compare FIPS to HEROP_ID
        mask = ~(mgeo_df[herop_id_col]).isin(prefix + study_df[fips_col])
        coverage[check] = mgeo_df[mask]

    print('Done checking!')

def report_coverage():
    print('Reporting coverage')
    for check, missing in coverage.items():
        mgeo_path = file_map[check]['mgeo']
        print(f'The following HEROP_IDs are present in master geography file ({mgeo_path}),\n')
        print(f'but no matching FIPS was found in the dataset ({check}):\n')
        print(missing['HEROP_ID'])

        # TODO: Write to CSV file?

    print('Done reporting!')

def read_csv(filepath):
    print(f'Reading {filepath}...')
    df = pd.read_csv(filepath, dtype=str)

    if 'FIPS' in df.columns:
        print(f'This file has FIPS column: {len(df.index)} rows found')
    elif 'HEROP_ID' in df.columns:
        print(f'This file has HEROP_ID column: {len(df.index)} rows found')
    else:
        print(f'WARNING! Neither FIPS nor HEROP_ID were found. Available columns: {str(df.columns)}')
    
    return df

def main():
    print('Running coverage checker...')
    check_coverage()
    report_coverage()

if __name__=="__main__":
    main()
