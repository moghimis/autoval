from datetime import datetime, timedelta

import pandas as pd

from autoval.dashboard.bundle import BundleLoader
from autoval.report_bundle import write_bundle


def _sample_cfg(tmp_path):
    return {
        "Analysis": {
            "reportdir": str(tmp_path),
            "name": "WaterLevel",
            "experimentdescr": "Test Run",
            "lonmin": -10.0,
            "lonmax": 10.0,
            "latmin": -5.0,
            "latmax": 5.0,
        }
    }


def _sample_station():
    info = {
        "nosid": "TEST123",
        "name": "Test Station",
        "lat": 1.0,
        "lon": 2.0,
        "state": "TS",
        "country": "US",
    }
    metrics = {"rmsd": 0.5, "bias": 0.1}
    series = {
        "time": [
            datetime(2024, 1, 1),
            datetime(2024, 1, 1) + timedelta(hours=1),
        ],
        "model": [0.2, 0.4],
        "obs": [0.1, 0.3],
        "extras": {"station_type": "nos", "has_obs": True},
    }
    detail = {"id": info["nosid"], "info": info, "metrics": metrics, "series": series}
    return info, metrics, detail


def test_bundle_writer_and_loader(tmp_path):
    cfg = _sample_cfg(tmp_path)
    info, metrics, detail = _sample_station()
    avg_stats = {"rmsd": metrics["rmsd"], "bias": metrics["bias"]}
    datespan = [datetime(2024, 1, 1), datetime(2024, 1, 2)]

    write_bundle(
        cfg=cfg,
        tag="run.test",
        info=[info],
        datespan=datespan,
        stats=[metrics],
        avg_stats=avg_stats,
        point_details=[detail],
        run_path="/tmp/model",
    )

    loader = BundleLoader(str(tmp_path))

    assert loader.report["run_id"] == "run.test"
    assert loader.report["bbox"]["lon_min"] == -10.0
    assert loader.stations.shape[0] == 1
    assert "rmsd" in loader.metrics

    ts = loader.load_timeseries("TEST123")
    assert isinstance(ts, pd.DataFrame)
    assert not ts.empty
    assert set(["time", "model", "obs"]).issubset(ts.columns)
