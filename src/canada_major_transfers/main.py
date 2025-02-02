#!/usr/bin/env python3
"""
main.py – Aggregate and Visualize Federal Transfers with Interactive Controls

This script:
  1. Downloads the HTML tables from:
       https://www.canada.ca/en/department-finance/programs/federal-transfers/major-federal-transfers.html
  2. For each table (assumed to represent one province/territory):
       - Renames the first column to "Component" and cleans component names
       - Replaces "-" with 0 and converts formatted strings to numbers
  3. Extracts rows for seven components:
         "Canada Health Transfer", "Canada Social Transfer", "Equalization",
         "Offshore Offsets", "Territorial Formula Financing",
         "Total - Federal Support", "Per Capita Allocation (dollars)"
     and only fiscal years from "2016-17" to "2025-26".
  4. Aggregates the data from all 14 tables (provinces/territories).
  5. Launches a Dash web server that displays for a chosen fiscal year a grouped (side‑by‑side)
     bar chart with:
         - x-axis: provinces/territories (with an option to include/exclude "Aggregate")
         - one bar per selected component (using different colours)
         - hover information showing the dollar amount.
     
Adjust the component names and fiscal years as necessary.
"""

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# Predefined titles for the 14 tables (assumed order on the page)
chart_titles = [
    "Federal Support to Provinces and Territories",
    "Federal Support to Newfoundland and Labrador",
    "Federal Support to Prince Edward Island",
    "Federal Support to Nova Scotia",
    "Federal Support to New Brunswick",
    "Federal Support to Quebec",
    "Federal Support to Ontario",
    "Federal Support to Manitoba",
    "Federal Support to Saskatchewan",
    "Federal Support to Alberta",
    "Federal Support to British Columbia",
    "Federal Support to Yukon",
    "Federal Support to Northwest Territories",
    "Federal Support to Nunavut"
]

def extract_province_name(title):
    """Extract province/territory name from a title string."""
    if "Provinces and Territories" in title:
        return "Aggregate"
    return title.replace("Federal Support to ", "").strip()

def get_tables(url):
    """Reads all HTML tables from the given URL and returns them as a list of DataFrames."""
    try:
        tables = pd.read_html(url)
        if not tables:
            raise ValueError("No tables found on the webpage.")
        return tables
    except Exception as e:
        print(f"Error fetching tables from {url}: {e}")
        return []

def clean_table(df):
    """
    Cleans a DataFrame assumed to contain federal transfer data:
      - Renames the first column to "Component"
      - Strips trailing digits from component names
      - Sets "Component" as the index
      - Replaces any "-" with 0 and converts all other values to numeric.
    """
    df = df.rename(columns={df.columns[0]: "Component"})
    df["Component"] = df["Component"].astype(str).str.replace(r"\s*\d+$", "", regex=True).str.strip()
    df = df.set_index("Component")
    df = df.replace("-", 0)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(r"[\$,]", "", regex=True), errors='coerce')
    return df

def aggregate_data(tables, province_names, years, components):
    """
    For each table, extracts only the rows for the specified components (case-insensitive)
    and only the columns for the given fiscal years.
    Returns a dictionary mapping province name to a DataFrame (index=components, columns=years).
    """
    data_dict = {}
    for i, table in enumerate(tables):
        try:
            clean_df = clean_table(table)
            # Filter rows by matching (case-insensitive)
            desired = [comp.lower() for comp in components]
            sel_df = clean_df[clean_df.index.str.lower().isin(desired)]
            # Reindex to ensure all desired components are present
            sel_df = sel_df.reindex(components, fill_value=0)
            # Select only the desired fiscal years
            sel_df = sel_df.reindex(columns=years, fill_value=0)
            data_dict[province_names[i]] = sel_df
        except Exception as e:
            print(f"Error processing table {i}: {e}")
    return data_dict

# Define fiscal years of interest and the 7 components
years = ["2016-17", "2017-18", "2018-19", "2019-20", "2020-21", 
         "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]

components = [
    "Canada Health Transfer",
    "Canada Social Transfer",
    "Equalization",
    "Offshore Offsets",
    "Territorial Formula Financing",
    "Total - Federal Support",
    "Per Capita Allocation (dollars)"
]

# Get data from the webpage and aggregate
url = "https://www.canada.ca/en/department-finance/programs/federal-transfers/major-federal-transfers.html"
tables = get_tables(url)
num_tables = min(14, len(tables))
tables = tables[:num_tables]
province_names = [extract_province_name(title) for title in chart_titles[:num_tables]]
data_dict = aggregate_data(tables, province_names, years, components)

# Create a long-format DataFrame for all provinces and fiscal years
# We will store a DataFrame for each province, then combine them.
def build_long_dataframe(year, include_aggregate=True):
    """
    For a given fiscal year, returns a long-format DataFrame with columns:
    'Province', 'Component', 'Value'
    Only includes provinces based on the include_aggregate flag.
    """
    rows = []
    for prov, df in data_dict.items():
        if (not include_aggregate) and (prov.lower() == "aggregate"):
            continue
        for comp in components:
            # Get the value (or 0 if missing)
            try:
                val = df.at[comp, year]
            except Exception:
                val = 0
            rows.append({"Province": prov, "Component": comp, "Value": val})
    return pd.DataFrame(rows)

# Set up the Dash app
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Federal Transfers Breakdown by Province/Territory"),
    html.Div([
        html.Label("Select Fiscal Year:"),
        dcc.Dropdown(
            id="year-dropdown",
            options=[{"label": y, "value": y} for y in years],
            value=years[0]
        ),
    ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top"}),
    html.Div([
        html.Label("Select Transfer Components:"),
        dcc.Checklist(
            id="component-checklist",
            options=[{"label": comp, "value": comp} for comp in components],
            value=components,
            labelStyle={'display': 'block'}
        ),
    ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top", "marginLeft": "2%"}),
    html.Div([
        html.Label("Include Aggregate?"),
        dcc.Checklist(
            id="aggregate-checklist",
            options=[{"label": "Include Aggregate", "value": "include"}],
            value=["include"],  # default is to include aggregate
            labelStyle={'display': 'inline-block'}
        )
    ], style={"width": "30%", "display": "inline-block", "verticalAlign": "top", "marginLeft": "2%"}),
    dcc.Graph(id="transfers-graph")
])

@app.callback(
    Output("transfers-graph", "figure"),
    Input("year-dropdown", "value"),
    Input("component-checklist", "value"),
    Input("aggregate-checklist", "value")
)
def update_graph(selected_year, selected_components, aggregate_val):
    # Determine whether to include aggregate based on checklist
    include_aggregate = "include" in aggregate_val if aggregate_val is not None else True
    df_long = build_long_dataframe(selected_year, include_aggregate)
    # Filter df_long to only include the selected components
    df_long = df_long[df_long["Component"].isin(selected_components)]
    # Create grouped bar chart using Plotly Express
    fig = px.bar(df_long, x="Province", y="Value", color="Component",
                 barmode="group",
                 labels={"Value": "Amount (Millions of Dollars)"},
                 title=f"Federal Transfers Breakdown for Fiscal Year {selected_year}")
    # The figure is interactive with hover info by default.
    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
