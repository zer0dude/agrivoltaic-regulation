# Agrivoltaik-Screening Bayern: Project Foundation Document

**Project goal:** Build a GIS-based screening map for Bavaria (initially southern Bavaria) that identifies agricultural areas with high potential for agrivoltaic systems, suitable for prioritizing landowner outreach.

**Methodological basis:** Hauger et al. (2025), "GIS-based potential analysis and agro-economic site selection for agrivoltaics using AHP in two German counties," *Renewable Energy* 247, 123039. The paper's approach — layered exclusion mapping + AHP-weighted suitability scoring — is adapted here for a broader geographic scope at reduced granularity.

**Date:** May 2026

---

## 1. Scope and Framing

**Geographic scope:** Freistaat Bayern, with initial focus on Oberbayern, Schwaben, and Niederbayern (southern Bavaria). These Regierungsbezirke offer a productive combination of high solar irradiation, significant permanent crop areas (notably hops in the Hallertau, orchards in the Bodenseeraum and along the Donau), and relatively flat to gently rolling terrain in the Alpine foothills and the Donau plain.

**Output:** A heat-map style screening layer over agricultural land, categorising areas into broad tiers of agrivoltaic suitability (high / moderate / low / excluded). The map is not a permit-readiness assessment — it identifies where to direct further investigation and outreach.

**What this map is for:** Identifying Gemeinden and clusters of agricultural parcels worth targeting for landowner conversations. It should answer: "Given what we can see from publicly available data, which areas have the fewest obvious obstacles and the strongest indicators of economic and agronomic fit?"

**What this map is not for:** Site-specific feasibility studies, grid connection guarantees, or permitting applications. Those require project-level data (Netzanschlussanfrage, Bauvoranfrage, parcel-level soil assessment) that cannot be obtained at screening scale.

---

## 2. Analytical Layers

The paper uses five suitability criteria (C1–C5) plus a set of exclusion layers. Below, each is assessed for scalability to Bavaria.

### 2.1 Exclusion Layers (Hard Restrictions)

These layers remove areas from consideration entirely. They correspond to the paper's "hard restrictions."

#### Layer E1: Non-agricultural land use
- **Purpose:** Restrict analysis to agricultural land only (arable, permanent crops, grassland)
- **Source:** CORINE Land Cover 2018 (CLC2018) or the newer CLCplus Backbone (10 m resolution, reference year 2021 or 2023 when available)
- **Access:** Free download from Copernicus Land Monitoring Service: https://land.copernicus.eu/en/products/corine-land-cover — vector (GeoPackage, Shapefile) and raster (GeoTIFF, 100 m) formats, no registration required. Also available via Google Earth Engine.
- **Relevant CLC classes for inclusion:**
  - 211: Non-irrigated arable land
  - 221: Vineyards
  - 222: Fruit trees and berry plantations
  - 231: Pastures / permanent grassland
  - 242: Complex cultivation patterns
  - 243: Land principally occupied by agriculture, with significant areas of natural vegetation
- **Resolution:** 25 ha minimum mapping unit (CLC2018), 10 m pixel (CLCplus). For screening purposes, CLC2018 is adequate but CLCplus is preferable if the 2023 update is available by the time of analysis.
- **Alternative Germany-specific source:** Digitales Landbedeckungsmodell (LBM-DE) from BKG, derived from ATKIS with higher geometric accuracy than CLC. Available from https://gdz.bkg.bund.de. Uses the same CLC nomenclature. Check current availability and licensing.
- **Difficulty:** Low. Straightforward download and clip to Bavaria boundary.
- **Notes:** This is the foundational layer. All other layers are intersected with this one. Without InVeKoS data, you cannot distinguish crop rotation or individual parcel-level crop types — only the broad CLC categories. Hops (critical for the Hallertau region) are not separately classified in CLC; they fall under arable land or complex cultivation patterns.

