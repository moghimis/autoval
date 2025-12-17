# Dashboard Dev Notes

## Local Development

1. Install deps (prefer virtualenv/conda):
   ```bash
   pip install -r requirements.txt
   ```
2. Generate a small bundle (see `docs/dashboard/README.md` for commands). For unit tests we rely on synthetic data in `tests/test_dashboard_bundle.py`.
3. Launch:
   ```bash
   autoval dashboard --bundle /tmp/autoval/reportdir --debug
   ```
   Dash serves at `http://127.0.0.1:8050`.

## Structure

- `autoval/report_bundle.py`: serialization helpers
- `autoval/dashboard/bundle.py`: bundle reader
- `autoval/dashboard/app.py`: Dash layout + callbacks
- `autoval/cli.py`: entry point for `autoval dashboard`

## Testing

- `pytest tests/test_dashboard_bundle.py` verifies:
  - bundle files are written,
  - files load via `BundleLoader`,
  - per-station parquet files contain the expected columns.
- Dash callbacks rely on Plotly Express; smoke-tests can be added later once we have automated UI testing needs.

## Future Work / Ideas

- Multi-run support (e.g., selecting across bundles) – wiring exists via CLI, would need aggregator logic.
- Map enhancements (basemaps, tooltips, etc.) once we can add Mapbox tokens.
- Persist sidebar state between sessions (Dash `dcc.Store` + JSON).
- Download buttons (CSV export per station / metric).
