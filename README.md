# Connecticut-Real-Estate-Sales-Dashboard
Loads Real_Estate_Sales_2001-2022_GL.csv, cleans &amp; filters data, then generates an interactive Panel dashboard with: Sankey diagram (Town → Residential Type), Map of sale locations, Tabular view of transactions. Includes a “Reset Filters” button to restore filters to their default settings.

Dependencies

This project was built in a Conda (Python 3.12) environment.
Below are the key packages required to run the dashboard:

* pandas – Data cleaning, preprocessing, and filtering of Connecticut real estate sales.
* numpy – Numerical backend for pandas and calculations.
* plotly – Interactive charts: Sankey diagram (plotly.graph_objects) and scatter map (plotly.express).
* panel – Main dashboard framework for layout, interactivity, and serving the web app.
* param – Reactive parameter system used by Panel for widget bindings.
* bokeh – Backend rendering engine for Panel.
* pyviz_comms – Communication layer for Panel ↔ Jupyter/browser interaction.
* tabulator (via panel.widgets.Tabulator) – Interactive, paginated data tables in the dashboard.
* tqdm – Progress bars (useful for data loading/debugging, not critical).
  
Installation
Using Conda (recommended):
Paste code into terminal:
“conda install pandas numpy plotly panel bokeh param pyviz_comms tqdm”
