
"""
file: real_estate_dashboard.py
author: Rishi Urs, Rianna Wadhwani
description: Main script for DS3500 HW3 Real Estate Sales Dashboard.
             Loads Real_Estate_Sales_2001-2022_GL.csv, cleans & filters data,
             then generates an interactive Panel dashboard with:
               - Sankey diagram (Town → Residential Type)
               - Map of sale locations
               - Tabular view of transactions
             Includes a “Reset Filters” button to restore defaults.
"""

from __future__ import annotations

import panel as pn
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_FILE: Path = Path(__file__).with_name("Real_Estate_Sales_2001-2022_GL.csv")
PORT:      int  = 5006

# ---------------------------------------------------------------------------
# Data API
# ---------------------------------------------------------------------------

class RealEstateAPI:
    """
    Load, clean, and filter real‐estate sales data.
    Parses 'Location' POINT into numeric lon/lat, coerces types,
    and provides filter_data().
    """
    def __init__(self):
        self.df: pd.DataFrame = pd.DataFrame()

    def load_data(self, filepath: Path):
        # Read CSV; low_memory=False to avoid dtype warnings
        df = pd.read_csv(filepath, low_memory=False)

        # Parse "POINT (lon lat)" into separate lon/lat columns
        df = df.dropna(subset=['Location'])
        coords = (
            df['Location']
              .str.extract(r'POINT \((-?\d+\.\d+) (-?\d+\.\d+)\)')
              .astype(float)
        )
        df['lon'], df['lat'] = coords[0], coords[1]

        # Coerce numeric fields and drop any rows missing these essentials
        df['Sale Amount'] = pd.to_numeric(df['Sale Amount'], errors='coerce')
        df['List Year']   = pd.to_numeric(df['List Year'], errors='coerce').astype(int)
        df = df.dropna(subset=['Sale Amount', 'List Year']).reset_index(drop=True)

        self.df = df

    def get_years(self):
        # Should return [2001, 2002, ..., 2022]
        return sorted(self.df['List Year'].unique())

    def get_towns(self):
        return sorted(self.df['Town'].dropna().unique())

    def get_residential_types(self):
        return sorted(self.df['Residential Type'].dropna().unique())

    def filter_data(
        self,
        year:   int | None,
        towns:  list[str],
        resi:   list[str],
        amount: tuple[int,int]):
        df = self.df
        if year is not None:
            df = df[df['List Year'] == year]
        if towns:
            df = df[df['Town'].isin(towns)]
        if resi:
            df = df[df['Residential Type'].isin(resi)]
        low, high = amount
        df = df[(df['Sale Amount'] >= low) & (df['Sale Amount'] <= high)]
        return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Initialize & load data
# ---------------------------------------------------------------------------

api = RealEstateAPI()
api.load_data(DATA_FILE)

# Compute global min/max of Sale Amount for reset
global_min = int(api.df['Sale Amount'].min())
global_max = int(api.df['Sale Amount'].max())

pn.extension('tabulator', 'plotly')

# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

year_select = pn.widgets.Select(
    name='Year',
    options=api.get_years(),
    value=api.get_years()[0]
)

town_select = pn.widgets.MultiSelect(
    name='Town',
    options=api.get_towns(),
    size=6
)

resi_select = pn.widgets.MultiSelect(
    name='Residential Type',
    options=api.get_residential_types(),
    size=6
)

sale_slider = pn.widgets.RangeSlider(
    name='Sale Amount ($)',
    start=global_min,
    end=global_max,
    step=10_000,
    value=(global_min, global_max)
)

width_slider = pn.widgets.IntSlider(
    name='Chart Width',
    start=400, end=2000, step=100, value=800
)

height_slider = pn.widgets.IntSlider(
    name='Chart Height',
    start=300, end=1500, step=100, value=600
)

# Reset button to restore all filters to defaults
reset_button = pn.widgets.Button(name='Reset Filters', button_type='default')

