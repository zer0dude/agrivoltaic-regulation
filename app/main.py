"""Agrivoltaic Screening Map — Bavaria.

Interactive map for agrivoltaic site screening. Use presets for a quick view of
eligible land after exclusions, or toggle individual layers to explore manually.

Run:
    uv run streamlit run app/main.py
"""

from __future__ import annotations

from pathlib import Path

import folium
import geopandas as gpd
import streamlit as st
from streamlit_folium import st_folium

LAYERS_GPKG = Path(__file__).resolve().parent.parent / "data" / "processed" / "layers.gpkg"

# ── Layer styles ──────────────────────────────────────────────────────────────

LAYER_STYLES: dict[str, dict] = {
    "bavaria_boundary": {
        "color": "#555555", "weight": 2, "fillOpacity": 0, "opacity": 0.9,
    },
    "agricultural_land": {
        "color": "#228B22", "weight": 0.3, "fillColor": "#90EE90", "fillOpacity": 0.55,
    },
    "eligible_hard_only": {
        "color": "#2E7D32", "weight": 0.5, "fillColor": "#66BB6A", "fillOpacity": 0.75,
    },
    "eligible_all_excl": {
        "color": "#1B5E20", "weight": 0.5, "fillColor": "#2E7D32", "fillOpacity": 0.75,
    },
    "non_agricultural_land": {
        "color": "#808080", "weight": 0, "fillColor": "#A9A9A9", "fillOpacity": 0.35,
    },
    "conservation_hard": {
        "color": "#CC0000", "weight": 0.3, "fillColor": "#CC0000", "fillOpacity": 0.5,
    },
    "flood_zones": {
        "color": "#1E90FF", "weight": 0.3, "fillColor": "#1E90FF", "fillOpacity": 0.5,
    },
    "slope_excluded": {
        "color": "#8B4513", "weight": 0.3, "fillColor": "#8B4513", "fillOpacity": 0.5,
    },
    "conservation_soft": {
        "color": "#FF8C00", "weight": 0.3, "fillColor": "#FF8C00", "fillOpacity": 0.4,
    },
    "water_protection": {
        "color": "#00CED1", "weight": 0.3, "fillColor": "#00CED1", "fillOpacity": 0.4,
    },
    "road_setback": {
        "color": "#E91E63", "weight": 0.3, "fillColor": "#E91E63", "fillOpacity": 0.45,
    },
    "rail_setback": {
        "color": "#673AB7", "weight": 0.3, "fillColor": "#673AB7", "fillOpacity": 0.45,
    },
    "water_setback": {
        "color": "#1565C0", "weight": 0.3, "fillColor": "#1565C0", "fillOpacity": 0.45,
    },
    "forest_setback": {
        "color": "#33691E", "weight": 0.3, "fillColor": "#33691E", "fillOpacity": 0.45,
    },
}

# ── Layer groups ──────────────────────────────────────────────────────────────

CONTEXT_LAYERS: list[tuple[str, str, bool]] = [
    ("non_agricultural_land", "Non-agricultural land", False),
]

HARD_EXCL_LAYERS: list[tuple[str, str, bool]] = [
    ("conservation_hard", "Conservation — strict",  False),
    ("flood_zones",       "Flood zones (HQ100)",    False),
    ("slope_excluded",    "Slope exclusion (>25%)", False),
]

SOFT_EXCL_LAYERS: list[tuple[str, str, bool]] = [
    ("conservation_soft", "Conservation — caution",    False),
    ("water_protection",  "Water protection zones",    False),
    ("road_setback",      "Road setback (40/20 m)",    False),
    ("rail_setback",      "Railway setback (40 m)",    False),
    ("water_setback",     "Water body setback (50 m)", False),
    ("forest_setback",    "Forest setback (30 m)",     False),
]

ALL_OVERLAY_LAYERS = CONTEXT_LAYERS + HARD_EXCL_LAYERS + SOFT_EXCL_LAYERS

LEGEND_ITEMS: list[tuple[str, str, str]] = [
    ("#90EE90", "Agricultural land",             "candidate base (manual mode)"),
    ("#66BB6A", "Eligible — hard excl. removed", "preset"),
    ("#2E7D32", "Eligible — all excl. removed",  "preset"),
    ("#A9A9A9", "Non-agricultural land",          "background context"),
    ("#CC0000", "Conservation — strict",          "hard exclusion"),
    ("#1E90FF", "Flood zones (HQ100)",            "hard exclusion"),
    ("#8B4513", "Slope >25%",                     "hard exclusion"),
    ("#FF8C00", "Conservation — caution",         "soft / case-by-case"),
    ("#00CED1", "Water protection",               "soft / case-by-case"),
    ("#E91E63", "Road setback",                   "soft / indicative setback"),
    ("#673AB7", "Railway setback",                "soft / indicative setback"),
    ("#1565C0", "Water body setback",             "soft / indicative setback"),
    ("#33691E", "Forest setback",                 "soft / indicative setback"),
]


