"""Cartographic JPEG rendering."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.offsetbox import AnnotationBbox, OffsetImage

from .pentades import pentade_label

NDVI_COLORS = ["#8B6914", "#C8A951", "#E8DCA0", "#B8D68A", "#5DA832", "#1E7A1E"]
ANOMALY_COLORS = ["#8B6914", "#C8A951", "#E8DCA0", "#B8D68A", "#5DA832", "#1E7A1E"]
DEPARTMENT_LABEL_POSITIONS = {
    "COUFFO": (1.30, 7.55),
    "PLATEAU": (3.15, 8.05),
    "OUEME": (3.25, 7.05),
    "MONO": (1.05, 6.75),
    "ATLANTIQUE": (1.75, 6.55),
    "LITTORAL": (2.55, 6.15),
}


def _extent(transform: object, shape: tuple[int, int]) -> tuple[float, float, float, float]:
    height, width = shape
    left = transform.c
    top = transform.f
    right = left + width * transform.a
    bottom = top + height * transform.e
    return left, right, bottom, top


def render_map(
    values: np.ma.MaskedArray,
    transform: object,
    product: str,
    year: int,
    pentade_num: int,
    boundary_path: str | Path,
    output_path: str | Path,
    logo_path: str | Path | None = None,
) -> Path:
    """Render one product using the fixed Météo Bénin-style layout."""
    if product not in {"ndvi", "anomaly"}:
        raise ValueError(f"Produit inconnu: {product}")
    boundaries = gpd.read_file(boundary_path).to_crs("EPSG:4326")
    fig = plt.figure(figsize=(14, 9.85), dpi=300, facecolor="white")
    ax = fig.add_axes((0.08, 0.09, 0.84, 0.73))
    cmap = LinearSegmentedColormap.from_list("ndvi_benin", NDVI_COLORS if product == "ndvi" else ANOMALY_COLORS)
    norm = Normalize(0.1, 0.9) if product == "ndvi" else Normalize(50, 150)
    ax.imshow(values, extent=_extent(transform, values.shape), origin="upper", cmap=cmap, norm=norm, interpolation="nearest")
    boundaries.boundary.plot(ax=ax, color="black", linewidth=0.8, zorder=3)
    country = boundaries.union_all()
    gpd.GeoSeries([country], crs="EPSG:4326").boundary.plot(ax=ax, color="black", linewidth=1.5, zorder=4)

    for _, row in boundaries.iterrows():
        name = row["Nom_Dept"]
        if name in DEPARTMENT_LABEL_POSITIONS:
            x, y = DEPARTMENT_LABEL_POSITIONS[name]
            point = row.geometry.representative_point()
            ax.annotate(name, xy=(point.x, point.y), xytext=(x, y), fontsize=10, fontweight="bold", ha="center", arrowprops={"arrowstyle": "-", "connectionstyle": "angle", "color": "black", "lw": 0.7})
        else:
            point = row.geometry.representative_point()
            ax.text(point.x, point.y, name, fontsize=10, fontweight="bold", ha="center", va="center")

    ax.set_xlim(-3.5, 8.5)
    ax.set_ylim(5.6, 13.6)
    ax.set_xticks(range(-3, 9))
    ax.set_yticks(range(6, 14))
    ax.tick_params(labelsize=11, direction="out", top=True, right=True, labeltop=True, labelright=True)
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
        spine.set_color("black")
    ax.set_xlabel("Longitude", fontsize=11)
    ax.set_ylabel("Latitude", fontsize=11)
    fig.text(
        0.5,
        0.955,
        "Indice Differentiel Normalise de Vegetation" if product == "ndvi" else "Anomalie de l'Indice Differentiel Normalise de Vegetation",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
    )
    fig.text(0.5, 0.925, f"eVIIRS 375m, {pentade_label(year, pentade_num)}", ha="center", va="center", fontsize=15)

    if logo_path and Path(logo_path).exists():
        image = plt.imread(logo_path)
        ax.add_artist(AnnotationBbox(OffsetImage(image, zoom=0.12), (-3.2, 13.3), frameon=False))
    else:
        ax.text(-3.2, 13.3, "LOGO", fontsize=12, fontweight="bold", color="#1E7A1E", ha="center", va="center")

    legend_ax = fig.add_axes((0.18, 0.045, 0.45, 0.035))
    gradient = np.linspace(norm.vmin, norm.vmax, 512).reshape(1, -1)
    legend_ax.imshow(gradient, aspect="auto", cmap=cmap, norm=norm)
    legend_ax.set_yticks([])
    if product == "ndvi":
        ticks = np.arange(0.1, 1.0, 0.1)
        labels = ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9"]
        legend_ax.set_xticks(np.linspace(0, 511, len(ticks)), labels=labels, fontsize=9)
        legend_ax.set_xlabel("Clairsemee                         Moderee                         Dense", fontsize=11, fontweight="bold", labelpad=8)
        legend_ax.set_title("NDVI", fontsize=12, fontweight="bold", loc="left", pad=8)
    else:
        ticks = [80, 90, 100, 110, 120, 150]
        positions = [(tick - norm.vmin) / (norm.vmax - norm.vmin) * 511 for tick in ticks]
        legend_ax.set_xticks(positions, labels=["<80", "90", "100", "110", "120", "150"], fontsize=9)
        legend_ax.set_xlabel("Faible                                  Normal                                  Fort", fontsize=11, fontweight="bold", labelpad=8)
        legend_ax.set_title("NDVI anomalie (%)", fontsize=12, fontweight="bold", loc="left", pad=8)
    for spine in legend_ax.spines.values():
        spine.set_visible(False)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, format="jpg", dpi=300, facecolor="white", pil_kwargs={"quality": 92})
    plt.close(fig)
    return output
