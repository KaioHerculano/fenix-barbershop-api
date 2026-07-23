import json
import logging
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


def resend_payload(message):
    return {
        "from": os.getenv(
            "RESEND_FROM_EMAIL", "Fenix BarberShop <onboarding@resend.dev>"
        ),
        "to": [message["to"]],
        "subject": message["subject"],
        "html": message["html"],
        "text": message["text"],
    }


def send_email(message):
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY is not configured")
        return {"sent": False, "reason": "missing_api_key"}

    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(resend_payload(message)).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        logger.exception("Resend rejected email with status %s", exc.code)
        return {"sent": False, "reason": "provider_error", "status": exc.code}
    except URLError:
        logger.exception("Resend email request failed")
        return {"sent": False, "reason": "network_error"}
