# CLAUDE.md — Agrivoltaic Screening Bavaria

Technical reference for AI-assisted development sessions. Read this before making any changes.

---

## Project Goal

Build a Streamlit-based interactive screening map identifying agricultural land in Bavaria with high agrivoltaic potential. Output: a layered heat map that lets users toggle exclusion and suitability layers to see which areas are free of restrictions and score well on suitability criteria. Intended use: directing landowner outreach, not site-specific permitting.

**This map is not:** a permit-readiness assessment, a grid capacity guarantee, or a parcel-level feasibility study.

---

## Architecture

Two-phase design:

1. **Preprocessing pipeline** (`scripts/`) — all heavy GIS work: clip to Bavaria, reproject, overlay, score. Run once; outputs to `data/processed/`. Tools: `geopandas`, `rasterio`, `fiona`, `shapely`, `numpy`.
2. **Streamlit app** (`app/`) — thin display layer loading pre-computed layers. No spatial computation at runtime. Tools: `streamlit`, `streamlit-folium`, `folium`.

**Target CRS:** ETRS89 / UTM Zone 32N — **EPSG:25832** for all processed outputs. CLC2018 arrives in EPSG:3035, DGM200 in a UTM32N geographic variant — reproject during preprocessing.

**Analysis unit:** TBD (250 m or 500 m regular grid, or H3 hexagonal grid). Decision deferred to Phase 3.

---

## Data Layers Reference

### Exclusion Layers

Hard exclusions remove land from consideration entirely. Soft exclusions flag land as "caution" but do not exclude.

#### E1 — Agricultural land base (CLC2018)
- **Status:** Downloaded
- **File:** `data/raw/E1_land_use/U2018_CLC2018_V2020_20u1.shp/U2018_CLC2018_V2020_20u1.shp`
- **Source CRS:** EPSG:3035 (ETRS89-LAEA)
- **Key column:** `Code_18`
- **Include classes:** 211 (arable), 221 (vineyards), 222 (fruit/berry), 231 (pasture), 242 (complex cultivation), 243 (agriculture + natural veg)
- **Notes:** Full-Europe coverage; must clip to Bavaria before any processing. Hops (Hallertau) not separately classified — fall under 211 or 242.

#### E2 — Conservation areas
- **Status:** Downloaded (10 shapefiles)
- **CRS:** All EPSG:25832
- **Path prefix:** `data/raw/E2_conservation_areas/`
- **Classification:**

| File | Type | Classification |
|------|------|----------------|
| `nlp_epsg25832_shp/nlp_epsg25832_shp.shp` | Nationalparke | Hard exclude |
| `nsg_epsg25832_shp/nsg_epsg25832_shp.shp` | Naturschutzgebiete | Hard exclude |
| `biosphaerenreservate_epsg25832_shp/biosphaerenreservate_epsg25832_shp.shp` | Biosphärenreservate | Hard (Kernzone) / Soft (others) — zonation attribute needed |
| `lsg_epsg25832_shp/lsg_epsg25832_shp.shp` | Landschaftsschutzgebiete | Soft flag |
| `naturparke_epsg25832_shp/naturparke_epsg25832_shp.shp` | Naturparke | Soft flag |
| `naturdenkmal_flaechig_epsg25832_shp/naturdenkmal_flaechig_epsg25832_shp.shp` | Naturdenkmal (polygon) | Hard exclude |
| `naturdenkmal_punktfoermig_epsg25832_shp/naturdenkmal_punktfoermig_epsg25832_shp.shp` | Naturdenkmal (point) | Hard exclude |
| `nationale_naturmonumente_epsg25832_shp/nationale_naturmonumente_epsg25832_shp.shp` | Nationale Naturmonumente | Hard exclude |
| `landschaftsbestandteil_flaechig_epsg25832_shp/landschaftsbestandteil_flaechig_epsg25832_shp.shp` | Landschaftsbestandteil (polygon) | Soft flag |
| `landschaftsbestandteil_punktfoermig_epsg25832_shp/landschaftsbestandteil_punktfoermig_epsg25832_shp.shp` | Landschaftsbestandteil (point) | Soft flag |

- **Missing:** Natura 2000 (FFH-Gebiete + Vogelschutzgebiete) — needed for hard exclusion and EEG eligibility (S4). Download from same LfU Bayern page.

#### E3 — Flood zones (HQ100)
- **Status:** Downloaded
- **File:** `data/raw/E3_flood_areas/hw_flaeche_gpkg/hw_flaeche.gpkg`
- **Format:** GeoPackage (may contain multiple layers — list with fiona)
- **Classification:** Hard exclude (HQ100 = festgesetzte + vorläufig gesicherte Überschwemmungsgebiete)

#### E4 — Water protection zones
- **Status:** Downloaded (2 shapefiles)
- **CRS:** EPSG:25832
- **Files:**
  - `data/raw/E4_water_protection_ares/twsg_epsg25832_shp/twsg_epsg25832.shp` — Trinkwasserschutzgebiete
  - `data/raw/E4_water_protection_ares/hqsg_epsg25832_shp/hqsg_epsg25832.shp` — Heilquellenschutzgebiete
- **Known gap:** Zone-level subdivision (I/II/III) not available in download — only outer boundary. Conservative approach: flag entire zone as caution. Zone I only is a hard exclusion, but cannot be distinguished from the data.
- **Folder name typo:** `E4_water_protection_ares` (missing 'a') — do not rename; use as-is.

