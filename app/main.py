"""Agrivoltaic Screening Map — Bavaria.

Interactive map showing exclusion layers for agrivoltaic site screening.
Toggle layers in the sidebar to see which areas are restricted.

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

# ── Layer config ──────────────────────────────────────────────────────────────

LAYER_STYLES: dict[str, dict] = {
    "bavaria_boundary": {
        "color": "#555555", "weight": 2, "fillOpacity": 0, "opacity": 0.9,
    },
    "agricultural_land": {
        "color": "#228B22", "weight": 0.3, "fillColor": "#90EE90", "fillOpacity": 0.55,
    },
    "conservation_hard": {
        "color": "#CC0000", "weight": 0.3, "fillColor": "#CC0000", "fillOpacity": 0.5,
    },
    "conservation_soft": {
        "color": "#FF8C00", "weight": 0.3, "fillColor": "#FF8C00", "fillOpacity": 0.4,
    },
    "flood_zones": {
        "color": "#1E90FF", "weight": 0.3, "fillColor": "#1E90FF", "fillOpacity": 0.5,
    },
    "water_protection": {
        "color": "#00CED1", "weight": 0.3, "fillColor": "#00CED1", "fillOpacity": 0.4,
    },
    "slope_excluded": {
        "color": "#8B4513", "weight": 0.3, "fillColor": "#8B4513", "fillOpacity": 0.5,
    },
    "non_agricultural_land": {
        "color": "#808080", "weight": 0, "fillColor": "#A9A9A9", "fillOpacity": 0.35,
    },
}

# Sidebar display label and default-on state for each toggleable layer
SIDEBAR_LAYERS: list[tuple[str, str, bool]] = [
    ("agricultural_land",     "E1  Agricultural land",          True),
    ("non_agricultural_land", "E6  Non-agricultural land",       False),
    ("conservation_hard",     "E2  Conservation — hard",         False),
    ("conservation_soft",     "E2  Conservation — soft",         False),
    ("flood_zones",           "E3  Flood zones (HQ100)",         False),
    ("water_protection",      "E4  Water protection zones",      False),
    ("slope_excluded",        "E5  Slope excluded (>25%)",       False),
]

LEGEND_ITEMS: list[tuple[str, str, str]] = [
    ("#90EE90", "E1 Agricultural land",         "eligible base"),
    ("#A9A9A9", "E6 Non-agricultural land",     "background exclusion"),
    ("#CC0000", "E2 Conservation (hard)",       "hard exclusion"),
    ("#FF8C00", "E2 Conservation (soft)",       "caution — case-by-case"),
    ("#1E90FF", "E3 Flood zones",               "hard exclusion"),
    ("#00CED1", "E4 Water protection",          "caution"),
    ("#8B4513", "E5 Slope >25%",                "hard exclusion"),
]


# ── Data loading (cached) ─────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading map layers...")
def _load_layers() -> dict[str, gpd.GeoDataFrame]:
    layers: dict[str, gpd.GeoDataFrame] = {}
    for name in LAYER_STYLES:
        layers[name] = gpd.read_file(LAYERS_GPKG, layer=name).to_crs(4326)
    return layers


@st.cache_data(show_spinner=False)
def _to_geojson(_gdf: gpd.GeoDataFrame, _name: str) -> str:
    # _name is unused but forces separate cache entries per layer
    return _gdf.to_json()


# ── Map builder ───────────────────────────────────────────────────────────────

def _build_map(layers: dict[str, gpd.GeoDataFrame], toggles: dict[str, bool]) -> folium.Map:
    m = folium.Map(
        location=[48.5, 11.5],
        zoom_start=7,
        tiles="CartoDB positron",
        prefer_canvas=True,
    )

    # Bavaria outline — always visible
    folium.GeoJson(
        _to_geojson(layers["bavaria_boundary"], "bavaria_boundary"),
        style_function=lambda _: LAYER_STYLES["bavaria_boundary"],
        name="Bavaria boundary",
        tooltip=None,
    ).add_to(m)

    # Toggleable layers — render in order (bottom to top)
    for key, label, _ in SIDEBAR_LAYERS:
        if not toggles.get(key, False):
            continue
        style = LAYER_STYLES[key]
        has_source = "source" in layers[key].columns
        folium.GeoJson(
            _to_geojson(layers[key], key),
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
        "Toggle layers to visualise exclusion zones over agricultural land. "
        "Based on Hauger et al. (2025), *Renewable Energy* 247."
    )

    layers = _load_layers()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Layer Controls")

        st.markdown("**Base**")
        toggles: dict[str, bool] = {}
        for key, label, default in SIDEBAR_LAYERS[:2]:
            toggles[key] = st.checkbox(label, value=default)

        st.markdown("**Exclusion layers**")
        for key, label, default in SIDEBAR_LAYERS[2:]:
            toggles[key] = st.checkbox(label, value=default)

        st.divider()
        st.markdown(
            "**Hard exclusions** (red/brown/blue): area removed from consideration.  \n"
            "**Soft flags** (orange/teal): require case-by-case review.  \n"
            "Hover over features for layer details."
        )
        st.divider()
        st.caption(
            "Data sources: Copernicus CLC2018 (E1), LfU Bayern (E2–E4), "
            "BKG DGM200 (E5), derived from E1 (E6). All layers EPSG:25832, "
            "geometry simplified at 25 m for display."
        )

    # ── Map ──────────────────────────────────────────────────────────────────
    m = _build_map(layers, toggles)
    st_folium(m, use_container_width=True, height=680, returned_objects=[])

    # ── Legend ───────────────────────────────────────────────────────────────
    st.markdown(_legend_html(), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
