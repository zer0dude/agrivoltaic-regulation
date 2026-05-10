#!/usr/bin/env python3
"""Phase 2 preprocessing pipeline for the agrivoltaic screening project.

Transforms raw GIS data (E1–E5) into clean, compact processed layers in data/processed/.
Run once; outputs become the sole data source for the Streamlit app.

Usage:
    uv run python scripts/preprocess.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import fiona
import rasterio
from rasterio.crs import CRS as RasterioCRS
from rasterio.features import shapes as rasterio_shapes
from rasterio.mask import mask as rio_mask
import shapely
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

# ── Path constants ────────────────────────────────────────────────────────────

E1_BASE = RAW / "E1_land_use"
E1_PARTITIONS = [
    E1_BASE / "U2018_CLC2018_V2020_20u1_1.shp" / "U2018_CLC2018_V2020_20u1.shp",
    E1_BASE / "U2018_CLC2018_V2020_20u1_2.shp" / "U2018_CLC2018_V2020_20u1.shp",
    E1_BASE / "U2018_CLC2018_V2020_20u1_3.shp" / "U2018_CLC2018_V2020_20u1.shp",
]
E2_BASE = RAW / "E2_conservation_areas"
E3_GPKG = RAW / "E3_flood_areas" / "hw_flaeche_gpkg" / "hw_flaeche.gpkg"
E4_BASE = RAW / "E4_water_protection_ares"
DGM200  = RAW / "E5_slope" / "dgm200.utm32s.gridascii" / "dgm200" / "dgm200_utm32s.asc"
DLM250_BASE = RAW / "E7_dlm250" / "dlm250.utm32s.shape.ebenen" / "daten"

# Bavaria bbox in EPSG:25832 with 5 km margin — used to pre-filter large DLM250 reads
_BAV_BBOX = (275000, 5225000, 875000, 5655000)

LAYERS_GPKG = OUT / "layers.gpkg"
SLOPE_TIF   = OUT / "slope_class.tif"

NUTS_URL = (
    "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/"
    "NUTS_RG_01M_2021_4326_LEVL_1.geojson"
)

# Agricultural CLC2018 class codes to include
AG_CLASSES = {"211", "221", "222", "231", "242", "243"}


def log(msg: str) -> None:
    print(f"  {msg}", flush=True)


def save_layer(gdf: gpd.GeoDataFrame, layer_name: str, simplify_m: float = 0.0) -> None:
    """Append a GeoDataFrame as a layer in the output GeoPackage.

    simplify_m: if > 0, simplify geometries to this tolerance (metres) before saving.
    At 200 m analysis resolution, 25 m is imperceptible but dramatically reduces file size.
    """
    if simplify_m > 0:
        gdf = gdf.copy()
        gdf["geometry"] = gdf.geometry.simplify(simplify_m, preserve_topology=True)
    gdf.to_file(LAYERS_GPKG, layer=layer_name, driver="GPKG")
    log(f"  -> saved layer '{layer_name}' ({len(gdf):,} features)")


# ── Step 1: Bavaria boundary ──────────────────────────────────────────────────

def step_bavaria() -> gpd.GeoDataFrame:
    print("\n[1/12] Bavaria boundary")
    log("downloading NUTS1 from Eurostat ...")
    nuts = gpd.read_file(NUTS_URL)
    bavaria = nuts[nuts["NUTS_ID"] == "DE2"].to_crs(25832)
    bavaria = bavaria[["NUTS_ID", "NUTS_NAME", "geometry"]].reset_index(drop=True)
    save_layer(bavaria, "bavaria_boundary")
    log(f"bbox: {tuple(round(v) for v in bavaria.total_bounds)}")
    return bavaria


# ── Step 2: E1 Agricultural land ─────────────────────────────────────────────

def step_agricultural_land(bavaria: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    print("\n[2/12] E1 — Agricultural land (CLC2018, 3 partitions)")
    parts = []
    for path in E1_PARTITIONS:
        clc = gpd.read_file(path)
        clc = clc[clc["Code_18"].astype(str).isin(AG_CLASSES)].copy()
        log(f"  {path.parent.name}: {len(clc):,} ag features")
        parts.append(clc)
    clc = pd.concat(parts, ignore_index=True)
    log(f"total before reproject+clip: {len(clc):,}  CRS: {clc.crs.to_epsg()}")
    clc = clc.to_crs(25832).clip(bavaria)
    log(f"after clip: {len(clc):,}")
    clc = clc[["Code_18", "geometry"]].reset_index(drop=True)
    save_layer(clc, "agricultural_land", simplify_m=25.0)
    return clc


# ── Step 3: E2 Conservation areas ────────────────────────────────────────────

def _load_e2(rel_path: str, source_label: str, buffer_m: float = 0.0) -> gpd.GeoDataFrame:
    """Load one E2 shapefile, add a source label, optionally buffer."""
    path = E2_BASE / rel_path
    gdf = gpd.read_file(path)
    if buffer_m > 0:
        gdf["geometry"] = gdf.geometry.buffer(buffer_m)
    gdf["source"] = source_label
    return gdf[["source", "geometry"]]


def step_conservation() -> None:
    print("\n[3/12] E2 — Conservation areas")

    hard_parts = [
        _load_e2("nsg_epsg25832_shp/nsg_epsg25832_shp.shp", "NSG"),
        _load_e2("nlp_epsg25832_shp/nlp_epsg25832_shp.shp", "NLP"),
        _load_e2("naturdenkmal_flaechig_epsg25832_shp/naturdenkmal_flaechig_epsg25832_shp.shp", "ND_flaeche"),
        _load_e2("nationale_naturmonumente_epsg25832_shp/nationale_naturmonumente_epsg25832_shp.shp", "NNM"),
        _load_e2("naturdenkmal_punktfoermig_epsg25832_shp/naturdenkmal_punktfoermig_epsg25832_shp.shp", "ND_punkt", buffer_m=30.0),
    ]
    hard = pd.concat(hard_parts, ignore_index=True)
    hard = gpd.GeoDataFrame(hard, crs=25832).explode(index_parts=False).reset_index(drop=True)
    log(f"conservation_hard: {len(hard):,} features from {len(hard_parts)} sources")
    save_layer(hard, "conservation_hard", simplify_m=25.0)

    soft_parts = [
        _load_e2("lsg_epsg25832_shp/lsg_epsg25832_shp.shp", "LSG"),
        _load_e2("biosphaerenreservate_epsg25832_shp/biosphaerenreservate_epsg25832_shp.shp", "BR"),
        _load_e2("naturparke_epsg25832_shp/naturparke_epsg25832_shp.shp", "NP"),
        _load_e2("landschaftsbestandteil_flaechig_epsg25832_shp/landschaftsbestandteil_flaechig_epsg25832_shp.shp", "LB_flaeche"),
        _load_e2("landschaftsbestandteil_punktfoermig_epsg25832_shp/landschaftsbestandteil_punktfoermig_epsg25832_shp.shp", "LB_punkt", buffer_m=30.0),
    ]
    soft = pd.concat(soft_parts, ignore_index=True)
    soft = gpd.GeoDataFrame(soft, crs=25832).explode(index_parts=False).reset_index(drop=True)
    log(f"conservation_soft: {len(soft):,} features from {len(soft_parts)} sources")
    save_layer(soft, "conservation_soft", simplify_m=25.0)


# ── Step 4: E3 Flood zones ────────────────────────────────────────────────────

def step_flood_zones() -> None:
    print("\n[4/12] E3 — Flood zones")
    flood = gpd.read_file(E3_GPKG, layer="hw_flaeche")
    flood = flood[["geometry"]].reset_index(drop=True)
    save_layer(flood, "flood_zones", simplify_m=25.0)


# ── Step 5: E4 Water protection zones ────────────────────────────────────────

def step_water_protection() -> None:
    print("\n[5/12] E4 — Water protection zones")
    twsg = gpd.read_file(E4_BASE / "twsg_epsg25832_shp" / "twsg_epsg25832.shp")
    hqsg = gpd.read_file(E4_BASE / "hqsg_epsg25832_shp" / "hqsg_epsg25832.shp")
    twsg["source"] = "TWSG"
    hqsg["source"] = "HQSG"
    water = pd.concat(
        [twsg[["source", "geometry"]], hqsg[["source", "geometry"]]],
        ignore_index=True,
    )
    water = gpd.GeoDataFrame(water, crs=25832)
    log(f"TWSG: {len(twsg):,}  HQSG: {len(hqsg):,}  merged: {len(water):,}")
    save_layer(water, "water_protection", simplify_m=25.0)


# ── Step 6: E5 Slope classification ──────────────────────────────────────────

def step_slope(bavaria: gpd.GeoDataFrame) -> None:
    print("\n[6/12] E5 — Slope classification (DGM200)")
    log("opening DGM200 raster (forcing CRS = EPSG:25832) ...")

    bavaria_geom = [bavaria.union_all().buffer(2000)]

    with rasterio.open(DGM200) as src:
        profile = src.profile.copy()
        log(f"raster size: {src.width}x{src.height}  res: {src.res[0]:.0f}m  nodata: {src.nodata}")

        # Force the correct CRS before masking
        profile.update(crs=RasterioCRS.from_epsg(25832))

        log("clipping to Bavaria (+2 km buffer) ...")
        dem_clipped, clipped_transform = rio_mask(
            src,
            bavaria_geom,
            crop=True,
            nodata=-9999.0,
            filled=True,
        )

    dem = dem_clipped[0].astype(np.float32)
    nodata_mask = dem == -9999.0
    dem[nodata_mask] = np.nan

    log(f"clipped size: {dem.shape[1]}x{dem.shape[0]}  valid pixels: {(~nodata_mask).sum():,}")

    log("computing slope (numpy gradient, cell size = 200 m) ...")
    dy, dx = np.gradient(dem, 200.0, 200.0)
    slope_pct = np.sqrt(dx**2 + dy**2) * 100.0

    log("classifying slope ...")
    classes = np.zeros(slope_pct.shape, dtype=np.uint8)
    classes[slope_pct <= 5]                         = 1
    classes[(slope_pct > 5)  & (slope_pct <= 10)]  = 2
    classes[(slope_pct > 10) & (slope_pct <= 15)]   = 3
    classes[(slope_pct > 15) & (slope_pct <= 20)]   = 4
    classes[(slope_pct > 20) & (slope_pct <= 25)]   = 5
    classes[slope_pct > 25]                         = 6
    classes[np.isnan(slope_pct)]                    = 0

    counts = {int(v): int((classes == v).sum()) for v in range(7)}
    log(f"class counts: {counts}")

    out_profile = {
        **profile,
        "driver": "GTiff",
        "dtype": "uint8",
        "count": 1,
        "nodata": 0,
        "compress": "lzw",
        "transform": clipped_transform,
        "height": dem.shape[0],
        "width": dem.shape[1],
    }

    with rasterio.open(SLOPE_TIF, "w", **out_profile) as dst:
        dst.write(classes[np.newaxis, :, :])

    size_mb = SLOPE_TIF.stat().st_size / 1024**2
    log(f"saved slope_class.tif  ({size_mb:.1f} MB)")


# ── Step 7: E5 slope excluded zone (vectorized) ──────────────────────────────

def step_slope_excluded() -> None:
    print("\n[7/12] E5 vector — slope excluded (>25%)")
    with rasterio.open(SLOPE_TIF) as src:
        data = src.read(1)
        transform = src.transform

    mask = (data == 6).astype(np.uint8)
    polys = [
        shape(geom)
        for geom, val in rasterio_shapes(mask, mask=mask, transform=transform)
        if val == 1
    ]
    if not polys:
        log("WARNING: no excluded slope pixels found — skipping layer")
        return
    gdf = gpd.GeoDataFrame({"geometry": polys}, crs=25832)
    gdf = gdf.dissolve().explode(index_parts=False).reset_index(drop=True)
    log(f"slope_excluded: {len(gdf):,} polygons after dissolve")
    save_layer(gdf, "slope_excluded", simplify_m=25.0)


# ── Step 8: E6 Non-agricultural land ─────────────────────────────────────────

def step_non_agricultural(bavaria: gpd.GeoDataFrame, ag_land: gpd.GeoDataFrame) -> None:
    print("\n[8/12] E6 — Non-agricultural land (Bavaria minus E1)")
    log("computing union of agricultural land ...")
    ag_union = ag_land.union_all()
    bav_poly = bavaria.union_all()
    log("computing difference (Bavaria minus agricultural) ...")
    non_ag_geom = bav_poly.difference(ag_union)
    gdf = gpd.GeoDataFrame({"geometry": [non_ag_geom]}, crs=25832)
    gdf = gdf.explode(index_parts=False).reset_index(drop=True)
    log(f"non_agricultural_land: {len(gdf):,} polygons")
    save_layer(gdf, "non_agricultural_land", simplify_m=25.0)


# ── Steps 9–12: E7 Infrastructure setback buffers ────────────────────────────

def step_road_setback(bavaria: gpd.GeoDataFrame) -> None:
    print("\n[9/14] E7 — Road setback buffer")
    roads = gpd.read_file(DLM250_BASE / "ver01_l.shp", bbox=_BAV_BBOX)
    roads = roads[roads["WDM"].astype(str).isin({"1301", "1303"})].copy()
    roads = roads.clip(bavaria)
    log(f"after Bavaria clip: {len(roads):,} features")

    autobahn  = roads[roads["WDM"].astype(str) == "1301"].copy()
    bundesstr = roads[roads["WDM"].astype(str) == "1303"].copy()

    parts: list[gpd.GeoDataFrame] = []
    if len(autobahn):
        buf = autobahn[["geometry"]].copy()
        buf["geometry"] = buf.geometry.buffer(40)
        buf["source"] = "Autobahn"
        parts.append(buf)
    if len(bundesstr):
        buf = bundesstr[["geometry"]].copy()
        buf["geometry"] = buf.geometry.buffer(20)
        buf["source"] = "Bundesstrasse"
        parts.append(buf)

    gdf = gpd.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=25832)
    gdf = gdf.dissolve(by="source").reset_index().explode(index_parts=False).reset_index(drop=True)
    log(f"road_setback: {len(gdf):,} polygons after dissolve")
    save_layer(gdf, "road_setback", simplify_m=25.0)


def step_rail_setback(bavaria: gpd.GeoDataFrame) -> None:
    print("\n[10/14] E7 — Railway setback buffer")
    rail = gpd.read_file(DLM250_BASE / "ver03_l.shp", bbox=_BAV_BBOX)
    rail = rail[rail["OBJART"].astype(str) == "42014"].clip(bavaria)
    log(f"after Bavaria clip: {len(rail):,} features")
    buf = rail[["geometry"]].copy()
    buf["geometry"] = buf.geometry.buffer(40)
    buf["source"] = "Eisenbahn"
    gdf = gpd.GeoDataFrame(buf, crs=25832)
    gdf = gdf.dissolve(by="source").reset_index().explode(index_parts=False).reset_index(drop=True)
    log(f"rail_setback: {len(gdf):,} polygons after dissolve")
    save_layer(gdf, "rail_setback", simplify_m=25.0)


def step_water_setback(bavaria: gpd.GeoDataFrame) -> None:
    print("\n[11/14] E7 — Water body setback buffer (50 m)")
    water = gpd.read_file(DLM250_BASE / "gew01_f.shp", bbox=_BAV_BBOX).clip(bavaria)
    log(f"after Bavaria clip: {len(water):,} features")
    buf = water[["geometry"]].copy()
    buf["geometry"] = buf.geometry.buffer(50)
    buf["source"] = "Gewaesser"
    gdf = gpd.GeoDataFrame(buf, crs=25832)
    gdf = gdf.dissolve(by="source").reset_index().explode(index_parts=False).reset_index(drop=True)
    log(f"water_setback: {len(gdf):,} polygons after dissolve")
    save_layer(gdf, "water_setback", simplify_m=25.0)


def step_forest_setback(bavaria: gpd.GeoDataFrame) -> None:
    print("\n[12/14] E7 — Forest setback buffer (30 m)")
    forest = gpd.read_file(DLM250_BASE / "veg02_f.shp", bbox=_BAV_BBOX).clip(bavaria)
    log(f"after Bavaria clip: {len(forest):,} features")
    buf = forest[["geometry"]].copy()
    buf["geometry"] = buf.geometry.buffer(30)
    buf["source"] = "Wald"
    gdf = gpd.GeoDataFrame(buf, crs=25832)
    gdf = gdf.dissolve(by="source").reset_index().explode(index_parts=False).reset_index(drop=True)
    log(f"forest_setback: {len(gdf):,} polygons after dissolve")
    save_layer(gdf, "forest_setback", simplify_m=25.0)


# ── Steps 13–14: Pre-computed preset eligible layers ─────────────────────────

def step_presets(ag_land: gpd.GeoDataFrame) -> None:
    print("\n[13/14] Presets — eligible land (hard exclusions removed)")
    hard_layer_names = ["conservation_hard", "flood_zones", "slope_excluded"]
    hard_parts = [gpd.read_file(LAYERS_GPKG, layer=l) for l in hard_layer_names]
    hard_combined = pd.concat(hard_parts, ignore_index=True)
    hard_combined["geometry"] = shapely.make_valid(hard_combined.geometry.values)
    hard_union_geom = hard_combined.union_all()
    hard_union_gdf = gpd.GeoDataFrame({"geometry": [hard_union_geom]}, crs=25832)
    eligible_hard = gpd.overlay(ag_land[["Code_18", "geometry"]], hard_union_gdf, how="difference")
    eligible_hard = eligible_hard[~eligible_hard.geometry.is_empty].reset_index(drop=True)
    log(f"eligible_hard_only: {len(eligible_hard):,} features")
    save_layer(eligible_hard, "eligible_hard_only", simplify_m=25.0)

    print("\n[14/14] Presets — eligible land (all exclusions removed)")
    soft_layer_names = [
        "conservation_soft", "water_protection",
        "road_setback", "rail_setback", "water_setback", "forest_setback",
    ]
    all_parts = hard_parts + [gpd.read_file(LAYERS_GPKG, layer=l) for l in soft_layer_names]
    all_combined = pd.concat(all_parts, ignore_index=True)
    all_combined["geometry"] = shapely.make_valid(all_combined.geometry.values)
    all_union_geom = all_combined.union_all()
    all_union_gdf = gpd.GeoDataFrame({"geometry": [all_union_geom]}, crs=25832)
    eligible_all = gpd.overlay(ag_land[["Code_18", "geometry"]], all_union_gdf, how="difference")
    eligible_all = eligible_all[~eligible_all.geometry.is_empty].reset_index(drop=True)
    log(f"eligible_all_excl: {len(eligible_all):,} features")
    save_layer(eligible_all, "eligible_all_excl", simplify_m=25.0)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("  Agrivoltaic Screening Bavaria -- Preprocessing Pipeline")
    print("=" * 60)

    OUT.mkdir(parents=True, exist_ok=True)

    # Remove stale GeoPackage so layers don't accumulate across re-runs
    if LAYERS_GPKG.exists():
        LAYERS_GPKG.unlink()
        log("removed existing layers.gpkg")

    try:
        bavaria = step_bavaria()
        ag_land = step_agricultural_land(bavaria)
        step_conservation()
        step_flood_zones()
        step_water_protection()
        step_slope(bavaria)
        step_slope_excluded()
        step_non_agricultural(bavaria, ag_land)
        step_road_setback(bavaria)
        step_rail_setback(bavaria)
        step_water_setback(bavaria)
        step_forest_setback(bavaria)
        step_presets(ag_land)
    except Exception as exc:
        print(f"\n[FAIL] {exc}", file=sys.stderr)
        raise

    layers_in_gpkg = fiona.listlayers(LAYERS_GPKG)
    print("\n" + "=" * 60)
    print("  All 14 steps complete.")
    print(f"  layers.gpkg : {LAYERS_GPKG.stat().st_size / 1024**2:.1f} MB  ({len(layers_in_gpkg)} layers)")
    print(f"  slope_class : {SLOPE_TIF.stat().st_size / 1024**2:.1f} MB")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
