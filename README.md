# Agrivoltaic Screening Map — Bavaria

GIS-based screening tool identifying agricultural land in Bavaria with high potential for agrivoltaic (agri-PV) installations. The output is a heat-map-style suitability layer for directing landowner outreach — not a permit-readiness assessment.

**Methodological basis:** Hauger et al. (2025), "GIS-based potential analysis and agro-economic site selection for agrivoltaics using AHP in two German counties," *Renewable Energy* 247, 123039.

**Geographic scope:** Freistaat Bayern, initially focused on Oberbayern, Schwaben, and Niederbayern.

---

## Data Layers

### Exclusion Layers (downloaded)

| ID | Layer | Source | File | Status |
|----|-------|--------|------|--------|
| E1 | Agricultural land (CLC2018) | Copernicus / EU | `data/raw/E1_land_use/` | ✓ Downloaded |
| E2 | Conservation areas (10 types) | LfU Bayern | `data/raw/E2_conservation_areas/` | ✓ Downloaded |
| E3 | Flood zones (HQ100) | LfU Bayern | `data/raw/E3_flood_areas/` | ✓ Downloaded |
| E4 | Water protection zones | LfU Bayern | `data/raw/E4_water_protection_ares/` | ✓ Downloaded |
| E5 | Terrain / slope (DGM200) | BKG | `data/raw/E5_slope/` | ✓ Downloaded |

### Exclusion Layers (pending)

| ID | Layer | Source | Status |
|----|-------|--------|--------|
| E6 | Built-up areas / forests / water | Derived from E1 | Pending |
| E7 | Distance buffers from infrastructure | DLM250 / OSM | Pending download |

### Suitability Scoring Layers (pending)

| ID | Layer | Weight | Source | Status |
|----|-------|--------|--------|--------|
| S1 | Grid proximity | 35% | OSM power data | Pending download |
| S2 | Slope | 10% | Derived from E5 | Pending |
| S3 | Agricultural land type | 15% | Derived from E1 | Pending |
| S4 | EEG subsidy eligibility | 15% | Derived from E2 + transport | Pending |
| S5 | BauGB §35 privileged permitting | 15% | Transport corridors | Pending |
| S6 | Solar irradiation | 10% | Bayerischer Solaratlas / PVGIS | Pending download |

---

## Setup

Requires Python ≥ 3.11 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

---

## Usage

### Audit all datasets

Verifies that every downloaded file is readable and structurally correct:

```bash
uv run python scripts/test_datasets.py
```

Prints a PASS / WARN / FAIL report for each of the 15 datasets.

---

## Target CRS

All analysis is conducted in **ETRS89 / UTM Zone 32N — EPSG:25832**, the standard for Bavaria. Input data in other CRS (CLC2018 arrives in EPSG:3035, DGM200 in UTM32N geographic variant) is reprojected during preprocessing.

---

## Project Status

**Phase 1 — Data audit** (current)
Data downloaded, no spatial processing yet. Running audit to confirm all datasets are usable before preprocessing begins.

**Phase 2 — Exclusion mapping** (next)
Preprocessing pipeline: clip to Bavaria, reproject, apply hard exclusion layers, output binary eligible/excluded map.

**Phase 3 — Suitability scoring**
Weighted overlay of S1–S6 criteria on eligible land.

**Phase 4 — Streamlit app**
Interactive map with toggleable layers and composite score visualization.

---

## Legal References

- EEG 2023 §37 — agrivoltaic feed-in tariff eligibility
- BauGB §35 Abs. 1 Nr. 8a — privileged permitting in the Außenbereich
- DIN SPEC 91434:2021-05 — requirements for agricultural primary use
- BNatSchG §§23–32 — protected area categories
- WHG §76, §78 — flood zone regulations
