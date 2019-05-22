""" module to plot choropleths """

from bokeh import plotting, models, io



def initialize_plot(formatting):
    """ Create Bokeh figure to which glyphs/elements can be added.

    :param (dict) formatting: see DEFAULTFORMAT from params.py
    :return: Bokeh figure object """

    bkplot = plotting.figure(title=formatting['title'],
                             background_fill_color=formatting['background_color'],
                             plot_width=formatting['width'],
                             plot_height=int(formatting['width']*HEIGHT_RATIO),
                             tools=formatting['tools'])
    bkplot.title.text_font = formatting['font']
    bkplot.title.text_font_size = formatting['title_fontsize']
    bkplot.grid.grid_line_color = None
    bkplot.axis.visible = False
    bkplot.border_fill_color = None
    bkplot.outline_line_color = None
    return plot


def draw_main(bkplot, geo_df, y_var, y_type, geolabel, formatting):
    """ Adds choropleth based on specified y_var to an existing Bokeh plot.

    :param (Bokeh object) plot: pre-defined Bokeh figure
    :param (gpd.DataFrame) geo_df: merged geopandas DataFrame from merge_to_geodf()
    :param (str) y_var: column name of variable to plot
    :param (str) y_type: 'sequential', 'divergent', or 'categorical' -- for palette
    :param (str) geolabel: column name to use. default is county/state name from shapefile
    :param (dict) formatting: see DEFAULTFORMAT from params.py
    :return: None (adds to Bokeh object) """

    geo_src = models.GeoJSONDataSource(geojson=geo_df.to_json())
    cmap = make_color_mapper(geo_df[y_var], y_type, formatting)

    shapes = bkplot.patches('xs', 'ys', fill_color={'field':y_var, 'transform': cmap},
                            fill_alpha=formatting['fill_alpha'],
                            line_color=formatting['line_color'],
                            line_width=formatting['line_width'], source=geo_src)

    hover = models.HoverTool(renderers=[shapes])
    hover.tooltips = [('name', f'@{geolabel}'),
                      (y_var, f'@{y_var}')]

    cbar = make_color_bar(cmap, formatting)
    plot.add_layout(cbar)
    bkplot.add_tools(hover)


def make_color_mapper(y_values, y_type, formatting):
    """ Generates color mapper which takes in values and outputs the color hexcode.

    :param (pd.Series) y_values: pandas Series to be plotted, for calculating min/max
    :param (str) y_type: 'sequential', 'divergent', or 'categorical' -- for palette
    :param (dict) formatting: see DEFAULTFORMAT from params.py
    :return: Bokeh colormapper object """

    try:
        palette = PALETTES[y_type][formatting['palette']][formatting['ncolors']]
    except KeyError:
        palette = get_palette_colors(formatting['palette'], formatting['ncolors'])

    mapper = {'lin':models.LinearColorMapper, 'log':models.LogColorMapper}[formatting['lin_or_log']]

    return mapper(palette=palette, low=c_min, high=c_max)


def make_color_bar(cmap, formatting):
    """ Generates color bar from make_color_mapper()

    :param (Bokeh object) cmap: colormapper from make_color_mapper()
    :param (dict) formatting: see DEFAULTFORMAT from params.py
    :return: None (adds to Bokeh object) """

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
                                title_standoff=int(formatting['width']*formatting['title_sf']))

    return color_bar


def draw_state(bkplot, formatting):
    """ Adds a state choropleth (default is transparent fill) to an existing Bokeh plot.

    :param (Bokeh object) plot: pre-defined Bokeh figure
    :param (dict) formatting: see DEFAULTFORMAT from params.py
    :return: None (adds to Bokeh object) """

    state_geojson = prc.shape_geojson('state', formatting['simplify']).to_json()
    state_source = models.GeoJSONDataSource(geojson=state_geojson)
    bkplot.patches('xs', 'ys', source=state_source,
                   fill_color=formatting['st_fill'], fill_alpha=formatting['st_alpha'],
                   line_color=formatting['st_line_color'], line_width=formatting['st_line_width'])


