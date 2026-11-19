import json
import logging

from django.conf import settings
from pywebpush import WebPushException, webpush

log = logging.getLogger(__name__)


def send_to_user(user, title, body, url="/"):
    """Send a Web Push notification to every device of the user. Returns how many were sent."""
    if not settings.VAPID_PRIVATE_KEY:
        log.warning("VAPID keys not configured - no push sent")
        return 0
    sent = 0
    for sub in user.push_subscriptions.all():
        try:
            webpush(
                subscription_info={"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_EMAIL},  # fresh dict every call (pywebpush mutates it)
            )
            sent += 1
        except WebPushException as e:
            status = getattr(e.response, "status_code", None)
            if status in (404, 410):
                sub.delete()  # subscription expired
            else:
                log.warning("Push failed: %s", e)
        except Exception:
            log.exception("Push failed")
    return sent
