#!/usr/bin/env python3
"""Verification script for processed data outputs.

Checks that every processed layer is readable, has correct CRS,
non-zero features, and bbox within Bavaria's extent.

Usage:
    uv run python scripts/verify_processed.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import fiona
import numpy as np
import rasterio
from pyproj import CRS

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "processed"
LAYERS_GPKG = OUT / "layers.gpkg"
SLOPE_TIF = OUT / "slope_class.tif"

# Bavaria bounding box in EPSG:25832 (generous margin)
BAV_XMIN, BAV_YMIN = 280000, 5230000
BAV_XMAX, BAV_YMAX = 870000, 5650000

EXPECTED_LAYERS = [
    "bavaria_boundary",
    "agricultural_land",
    "conservation_hard",
    "conservation_soft",
    "flood_zones",
    "water_protection",
]

_results: list[tuple[str, str, str]] = []


def _record(name: str, status: str, detail: str = "") -> None:
    _results.append((name, status, detail))
    icon = {"PASS": "OK  ", "WARN": "WARN", "FAIL": "FAIL"}[status]
    suffix = f"  -- {detail}" if detail else ""
    print(f"  [{icon}]  {name}{suffix}")


def _epsg(crs_obj) -> int | None:
    if crs_obj is None:
        return None
    try:
        return CRS(crs_obj).to_epsg()
    except Exception:
        return None


def _within_bavaria(bbox: tuple) -> bool:
    xmin, ymin, xmax, ymax = bbox
    return (
        xmin >= BAV_XMIN - 5000
        and ymin >= BAV_YMIN - 5000
        and xmax <= BAV_XMAX + 5000
        and ymax <= BAV_YMAX + 5000
    )


def check_gpkg() -> None:
    if not LAYERS_GPKG.exists():
        _record("layers.gpkg exists", "FAIL", "file not found")
        return
    _record("layers.gpkg exists", "PASS", f"{LAYERS_GPKG.stat().st_size / 1024**2:.1f} MB")

    try:
        found_layers = fiona.listlayers(LAYERS_GPKG)
    except Exception as exc:
        _record("layers.gpkg readable", "FAIL", str(exc))
        return
    _record("layers.gpkg readable", "PASS", f"layers: {found_layers}")

    missing = [l for l in EXPECTED_LAYERS if l not in found_layers]
    if missing:
        _record("expected layers present", "FAIL", f"missing: {missing}")
    else:
        _record("expected layers present", "PASS", f"all {len(EXPECTED_LAYERS)} layers found")

    for layer in EXPECTED_LAYERS:
        if layer not in found_layers:
            continue
        try:
            with fiona.open(LAYERS_GPKG, layer=layer) as src:
                n = len(src)
                crs_epsg = _epsg(src.crs)
                bbox = src.bounds
        except Exception as exc:
            _record(f"  layer/{layer}", "FAIL", str(exc))
            continue

        issues: list[str] = []
        if n == 0:
            issues.append("0 features")
        if crs_epsg != 25832:
            issues.append(f"CRS=EPSG:{crs_epsg} (expected 25832)")
        if not _within_bavaria(bbox):
            issues.append(f"bbox outside Bavaria: {tuple(round(v) for v in bbox)}")

        detail = f"n={n:,}  EPSG:{crs_epsg}  bbox=({bbox[0]:.0f},{bbox[1]:.0f},{bbox[2]:.0f},{bbox[3]:.0f})"
        status = "WARN" if issues else "PASS"
        full = f"{detail}  ISSUES: {'; '.join(issues)}" if issues else detail
        _record(f"  layer/{layer}", status, full)


def check_slope() -> None:
    if not SLOPE_TIF.exists():
        _record("slope_class.tif exists", "FAIL", "file not found")
        return

    size_mb = SLOPE_TIF.stat().st_size / 1024**2
    status = "PASS" if size_mb < 20 else "WARN"
    _record("slope_class.tif exists", status, f"{size_mb:.1f} MB")

    try:
        with rasterio.open(SLOPE_TIF) as src:
            crs_epsg = _epsg(src.crs)
            nodata = src.nodata
            # Sample a strip of pixels to check value range
            sample = src.read(1, window=rasterio.windows.Window(
                src.width // 4, src.height // 4,
                src.width // 2, src.height // 2,
            ))
            unique_vals = set(np.unique(sample).tolist())
            valid_vals = {0, 1, 2, 3, 4, 5, 6}
            bad_vals = unique_vals - valid_vals
    except Exception as exc:
        _record("slope_class.tif readable", "FAIL", str(exc))
        return

    issues: list[str] = []
    if crs_epsg != 25832:
        issues.append(f"CRS=EPSG:{crs_epsg} (expected 25832)")
    if nodata != 0:
        issues.append(f"nodata={nodata} (expected 0)")
    if bad_vals:
        issues.append(f"unexpected pixel values: {bad_vals}")
    if not (unique_vals & {1, 2, 3, 4, 5}):
        issues.append("no slope class values 1-5 found in sample")

    detail = f"EPSG:{crs_epsg}  nodata={nodata}  values in sample: {sorted(unique_vals)}"
    status = "WARN" if issues else "PASS"
    full = f"{detail}  ISSUES: {'; '.join(issues)}" if issues else detail
    _record("slope_class.tif readable", status, full)


def main() -> None:
    print("\n" + "=" * 60)
    print("  Agrivoltaic Screening Bavaria -- Processed Data Audit")
    print("=" * 60)

    print("\nGeoPackage (vector layers)")
    check_gpkg()

    print("\nSlope raster")
    check_slope()

    n_pass = sum(1 for _, s, _ in _results if s == "PASS")
    n_warn = sum(1 for _, s, _ in _results if s == "WARN")
    n_fail = sum(1 for _, s, _ in _results if s == "FAIL")
    total = len(_results)

    print("\n" + "=" * 60)
    print(f"  {n_pass}/{total} PASS   {n_warn} WARN   {n_fail} FAIL")
    print("=" * 60)

    if n_fail:
        print("\nFailed -- rerun preprocess.py:")
        for name, status, detail in _results:
            if status == "FAIL":
                print(f"  [FAIL]  {name.strip()}: {detail}")
    if n_warn:
        print("\nWarnings -- review before proceeding:")
        for name, status, detail in _results:
            if status == "WARN":
                print(f"  [WARN]  {name.strip()}: {detail}")
    print()

    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