def _reset_filters(event):
    # Restore defaults:
    year_select.value   = api.get_years()[0]
    town_select.value   = []
    resi_select.value   = []
    sale_slider.start   = global_min
    sale_slider.end     = global_max
    sale_slider.value   = (global_min, global_max)

reset_button.on_click(_reset_filters)

# ---------------------------------------------------------------------------
# Dynamic slider update per year
# ---------------------------------------------------------------------------

def _update_sale_slider(event):
    # When year changes, limit slider to that year's data range
    yr = event.new
    df_yr = api.filter_data(yr, [], [], (global_min, global_max))
    if not df_yr.empty:
        lo, hi = int(df_yr['Sale Amount'].min()), int(df_yr['Sale Amount'].max())
        sale_slider.start = lo
        sale_slider.end   = hi
        sale_slider.value = (lo, hi)

year_select.param.watch(_update_sale_slider, 'value')

# ---------------------------------------------------------------------------
# Plotting functions
# ---------------------------------------------------------------------------

def make_sankey(
    year: int, towns: list[str], resi: list[str],
    amount: tuple[int,int], w: int, h: int):
    """
    Build a Sankey diagram grouped Town → Residential Type.
    Fills missing Residential Type with 'Unknown'.
    """
    df = api.filter_data(year, towns, resi, amount)
    df['Residential Type'] = df['Residential Type'].fillna('Unknown')
    grp = df.groupby(['Town','Residential Type']).size().reset_index(name='count')

    towns_list = sorted(grp['Town'].unique())
    resi_list  = sorted(grp['Residential Type'].unique())
    labels     = towns_list + resi_list
    index_map  = {lab: i for i, lab in enumerate(labels)}

    fig = go.Figure(go.Sankey(
        node=dict(label=labels, pad=15, thickness=20),
        link=dict(
            source=grp['Town'].map(index_map),
            target=grp['Residential Type'].map(index_map),
            value=grp['count']
        )
    ))
    fig.update_layout(width=w, height=h, margin=dict(l=50,r=50,t=50,b=50))
    return fig

def make_map(
    year: int, towns: list[str], resi: list[str],
    amount: tuple[int,int]):
    """Render a scatter map of sale points."""
    df = api.filter_data(year, towns, resi, amount)
    return px.scatter_map(
        df,
        lat='lat', lon='lon',
        hover_name='Address',
        hover_data=['Sale Amount','List Year','Residential Type'],
        zoom=8, height=600, width=800
    )

def make_table(
    year: int, towns: list[str], resi: list[str],
    amount: tuple[int,int]):
    """Display filtered transactions in a paginated table."""
    df = api.filter_data(year, towns, resi, amount)
    return pn.widgets.Tabulator(df, pagination='remote', page_size=10)

# ---------------------------------------------------------------------------
# Bind plots to widgets
# ---------------------------------------------------------------------------

sankey_pane = pn.bind(
    make_sankey,
    year_select, town_select, resi_select,
    sale_slider, width_slider, height_slider
)

map_pane   = pn.bind(
    make_map,
    year_select, town_select, resi_select,
    sale_slider
)

table_pane = pn.bind(
    make_table,
    year_select, town_select, resi_select,
    sale_slider
)

# ---------------------------------------------------------------------------
# Dashboard layout
# ---------------------------------------------------------------------------

filter_card = pn.Card(
    pn.Column(
        year_select,
        town_select,
        resi_select,
        sale_slider,
        reset_button
    ),
    title="Filters",
    width=300
)

control_card = pn.Card(
    pn.Column(width_slider, height_slider),
    title="Chart Controls",
    width=300
)

template = pn.template.FastListTemplate(
    title="Connecticut Real Estate Sales Dashboard",
    sidebar=[filter_card, control_card],
    main=[pn.Tabs(
        ("Sankey", sankey_pane),
        ("Map",    map_pane),
        ("Table",  table_pane)
    )],
    header_background='#003366',
    theme_toggle=False
)

# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pn.serve(template, port=PORT, show=True)