#!/usr/bin/env python3
"""Dataset audit script for the agrivoltaic screening project.

Checks that every downloaded file is readable, has the expected CRS,
has non-zero features/pixels, and reports PASS / WARN / FAIL.

Usage:
    uv run python scripts/test_datasets.py
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import fiona
    import rasterio
    import rasterio.windows
    from pyproj import CRS
except ImportError as e:
    print(f"Missing dependency: {e}\nRun: uv sync")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "raw"

_results: list[tuple[str, str, str]] = []


def _record(name: str, status: str, detail: str = "") -> None:
    _results.append((name, status, detail))
    icon = {"PASS": "OK  ", "WARN": "WARN", "FAIL": "FAIL"}[status]
    suffix = f"  -- {detail}" if detail else ""
    print(f"  [{icon}]  {name}{suffix}")


def _epsg_from_crs(crs_obj) -> int | None:
    """Resolve EPSG code from either a pyproj.CRS or a fiona CRS dict."""
    if crs_obj is None:
        return None
    try:
        return CRS(crs_obj).to_epsg()
    except Exception:
        return None


def audit_vector(
    name: str,
    path: Path,
    expected_epsg: int | None = None,
    required_cols: list[str] | None = None,
) -> None:
    if not path.exists():
        _record(name, "FAIL", f"not found: {path.relative_to(ROOT)}")
        return
    try:
        with fiona.open(path) as src:
            n = len(src)
            crs_epsg = _epsg_from_crs(src.crs)
            bbox = src.bounds
            props = list(src.schema["properties"].keys())
            geom_type = src.schema.get("geometry", "?")
    except Exception as exc:
        _record(name, "FAIL", str(exc))
        return

    issues: list[str] = []
    if n == 0:
        issues.append("0 features")
    if expected_epsg is not None and crs_epsg != expected_epsg:
        issues.append(f"CRS=EPSG:{crs_epsg} (expected EPSG:{expected_epsg})")
    if required_cols:
        missing = [c for c in required_cols if c not in props]
        if missing:
            issues.append(f"missing columns: {missing}")

    bbox_str = f"({bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f})"
    detail = f"n={n:,}  geom={geom_type}  EPSG:{crs_epsg}  bbox={bbox_str}"
    status = "WARN" if issues else "PASS"
    full_detail = f"{detail}  ISSUES: {'; '.join(issues)}" if issues else detail
    _record(name, status, full_detail)


def audit_gpkg(name: str, path: Path) -> None:
    """Inspect all layers inside a GeoPackage."""
    if not path.exists():
        _record(name, "FAIL", f"not found: {path.relative_to(ROOT)}")
        return
    try:
        layers = fiona.listlayers(path)
    except Exception as exc:
        _record(name, "FAIL", f"cannot list layers — {exc}")
        return

    print(f"\n  {name}  [{len(layers)} layer(s): {', '.join(layers)}]")
    for layer in layers:
        try:
            with fiona.open(path, layer=layer) as src:
                n = len(src)
                crs_epsg = _epsg_from_crs(src.crs)
                geom_type = src.schema.get("geometry", "?")
                bbox = src.bounds
        except Exception as exc:
            _record(f"  {name}/{layer}", "FAIL", str(exc))
            continue

        bbox_str = f"({bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f})"
        detail = f"n={n:,}  geom={geom_type}  EPSG:{crs_epsg}  bbox={bbox_str}"
        status = "PASS" if n > 0 else "WARN"
        _record(f"  {name}/{layer}", status, detail)


def audit_raster(name: str, path: Path, expected_res_m: float | None = None) -> None:
    if not path.exists():
        _record(name, "FAIL", f"not found: {path.relative_to(ROOT)}")
        return
    try:
        with rasterio.open(path) as src:
            crs_epsg = _epsg_from_crs(src.crs)
            res_x, res_y = src.res
            bounds = src.bounds
            nodata = src.nodata
            bands = src.count
            height, width = src.height, src.width
            # Sample one pixel from the centre to confirm data is readable
            cx, cy = width // 2, height // 2
            window = rasterio.windows.Window(cx, cy, 1, 1)
            val = float(src.read(1, window=window)[0, 0])
    except Exception as exc:
        _record(name, "FAIL", str(exc))
        return

    issues: list[str] = []
    if nodata is None:
        issues.append("no nodata value defined")
    if expected_res_m is not None and abs(res_x - expected_res_m) > 20:
        issues.append(f"resolution {res_x:.1f}m (expected ~{expected_res_m}m)")

    detail = (
        f"EPSG:{crs_epsg}  res={res_x:.0f}m×{res_y:.0f}m  "
        f"size={width}×{height}  bands={bands}  nodata={nodata}  centre={val:.1f}"
    )
    status = "WARN" if issues else "PASS"
    full_detail = f"{detail}  ISSUES: {'; '.join(issues)}" if issues else detail
    _record(name, status, full_detail)


def main() -> None:
    print("\n" + "=" * 60)
    print("  Agrivoltaic Screening Bavaria — Dataset Audit")
    print("=" * 60)

    # ── E1: CLC2018 ──────────────────────────────────────────────
    print("\nE1 — Agricultural land (CLC2018)")
    audit_vector(
        "CLC2018 shapefile",
        DATA / "E1_land_use" / "U2018_CLC2018_V2020_20u1.shp" / "U2018_CLC2018_V2020_20u1.shp",
        expected_epsg=3035,
        required_cols=["Code_18"],
    )

    # ── E2: Conservation areas ────────────────────────────────────
    print("\nE2 — Conservation areas (LfU Bayern)")
    e2 = DATA / "E2_conservation_areas"
    e2_layers = [
        ("Naturschutzgebiete (NSG)", "nsg_epsg25832_shp/nsg_epsg25832_shp.shp"),
        ("Nationalparke (NLP)", "nlp_epsg25832_shp/nlp_epsg25832_shp.shp"),
        ("Landschaftsschutzgebiete (LSG)", "lsg_epsg25832_shp/lsg_epsg25832_shp.shp"),
        ("Biosphärenreservate", "biosphaerenreservate_epsg25832_shp/biosphaerenreservate_epsg25832_shp.shp"),
        ("Naturparke", "naturparke_epsg25832_shp/naturparke_epsg25832_shp.shp"),
        ("Naturdenkmal – Flächen", "naturdenkmal_flaechig_epsg25832_shp/naturdenkmal_flaechig_epsg25832_shp.shp"),
        ("Naturdenkmal – Punkte", "naturdenkmal_punktfoermig_epsg25832_shp/naturdenkmal_punktfoermig_epsg25832_shp.shp"),
        ("Nationale Naturmonumente", "nationale_naturmonumente_epsg25832_shp/nationale_naturmonumente_epsg25832_shp.shp"),
        ("Landschaftsbestandteil – Flächen", "landschaftsbestandteil_flaechig_epsg25832_shp/landschaftsbestandteil_flaechig_epsg25832_shp.shp"),
        ("Landschaftsbestandteil – Punkte", "landschaftsbestandteil_punktfoermig_epsg25832_shp/landschaftsbestandteil_punktfoermig_epsg25832_shp.shp"),
    ]
    for label, rel in e2_layers:
        audit_vector(label, e2 / rel, expected_epsg=25832)

    # ── E3: Flood zones ───────────────────────────────────────────
    print("\nE3 — Flood zones (GeoPackage)")
    audit_gpkg(
        "hw_flaeche",
        DATA / "E3_flood_areas" / "hw_flaeche_gpkg" / "hw_flaeche.gpkg",
    )

    # ── E4: Water protection zones ────────────────────────────────
    print("\nE4 — Water protection zones")
    e4 = DATA / "E4_water_protection_ares"
    audit_vector("Trinkwasserschutzgebiete (TWSG)", e4 / "twsg_epsg25832_shp" / "twsg_epsg25832.shp", expected_epsg=25832)
    audit_vector("Heilquellenschutzgebiete (HQSG)", e4 / "hqsg_epsg25832_shp" / "hqsg_epsg25832.shp", expected_epsg=25832)

    # ── E5: DGM200 raster ─────────────────────────────────────────
    print("\nE5 — Terrain / slope (DGM200 raster)")
    audit_raster(
        "DGM200 ASC grid",
        DATA / "E5_slope" / "dgm200.utm32s.gridascii" / "dgm200" / "dgm200_utm32s.asc",
        expected_res_m=200,
    )

    # ── Summary ───────────────────────────────────────────────────
    n_pass = sum(1 for _, s, _ in _results if s == "PASS")
    n_warn = sum(1 for _, s, _ in _results if s == "WARN")
    n_fail = sum(1 for _, s, _ in _results if s == "FAIL")
    total = len(_results)

    print("\n" + "=" * 60)
    print(f"  {n_pass}/{total} PASS   {n_warn} WARN   {n_fail} FAIL")
    print("=" * 60)

    if n_fail:
        print("\nFailed -- immediate action required:")
        for name, status, detail in _results:
            if status == "FAIL":
                print(f"  [FAIL]  {name.strip()}: {detail}")
    if n_warn:
        print("\nWarnings -- review before processing:")
        for name, status, detail in _results:
            if status == "WARN":
                print(f"  [WARN]  {name.strip()}: {detail}")
    print()

    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
