# Geospatial Crime Mapping with Folium

Interactive geospatial visualization of **San Francisco crime incidents** using
`folium` (Leaflet.js). The notebook builds up from a basic map to progressively
richer views: individual incident markers, category pop-ups, and marker
clustering for dense areas.

## Notebook

`sf_crime_folium.ipynb`

- Loads the SF incident dataset into a pandas DataFrame and reduces to a
  workable sample
- Plots incident locations as a Folium `FeatureGroup` of circle markers
- Adds pop-up labels (crime category) on the markers
- Groups dense markers with `folium.plugins.MarkerCluster`

## Skills demonstrated

- Geospatial data handling (lat/long coordinates)
- Interactive mapping with Folium: markers, pop-ups, and clustering
- Working with a real-world municipal incident dataset (sampling for performance)

## Data

Source: **San Francisco Police Department incident reports** (2016, public
open-data release). The notebook loads the CSV directly from a public URL, so it
runs top-to-bottom with no manual download. Saved map outputs are included so the
notebook renders on GitHub.

## Run it

```bash
pip install -r requirements.txt
jupyter lab
```
