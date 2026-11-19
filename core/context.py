from django.conf import settings


NAV_SECTIONS = [("/plante", "plants"), ("/animale", "pets"), ("/scan", "pets"), ("/forum", "forum")]


def globals(request):
    section = "home" if request.path == "/" else ""
    for prefix, name in NAV_SECTIONS:
        if request.path.startswith(prefix):
            section = name
    return {
        "google_enabled": bool(settings.GOOGLE_CLIENT_ID),
        "vapid_public_key": settings.VAPID_PUBLIC_KEY,
        "nav_section": section,
    }
