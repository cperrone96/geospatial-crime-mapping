"""Validate and summarize an archived 2016 San Francisco incident dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "raw" / "sf_incidents_2016.csv.gz"
REQUIRED_COLUMNS = {
    "PdId", "Category", "Date", "Time", "PdDistrict", "Resolution", "X", "Y"
}


def load_incidents(path: Path = DATA_PATH) -> tuple[pd.DataFrame, dict]:
    data = pd.read_csv(path)
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    data["X"] = pd.to_numeric(data["X"], errors="coerce")
    data["Y"] = pd.to_numeric(data["Y"], errors="coerce")
    report_date = pd.to_datetime(data["Date"], format="%m/%d/%Y %I:%M:%S %p", errors="coerce")
    report_time = pd.to_timedelta(data["Time"].astype(str) + ":00", errors="coerce")
    data["reported_at"] = report_date + report_time
    valid_coordinates = data["X"].between(-123.0, -122.0) & data["Y"].between(37.0, 38.0)
    quality = {
        "source_rows": int(len(data)),
        "missing_coordinates": int(data[["X", "Y"]].isna().any(axis=1).sum()),
        "coordinates_outside_documented_sf_bounds": int((~valid_coordinates).sum()),
        "unparsed_report_timestamps": int(data["reported_at"].isna().sum()),
        "duplicate_incident_ids": int(data["PdId"].duplicated().sum()),
    }
    clean = data.loc[valid_coordinates & data["reported_at"].notna()].copy()
    if clean.empty:
        raise ValueError("No valid incidents remained after validation")
    return clean, quality


def deterministic_map_sample(data: pd.DataFrame, n: int = 500) -> pd.DataFrame:
    """Return a seeded display sample; it is not an inferential sample."""
    n = min(n, len(data))
    return (
        data.sample(n=n, random_state=42)
        .sort_values("reported_at")[["PdId", "Category", "PdDistrict", "reported_at", "Y", "X"]]
        .reset_index(drop=True)
    )


def create_map(points: pd.DataFrame):
    """Create a Folium marker-cluster map from an explicit point table."""
    import folium
    from folium.plugins import MarkerCluster

    crime_map = folium.Map(location=[37.77, -122.42], zoom_start=12, tiles="CartoDB positron")
    cluster = MarkerCluster(name="Reported incidents").add_to(crime_map)
    for row in points.itertuples(index=False):
        folium.Marker(
            location=[row.Y, row.X],
            tooltip=f"{row.Category} | {row.PdDistrict}",
        ).add_to(cluster)
    folium.LayerControl().add_to(crime_map)
    return crime_map


def run(output_dir: Path | None = None, write_map: bool = False) -> dict:
    output_dir = output_dir or ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    data, quality = load_incidents()
    category = data["Category"].value_counts().rename_axis("category").reset_index(name="reported_incidents")
    district = data["PdDistrict"].fillna("UNKNOWN").value_counts().rename_axis("district").reset_index(name="reported_incidents")
    sample = deterministic_map_sample(data)
    category.to_csv(output_dir / "category_counts.csv", index=False)
    district.to_csv(output_dir / "district_counts.csv", index=False)
    sample.to_csv(output_dir / "map_sample.csv", index=False)
    if write_map:
        create_map(sample).save(output_dir / "incident_map.html")
    metrics = {
        "analysis_type": "descriptive_coursework",
        "observation_unit": "police incident report",
        "valid_rows": int(len(data)),
        "display_sample_rows": int(len(sample)),
        "data_quality": quality,
        "largest_category": category.iloc[0].to_dict(),
        "largest_district": district.iloc[0].to_dict(),
        "nonclaim": "Counts are neither crime rates nor evidence that a location is safe or unsafe.",
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--write-map", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.output_dir, args.write_map), indent=2))