# ── Data loading (cached) ─────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading map layers...")
def _load_layers(gpkg_mtime: float) -> dict[str, gpd.GeoDataFrame]:
    layers: dict[str, gpd.GeoDataFrame] = {}
    for name in LAYER_STYLES:
        layers[name] = gpd.read_file(LAYERS_GPKG, layer=name).to_crs(4326)
    return layers


@st.cache_data(show_spinner=False)
def _to_geojson(_gdf: gpd.GeoDataFrame, name: str, gpkg_mtime: float) -> str:
    return _gdf.to_json()


# ── Map builder ───────────────────────────────────────────────────────────────

def _build_map(
    layers: dict[str, gpd.GeoDataFrame],
    toggles: dict[str, bool],
    gpkg_mtime: float,
    preset: str | None,
) -> folium.Map:
    m = folium.Map(
        location=[48.5, 11.5],
        zoom_start=7,
        tiles="CartoDB positron",
        prefer_canvas=True,
    )

    # Bavaria outline — always visible
    folium.GeoJson(
        _to_geojson(layers["bavaria_boundary"], "bavaria_boundary", gpkg_mtime),
        style_function=lambda _: LAYER_STYLES["bavaria_boundary"],
        name="Bavaria boundary",
        tooltip=None,
    ).add_to(m)

    # Candidate area: preset layer OR raw agricultural land
    if preset == "hard_only":
        folium.GeoJson(
            _to_geojson(layers["eligible_hard_only"], "eligible_hard_only", gpkg_mtime),
            style_function=lambda _: LAYER_STYLES["eligible_hard_only"],
            name="Eligible land (hard excl. removed)",
            tooltip=folium.GeoJsonTooltip(fields=["Code_18"], aliases=["Land type:"]),
        ).add_to(m)
    elif preset == "all_excl":
        folium.GeoJson(
            _to_geojson(layers["eligible_all_excl"], "eligible_all_excl", gpkg_mtime),
            style_function=lambda _: LAYER_STYLES["eligible_all_excl"],
            name="Eligible land (all excl. removed)",
            tooltip=folium.GeoJsonTooltip(fields=["Code_18"], aliases=["Land type:"]),
        ).add_to(m)
    else:
        folium.GeoJson(
            _to_geojson(layers["agricultural_land"], "agricultural_land", gpkg_mtime),
            style_function=lambda _: LAYER_STYLES["agricultural_land"],
            name="Agricultural land",
        ).add_to(m)

    # Overlay layers — rendered in order on top of candidate area
    for key, label, _ in ALL_OVERLAY_LAYERS:
        if not toggles.get(key, False):
            continue
        style = LAYER_STYLES[key]
        has_source = "source" in layers[key].columns
        folium.GeoJson(
            _to_geojson(layers[key], key, gpkg_mtime),
            style_function=lambda _, s=style: s,
            tooltip=(
                folium.GeoJsonTooltip(fields=["source"], aliases=["Type:"])
                if has_source else None
            ),
            name=label,
        ).add_to(m)

    return m


# ── Legend HTML ───────────────────────────────────────────────────────────────

