import argparse
import json
from typing import List, Optional

import dash
from dash import Dash, Input, Output, State, dash_table, dcc, html
import plotly.express as px

from .bundle import BundleLoader


def create_dash_app(bundle_path: str) -> Dash:
    loader = BundleLoader(bundle_path)
    stations_df = loader.stations.copy()
    metrics = loader.metrics
    default_metric = metrics[0] if metrics else None
    station_records = stations_df.to_dict("records")
    metric_options = [{"label": m.upper(), "value": m} for m in metrics]

    app = Dash(__name__)
    app.title = f"Autoval Dashboard · {loader.report.get('run_id', '')}"

    overview_cards = []
    for metric, value in (loader.report.get("metrics_summary") or {}).items():
        overview_cards.append(
            html.Div(
                [
                    html.Div(metric.upper(), className="kpi-label"),
                    html.Div(f"{value:.3f}" if isinstance(value, (float, int)) else value, className="kpi-value"),
                ],
                className="kpi-card",
            )
        )

    app.layout = html.Div(
        [
            dcc.Store(id="selected-station", data=None),
            html.Div(
                [
                    html.H2("Autoval Dashboard"),
                    html.P(f"Run: {loader.report.get('run_id')}"),
                    html.P(f"Domain: {loader.report.get('domain')}"),
                    html.Label("Station"),
                    dcc.Dropdown(
                        id="station-dropdown",
                        options=loader.station_options(),
                        placeholder="Search station...",
                        value=None,
                        clearable=True,
                    ),
                    html.Label("Metric"),
                    dcc.Dropdown(
                        id="metric-dropdown",
                        options=metric_options,
                        value=default_metric,
                        clearable=False,
                    ),
                ],
                className="sidebar",
                style={
                    "width": "280px",
                    "padding": "1rem",
                    "background": "#f4f6fb",
                    "borderRight": "1px solid #d0d7de",
                    "height": "100vh",
                    "overflowY": "auto",
                },
            ),
            html.Div(
                [
                    dcc.Tabs(
                        id="main-tabs",
                        value="overview",
                        children=[
                            dcc.Tab(
                                label="Overview",
                                value="overview",
                                children=[
                                    html.Div(className="overview-grid", children=overview_cards),
                                    html.Pre(
                                        json.dumps(loader.report, indent=2),
                                        style={
                                            "background": "#f6f8fa",
                                            "padding": "0.75rem",
                                            "borderRadius": "4px",
                                            "overflowX": "auto",
                                        },
                                    ),
                                ],
                            ),
                            dcc.Tab(
                                label="Maps",
                                value="maps",
                                children=[dcc.Graph(id="map-graph")],
                            ),
                            dcc.Tab(
                                label="Metrics",
                                value="metrics",
                                children=[
                                    dcc.Graph(id="metric-histogram"),
                                    dcc.Graph(id="metric-boxplot"),
                                ],
                            ),
                            dcc.Tab(
                                label="Stations",
                                value="stations",
                                children=[
                                    dash_table.DataTable(
                                        id="stations-table",
                                        data=station_records,
                                        columns=[{"name": col, "id": col} for col in stations_df.columns],
                                        filter_action="native",
                                        sort_action="native",
                                        page_size=15,
                                        row_selectable="single",
                                    )
                                ],
                            ),
                            dcc.Tab(
                                label="Station Detail",
                                value="station-detail",
                                children=[dcc.Graph(id="station-timeseries")],
                            ),
                        ],
                    )
                ],
                className="content",
                style={"flex": "1", "padding": "1rem"},
            ),
        ],
        className="dashboard-root",
        style={"display": "flex", "minHeight": "100vh", "fontFamily": "sans-serif"},
    )

    @app.callback(
        Output("selected-station", "data"),
        Input("station-dropdown", "value"),
        Input("stations-table", "active_cell"),
        State("stations-table", "data"),
        prevent_initial_call=True,
    )
    def update_selected_station(dropdown_value, active_cell, table_data):
        triggered = dash.callback_context.triggered_id
        if triggered == "station-dropdown" and dropdown_value:
            return dropdown_value
        if triggered == "stations-table" and active_cell:
            row_idx = active_cell.get("row")
            if row_idx is not None and 0 <= row_idx < len(table_data):
                return table_data[row_idx]["station_id"]
        return dash.no_update

    @app.callback(
        Output("stations-table", "selected_rows"),
        Input("selected-station", "data"),
        State("stations-table", "data"),
    )
    def sync_table_selection(selected_station, rows):
        if not selected_station:
            return []
        for idx, row in enumerate(rows):
            if row["station_id"] == selected_station:
                return [idx]
        return []

    @app.callback(
        Output("station-dropdown", "value"),
        Input("selected-station", "data"),
    )
    def sync_dropdown(selected_station):
        return selected_station

    @app.callback(
        Output("map-graph", "figure"),
        Input("metric-dropdown", "value"),
    )
    def update_map(metric):
        df = stations_df.dropna(subset=["lat", "lon"])
        if df.empty:
            return px.scatter_geo()
        color = metric if metric in df.columns else None
        fig = px.scatter_geo(
            df,
            lat="lat",
            lon="lon",
            color=color,
            hover_name="station_id",
            title="Station Map",
        )
        fig.update_layout(legend_title="Metric")
        return fig

    @app.callback(
        Output("metric-histogram", "figure"),
        Output("metric-boxplot", "figure"),
        Input("metric-dropdown", "value"),
    )
    def update_metric_charts(metric):
        if metric not in stations_df.columns:
            empty_fig = px.histogram(title="No metric data")
            return empty_fig, empty_fig
        metric_series = stations_df[metric].dropna()
        if metric_series.empty:
            empty_fig = px.histogram(title="No metric data")
            return empty_fig, empty_fig
        metric_df = metric_series.to_frame(name=metric)
        hist = px.histogram(metric_df, x=metric, nbins=25, title=f"{metric.upper()} Distribution")
        box = px.box(metric_df, y=metric, points=False, title=f"{metric.upper()} Boxplot")
        return hist, box

    @app.callback(
        Output("station-timeseries", "figure"),
        Input("selected-station", "data"),
    )
    def update_station_timeseries(station_id):
        if not station_id:
            return px.line(title="Select a station to view time series.")
        ts = loader.load_timeseries(station_id)
        if ts is None or ts.empty:
            return px.line(title=f"No time series data for {station_id}")
        melted = ts.melt(id_vars=["time"], value_vars=["obs", "model"], var_name="series", value_name="value")
        fig = px.line(
            melted,
            x="time",
            y="value",
            color="series",
            title=f"Obs vs Model · {station_id}",
            labels={"value": "Water Level"},
        )
        return fig

    return app


def _parse_args(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(description="Launch the Autoval Dash dashboard.")
    parser.add_argument("--bundle", required=True, help="Path to the bundle directory.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None):
    args = _parse_args(argv)
    app = create_dash_app(args.bundle)
    app.run_server(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
