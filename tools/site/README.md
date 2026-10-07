# Site analysis data

Everything the test-fit deck shows about the site comes from here.

| File | What it is |
|---|---|
| `facts.json` | From the site visit and the brief: address, plus code, super built-up and carpet area, headcount, the due-diligence table and notes. Edit by hand. |
| `fetch.py` | Downloads the open data into `raw/` (not committed, about 25 MB). |
| `site.py prep` | `raw/` → `context.json` (committed): figure-ground, roads and their names, metro, landmarks with walking distances, Regalium's footprint, wind rose, monthly rain and temperature. |
| `site.py build realfit.json site.json` | Run by `tools/testfit/run.sh`. Places the plan on the site (north), traces the sun across the layout, and merges everything into `site.json`. |

## Sources

- **Overture Maps Foundation**, release 2026-09-23.1: buildings, roads, places and land use. This is OpenStreetMap data under the ODbL, so the map credits "© OpenStreetMap contributors".
- **NOAA NCEI ISD-lite**, station 432950 (IMD Bangalore, 5 km NNW of the site): 3-hourly wind, 2014–2025.
- **NOAA NCEI GHCN-daily**, IN009010100 (Bangalore): daily rain and temperature, 1991–2020 averages; quality-flagged days dropped.
- **Sun**: NOAA general solar-position equations, IST; ASHRAE clear-sky direct beam.

The OpenStreetMap, Overpass and Nominatim servers are blocked from the build environment, which is why the map comes from Overture's S3 copy.