def _legend_html() -> str:
    rows = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">'
        f'<div style="width:14px;height:14px;background:{colour};border-radius:2px;'
        f'flex-shrink:0"></div>'
        f'<span style="font-size:12px"><b>{label}</b> — {note}</span></div>'
        for colour, label, note in LEGEND_ITEMS
    )
    return (
        '<div style="background:white;padding:10px 12px;border-radius:6px;'
        'border:1px solid #ccc;line-height:1.5">'
        f"<b style='font-size:13px'>Legend</b><br>{rows}</div>"
    )


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Agrivoltaic Screening — Bavaria",
        page_icon=":sunny:",
        layout="wide",
    )

    st.title("Agrivoltaic Screening Map — Bavaria")
    st.caption(
        "GIS-based site screening for agrivoltaic installations. "
        "Use presets for an instant view of eligible land, or toggle layers manually. "
        "Based on [Hauger et al. (2025), *Renewable Energy* 247](https://doi.org/10.1016/j.renene.2025.123039)."
    )

    gpkg_mtime = LAYERS_GPKG.stat().st_mtime
    layers = _load_layers(gpkg_mtime)

    if "preset" not in st.session_state:
        st.session_state["preset"] = None

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Screening Controls")

        # Candidate area
        st.markdown("**Candidate Area**")
        st.markdown(
            '<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">'
            '<div style="width:14px;height:14px;background:#90EE90;border:1px solid #228B22;'
            'border-radius:2px;flex-shrink:0"></div>'
            '<span style="font-size:13px">Agricultural land</span></div>',
            unsafe_allow_html=True,
        )
        toggles: dict[str, bool] = {}
        toggles["non_agricultural_land"] = st.checkbox(
            "Display Non-agricultural land", value=False,
        )

        # Presets
        st.markdown("**Presets**")
        st.caption("Pre-computed")
        preset = st.session_state.get("preset", None)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(
                "Agricultural land with HARD exclusions removed",
                type="primary" if preset == "hard_only" else "secondary",
                use_container_width=True,
            ):
                st.session_state["preset"] = "hard_only"
                st.rerun()
        with c2:
            if st.button(
                "Agricultural land with HARD & SOFT exclusions removed",
                type="primary" if preset == "all_excl" else "secondary",
                use_container_width=True,
            ):
                st.session_state["preset"] = "all_excl"
                st.rerun()
        with c3:
            if st.button(
                "Reset",
                type="primary" if preset is None else "secondary",
                use_container_width=True,
            ):
                st.session_state["preset"] = None
                st.rerun()

        # Hard exclusions
        st.markdown("**Hard Exclusions**")
        for key, label, default in HARD_EXCL_LAYERS:
            toggles[key] = st.checkbox(label, value=default)

        # Soft exclusions
        st.markdown("**Soft Exclusions**")
        for key, label, default in SOFT_EXCL_LAYERS:
            toggles[key] = st.checkbox(label, value=default)

        st.divider()
        st.markdown(
            "**Hard exclusions**: legally or technically not feasible.  \n"
            "**Soft exclusions**: require case-by-case review.  \n"
            "Setbacks are indicative distances, not statutory exclusions.  \n"
            "Hover over features for layer details."
        )
        st.divider()
        st.caption(
            "Data: Copernicus CLC2018, LfU Bayern, BKG DGM200 + DLM250 (2024), "
            "Eurostat NUTS 2021. All layers EPSG:25832, simplified at 25 m."
        )

    # ── Map ──────────────────────────────────────────────────────────────────
    preset = st.session_state.get("preset", None)
    m = _build_map(layers, toggles, gpkg_mtime, preset)
    st_folium(m, use_container_width=True, height=680, returned_objects=[])

    # ── Legend ───────────────────────────────────────────────────────────────
    st.markdown(_legend_html(), unsafe_allow_html=True)

    # ── Info panel ───────────────────────────────────────────────────────────
    with st.expander("About this tool", expanded=False):
        st.markdown("""
**Agrivoltaic Site Screening — Bavaria**

This tool identifies agricultural land in Bavaria with low conflict potential for
agrivoltaic installations (combined solar energy and farming). It supports preliminary
landowner outreach — it is not a permit readiness assessment or grid capacity guarantee.

**Methodology:** [Hauger et al. (2025), *Renewable Energy* 247](https://doi.org/10.1016/j.renene.2025.123039).

| Layer group | Source |
|---|---|
| Agricultural land | Copernicus CLC2018 |
| Conservation areas | LfU Bayern |
| Flood zones | LfU Bayern |
| Water protection | LfU Bayern |
| Slope (terrain) | BKG DGM200 |
| Infrastructure setbacks | BKG DLM250 (2024) |
| Bavaria boundary | Eurostat NUTS 2021 |

**Hard exclusions** are areas where agrivoltaic development is legally or technically
not feasible: strict conservation zones (Naturschutzgebiete, Nationalparke, Naturdenkmal),
flood plains (HQ100), and slopes above 25%.

**Soft exclusions** require case-by-case review: landscape conservation areas, water
protection zones (zone boundaries approximate, no zone-level subdivision available), and
infrastructure setback distances (indicative — not statutory exclusions under German law).

**Limitations:** [Hauger et al. (2025)](https://doi.org/10.1016/j.renene.2025.123039) identify further criteria such as proximity to grid connection infrastructure
and agricultural land type (crop synergy) as highly important suitability criteria. Such data is difficult to access, especially at scale. The screening results therefore reflect
exclusion constraints only, not full suitability scoring as described in the paper.

---
*Made by Brian Jin ([brianjin150@gmail.com](mailto:brianjin150@gmail.com)) for educational purposes.*
        """)


if __name__ == "__main__":
    main()
