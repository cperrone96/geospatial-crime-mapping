# San Francisco Incident Mapping & Data-Quality Audit

> **Scope:** An independently remediated IBM *Data Visualization with Python* coursework artifact. It demonstrates geospatial validation, deterministic sampling, aggregation, and interactive mapping; it is not a crime-risk model.

## Question and decision context

What categories and police districts account for the most incident reports in this archived 2016 extract, and can its coordinates support an exploratory point map? The map is a descriptive review tool for analysts—not a basis for policing, housing, travel, or personal-safety decisions.

## Data and design

- Observation unit: one SFPD incident report; 150,500 source rows.
- Source: 2016 municipal incident-report extract distributed through IBM Skills Network and traced to DataSF.
- Version: retrieval date, URLs, compressed and uncompressed SHA-256 checksums, and licensing caveat are in [`data/SOURCES.json`](data/SOURCES.json).
- Quality checks: required schema, timestamp parsing, unique incident IDs, and documented San Francisco coordinate bounds.
- Display: a seeded 500-record sample keeps the browser map responsive. Aggregated counts use all valid rows.

## Findings

All 150,500 records had parseable timestamps and coordinates inside the documented bounds; no duplicate `PdId` values were detected. `LARCENY/THEFT` was the largest category (40,409 reports), and `SOUTHERN` the largest district grouping (28,445 reports). These are raw report counts—not population-, exposure-, or time-adjusted rates.

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python analysis.py --write-map
python -m unittest discover -s tests -v
jupyter execute sf_crime_folium.ipynb
```

Outputs include JSON quality metrics, category/district tables, a reproducible map sample, and `incident_map.html`. CI repeats the script, tests, and clean-kernel notebook run.

## Limitations and nonclaims

- Incident reports reflect reporting, recording, enforcement, and administrative processes; they are not all events that occurred.
- Counts lack population, foot-traffic, land-use, and exposure denominators and must not be interpreted as rates.
- Multiple reports can relate to one event even when report IDs are unique.
- The map does not estimate causes, treatment effects, future risk, or whether any area is safe or unsafe.