#### Layer E2: Nature and landscape conservation areas
- **Purpose:** Exclude areas where installation is legally prohibited or highly restricted
- **Source:** Bayerisches Landesamt für Umwelt (LfU Bayern)
- **Access:** Free Shapefile download from https://www.lfu.bayern.de/natur/schutzgebiete/schutzgebietsabgrenzungen/index.htm — updated approximately annually. Also available via WFS from Geoportal Bayern.
- **Categories available (each as a separate Shapefile):**
  - Nationalparke (Berchtesgaden — hard exclusion)
  - Naturschutzgebiete (hard exclusion)
  - Biosphärenreservate (Berchtesgadener Land, Rhön — zonation matters: Zone I = hard, others = flag)
  - Landschaftsschutzgebiete (flag as caution — these cover large areas in Bavaria and are not necessarily a veto for agrivoltaics, but require case-by-case assessment)
  - Naturparke (not necessarily an exclusion — many overlap with agricultural land)
  - FFH-Gebiete and Vogelschutzgebiete (Natura 2000): separate download from the same LfU page, also as Shapefile
- **Simplified classification for this project:**
  - **Exclude (hard):** Nationalparke, Naturschutzgebiete, Biosphärenreservat Kernzone
  - **Flag (soft):** Landschaftsschutzgebiete, FFH-Gebiete, Vogelschutzgebiete, Biosphärenreservat Pflege-/Entwicklungszone
- **Difficulty:** Low. Well-organised, free, GIS-ready data. The interpretive challenge (hard vs. soft for agrivoltaics specifically) cannot be resolved from the data alone, but the simplified classification above is a defensible starting point.

