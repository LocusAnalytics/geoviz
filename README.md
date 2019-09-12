# geoviz
Plotting library for creating interactive and static choropleths.


*Tutorial*: http://locusanalytics.github.io/files/geoviz_tutorial.html


Choropleths can take in dataframes or csv files, and plot sequential, divergent, and categorical data.
Future updates will allow user to supply their own shapefiles; the package current has functionality to plot US maps at the state, metropolitan statistical area, or county level (all shapefiles include Hawaii and Alaska).

![Sequential data demo](plots/demo2.png)
![Divergent data demo](plots/demo3.png)

Plots can be outputted as as interactive html files or interactive Bokeh plots. The latter can only be done in Jupyter Notebooks. Static png or svg files can be saved manually once the above is generated using a widget button.

For more information on usage, please see the tutorial.
