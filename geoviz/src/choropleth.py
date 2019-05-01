import json

import pandas as pd
import geopandas as gpd
import requests
from bokeh import plotting, models, io, transform, palettes
from selenium import webdriver

from src.params import DEFAULTFORMAT, COLORS, get_palette_colors

def shape_geojson(geography='county'):
    """ Loads shapefiles as geopandas dataframe.
    :param geography: (str) 'state', 'county', or filepath
    :return: DataFrame
    """
    if geography == 'county':
        return gpd.read_file('data/shapefiles/us-albers-counties.json.txt')
    elif geography == 'state':
        return gpd.read_file('data/shapefiles/us-albers.json.txt')
    else:
        ## if using custom shapefile
        print('reading in geojson/shape file...')
        return gpd.read_file(geography)

def merge_to_geodf(shape_df, file_or_df, geoid_var, geoid_type,
                     geolvl='county', how_merge='right'):
    """ Combines data and geojson into GeoPandas dataframe that can easily be
    transformed into Bokeh GeoJSONDataSource.

    :param geography: (str) 'state', 'county', or filepath
    :return: GeoPandas DataFrame
    """
    ## if file is string and not dataframe, read it in as dataframe
    if isinstance(file_or_df, str):
        if isinstance(geoid_var, (list, tuple, set)):
            file_or_df = pd.read_csv(file_or_df, dtype={var:str for var in geoid_var})
        else:
            file_or_df = pd.read_csv(file_or_df, dtype={geoid_var:str})

    ## identify which property of the geojson to merge on
    shape_geoid = {'state': {'fips':'fips_state', 'name':'name', 'abbrev':'iso_3166_2'},
            'county': {'fips':'fips', 'name':'name'}}[geolvl][geoid_type]

    geo_df = shape_df.merge(file_or_df, how=how_merge, left_on=shape_geoid, right_on=geoid_var,
                            suffixes=('ori', ''))
    return geo_df

def draw_state(plot, formatting):
    state_source = models.GeoJSONDataSource(geojson=shape_geojson('state').to_json())
    plot.patches('xs', 'ys', source=state_source, fill_alpha=formatting['st_alpha'],
                 line_color=formatting['st_line_color'], line_width=formatting['st_line_width'],
                 fill_color=formatting['st_fill'])

def draw_main(plot, geo_src, geo_df, y_var, y_type, formatting):
    cmap = make_color_mapper(geo_df[y_var], y_type, formatting)

    shapes = plot.patches('xs', 'ys', fill_color={'field':y_var, 'transform': cmap},
                       fill_alpha=formatting['fill_alpha'], line_color=formatting['line_color'],
                       line_width=formatting['line_width'], source=geo_src)

    hover = models.HoverTool(renderers=[shapes])

    hover.tooltips = [('name', '@name'),
                      (y_var, f'@{y_var}')]
    plot.add_tools(hover)

    color_bar = models.ColorBar(color_mapper=cmap, label_standoff=10, location='bottom_right',
                                # formatter=models.NumeralTickFormatter('0,000'),
                                formatter=models.NumeralTickFormatter(format=formatting['cbar_text']),
                                background_fill_color=None)
    plot.add_layout(color_bar)


def make_color_mapper(series, y_type, formatting):
    c_min = formatting.get('cbar_min', min(series))
    c_max = formatting.get('cbar_max', max(series))

    try:
        palette = COLORS[y_type][formatting['palette']][formatting['ncolors']]
    except KeyError:
        palette = get_palette_colors(formatting['palette'], formatting['ncolors'])

    mapper = {'lin':models.LinearColorMapper, 'log':models.LogColorMapper}[formatting['lin_or_log']]

    return mapper(palette=palette, low=c_min, high=c_max)

# def save_plot(plot, save_as):
#     """ saves plot as particular format"""
#     # 'https://chromedriver.storage.googleapis.com/72.0.3626.69/chromedriver_mac64.zip'
#     fformat = save_as.split('.')[-1]
#     save_fx = {'png':io.export_png, 'html':io.output_file, 'svg':io.export_svgs}[fformat]
#     if fformat == 'svg':
#         plot.output_backend = "svg"
#     save_fx(plot, save_as, webdriver=webdriver.Chrome())
#

def choropleth_county(file_or_df, geoid_var, geoid_type, y_var, y_type, state='before',
                      formatting=None, output=False, dropna=True):
    """ Plots county-level choropleth

    """
    FORMAT = DEFAULTFORMAT.copy()
    if formatting:
        FORMAT.update(formatting)

    shape_df = shape_geojson('county')
    geo_df = merge_to_geodf(shape_df, file_or_df, geoid_var, geoid_type)
    if dropna:
        geo_df = geo_df[geo_df[y_var].notnull()]

    geo_src = models.GeoJSONDataSource(geojson=geo_df.to_json())

    plot = plotting.figure(title=FORMAT['title'], background_fill_color=FORMAT['background_color'],
                           plot_width=FORMAT['wt'], plot_height=FORMAT['ht'],
                           tools='save, pan, box_zoom, reset', active_drag = 'box_zoom')

    if state == 'before':
        draw_state(plot, FORMAT)

    draw_main(plot, geo_src, geo_df, y_var, y_type, FORMAT)

    if state == 'after':
        draw_state(plot, FORMAT)

    # ## county
    plot.grid.grid_line_color = None
    plot.axis.visible = False

    if output == 'bokeh':
        return plot
    elif output == 'html':
        io.output_file('bokeh_plot.html')
        io.save(plot, 'bokeh_plot.html')
    else:
        io.output_notebook()
        if output == 'svg':
            plot.output_backend = 'svg'
        plotting.show(plot)
    ## return to original state
    io.reset_output()
    FORMAT = DEFAULTFORMAT.copy()

def empty_map(geo='state', formatting=None, output='svg'):
    FORMAT = DEFAULTFORMAT.copy()
    if formatting:
        FORMAT.update(formatting)

    shape_df = shape_geojson(geo, FORMAT['simplify'])
    geo_src = models.GeoJSONDataSource(geojson=shape_df.to_json())

    plot = plotting.figure(title=FORMAT['title'], background_fill_color=FORMAT['background_color'],
                           plot_width=FORMAT['wt'], plot_height=FORMAT['ht'],
                           tools=FORMAT['tools'])
    plot.grid.grid_line_color = None
    plot.axis.visible = False

    plot.patches('xs', 'ys', fill_color=None, line_color=FORMAT['line_color'],
                       line_width=FORMAT['line_width'], source=geo_src)

    io.output_notebook()
    if output == 'svg':
        plot.output_backend = 'svg'
    plotting.show(plot)

    io.reset_output()
    FORMAT = DEFAULTFORMAT.copy()
