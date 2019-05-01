"""
Parameters for geoviz
"""
from bokeh.palettes import *

def get_palette_colors(palette_label, ncolors):
    palette = eval(f'{palette_label}{ncolors}').copy()
    palette.reverse()
    return palette

DEFAULTFORMAT = {## plot properties
          'ht':600, 'wt':1000, 'background_color':None,
          'title':'', 'font':'futura', 'title_fontsize':None,
          'tools':'zoom_in,zoom_out,pan,reset,save',
          ## main map properties
          'fill_alpha':0.8, 'line_color':'#d3d3d3', 'line_width':0.5, 'simplify':0,
          ## color bar properties
          'lin_or_log':'lin', 'ncolors':7, 'palette':1,
          'cbar_fontsize':None, 'cbar_textfmt':'0,000',
          'cbar_title':'', 'cbar_title_align':'center','cbar_style':None,
          'cbar_tick_color':'black', 'cbar_tick_alpha':1,
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
            palette = get_palette_colors(label, n)
            COLORS[ptype][label][n] = palette
            COLORS[ptype][rank+1][n] = palette

for i in COLORS['sequential'][2]:
    COLORS['sequential'][2][i][-1] = '#0a3959'
