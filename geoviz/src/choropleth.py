""" module to plot choropleths """

from bokeh import plotting, models, io



def initialize_plot(formatting):
    """ Create Bokeh figure

    :param (dict) formatting: see DEFAULTFORMAT from params.py
    :return: Bokeh figure object """

    plot = plotting.figure(title=formatting['title'],
                           background_fill_color=formatting['background_color'],
                           plot_width=formatting['width'],
                           plot_height=formatting['width']*HEIGHT_RATIO,
                           tools=formatting['tools'])
    plot.title.text_font = formatting['font']
    plot.title.text_font_size = formatting['title_fontsize']
    plot.grid.grid_line_color = None
    plot.axis.visible = False
    plot.border_fill_color = None
    plot.outline_line_color = None
    return plot


def draw_state(plot, formatting):
    """ Adds a state choropleth (default is transparent fill) to an existing Bokeh plot.

    :param (Bokeh object) plot: pre-defined Bokeh figure
    :param (dict) formatting: see DEFAULTFORMAT from params.py
    :return: None (adds to Bokeh object) """

    state_geojson = shape_geojson('state', formatting['simplify']).to_json()
    state_source = models.GeoJSONDataSource(geojson=state_geojson)
    plot.patches('xs', 'ys', source=state_source,
                 fill_color=formatting['st_fill'], fill_alpha=formatting['st_alpha'],
                 line_color=formatting['st_line_color'], line_width=formatting['st_line_width'])


def draw_main(plot, geo_df, y_var, y_type, formatting):
    """ Adds choropleth based on specified y_var to an existing Bokeh plot.

    :param (Bokeh object) plot: pre-defined Bokeh figure
    :param (gpd.DataFrame) geo_df: merged geopandas DataFrame from merge_to_geodf()
    :param (str) y_var: column name of variable to plot
    :param (str) y_type: 'sequential', 'divergent', or 'categorical' -- for palette
    :param (dict) formatting: see DEFAULTFORMAT from params.py
    :return: None (adds to Bokeh object) """

    geo_src = models.GeoJSONDataSource(geojson=geo_df.to_json())
    cmap = make_color_mapper(geo_df[y_var], y_type, formatting)

    shapes = plot.patches('xs', 'ys', fill_color={'field':y_var, 'transform': cmap},
                          fill_alpha=formatting['fill_alpha'], line_color=formatting['line_color'],
                          line_width=formatting['line_width'], source=geo_src)

    hover = models.HoverTool(renderers=[shapes])
    hover.tooltips = [('name', '@name'),
                      (y_var, f'@{y_var}')]
    plot.add_tools(hover)

    cbar = make_color_bar(cmap, formatting)
    plot.add_layout(cbar)


def make_color_mapper(y_values, y_type, formatting):
    """ Generates color mapper which takes in values and outputs the color hexcode.

    :param (pd.Series) y_values: pandas Series to be plotted, for calculating min/max
    :param (str) y_type: 'sequential', 'divergent', or 'categorical' -- for palette
    :param (dict) formatting: see DEFAULTFORMAT from params.py
    :return: Bokeh colormapper object """

    c_min = formatting.get('cbar_min', min(y_values))
    c_max = formatting.get('cbar_max', max(y_values))

    try:
        palette = COLORS[y_type][formatting['palette']][formatting['ncolors']]
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
                                formatter=models.NumeralTickFormatter(
                                format=formatting['cbar_textfmt']),
                                major_label_text_font_size=formatting['cbar_fontsize'],
                                major_label_text_font=formatting['font'],
                                major_tick_line_color=formatting['cbar_tick_color'],
                                major_tick_line_alpha=formatting['cbar_tick_alpha'],
                                title=formatting['cbar_title'],
                                title_text_font_size=formatting['cbar_fontsize'],
                                title_text_font=formatting['font'],
                                title_text_align=formatting['cbar_title_align'],
                                title_text_font_style=formatting['cbar_style'],
                                title_standoff=int(formatting['width']*formatting['title_sf_ratio']))

    return color_bar


