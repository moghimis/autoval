# Dashboard Testing Guide

This guide covers how to grab a minimal dataset, generate a bundle, and launch the Dash UI for manual verification.

## 1. Download Example Data

The repository ships with example configuration files in `tests/`. Pick one that matches your environment (e.g., `tests/test4_global.ini`). Copy it to a writable location and update the paths under `[Paths]` / `[Analysis]` so they point to directories you can access.

To pull the required model/obs files, you can reuse the bash drivers in `tests/*.bash`. For example:

```bash
cp tests/drive.test.estofs.glo.v4.cwl.bash run_dash.bash
chmod +x run_dash.bash
# Edit run_dash.bash to update mount paths, tmp dirs, etc.
./run_dash.bash
```

Those scripts orchestrate all `wget`/`rsync` calls needed to stage data under `cfg['Analysis']['localdatadir']`. If you prefer manual control, inspect the `*.bash` file to see each download step.

## 2. Generate a Bundle

Once the example data is in place, run Autoval with the new report flag:

```bash
python autoval/validate/run.py \
  --iniFile /path/to/test4_global.ini \
  --paths /path/to/model/output \
  --report dash
```

This keeps the legacy HTML pages but also drops the Dash bundle files (see `docs/dashboard/BUNDLE_SPEC.md`) inside `cfg['Analysis']['reportdir']`.

## 3. Launch the Dashboard

Create/activate the virtualenv (`autoval-env`) or use your existing environment, then:

```bash
autoval dashboard --bundle /path/to/reportdir --host 0.0.0.0 --port 8050
# or
python -m autoval.dashboard.app --bundle /path/to/reportdir
```

Visit the printed URL (`http://127.0.0.1:8050` by default) and explore the tabs:

1. Overview – run metadata + KPI cards.
2. Maps – station scatter colored by the selected metric.
3. Metrics – histogram + boxplot.
4. Stations – sortable/filterable table.
5. Station Detail – interactive obs vs model lines.

Use the sidebar dropdowns/search to jump between stations and metrics.

## 4. Smoke Test Without Real Data

For quick CI/local checks, run:

```bash
PYTHONPATH=. python tests/test_dashboard_bundle.py
```

It builds a synthetic bundle and ensures the loader + parquet files work, so you can validate the dashboard wiring even when no “real” data is available.