#### Layer E3: Flood zones
- **Purpose:** Exclude 100-year flood areas (HQ100)
- **Source:** LfU Bayern — Hochwassergefahrenflächen
- **Access:** Available as WMS from Geoportal Bayern. The UmweltAtlas Bayern (https://www.lfu.bayern.de/umweltdaten/geodatendienste/index_download.htm) provides WMS layers for festgesetzte and vorläufig gesicherte Überschwemmungsgebiete. Direct Shapefile download may require a data request to the LfU Datenstelle. Check the download catalogue at the LfU Geodatendienste page.
- **Key layers:**
  - Festgesetzte Überschwemmungsgebiete (HQ100) — hard exclusion
  - Vorläufig gesicherte Überschwemmungsgebiete — hard exclusion (legally equivalent during the interim period)
- **Difficulty:** Low–Medium. WMS is freely accessible for visualisation; for GIS analysis you need the vector data. This may require a formal data request, but LfU is generally responsive. Worst case, you can digitise from the WMS at screen scale, or use the WFS endpoint if available.
- **Fallback:** The BfG (Bundesanstalt für Gewässerkunde) via GovData provides INSPIRE-compliant Überschwemmungsgebiete data for all of Germany, which includes Bavaria.

#### Layer E4: Water protection zones
- **Purpose:** Exclude innermost drinking water protection zones
- **Source:** LfU Bayern — Wasserschutzgebiete
- **Access:** Free Shapefile download from https://www.lfu.bayern.de/umweltdaten/geodatendienste/pretty_downloaddienst.htm?dld=wsg.xml — available in ETRS89/UTM32 and ETRS89 geographic coordinates. Licensed under CC BY-SA 4.0.
- **Key distinction:** The Shapefile contains Umringe (outer boundaries) of Trinkwasserschutzgebiete and Heilquellenschutzgebiete. Zone-level subdivision (Zone I, II, III) is **not** available in the download — only the overall perimeter. For zone-specific information, you would need to contact the zuständige Kreisverwaltungsbehörde.
- **Simplified approach:** Flag entire water protection zones as caution areas. Only Zone I (innermost, Fassungsbereich) is a clear hard exclusion, but since the download doesn't distinguish zones, a conservative approach would exclude the entire Schutzgebiet or — more proportionally — flag it and accept the imprecision.
- **Difficulty:** Low for download; the zone-subdivision limitation is a known gap.

#### Layer E5: Slope > 25%
- **Purpose:** Exclude terrain too steep for agrivoltaic installation
- **Source:** BKG — Digitales Geländemodell Gitterweite 200 m (DGM200)
- **Access:** Free download (Open Data, Datenlizenz Deutschland Namensnennung 2.0) from https://gdz.bkg.bund.de/index.php/default/open-data/digitales-gelandemodell-gitterweite-200-m-dgm200.html — covers all of Germany.
- **Processing:** Import DGM200 raster into QGIS → Raster > Analysis > Slope → classify into percentage slope → exclude >25%. For finer resolution, the Bayerische Vermessungsverwaltung offers DGM1 (1 m grid) and DGM5 (5 m grid) for Bavaria, but these may require a fee or data agreement. DGM200 is sufficient for screening.
- **Difficulty:** Low. Standard raster processing.

#### Layer E6: Built-up areas, forests, water bodies
- **Purpose:** Exclude non-eligible land uses not already captured by E1
- **Source:** Same as E1 (CORINE / LBM-DE). These are the CLC classes not included in the agricultural filter.
- **Difficulty:** None beyond E1 processing — this is the complement of the agricultural land selection.

#### Layer E7: Distance buffers from infrastructure
- **Purpose:** Apply minimum setback distances as per legal requirements
- **Source:** BKG — Digitales Landschaftsmodell (DLM250 or Basis-DLM)
- **Access:** DLM250 is available as Open Data from BKG. Basis-DLM has higher resolution but is not free.
- **Buffers to apply (from the paper):**
  - 50 m from water bodies (Gewässer)
  - 30 m from forests
  - 40 m from highways (Autobahnen) and railways
  - 20 m from national roads (Bundesstraßen)
- **Note:** These same transport infrastructure layers also serve as the basis for the positive 200 m EEG/BauGB buffer (see suitability criteria below). Extract once, buffer twice.
- **Difficulty:** Low–Medium. DLM250 is free but coarser; Basis-DLM is geometrically better but may cost. For screening, DLM250 plus OSM road/rail data is a viable combination.

---

### 2.2 Suitability Scoring Layers

After exclusions, remaining agricultural land is scored on the following criteria. The paper's AHP weights are noted; for a screening map, these can be applied as-is or simplified to a tier-based scoring.

#### Layer S1: Proximity to grid connection infrastructure (Paper weight: 50%)

This is the most important criterion and the hardest to replicate at scale.

- **Ideal source:** Actual grid data from Verteilnetzbetreiber (as used in the paper)
- **Availability for Bavaria:** Not centrally available. Bavaria's distribution grid is operated by multiple companies including Bayernwerk Netz (by far the largest, a subsidiary of E.ON, covering most of rural Bavaria), Stadtwerke München, LEW Verteilnetz, and others. Each would need to be approached individually, and there is no obligation to share.
- **Feasible proxy:** OpenStreetMap power infrastructure data
  - **What OSM contains for Germany:** Power lines (tagged by voltage), transmission towers, substations, power plants, transformers. Germany has among the best OSM power infrastructure coverage globally. A recent (2025) validation study in *Scientific Data* confirmed that OSM coverage of the European high-voltage grid is close to complete.
  - **Limitation:** OSM covers transmission (≥110 kV) and major distribution (20–110 kV) infrastructure well, but local distribution (niederspannungsnetz, <20 kV) and individual transformer stations (Ortsnetzstationen) are inconsistently mapped. For agrivoltaic projects up to 5 MWp, medium-voltage connection points are relevant — OSM coverage here is partial but still useful as a rough proximity indicator.
  - **Access options:**
    - **Free:** Download the Germany OSM extract from Geofabrik (https://download.geofabrik.de/europe/germany.html), filter for `power=*` tags. Format: PBF (convertible to Shapefile/GeoPackage with ogr2ogr or osmium).
    - **Free, pre-visualised:** Open Infrastructure Map (https://openinframap.org/) renders all power infrastructure from OSM — useful for visual inspection.
    - **Paid, pre-processed:** Infrageomatics (https://www.infrageomatics.com/products/osm-export) offers cleaned GeoPackage/Shapefile exports of OSM power data, with schema documentation. One-off purchase, delivered within hours.
    - **Academic/research:** PyPSA-Eur project provides a cleaned OSM-based European transmission grid dataset via Zenodo, with substations, lines, transformers, and voltage levels.
  - **Processing:** Extract substations and power lines for Bavaria → buffer at 250 m, 500 m, 750 m, 1000 m, 1500 m (matching the paper's distance classes) → overlay with agricultural land.
  - **Additional proxy:** Include Gewerbegebiete (commercial/industrial zones) from OSM or ATKIS as proxy indicators of grid capacity, since these areas have robust grid connections.
- **Difficulty:** Medium. The data exists and is free, but it's a proxy for the real thing. The main risk is false negatives — areas that are actually close to a suitable grid connection point but where OSM doesn't map the local infrastructure. For a screening map, this is acceptable; any specific site would require a Netzanschlussanfrage to the local Verteilnetzbetreiber regardless.
- **Weight recommendation for screening:** Retain high weight (40–50%), but note the proxy limitation in the map documentation.

#### Layer S2: Slope (Paper weight: 11%)
- **Source:** Same DGM200 as exclusion layer E5
- **Processing:** Classify slope into tiers:
  - 0–5%: best suitable (score 5)
  - 5–10%: suitable (score 4)
  - 10–15%: moderately suitable (score 3)
  - 15–20%: marginally suitable (score 2)
  - 20–25%: less suitable (score 1)
  - >25%: excluded (handled in E5)
- **Difficulty:** Low. Trivial extension of E5 processing.

#### Layer S3: Agricultural land type / crop synergy potential (Paper weight: 8%)
- **Source:** CORINE Land Cover (from E1)
- **Scoring based on the paper's synergy classification (Hauger et al. 2024, referenced as [72]):**
  - Fruits, berries, grapes (CLC 221, 222): score 5 — highest synergy due to hail/rain protection replacement
  - Arable land / cereals, leafy vegetables, root crops (CLC 211): score 3–4 depending on crop, but CLC doesn't distinguish crops within arable land → assign score 4 as a default
  - Permanent grassland (CLC 231): score 3
  - Complex cultivation patterns (CLC 242): score 3–4
- **Bavaria-specific consideration:** The Hallertau hop-growing region (world's largest contiguous hop cultivation area) represents a significant opportunity. Hops are classified as "Hop" in the paper's scoring (score 3), but the tall trellis structures already used in hop cultivation create an interesting structural parallel with elevated agrivoltaic systems. However, CLC does not distinguish hops from other arable crops.
- **InVeKoS alternative:** If access to InVeKoS data from the Bayerisches Staatsministerium für Ernährung, Landwirtschaft, Forsten und Tourismus (StMELF) can be obtained, this layer improves dramatically — you gain parcel-level crop identification, multi-year rotation data, and much finer spatial resolution. This is worth pursuing but should be treated as an enhancement, not a prerequisite.
- **Difficulty:** Low with CLC; data request effort with InVeKoS.
- **Weight recommendation for screening:** Increase to 15–20% given the importance of crop type for agrivoltaic synergies.

#### Layer S4: EEG subsidy eligibility (Paper weight: 17%)
- **Purpose:** Identify agricultural land eligible for feed-in tariff support under EEG §37
- **Criteria:**
  - Agricultural land (arable, permanent crops, permanent grassland) outside Natura 2000 areas: eligible
  - Land within 200 m buffer of railways and Autobahnen: eligible regardless of other criteria
- **Sources:**
  - Natura 2000 boundaries: already obtained for E2 (FFH + Vogelschutzgebiete from LfU Bayern)
  - Railways and Autobahnen: from DLM250 (BKG) or OSM
- **Processing:** Intersect agricultural land with Natura 2000 layer. Agricultural land NOT in Natura 2000 = eligible. Additionally, the 200 m transport corridor buffer adds eligible area even within Natura 2000 (if agricultural).
- **Scoring:** Binary — eligible (score 5) vs. not eligible (score 1). This is a significant economic factor: without EEG support, most small-to-medium agrivoltaic projects are not financially viable.
- **Difficulty:** Low. All source data already obtained for other layers.

#### Layer S5: BauGB §35 privileged permitting (Paper weight: 14%)
- **Purpose:** Identify areas where building permit processes are simplified
- **Criteria:**
  - Agricultural parcel ≤ 25,000 m²: privileged
  - Land within 200 m buffer of railways and Autobahnen: privileged regardless of size
- **Sources:** Same transport infrastructure data as S4. Parcel size data requires Flurstücksdaten from the Bayerische Vermessungsverwaltung — this is available but may involve fees. Without it, only the transport corridor criterion can be mapped.
- **Simplified approach for screening:** Map only the 200 m transport corridor buffer as "privileged." Accept that the 25,000 m² criterion cannot be mapped without parcel data, and note this in the documentation. Given that many Bavarian agricultural parcels (Feldstücke) exceed 25,000 m² (= 2.5 ha), this criterion's practical impact is limited anyway — it mainly affects smaller-scale installations.
- **Difficulty:** Low for the corridor criterion; High for the parcel size criterion.

#### Layer S6: Solar irradiation (Not in paper — added for broader scope)
- **Purpose:** Score areas by solar resource quality
- **Source:** Bayerischer Solaratlas — available as WMS from Energie-Atlas Bayern / LfU (Globalstrahlung in kWh/m², monthly and annual means, 1 km × 1 km resolution, based on DWD data 1981–2010). Recently updated and now available with download capability.
- **Access:** WMS endpoint from Geoportal Bayern, also viewable in Energie-Atlas Bayern (https://www.energieatlas.bayern.de). The WMS can be loaded directly into QGIS. Alternatively, use EU PVGIS (https://re.jrc.ec.europa.eu/pvg_tools/en/) for point-specific queries or the PVGIS-SARAH2 raster dataset for spatial analysis.
- **Scoring:** Bavaria ranges from roughly 1,050 kWh/m²/year in northern areas to 1,250+ kWh/m²/year in the southern Alpine foothills. A simple classification:
  - >1,200 kWh/m²: score 5
  - 1,150–1,200: score 4
  - 1,100–1,150: score 3
  - 1,050–1,100: score 2
  - <1,050: score 1
- **Weight recommendation:** 10%. The variation within Bavaria is meaningful but not dramatic.
- **Difficulty:** Low. WMS can be consumed directly in QGIS; raster extraction is straightforward.

---

## 3. Data Source Summary

| Layer | Source | URL / Access | Format | Cost | Difficulty |
|-------|--------|-------------|--------|------|------------|
| Agricultural land | CORINE Land Cover 2018 / CLCplus | https://land.copernicus.eu | GeoTIFF, GeoPackage, Shapefile | Free | Low |
| Agricultural land (DE-specific) | LBM-DE (BKG) | https://gdz.bkg.bund.de | Various | Free (Open Data) | Low |
| Conservation areas | LfU Bayern Schutzgebietsabgrenzungen | https://www.lfu.bayern.de/natur/schutzgebiete/schutzgebietsabgrenzungen/ | Shapefile | Free | Low |
| Natura 2000 (FFH + SPA) | LfU Bayern Natura2000 Download | Same LfU download page | Shapefile | Free | Low |
| Flood zones | LfU Bayern Hochwassergefahrenflächen | https://www.lfu.bayern.de/umweltdaten/geodatendienste/ | WMS (vector may require request) | Free | Low–Med |
| Water protection zones | LfU Bayern Wasserschutzgebiete | https://www.lfu.bayern.de/.../pretty_downloaddienst.htm?dld=wsg.xml | Shapefile (ETRS89) | Free (CC BY-SA) | Low |
| Terrain / slope | BKG DGM200 | https://gdz.bkg.bund.de (search DGM200) | Raster (ASCII grid) | Free (Open Data) | Low |
| Transport infrastructure | BKG DLM250 + OSM | https://gdz.bkg.bund.de + https://download.geofabrik.de/europe/germany.html | Various | Free | Low–Med |
| Power grid (proxy) | OpenStreetMap power data | https://download.geofabrik.de or https://openinframap.org | PBF → Shapefile | Free (or paid via Infrageomatics for clean export) | Medium |
| Solar irradiation | Bayerischer Solaratlas (LfU/StMWi) | WMS via Geoportal Bayern / Energie-Atlas Bayern | WMS raster | Free (CC BY-SA) | Low |
| Crop-level data (enhancement) | InVeKoS (StMELF Bayern) | Formal data request to StMELF | Parcel polygons | Unknown — likely requires justification | High |

---

## 4. Workflow

### Phase 1: Data acquisition and preparation (est. 2–3 weeks)

1. Download all freely available datasets listed above
2. Clip all layers to Bavaria state boundary (or to selected Regierungsbezirke for initial pilot)
3. Reproject everything to ETRS89 / UTM Zone 32N (EPSG:25832) — standard for Bavaria
4. For OSM power data: extract from PBF, filter for `power=line`, `power=substation`, `power=plant`, `power=tower`, retain voltage tags
5. Assess flood zone data availability — if WMS-only, test WFS endpoint or submit data request to LfU

### Phase 2: Exclusion mapping (est. 1 week)

1. Create agricultural land base layer from CLC/LBM-DE
2. Apply hard exclusions sequentially: conservation areas (E2), flood zones (E3), water protection (E4, simplified), slope >25% (E5), distance buffers (E7)
3. Output: binary map of "eligible agricultural land" vs. "excluded"

### Phase 3: Suitability scoring (est. 1–2 weeks)

1. For each eligible pixel/polygon, calculate scores for S1–S6
2. Apply weighted overlay (using paper's AHP weights as baseline, adjusted for added solar irradiation criterion)
3. Classify into suitability tiers (5 = high to 1 = low)
4. Generate maps at Landkreis and Gemeinde level for easy communication

### Phase 4: Validation and documentation (est. 1 week)

1. Cross-check high-suitability areas against known agrivoltaic installations in Bavaria
2. Spot-check a sample of "best suitable" areas using aerial imagery (BayernAtlas or Google Earth) to verify they are indeed agricultural land with plausible conditions
3. Document all assumptions, simplifications, and known data gaps
4. Prepare summary materials for stakeholder communication

**Total estimated timeline:** 5–7 weeks for a single analyst with GIS competence (QGIS).

---

## 5. Known Limitations and Data Gaps

**Grid connection capacity:** Proximity to a substation or power line does not guarantee feed-in capacity. The map cannot assess Netzkapazität. This must be stated prominently in any output.

**County-specific regulatory interpretation:** The paper demonstrates that the hard/soft distinction for conservation designations varies by county. This project applies a simplified statewide classification. Some areas flagged as "caution" may in practice be hard vetoes in specific Landkreise, and vice versa.

**Regional planning data (Regionalpläne):** Bavaria has 18 Planungsregionen, each with its own Regionalplan. The Vorrang- and Vorbehaltsgebiete designations (for agriculture, raw materials, flood control, green corridors, etc.) are not incorporated in this screening. Some of these are available digitally from the individual Regionale Planungsverbände, but the effort to harmonise 18 different data sources is disproportionate for a screening exercise. The Energie-Atlas Bayern partially integrates some planning constraints — worth checking.

**Crop rotation:** Without InVeKoS data, no temporal crop information is available. Areas classified as "arable" in CLC may be growing maize (low synergy) or cereals (moderate synergy) — this cannot be distinguished.

**Acceptance and social factors:** No proxy for local community or farmer attitudes is included. Acceptance is critical for implementation but cannot be spatially modelled from available data.

**Meadow orchards (Streuobstwiesen):** The paper excludes these as technically unsuitable. They are ecologically valuable and culturally significant in parts of Bavaria (Fränkische Schweiz, Bodenseeregion). CLC does not distinguish them from other fruit tree plantations. If InVeKoS data is obtained, Streuobstwiesen can be identified and excluded.

**Parcel geometry:** Without Flurstücksdaten, parcel size and shape cannot be assessed. Very small or irregularly shaped fields are economically unsuitable but cannot be filtered out.

---

## 6. First Steps

Before any GIS work begins, the immediate actions are to verify data availability:

1. **Visit LfU Bayern download pages** — confirm that Schutzgebiete, Natura 2000, and Wasserschutzgebiete Shapefiles are downloadable as described. Test one download to verify format, CRS, and attribute schema.

2. **Test the flood zone data path** — check whether WFS (not just WMS) is available for Überschwemmungsgebiete, or whether a formal data request is needed.

3. **Download the Germany OSM extract** from Geofabrik and test power infrastructure extraction — assess coverage quality for a sample area in southern Bavaria (e.g., Landkreis Rosenheim or Landkreis Oberallgäu).

4. **Check Energie-Atlas Bayern** — the portal integrates multiple datasets (Schutzgebiete, Stromnetze, Vorrang-/Vorbehaltsgebiete). Evaluate whether its built-in layers can substitute for some of the individual downloads, and whether its data export functionality is sufficient.

5. **Assess InVeKoS data access** — draft a data request to StMELF Bayern. Frame the request around research/sustainability objectives. This is a bonus layer, not a prerequisite, but pursuing it early gives maximum lead time.

6. **Download DGM200 and CORINE** — these are guaranteed-available and zero-friction. Start with these to build the analysis skeleton while other data sources are being verified.

---

## 7. Suggested Weighting Scheme

Adapting the paper's AHP weights for a six-criterion screening model:

| Criterion | Paper weight | Screening weight | Rationale |
|-----------|-------------|-----------------|-----------|
| Grid proximity (proxy) | 50% | 35% | Reduced because proxy data is less reliable than real grid data |
| Slope | 11% | 10% | Unchanged — terrain is terrain |
| Agricultural area / crop type | 8% | 15% | Increased — crop synergy is a key differentiator for agrivoltaic value proposition |
| EEG eligibility | 17% | 15% | Slightly reduced |
| BauGB privilege | 14% | 15% | Slightly increased — permitting ease is important for outreach viability |
| Solar irradiation | — | 10% | Added — meaningful variation at Bundesland scale |

These weights are a starting point. The paper's sensitivity analysis shows results are meaningfully affected by weighting — consider running the analysis with both these weights and an equal-weight scenario (16.7% each) to see how robust the top-tier areas are.

---

## Appendix: Coordinate Reference System

All data should be harmonised to **ETRS89 / UTM Zone 32N (EPSG:25832)**, which is the standard CRS for Bavaria and is used by the Bayerische Vermessungsverwaltung and the LfU. Some federal datasets from BKG arrive in ETRS89 geographic (EPSG:4258) or UTM Zone 33N — reproject as needed. CORINE data from Copernicus arrives in ETRS89-LAEA (EPSG:3035) — also requires reprojection.

## Appendix: Key Legal References

- **EEG 2023 §37:** Ausschreibungen für Solaranlagen des ersten Segments — defines subsidy eligibility for agrivoltaic systems
- **BauGB §35 Abs. 1 Nr. 8a:** Privilegierung von Agri-PV-Anlagen im Außenbereich
- **DIN SPEC 91434:2021-05:** Agri-Photovoltaik-Anlagen — Anforderungen an die landwirtschaftliche Hauptnutzung (the pre-standard ensuring agriculture remains primary use)
- **BNatSchG §§23–32:** Schutzgebietskategorien
- **WHG §76, §78:** Überschwemmungsgebiete
- **BayWG Art. 46:** Bayerische Umsetzung der Überschwemmungsgebietsregelungen
