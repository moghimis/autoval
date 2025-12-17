# Autoval Plotly/Dash Dashboard

The dashboard replaces the static HTML + PNG layer with an interactive Plotly/Dash experience. The validation / metric computation pipeline stays unchanged – a new “bundle” of metadata, station summaries, and per-station time series is emitted and the dashboard reads only from that bundle.

## Quickstart

1. **Generate a bundle** (adds HTML + Dash outputs)  
   ```bash
   python autoval/validate/run.py --iniFile <cfg.ini> --paths <ofs_path> --report dash
   ```
   The run output directory now contains `report.json`, `stations.parquet`, and `timeseries/`.

2. **Launch the dashboard**  
   ```bash
   autoval dashboard --bundle /path/to/reportdir
   # or
   python -m autoval.dashboard.app --bundle /path/to/reportdir
   ```
   Visit `http://127.0.0.1:8050` (configurable via `--host/--port`).

3. **Explore**  
   - Sidebar: pick stations, metrics, and review run metadata.  
   - Tabs: Overview, station map, metric distributions, sortable station table, and interactive station-detail charts.

## Bundle Layout (TL;DR)

```
<report dir>/
├── index.htm                 # legacy HTML
├── img/                      # legacy PNGs
├── report.json               # run metadata + bbox + KPI summary
├── stations.parquet          # station metadata + metrics
└── timeseries/
    └── ts_station=<ID>.parquet
```

See `docs/dashboard/BUNDLE_SPEC.md` for the full schema, data types, and versioning rules.

## Requirements

- New Python deps: `dash`, `plotly`, `pandas`, `pyarrow`.
- `autoval dashboard` console entrypoint (see `setup.cfg`) plus `python -m autoval.dashboard.app`.
- Bundles are deterministic; rerunning the same job overwrites the bundle inside the same `reportdir`.

## Troubleshooting

- `RuntimeError: Dashboard bundle requires station statistics` → ensure `Analysis.pointdatastats=1` so stations are processed.
- Empty graphs → check `stations.parquet` (via `python - <<'PY' ...`), confirm metrics columns exist.
- Dash port already in use → pass `--port` to the CLI.
