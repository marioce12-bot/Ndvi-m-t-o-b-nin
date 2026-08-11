"""Raster clipping, masking, and decoding."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask


def process_raster(
    raster_path: str | Path,
    product: str,
    boundary_path: str | Path,
) -> tuple[np.ma.MaskedArray, rasterio.Affine]:
    """Clip and decode one USGS eVIIRS raster to Benin departments."""
    if product not in {"ndvi", "anomaly"}:
        raise ValueError(f"Produit inconnu: {product}")

    boundaries = gpd.read_file(boundary_path).to_crs("EPSG:4326")
    if len(boundaries) != 12 or (~boundaries.geometry.is_valid).any():
        raise ValueError("Les limites ADM1 du Benin doivent contenir 12 geometries valides")

    with rasterio.open(raster_path) as source:
        if source.crs != rasterio.CRS.from_epsg(4326):
            raise ValueError(f"CRS raster inattendu: {source.crs}")
        clipped, transform = mask(source, boundaries.geometry, crop=True, filled=False)

    raw = clipped[0].astype(np.float32)
    invalid = np.ma.getmaskarray(clipped[0])
    # USGS documents 255 as nodata and 201..255 as invalid NDVI values.
    # DN == 0 is the interim cloud/quality mask present in both current products.
    invalid |= raw == 0
    if product == "ndvi":
        invalid |= raw >= 201
        values = (raw - 100) / 100
    else:
        # Percent of Mean is already expressed directly in percent; DN 200 is valid.
        values = raw
    return np.ma.masked_array(values, mask=invalid), transform
