from collections import defaultdict

from django.core.management.base import BaseCommand
from django.utils import timezone

from core import push
from core.models import CareTask


class Command(BaseCommand):
    help = "Send a Web Push notification for every due care task (run every 15 minutes)"

    def handle(self, *args, **opts):
        now = timezone.localtime()
        today = now.date()
        if now.hour < 8:  # no notifications at night
            return
        tasks = (CareTask.objects.filter(active=True, next_due__lte=today)
                 .exclude(last_notified=today).select_related("owner", "plant", "pet"))
        by_user = defaultdict(list)
        for t in tasks:
            by_user[t.owner].append(t)
        for user, items in by_user.items():
            body = "; ".join(f"{t.title} – {t.target_name}" for t in items[:5])
            if len(items) > 5:
                body += f" (+{len(items) - 5})"
            if push.send_to_user(user, f"De făcut azi: {len(items)}", body, "/"):
                CareTask.objects.filter(pk__in=[t.pk for t in items]).update(last_notified=today)
                self.stdout.write(f"Notified {user}: {len(items)} tasks")
