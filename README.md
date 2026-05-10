# Agrivoltaic Screening Map — Bavaria

Interactive GIS-based screening tool identifying agricultural land in Bavaria with low conflict potential for agrivoltaic (agri-PV) installations. Supports preliminary landowner outreach — not a permit readiness assessment or grid capacity guarantee.

**Methodology:** [Hauger et al. (2025), *Renewable Energy* 247](https://doi.org/10.1016/j.renene.2025.123039)

Made by Brian Jin ([brianjin150@gmail.com](mailto:brianjin150@gmail.com)) for educational purposes.

---

## Running the app

```
uv sync
uv run streamlit run app/main.py
```

The preprocessing pipeline (`scripts/preprocess.py`) has already been run and the processed layers are included in `data/processed/layers.gpkg`. To regenerate:

```
uv run python scripts/preprocess.py
uv run python scripts/verify_processed.py
```

---

## Data sources

| Layer group | Source |
|---|---|
| Agricultural land | Copernicus CLC2018 |
| Conservation areas | LfU Bayern |
| Flood zones | LfU Bayern |
| Water protection | LfU Bayern |
| Slope (terrain) | BKG DGM200 |
| Infrastructure setbacks | BKG DLM250 (2024) |
| Bavaria boundary | Eurostat NUTS 2021 |

All layers processed to EPSG:25832, simplified at 25 m tolerance.

---

## Layer classification

**Hard exclusions** — areas where agrivoltaic development is legally or technically not feasible: strict conservation zones (Naturschutzgebiete, Nationalparke, Naturdenkmal), flood plains (HQ100), and slopes above 25%.

**Soft exclusions** — require case-by-case review: landscape conservation areas, water protection zones (zone boundaries approximate, no zone-level subdivision available), and infrastructure setback distances (indicative — not statutory exclusions under German law).

**Presets** — two pre-computed eligible land layers are available for instant loading:
- *Hard exclusions removed:* agricultural land minus hard exclusions
- *All exclusions removed:* agricultural land minus hard and soft exclusions

---

## Limitations

[Hauger et al. (2025)](https://doi.org/10.1016/j.renene.2025.123039) identify proximity to grid connection infrastructure and agricultural land type (crop synergy) as highly important suitability criteria. Neither is included in this tool: grid connection data at the distribution level is not publicly available at sufficient resolution, and crop-type data (InVeKoS) requires a formal data request. The screening results therefore reflect exclusion constraints only, not full suitability scoring as described in the paper.
