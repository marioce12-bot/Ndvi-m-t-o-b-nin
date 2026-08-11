"""USGS eVIIRS product registry."""

BASE_URL = "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/africa/west/pentadal/eviirs/ndvi"

PRODUCTS = {
    "ndvi": {
        "label": "NDVI",
        "directory": f"{BASE_URL}/temporallysmoothedndvi/downloads/pentadal/",
        "pattern": r"wa(?P<yy>\d{2})(?P<pp>\d{2})\.zip",
    },
    "anomaly": {
        "label": "NDVI anomalie",
        "directory": f"{BASE_URL}/percentofmean/downloads/pentadal/",
        "pattern": r"wa(?P<yy>\d{2})(?P<pp>\d{2})pct\.zip",
    },
}
