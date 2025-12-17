# Dashboard Architecture & Design Notes

## Goals

- Keep validation + metric computation untouched.
- Emit a lean bundle (JSON + Parquet) from the existing reporting layer.
- Build a Dash UI that only reads from that bundle.

## High-Level Flow

```
validate/run.py
└── waterlevel.waterLevel(...)
    └── stationValidation(...)  # metrics + time series already in memory
        └── report_bundle.write_bundle(...)
            ├── report.json
            ├── stations.parquet
            └── timeseries/ts_station=<ID>.parquet

dash CLI
└── autoval.dashboard.app:create_dash_app
    ├── BundleLoader (reads bundle)
    └── Dash layout + callbacks
```

## Modules

- `autoval/report_bundle.py`
  - Converts the in-memory station objects into structured files.
  - Keeps filesystem-friendly filenames and deterministic output.
  - No recomputation; uses the same `info`, `metrics`, and time series created for PNG plots.

- `autoval/dashboard/bundle.py`
  - Small loader that validates bundle structure and exposes helpers:
    - `report` (metadata dict),
    - `stations` (`pandas.DataFrame`),
    - `metrics` (available metric columns),
    - `load_timeseries(station_id)` (lazily reads parquet per station).

- `autoval/dashboard/app.py`
  - Dash layout with sidebar filters and the required tabs.
  - Callbacks update map + hist/box chart + DataTable selection + station-detail plot.
  - Reads from the loader only; no model/obs files are parsed.

- `autoval/cli.py`
  - Minimal subcommand router providing `autoval dashboard --bundle ...`.

## UI Structure

- **Sidebar**: run metadata, station dropdown, metric selector.
- **Tabs**:
  1. Overview – KPI cards + raw metadata.
  2. Maps – scatter_geo colored by metric.
  3. Metrics – histogram + box plot for the selected metric.
  4. Stations – searchable/sortable DataTable.
  5. Station Detail – obs vs model line chart.

## Constraints / Trade-offs

- Dependency footprint intentionally limited to Dash + Plotly + pandas + pyarrow.
- Time series remain per-station parquet files to keep memory usage bounded.
- Bundle format versioned via `BUNDLE_VERSION` in `report_bundle.py`.
- When `Analysis.pointdatastats=0` there is no dashboard bundle (by design, because no station data exists).
