import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from autoval.report_bundle import sanitize_station_id

_STATION_METADATA_COLUMNS = {
    "station_id",
    "name",
    "lat",
    "lon",
    "state",
    "country",
    "station_type",
    "has_obs",
    "timeseries_path",
}


class BundleLoader:
    """
    Utility class for reading dashboard bundles.
    """

    def __init__(self, bundle_root: str):
        self.root = Path(bundle_root).expanduser().resolve()
        self.report = self._load_report()
        self.stations = self._load_stations()
        self.metrics = self._detect_metric_columns()

    def _load_report(self) -> Dict:
        report_path = self.root / "report.json"
        if not report_path.exists():
            raise FileNotFoundError(f"Missing report.json in {self.root}")
        with open(report_path, "r", encoding="utf-8") as fp:
            return json.load(fp)

    def _load_stations(self) -> pd.DataFrame:
        stations_path = self.root / "stations.parquet"
        if not stations_path.exists():
            raise FileNotFoundError(f"Missing stations.parquet in {self.root}")
        return pd.read_parquet(stations_path)

    def _detect_metric_columns(self) -> List[str]:
        exclude = set(_STATION_METADATA_COLUMNS)
        return [c for c in self.stations.columns if c not in exclude]

    def station_options(self) -> List[Dict[str, str]]:
        return [
            {"label": f"{row['station_id']} - {row['name']}", "value": row["station_id"]}
            for _, row in self.stations.iterrows()
        ]

    def timeseries_path(self, station_id: str) -> Optional[Path]:
        match = self.stations.loc[self.stations["station_id"] == station_id]
        if match.empty:
            return None
        rel_path = match.iloc[0].get("timeseries_path")
        if not rel_path:
            rel_path = Path("timeseries") / f"ts_station={sanitize_station_id(station_id)}.parquet"
        return (self.root / rel_path).resolve()

    def load_timeseries(self, station_id: str) -> Optional[pd.DataFrame]:
        ts_path = self.timeseries_path(station_id)
        if not ts_path or not ts_path.exists():
            return None
        return pd.read_parquet(ts_path)


__all__ = ["BundleLoader"]
