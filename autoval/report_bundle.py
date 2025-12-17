import json
import math
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

BUNDLE_VERSION = "1.0"

def sanitize_station_id(station_id: Optional[str]) -> str:
    """
    Generates a filesystem-friendly station identifier.
    """
    if not station_id:
        return "station"
    safe_chars = []
    for char in str(station_id):
        if char.isalnum() or char in ("-", "_"):
            safe_chars.append(char)
        else:
            safe_chars.append("_")
    return "".join(safe_chars)


def _to_iso(value: Any) -> Optional[str]:
    if value in (None, [], {}):
        return None
    if isinstance(value, str):
        return value
    try:
        timestamp = pd.to_datetime(value)
    except Exception:
        return str(value)
    if pd.isna(timestamp):
        return None
    return timestamp.tz_localize(None) if hasattr(timestamp, "tz_localize") else timestamp


def _iso_string(value: Any) -> Optional[str]:
    ts = _to_iso(value)
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts.isoformat()
    return str(ts)


def _series_to_list(series: Any, target_length: Optional[int] = None) -> List[Any]:
    if series is None or (isinstance(series, float) and math.isnan(series)):
        if target_length is None:
            return []
        return [np.nan] * target_length
    if isinstance(series, np.ndarray):
        values = series.tolist()
    elif isinstance(series, (list, tuple)):
        values = list(series)
    else:
        values = [series]
    if target_length is not None and len(values) < target_length:
        values.extend([np.nan] * (target_length - len(values)))
    return values


def _prepare_station_row(
    idx: int,
    info: Mapping[str, Any],
    metrics: Mapping[str, Any],
    detail: Mapping[str, Any],
) -> Dict[str, Any]:
    station_id = info.get("nosid") or detail.get("id") or f"station_{idx:04d}"
    row: Dict[str, Any] = {
        "station_id": station_id,
        "name": info.get("name"),
        "lat": info.get("lat"),
        "lon": info.get("lon"),
        "state": info.get("state"),
        "country": info.get("country"),
        "station_type": "unknown",
        "has_obs": True,
        "timeseries_path": None,
    }
    extras = detail.get("series", {}).get("extras", {})
    row["station_type"] = extras.get("station_type", row["station_type"])
    row["has_obs"] = extras.get("has_obs", row["has_obs"])
    for key, value in metrics.items():
        row[key] = value
    return row


def write_bundle(
    cfg: Mapping[str, Mapping[str, Any]],
    tag: str,
    info: Sequence[Mapping[str, Any]],
    datespan: Sequence[Any],
    stats: Sequence[Mapping[str, Any]],
    avg_stats: Mapping[str, Any],
    point_details: Sequence[Mapping[str, Any]],
    run_path: str,
) -> Path:
    """
    Writes the dashboard bundle (metadata, station summary, and per-station time series).
    """
    if not point_details:
        raise RuntimeError(
            "Dashboard bundle requires station statistics. "
            "Enable Analysis.pointdatastats in the configuration."
        )

    report_dir = Path(cfg["Analysis"]["reportdir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    timeseries_dir = report_dir / "timeseries"
    if timeseries_dir.exists():
        shutil.rmtree(timeseries_dir)
    timeseries_dir.mkdir(parents=True, exist_ok=True)

    bbox = {
        "lon_min": cfg["Analysis"].get("lonmin"),
        "lon_max": cfg["Analysis"].get("lonmax"),
        "lat_min": cfg["Analysis"].get("latmin"),
        "lat_max": cfg["Analysis"].get("latmax"),
    }
    window = {
        "start": _iso_string(datespan[0]) if datespan else None,
        "end": _iso_string(datespan[-1]) if datespan else None,
    }
    summary = avg_stats if isinstance(avg_stats, Mapping) else {}
    metadata = {
        "bundle_version": BUNDLE_VERSION,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "run_id": tag,
        "domain": cfg["Analysis"].get("name"),
        "experiment": cfg["Analysis"].get("experimentdescr"),
        "analysis_window": window,
        "bbox": bbox,
        "model_path": run_path,
        "metrics_summary": summary,
        "station_count": len(info),
    }

    station_rows: List[Dict[str, Any]] = []
    series_payloads: List[Dict[str, Any]] = []
    for idx, station_info in enumerate(info):
        metrics = stats[idx] if idx < len(stats) else {}
        detail = point_details[idx] if idx < len(point_details) else {}
        row = _prepare_station_row(idx, station_info, metrics, detail)
        series = detail.get("series")
        if series:
            safe_id = sanitize_station_id(row["station_id"])
            filename = f"ts_station={safe_id}.parquet"
            rel_path = Path("timeseries") / filename
            row["timeseries_path"] = str(rel_path)
            series_payloads.append(
                {
                    "filename": timeseries_dir / filename,
                    "series": series,
                    "station_id": row["station_id"],
                }
            )
        station_rows.append(row)

    stations_df = pd.DataFrame(station_rows)
    stations_path = report_dir / "stations.parquet"
    stations_df.to_parquet(stations_path, index=False)

    for payload in series_payloads:
        series = payload["series"]
        times = pd.to_datetime(_series_to_list(series.get("time")))
        model_values = _series_to_list(series.get("model"), len(times))
        obs_values = _series_to_list(series.get("obs"), len(times))
        extras = series.get("extras", {})
        ts_df = pd.DataFrame(
            {
                "time": times,
                "model": model_values,
                "obs": obs_values,
            }
        )
        for key, value in extras.items():
            ts_df[key] = value
        ts_df["station_id"] = payload["station_id"]
        ts_df.to_parquet(payload["filename"], index=False)

    report_path = report_dir / "report.json"
    with open(report_path, "w", encoding="utf-8") as fp:
        json.dump(metadata, fp, indent=2)

    return report_path


__all__ = ["write_bundle", "sanitize_station_id"]