#### E5 — Terrain / slope
- **Status:** Downloaded
- **File:** `data/raw/E5_slope/dgm200.utm32s.gridascii/dgm200/dgm200_utm32s.asc`
- **Format:** ASCII grid raster, 200 m resolution, full Germany
- **CRS:** Check on open — expect UTM32N
- **Processing:** Open with rasterio → compute slope (use numpy gradient or richdem) → clip to Bavaria → classify (>25% = hard exclude, 0–25% = suitability score for S2)
- **Size:** 87.9 MB — clip to Bavaria before any downstream use

#### E6 — Built-up areas, forests, water bodies
- **Status:** Pending (derived from E1)
- **Notes:** Simply the complement of the E1 agricultural land selection from CLC2018.

#### E7 — Distance buffers from infrastructure
- **Status:** Pending data download
- **Source:** DLM250 (BKG Open Data) or OSM
- **Buffers:** 50 m from water bodies, 30 m from forests, 40 m from Autobahnen + railways, 20 m from Bundesstraßen
- **Note:** Same transport layer also used for the 200 m EEG/BauGB positive buffer (S4, S5).

---

### Suitability Scoring Layers

Applied to land that passes all exclusion filters.

#### S1 — Grid proximity (weight: 35%)
- **Status:** Pending data download
- **Source:** OSM power infrastructure (Geofabrik Germany extract, `power=line`, `power=substation`)
- **Proxy limitation:** OSM covers transmission + major distribution well; local Niederspannungsnetz inconsistently mapped. Document this clearly.
- **Processing:** Buffer at 250/500/750/1000/1500 m → score 5 down to 1

#### S2 — Slope (weight: 10%)
- **Status:** Pending (derived from E5)
- **Scoring:** 0–5% → 5, 5–10% → 4, 10–15% → 3, 15–20% → 2, 20–25% → 1

#### S3 — Agricultural land type / crop synergy (weight: 15%)
- **Status:** Pending (derived from E1)
- **Scoring:** CLC 221/222 (fruit/vine) → 5, CLC 211 (arable) → 4, CLC 231 (pasture) → 3, CLC 242/243 → 3–4

#### S4 — EEG subsidy eligibility (weight: 15%)
- **Status:** Pending
- **Logic:** Agricultural land NOT in Natura 2000 = eligible (score 5). Additionally, 200 m buffer of railways + Autobahnen = eligible regardless.
- **Depends on:** Natura 2000 download (missing) + transport infrastructure (missing)

#### S5 — BauGB §35 privileged permitting (weight: 15%)
- **Status:** Pending
- **Simplified approach:** Map only the 200 m transport corridor (railways + Autobahnen). Parcel size criterion (≤25,000 m²) requires Flurstücksdaten — not pursued at this stage.

#### S6 — Solar irradiation (weight: 10%)
- **Status:** Pending data download
- **Source:** PVGIS-SARAH2 raster or Bayerischer Solaratlas WMS
- **Scoring:** >1200 kWh/m²/year → 5, descending by 50 kWh steps

---

## Missing Data (still to obtain)

| Dataset | Source | Priority |
|---------|--------|----------|
| Natura 2000 (FFH + SPA) | LfU Bayern — same download page as E2 | High (needed for S4) |
| Transport infrastructure (Autobahnen, Bundesstraßen, railways) | DLM250 (BKG) or OSM Geofabrik | High (needed for E7, S4, S5) |
| OSM power grid (lines + substations) | Geofabrik Germany PBF | High (S1) |
| Bavaria state boundary | BKG or NaturalEarth | High (needed to clip E1, E5) |
| Solar irradiation raster | PVGIS / Energie-Atlas Bayern | Medium (S6) |
| InVeKoS parcel data | StMELF Bayern (formal request) | Low / bonus |

---

## Known Limitations

- Grid proximity (S1) uses OSM as proxy — cannot assess actual Netzkapazität
- E4 water protection zones lack zone-level subdivision (I/II/III)
- E2 Biosphärenreservate zone distinction (Kernzone vs. others) needs attribute inspection
- No Regionalplan data (18 Planungsregionen — too complex to harmonise for screening)
- No InVeKoS crop rotation data
- No parcel size data (Flurstücksdaten)
- Social/acceptance factors not modelled

---

## Tech Stack

```
geopandas >= 1.0        # vector GIS
rasterio >= 1.3         # raster I/O
fiona >= 1.10           # low-level vector I/O, layer listing
shapely >= 2.0          # geometry operations
pyproj >= 3.6           # CRS transformations
numpy >= 2.0            # raster math
streamlit >= 1.35       # app framework
streamlit-folium >= 0.20  # Folium integration for Streamlit
folium >= 0.17          # Leaflet.js map wrapper
```

Dev: `pytest`, `jupyter`, `ipykernel`

Environment managed with **uv**. Run `uv sync` to install.

---

## Phased Roadmap

| Phase | Goal | Key outputs |
|-------|------|-------------|
| 1 — Data audit | Verify all downloaded datasets are usable | `scripts/test_datasets.py` report |
| 2 — Exclusion mapping | Clip, reproject, apply hard exclusions | `data/processed/eligible_land.gpkg` |
| 3 — Suitability scoring | Weighted overlay → suitability tiers | `data/processed/suitability_grid.gpkg` |
| 4 — Streamlit app | Interactive map with layer toggles | `app/main.py` |
