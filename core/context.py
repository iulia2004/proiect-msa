from django.conf import settings


def globals(request):
    return {
        "google_enabled": bool(settings.GOOGLE_CLIENT_ID),
        "vapid_public_key": settings.VAPID_PUBLIC_KEY,
    }
