import json

import pandas as pd
import geopandas as gpd
import requests
from bokeh import plotting, models, io, transform, palettes
from selenium import webdriver

from src.params import DEFAULTFORMAT, COLORS, get_palette_colors

def shape_geojson(geography='county', simplify=0):
    """ Loads shapefiles as geopandas dataframe.
    :param geography: (str) 'state', 'county', or filepath
    :return: DataFrame
    """
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
    state_geojson = shape_geojson('state', formatting['simplify']).to_json()
    state_source = models.GeoJSONDataSource(geojson=state_geojson)
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

    cbar = make_color_bar(plot, cmap, formatting)
    plot.add_layout(cbar)


def make_color_mapper(series, y_type, formatting):
    c_min = formatting.get('cbar_min', min(series))
    c_max = formatting.get('cbar_max', max(series))

    try:
        palette = COLORS[y_type][formatting['palette']][formatting['ncolors']]
    except KeyError:
        palette = get_palette_colors(formatting['palette'], formatting['ncolors'])

    mapper = {'lin':models.LinearColorMapper, 'log':models.LogColorMapper}[formatting['lin_or_log']]

    return mapper(palette=palette, low=c_min, high=c_max)

def make_color_bar(plot, cmap, formatting):
    color_bar = models.ColorBar(color_mapper=cmap, label_standoff=10, location='bottom_right',
                                background_fill_color=None, 

                                formatter=models.NumeralTickFormatter(format=formatting['cbar_textfmt']),
                                major_label_text_font_size=formatting['cbar_fontsize'],
                                major_label_text_font=formatting['font'],
                                major_tick_line_color=formatting['cbar_tick_color'],
                                major_tick_line_alpha=formatting['cbar_tick_alpha'],

                                title=formatting['cbar_title'],
                                title_text_font_size=formatting['cbar_fontsize'],
                                title_text_font=formatting['font'],
                                title_text_align=formatting['cbar_title_align'],
                                title_text_font_style=formatting['cbar_style'],
                                title_standoff=int(formatting['ht']*0.01))
    return color_bar

def initialize_plot(formatting):
    plot = plotting.figure(title=formatting['title'],
                           background_fill_color=formatting['background_color'],
                           plot_width=formatting['wt'], plot_height=formatting['ht'],
                           tools=formatting['tools'])
    plot.title.text_font = formatting['font']
    plot.title.text_font_size = formatting['title_fontsize']
    plot.grid.grid_line_color = None
    plot.axis.visible = False
    plot.border_fill_color
    plot.outline_line_color=None
    return plot

def choropleth_county(file_or_df, geoid_var, geoid_type, y_var, y_type, state='before',
                      formatting=None, output=False, dropna=True):
    FORMAT = DEFAULTFORMAT.copy()
    if formatting:
        FORMAT.update(formatting)

    shape_df = shape_geojson('county', FORMAT['simplify'])
    geo_df = merge_to_geodf(shape_df, file_or_df, geoid_var, geoid_type)
    if dropna:
        geo_df = geo_df[geo_df[y_var].notnull()]

    geo_src = models.GeoJSONDataSource(geojson=geo_df.to_json())

    plot = initialize_plot(FORMAT)

    if state == 'before':
        draw_state(plot, FORMAT)

    draw_main(plot, geo_src, geo_df, y_var, y_type, FORMAT)

    if state == 'after':
        draw_state(plot, FORMAT)

    # ## county

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
