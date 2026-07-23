# Geospatial Crime Mapping with Folium

Interactive geospatial visualization of **San Francisco crime incidents** using
`folium` (Leaflet.js). The notebook builds up from a basic map to progressively
richer views: individual incident markers, hover pop-ups, marker clustering for
dense areas, and a choropleth summarizing incident counts by district.

## Notebook

`sf_crime_folium.ipynb`

- Loads the SF incident dataset into a pandas DataFrame and reduces to a
  workable sample
- Plots incident locations as a Folium `FeatureGroup` of circle markers
- Adds pop-up labels (crime category) on hover
- Groups dense markers with `folium.plugins.MarkerCluster`
- Renders a district-level choropleth

## Skills demonstrated

- Geospatial data handling (lat/long, GeoJSON boundaries)
- Interactive mapping with Folium: markers, pop-ups, clustering, choropleth
- Working with a large real-world incident dataset (sampling for performance)

## Data

Source: **San Francisco Police Department incident reports** (public open-data
release). The full CSV is large (~500 MB) and is **not** committed here; saved
map outputs are included so the notebook renders on GitHub. To re-run, download
the SFPD incidents CSV and point the `read_csv` cell at it locally.

## Run it

```bash
pip install -r requirements.txt
jupyter lab
```