def draw_choropleth_layers(order, plot, geo_df, y_var, y_type, formatting):
    """ Draws multi-layer choropleths (main + state outlines)

    :param (str) order: ['before', 'after', 'both']; order of drawing state outline
    :param (Bokeh object) plot: pre-defined Bokeh figure
    :param (gpd.DataFrame) geo_df: merged geopandas DataFrame from merge_to_geodf()
    :param (str) y_var: column name of variable to plot
    :param (str) y_type: 'sequential', 'divergent', or 'categorical' -- for palette
    :param (dict) formatting: see DEFAULTFORMAT from params.py
    :return: None (adds to Bokeh object) """

    if order in ['before', 'both']:
        draw_state(plot, formatting)
    draw_main(plot, geo_df, y_var, y_type, formatting)
    if order == 'after':
        draw_state(plot, formatting)
    elif order == 'both':
        temp_formatting = formatting.copy()
        temp_formatting['st_fill'] = None
        draw_state(plot, temp_formatting)


def save_plot(plot, output):
    """ Determines how choropleth plot is saved.

    :param (Bokeh object) plot: pre-defined Bokeh figure
    :param (str) output: ['svg', 'html', 'bokeh'] How plot should be saved.
                         If 'html', saves as html.
                         If 'svg' or default (None), outputs in Notebook; save using toolbar.
                         If 'bokeh', outputs Bokeh figure object for further customization.
    :return: None (adds to Bokeh object) """

    if output == 'html':
        io.output_file('bokeh_plot.html')
        io.save(plot, 'bokeh_plot.html')
    else:
        io.output_notebook()
        if output == 'svg':
            plot.output_backend = 'svg'
        plotting.show(plot)


def choropleth_county(file_or_df, geoid_var, geoid_type, y_var, y_type, state_outline=None,
                      formatting=None, output=False, dropna=True):
    """Short summary.

    :param (str/pd.DataFrame) file_or_df: csv filepath or pandas/geopandas DataFrame with geoid_var
    :param (str) geoid_var: name of column containing the geo ID to match on
    :param (str) geoid_type: 'fips' (recommended), 'name', or 'abbrev'
    :param (str) y_var: column name of variable to plot
    :param (str) y_type: 'sequential', 'divergent', or 'categorical' -- for palette
    :param (str) state_outline: ['before','after','both','None']; when to plot state outline map
    :param (dict) formatting: if custom dict is passed, update DEFAULTFORMAT with those key-values
    :param (str) output: see save_plot()
    :param (bool) dropna: default True, if false, keeps rows where y_var is nan.
    :return: if output is 'bokeh', returns Bokeh object; else None """

    ## get default plot formatting and update if necessary
    FORMAT = DEFAULTFORMAT.copy()
    if formatting:
        FORMAT.update(formatting)

    ## process data
    shape_df = shape_geojson('county', FORMAT['simplify'])
    geo_df = merge_to_geodf(shape_df, file_or_df, geoid_var, geoid_type,
                            geolvl='county', how_merge='inner')
    if dropna:
        geo_df = geo_df[geo_df[y_var].notnull()]

    ## plot and save choropleth
    plot = initialize_plot(FORMAT)
    draw_choropleth_layers(state_outline, plot, geo_df, y_var, y_type, FORMAT)

    if output != 'bokeh':
        save_plot(plot, output)
        ## return to original state
        io.reset_output()
        FORMAT = DEFAULTFORMAT.copy()
    return plot


def empty_map(geo='state', formatting=None, output='svg'):
    """Generate map outline (no fill).

    :param (str) geo: 'state' or 'county'
    :param (dict) formatting: if custom dict is passed, update DEFAULTFORMAT with those key-values
    :param (str) output: see save_plot()
    :return: if output is 'bokeh', returns Bokeh object; else None """

    ## get default plot formatting and update if necessary
    FORMAT = DEFAULTFORMAT.copy()
    if formatting:
        FORMAT.update(formatting)

    ## process data
    shape_df = shape_geojson(geo, FORMAT['simplify'])
    geo_src = models.GeoJSONDataSource(geojson=shape_df.to_json())

    ## plot and save choropleth
    plot = initialize_plot(formatting)
    plot.patches('xs', 'ys', fill_color=None, line_color=FORMAT['line_color'],
                 line_width=FORMAT['line_width'], source=geo_src)

    if output != 'bokeh':
        save_plot(plot, output)
        ## return to original state
        io.reset_output()
        FORMAT = DEFAULTFORMAT.copy()
    return plot
