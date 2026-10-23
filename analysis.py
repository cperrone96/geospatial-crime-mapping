"""Validate, summarize and map San Francisco police incident reports from 2016.

Each source row is one offense within an incident: an incident number
(``IncidntNum``) can carry several offenses, each with its own ``PdId``.
Counts are therefore reported both as offense records and as distinct
incidents.

Run ``python analysis.py --write-map`` to regenerate ``outputs/``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "raw" / "sf_incidents_2016.csv.gz"
REQUIRED_COLUMNS = {"IncidntNum", "PdId", "Category", "Date", "Time", "PdDistrict", "Resolution", "X", "Y"}
# Generous bounding box around San Francisco; rows outside it would be geocoding errors.
LON_BOUNDS = (-123.0, -122.0)
LAT_BOUNDS = (37.0, 38.0)
SEED = 42


def load_incidents(path: Path = DATA_PATH) -> tuple[pd.DataFrame, dict]:
    """Load offense records, parse timestamps, and drop rows that fail validation."""
    data = pd.read_csv(path)
    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    data["X"] = pd.to_numeric(data["X"], errors="coerce")
    data["Y"] = pd.to_numeric(data["Y"], errors="coerce")
    incident_date = pd.to_datetime(data["Date"], format="%m/%d/%Y %I:%M:%S %p", errors="coerce")
    time_of_day = pd.to_timedelta(data["Time"].astype(str) + ":00", errors="coerce")
    data["incident_time"] = incident_date + time_of_day
    data["PdDistrict"] = data["PdDistrict"].fillna("UNKNOWN")
    valid_coordinates = data["X"].between(*LON_BOUNDS) & data["Y"].between(*LAT_BOUNDS)
    quality = {
        "offense_records": int(len(data)),
        "distinct_incidents": int(data["IncidntNum"].nunique()),
        "missing_coordinates": int(data[["X", "Y"]].isna().any(axis=1).sum()),
        "coordinates_outside_sf_bounding_box": int((~valid_coordinates).sum()),
        "unparsed_timestamps": int(data["incident_time"].isna().sum()),
        "duplicate_offense_ids": int(data["PdId"].duplicated().sum()),
        "missing_district": int(data["PdDistrict"].eq("UNKNOWN").sum()),
    }
    clean = data.loc[valid_coordinates & data["incident_time"].notna()].copy()
    if clean.empty:
        raise ValueError("No valid records remained after validation")
    return clean, quality


def incidents(data: pd.DataFrame) -> pd.DataFrame:
    """One row per incident (its first offense record)."""
    return data.sort_values("PdId").drop_duplicates("IncidntNum").reset_index(drop=True)


def category_counts(data: pd.DataFrame) -> pd.DataFrame:
    """Offense records and distinct incidents per category."""
    table = data.groupby("Category").agg(offense_records=("PdId", "size"), incidents=("IncidntNum", "nunique"))
    table["share_of_incidents"] = table["incidents"] / data["IncidntNum"].nunique()
    return table.sort_values("incidents", ascending=False).reset_index().rename(columns={"Category": "category"})


def district_counts(data: pd.DataFrame) -> pd.DataFrame:
    """Distinct incidents per police district, with each district's share."""
    table = data.groupby("PdDistrict")["IncidntNum"].nunique().sort_values(ascending=False)
    out = table.rename("incidents").rename_axis("district").reset_index()
    out["share"] = out["incidents"] / out["incidents"].sum()
    return out


def hourly_profile(data: pd.DataFrame) -> pd.Series:
    """Share of incidents by hour of day (the recorded incident time)."""
    return incidents(data)["incident_time"].dt.hour.value_counts(normalize=True).sort_index()


def deterministic_map_sample(data: pd.DataFrame, n: int = 500) -> pd.DataFrame:
    """Seeded sample of incidents for display; it is not an inferential sample."""
    unique = incidents(data)
    return (
        unique.sample(n=min(n, len(unique)), random_state=SEED)
        .sort_values("incident_time")[["IncidntNum", "Category", "PdDistrict", "incident_time", "Y", "X"]]
        .reset_index(drop=True)
    )


def create_map(points: pd.DataFrame):
    """Folium map with a marker-cluster layer for the sampled incidents."""
    import folium
    from folium.plugins import MarkerCluster

    crime_map = folium.Map(location=[37.77, -122.42], zoom_start=12, tiles="OpenStreetMap")
    cluster = MarkerCluster(name="Incidents (sample)").add_to(crime_map)
    for row in points.itertuples(index=False):
        folium.Marker(location=[row.Y, row.X], tooltip=f"{row.Category} | {row.PdDistrict}").add_to(cluster)
    folium.LayerControl().add_to(crime_map)
    return crime_map


def plot_density(data: pd.DataFrame, path: Path) -> None:
    """Hexbin map of incident locations (all incidents, not the display sample)."""
    from matplotlib.figure import Figure  # object API: no global backend or pyplot state

    unique = incidents(data)
    surface, ink, muted = "#fcfcfb", "#0b0b0b", "#52514e"
    fig = Figure(figsize=(7, 7), dpi=150, facecolor=surface)
    ax = fig.subplots()
    ax.set_facecolor(surface)
    hb = ax.hexbin(unique["X"], unique["Y"], gridsize=110, bins="log", cmap="Blues", mincnt=1, linewidths=0)
    ax.set_aspect(1 / 0.79)  # roughly equal distances at 37.8 degrees N
    ax.set_xticks([])
    ax.set_yticks([])
    for side in ax.spines.values():
        side.set_visible(False)
    cbar = fig.colorbar(hb, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label("Incidents per hexagon (log scale)", color=muted)
    cbar.outline.set_visible(False)
    cbar.ax.tick_params(colors=muted)
    ax.set_title(f"San Francisco police incidents, 2016 (n = {len(unique):,})", loc="left", fontsize=11, color=ink)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, facecolor=surface, bbox_inches="tight")


def run(output_dir: Path | None = None, write_map: bool = False) -> dict:
    output_dir = output_dir or ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    data, quality = load_incidents()
    category = category_counts(data)
    district = district_counts(data)
    sample = deterministic_map_sample(data)
    hours = hourly_profile(data)
    category.to_csv(output_dir / "category_counts.csv", index=False)
    district.to_csv(output_dir / "district_counts.csv", index=False)
    sample.to_csv(output_dir / "map_sample.csv", index=False)
    plot_density(data, output_dir / "figures" / "incident_density.png")
    if write_map:
        create_map(sample).save(output_dir / "incident_map.html")
    top3 = category.head(3)  # an incident with offenses in two categories counts in both
    metrics = {
        "data_quality": quality,
        "valid_offense_records": int(len(data)),
        "valid_incidents": int(data["IncidntNum"].nunique()),
        "offenses_per_incident_mean": float(len(data) / data["IncidntNum"].nunique()),
        "top_categories_by_incidents": top3.to_dict(orient="records"),
        "largest_district": district.iloc[0].to_dict(),
        "busiest_hour": {"hour": int(hours.idxmax()), "share": float(hours.max())},
        "quietest_hour": {"hour": int(hours.idxmin()), "share": float(hours.min())},
        "display_sample_incidents": int(len(sample)),
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate and summarize SF incident reports")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--write-map", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.output_dir, args.write_map), indent=2))
