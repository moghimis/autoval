# Bundle Specification

Bundle root = the report output directory (`cfg['Analysis']['reportdir']`).

```
reportdir/
├── report.json
├── stations.parquet
└── timeseries/
    └── ts_station=<ID>.parquet
```

## report.json

| Field | Type | Notes |
| --- | --- | --- |
| `bundle_version` | string | Semantic version of the bundle schema (`1.0`). |
| `generated_at` | ISO8601 string | UTC timestamp when bundle was written. |
| `run_id` | string | Experiment tag (`tag`). |
| `domain` | string | `Analysis.name`. |
| `experiment` | string | `Analysis.experimentdescr`. |
| `analysis_window.start/end` | ISO8601 string or null | Values from the station date span (if computed). |
| `bbox.lon_min/lon_max/lat_min/lat_max` | float | Bounding box from config. |
| `model_path` | string | Original `--paths` entry used in the run. |
| `metrics_summary` | object | Dict from `computeAvgStats` (if available). |
| `station_count` | int | Number of stations in `stations.parquet`. |

## stations.parquet

Parquet table with one row per station. Columns:

- `station_id`, `name`, `lat`, `lon`, `state`, `country`
- `station_type` (`nos`, `ioc`, `virtual`, …)
- `has_obs` (bool)
- `timeseries_path` (relative path to parquet file, may be `null` if no series)
- Metric columns (e.g., `rmsd`, `bias`, `rval`, `skil`, `npts`, …)

Column order within the parquet file is deterministic but consumers should rely on column names, not positions.

## timeseries/ts_station=<ID>.parquet

Per-station parquet files. `<ID>` is the sanitized station id (non-alphanumeric characters replaced with `_`). Columns:

- `station_id`
- `time` (`datetime64[ns]`)
- `model` (float)
- `obs` (float, may be NaN if no observations)
- `station_type`, `has_obs`, `has_nowcast`, `dynamic_bias`, `virtual` (copied from the plotting context)

The folder is rebuilt for each run; stale files are removed before writing.

## Versioning

- `BUNDLE_VERSION` is bumped when the schema changes. Dashboard loaders read the version from `report.json` so compatible changes can be handled gracefully.
- Tests (`tests/test_dashboard_bundle.py`) exercise round-trip creation + load + timeseries parsing.
