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
    "COUFFO": (0.88, 7.72),
    "PLATEAU": (3.25, 7.72),
    "OUEME": (3.25, 6.42),
    "MONO": (0.96, 6.82),
    "ATLANTIQUE": (1.12, 6.16),
    "LITTORAL": (3.12, 6.04),
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
    # Keep the reference aspect ratio while giving the map and lower-left legend
    # nearly the full canvas. The legend coordinates below are derived from this axis.
    ax = fig.add_axes((0.032, 0.072, 0.936, 0.886))
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
            connectionstyle = "angle,angleA=0,angleB=90" if name == "ATLANTIQUE" else "angle"
            # Route ATLANTIQUE rightward first, then vertically upward into
            # its polygon, matching the annotated reference and clearing MONO.
            anchor = (2.18, 6.40) if name == "ATLANTIQUE" else (point.x, point.y)
            ax.annotate(name, xy=anchor, xytext=(x, y), fontsize=10, fontweight="normal", ha="center", va="center", arrowprops={"arrowstyle": "-", "connectionstyle": connectionstyle, "color": "black", "lw": 0.75, "shrinkA": 0, "shrinkB": 0})
        else:
            point = row.geometry.representative_point()
            ax.text(point.x, point.y, name, fontsize=10, fontweight="normal", ha="center", va="center")

    ax.set_xlim(-3.5, 8.5)
    ax.set_ylim(5.6, 13.6)
    ax.set_xticks(range(-3, 9))
    ax.set_yticks(range(6, 14))
    ax.tick_params(labelsize=11, direction="out", top=True, right=True, labeltop=True, labelright=True)
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
        spine.set_color("black")
    ax.set_xlabel("")
    ax.set_ylabel("")
    fig.text(
        0.5,
        0.935,
        "Indice Differentiel Normalise de Vegetation" if product == "ndvi" else "Anomalie de l'Indice Differentiel Normalise de Vegetation",
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
    )
    fig.text(0.5, 0.895, f"eVIIRS 375m, Pentade {pentade_num} ({pentade_label(year, pentade_num)})", ha="center", va="center", fontsize=15)

    if logo_path and Path(logo_path).exists():
        image = plt.imread(logo_path)
        ax.add_artist(AnnotationBbox(OffsetImage(image, zoom=0.16), (-2.72, 12.93), frameon=True, bboxprops={"facecolor": "white", "edgecolor": "#333333", "linewidth": 0.8, "boxstyle": "round,pad=0.35"}, pad=0.15))
    else:
        ax.text(-2.72, 12.93, "LOGO", fontsize=12, fontweight="bold", color="#1E7A1E", ha="center", va="center", bbox={"facecolor": "white", "edgecolor": "#333333", "pad": 8})

    # Convert the requested data-space box (-3..1, 6.3..7.8) to figure space.
    xmin, xmax = -3.5, 8.5
    ymin, ymax = 5.6, 13.6
    ax_left, ax_bottom, ax_width, ax_height = ax.get_position().bounds
    def data_to_figure(x: float, y: float) -> tuple[float, float]:
        return (ax_left + ax_width * (x - xmin) / (xmax - xmin), ax_bottom + ax_height * (y - ymin) / (ymax - ymin))

    # Compact box matching the reference: it stays below Couffo/Plateau
    # leaders and above the coastal labels and their horizontal callouts.
    legend_left, legend_bottom = data_to_figure(-3.18, 6.48)
    legend_right, legend_top = data_to_figure(0.55, 7.27)
    legend_ax = fig.add_axes(
        (legend_left, legend_bottom, legend_right - legend_left, legend_top - legend_bottom),
        facecolor="white",
        frameon=True,
        zorder=10,
    )
    legend_ax.patch.set_alpha(1.0)
    gradient = np.linspace(norm.vmin, norm.vmax, 512).reshape(1, -1)
    legend_ax.imshow(gradient, aspect="auto", cmap=cmap, norm=norm)
    legend_ax.set_yticks([])
    legend_ax.set_xlim(0, 511)
    legend_ax.set_ylim(-0.43, 1.0)
    if product == "ndvi":
        ticks = np.arange(0.1, 1.0, 0.1)
        labels = ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9"]
        legend_ax.set_xticks(np.linspace(0, 511, len(ticks)), labels=labels, fontsize=9)
        legend_ax.tick_params(axis="x", pad=1)
        legend_ax.text(0.02, -0.26, "Clairsemee", transform=legend_ax.transAxes, fontsize=9, fontweight="bold", ha="left", va="top")
        legend_ax.text(0.50, -0.26, "Moderee", transform=legend_ax.transAxes, fontsize=9, fontweight="bold", ha="center", va="top")
        legend_ax.text(0.98, -0.26, "Dense", transform=legend_ax.transAxes, fontsize=9, fontweight="bold", ha="right", va="top")
        legend_ax.text(0.0, 1.05, "NDVI", transform=legend_ax.transAxes, fontsize=10, fontweight="bold", ha="left", va="bottom")
    else:
        ticks = [80, 90, 100, 110, 120, 150]
        positions = [(tick - norm.vmin) / (norm.vmax - norm.vmin) * 511 for tick in ticks]
        legend_ax.set_xticks(positions, labels=["<80", "90", "100", "110", "120", "150"], fontsize=9)
        legend_ax.tick_params(axis="x", pad=1)
        legend_ax.text(0.02, -0.26, "Faible", transform=legend_ax.transAxes, fontsize=9, fontweight="bold", ha="left", va="top")
        legend_ax.text(0.50, -0.26, "Normal", transform=legend_ax.transAxes, fontsize=9, fontweight="bold", ha="center", va="top")
        legend_ax.text(0.98, -0.26, "Fort", transform=legend_ax.transAxes, fontsize=9, fontweight="bold", ha="right", va="top")
        legend_ax.text(0.0, 1.05, "NDVI anomalie (%)", transform=legend_ax.transAxes, fontsize=10, fontweight="bold", ha="left", va="bottom")
    for spine in legend_ax.spines.values():
        spine.set_visible(False)
    # Keep every legend label inside the opaque block and above leader lines.
    legend_ax.set_clip_on(False)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, format="jpg", dpi=300, facecolor="white", pil_kwargs={"quality": 92})
    plt.close(fig)
    return output
