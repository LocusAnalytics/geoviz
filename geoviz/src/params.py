"""
Parameters for geoviz
"""
from bokeh.palettes import *

FORMAT = {## plot properties
          'title':'', 'ht':800, 'wt':1000, 'background_color':None,
          ## main map properties
          'fill_alpha':0.8, 'line_color':'#d3d3d3', 'line_width':0.5,
          ## color bar properties
          'lin_or_log':'lin', 'ncolors':7, 'palette':1, 'cbar_text':'0,000',
          'cbar_min':None, 'cbar_max':None,
          ## state map properties
          'st_alpha':1, 'st_fill':None, 'st_line_color':'black', 'st_line_width':1}

palette_dict = {'sequential': ['RdPu', 'YlGnBu', 'YlOrRd'],
                'sequential_single' :['Blues', 'Greens', 'Purples'],
                'divergent': ['BrBG', 'RdBu', 'PiYG'],
                'categorical': ['Dark2_', 'Set1_', 'Set3_']}

max_n = {'sequential':9, 'sequential_single':9, 'divergent':11, 'categorical':8}


COLORS = {ptype:{} for ptype in palette_dict}
for ptype in palette_dict:
    for rank, label in enumerate(palette_dict[ptype]):
        COLORS[ptype][label] = {}
        COLORS[ptype][rank+1] = {}
        for n in range(3, max_n[ptype]+1):
            palette = eval(f'{label}{n}')
            palette.reverse()
            COLORS[ptype][label][n] = palette
            COLORS[ptype][rank+1][n] = palette