def draw_choropleth_layers(order, bkplot, geo_df, y_var, y_type, geolabel, formatting):
    """ Draws multi-layer choropleths (main + state outlines)

    :param (str) order: ['before', 'after', 'both']; order of drawing state outline
    :param (Bokeh object) plot: pre-defined Bokeh figure
    :param (gpd.DataFrame) geo_df: merged geopandas DataFrame from merge_to_geodf()
    :param (str) y_var: column name of variable to plot
    :param (str) y_type: 'sequential', 'divergent', or 'categorical' -- for palette
    :param (str) geolabel: column name to use. default is county/state name from shapefile
    :param (dict) formatting: see DEFAULTFORMAT from params.py
    :return: None (adds to Bokeh object) """

    if order in ['before', 'both']:
        draw_state(bkplot, formatting)
    draw_main(bkplot, geo_df, y_var, y_type, geolabel, formatting)
    if order == 'after':
        draw_state(bkplot, formatting)
    elif order == 'both':
        temp_formatting = formatting.copy()
        temp_formatting['st_fill'] = None
        draw_state(bkplot, temp_formatting)


def save_plot(bkplot, output):
    """ Determines how choropleth plot is saved.

    :param (Bokeh object) plot: pre-defined Bokeh figure
    :param (str) output: ['svg', 'html', 'bokeh'] How plot should be saved.
                         If 'html', saves as html.
                         If 'svg' or default (None), outputs in Notebook; save using toolbar.
                         If 'bokeh', outputs Bokeh figure object for further customization.
    :return: None (adds to Bokeh object) """

    if output == 'html':
        io.output_file('bokeh_plot.html')
        io.save(bkplot, 'bokeh_plot.html')
    else:
        io.output_notebook()
        if output == 'svg':
            bkplot.output_backend = 'svg'
        plotting.show(plot)


def plot(file_or_df, geoid_var, geoid_type, y_var, y_type, state_outline=None,
         geolvl='county', geolabel='name', formatting=None, output=False, dropna=True):
    """Short summary.

    :param (str/pd.DataFrame) file_or_df: csv filepath or pandas/geopandas DataFrame with geoid_var
    :param (str) geoid_var: name of column containing the geo ID to match on
    :param (str) geoid_type: 'fips' (recommended), 'name', or 'abbrev' (state only)
    :param (str) y_var: column name of variable to plot
    :param (str) y_type: 'sequential', 'divergent', or 'categorical' -- for palette
    :param (str) state_outline: ['before','after','both','None']; when to plot state outline map
    :param (str) geolvl: 'county' or 'state'
    :param (str) geolabel: column name to use. default is county/state name from shapefile
    :param (dict) formatting: if custom dict is passed, update DEFAULTFORMAT with those key-values
    :param (str) output: see save_plot()
    :param (bool) dropna: default True, if false, keeps rows where y_var is nan.
    :return: if output is 'bokeh', returns Bokeh object; else None """

    ## get default plot formatting and update if necessary
    temp_format = DEFAULTFORMAT.copy()
    if formatting:
        temp_format.update(formatting)

    ## process data
    shape_df = prc.shape_geojson(geolvl, temp_format['simplify'])
    geo_df = prc.merge_to_geodf(shape_df, file_or_df, geoid_var, geoid_type,
                                geolvl=geolvl, how_merge='inner')

    if dropna:
        geo_df = geo_df[geo_df[y_var].notnull()]

    ## plot and save choropleth
    bkplot = initialize_plot(temp_format)
    draw_choropleth_layers(state_outline, bkplot, geo_df, y_var, y_type, geolabel, temp_format)

    if output != 'bokeh':
        save_plot(bkplot, output)
        ## return to original state
        io.reset_output()
        temp_format = DEFAULTFORMAT.copy()
    return plot


def plot_empty(geo='state', formatting=None, output='svg'):
    """Generate map outline (no fill).

    :param (str) geo: 'state' or 'county'
    :param (dict) formatting: if custom dict is passed, update DEFAULTFORMAT with those key-values
    :param (str) output: see save_plot()
    :return: if output is 'bokeh', returns Bokeh object; else None """

    ## get default plot formatting and update if necessary
    temp_format = DEFAULTFORMAT.copy()
    if formatting:
        temp_format.update(formatting)

    ## process data
    shape_df = prc.shape_geojson(geo, temp_format['simplify'])
    geo_src = models.GeoJSONDataSource(geojson=shape_df.to_json())

    ## plot and save choropleth
    bkplot = initialize_plot(formatting)
    bkplot.patches('xs', 'ys', fill_color=None, line_color=temp_format['line_color'],
                   line_width=temp_format['line_width'], source=geo_src)

    if output != 'bokeh':
        save_plot(bkplot, output)
        ## return to original state
        io.reset_output()
        temp_format = DEFAULTFORMAT.copy()
    return bkplot
