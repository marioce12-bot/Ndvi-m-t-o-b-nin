"""EmailJS notifications."""

import logging

import requests

from .config import get_settings

logger = logging.getLogger(__name__)


def notify(product_label: str, pentade_label: str, image_url: str, status_text: str, recipient_email: str) -> None:
    settings = get_settings()
    required = (settings.emailjs_service_id, settings.emailjs_template_id, settings.emailjs_public_key, settings.emailjs_private_key)
    if all(required):
        payload = {"service_id": settings.emailjs_service_id, "template_id": settings.emailjs_template_id, "user_id": settings.emailjs_public_key, "accessToken": settings.emailjs_private_key, "template_params": {"product_label": product_label, "pentade_label": pentade_label, "image_url": image_url, "status_text": status_text, "recipient_email": recipient_email}}
        try:
            response = requests.post("https://api.emailjs.com/api/v1.0/email/send", json=payload, timeout=10)
            response.raise_for_status()
        except requests.RequestException:
            logger.warning("Echec notification EmailJS", exc_info=True)
    else:
        logger.warning("EmailJS non configure; notification ignoree")
