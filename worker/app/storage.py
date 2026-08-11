"""Cloudinary image storage."""

from pathlib import Path

import cloudinary
import cloudinary.uploader

from .config import get_settings


def upload_image(path: str | Path, public_id: str) -> tuple[str, str]:
    settings = get_settings()
    if not all((settings.cloudinary_cloud_name, settings.cloudinary_api_key, settings.cloudinary_api_secret)):
        raise RuntimeError("Variables Cloudinary incompletes")
    cloudinary.config(cloud_name=settings.cloudinary_cloud_name, api_key=settings.cloudinary_api_key, api_secret=settings.cloudinary_api_secret, secure=True)
    result = cloudinary.uploader.upload(str(path), folder="ndvi-benin", public_id=public_id, overwrite=True, resource_type="image", format="jpg")
    image_url = result["secure_url"]
    thumbnail_url = cloudinary.CloudinaryImage(f"ndvi-benin/{public_id}").build_url(width=400, height=286, crop="fill", secure=True, format="jpg")
    return image_url, thumbnail_url
