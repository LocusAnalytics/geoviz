""" module to process geographic data """

import pandas as pd
import geopandas as gpd

from src.params import LSAD

def shape_geojson(geography='county', simplify=0.028):
    """ Loads GeoJSON/TopoJSON/shapefiles as geopandas DataFrame. String argument available only
    for composite state and county GeoJSON.

    :param (str) geography: 'state', 'county', or filepath
    :param (float) simplify: how much to simplify the geojson shapes; where 0 is unsimplified, and
                             0.1 being the recommended max simplification.
    :return: geopandas DataFrame with 'geometry' column for plotting """

    if geography == 'county':
        geo_df = gpd.read_file('data/shapefiles/us-albers-counties.json.txt')
    elif geography == 'state':
        geo_df = gpd.read_file('data/shapefiles/us-albers.json.txt')
    else:
        ## if using custom shapefile
        print('reading in geojson/shape file...')
        geo_df = gpd.read_file(geography)
    geo_df['geometry'] = geo_df.simplify(simplify)
    return geo_df


def strip_name(name, remove=None):
    """ Removes suffixes like '... County' or '... Parish' from area names.

    :param (str) name: area name string to be processed
    :param (list) remove: default is Legal Statistical Area Definition (see params.py)
    :return: processed name """
    if remove is None:
        remove = LSAD

    words = name.split(' ')
    if words[-1].lower() in remove:
        name = ' '.join(words[:-1])
    return name


def cbsa_to_fips(msa_df, cbsa_var):
    """ Splits and duplicates rows in a CBSA/MSA dataset so the rows are the underlying counties.
    This is done using pd.merge(). If there are duplicate column names, the passed df is kept as is,
    while the duplicates from the crosswalk are suffixed with "_omb".

    :param (DataFrame) df: pandas or geopandas DataFrame
    :param (str) cbsa_var: name of the CBSA/MSA code column
    :return: the new dataframe with additional columns ['cbsa', 'cbsa_name', 'county_name', 'fips']
    """
    omb = pd.read_csv('data/external/omb_msa_2017.csv', dtype=str)
    fips_df = omb.merge(msa_df, right_on=cbsa_var, left_on='cbsa',
                        how='inner', suffixes=('_omb', ''))
    return fips_df


def merge_to_geodf(shape_df, file_or_df, geoid_var, geoid_type, geolvl='county'):
    """ Merges a DataFrame (or csv file) to a shape file on a geo ID (e.g FIPS code or name).
    If there are duplicate column names, the passed df is kept as is, while the duplicates from
    the shapefile are suffixed with "_shape".

    :param (gpd.DataFrame) shape_df: geopandas DataFrame
    :param (str/pd.DataFrame) file_or_df: csv filepath or pandas/geopandas DataFrame with geoid_var
    :param (str) geoid_var: if str, name of column containing the geo ID to match on.
    :param (str) geoid_type: 'fips' (recommended), 'name', or 'abbrev'
    :param (str) geolvl: 'county' or 'state' -- determines what attribute of geojson to merge on
    :return: merged DataFrame that has 'geometry' column for plotting shapes """

    ## if file is string and not DataFrame, read it in as dataframe
    if isinstance(file_or_df, str):
        file_or_df = pd.read_csv(file_or_df, dtype={geoid_var:str})

    if geoid_type == 'name':
        file_or_df[geoid_var] = file_or_df[geoid_var].apply(strip_name)
    elif geoid_type == 'cbsa':
        file_or_df = cbsa_to_fips(file_or_df, geoid_var)
        geoid_var = 'fips'
        geoid_type = 'fips'

    ## identify which property of the geojson to merge on
    shape_geoid = {'state': {'fips':'fips_state', 'name':'name', 'abbrev':'iso_3166_2'},
                   'county': {'fips':'fips', 'name':'name'}}[geolvl][geoid_type]

    geo_df = shape_df.merge(file_or_df, how='inner', left_on=shape_geoid, right_on=geoid_var,
                            suffixes=('_shape', ''))
    no_shape = set(file_or_df[geoid_var]) - set(geo_df[geoid_var])
    if no_shape:
        print(f'Areas with no shape found:\n{no_shape}')
    return geo_df