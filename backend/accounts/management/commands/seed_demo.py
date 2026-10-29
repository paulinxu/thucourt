import os
from datetime import datetime, timedelta
from uuid import uuid4

from accounts.models import User, VerificationRequest
from community.models import BehaviorRating, Friendship, Message, TennisFeedback
from community.services import pair_key
from courts.models import Area, Posting, Slot
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from matches.models import Match
from matches.services import decide_match, submit_match


class Command(BaseCommand):
    help = "Create synthetic demo users and upcoming court data. Safe to rerun; existing passwords are not reset."

    def handle(self, *args, **options):
        if not settings.DEBUG or not settings.DEMO_MODE:
            raise CommandError("Demo seeding requires DEBUG=true and DEMO_MODE=true.")
        password = os.environ.get("DEMO_PASSWORD", "court-demo-2026")
        users = []
        for index, (username, name, level) in enumerate(
            [
                ("alice", "林间发球", 3.0),
                ("bob", "底线漫游者", 3.5),
                ("carol", "网前小鹿", 2.5),
                ("dave", "追风正手", 4.0),
                ("pending", "新来的球友", 2.0),
                ("admin", "球场管理员", 3.0),
            ]
        ):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "display_name": name,
                    "level": level,
                    "verification": "pending" if username == "pending" else "approved",
                    "is_staff": username == "admin",
                    "is_superuser": username == "admin",
                },
            )
            if created:
                user.set_password(
                    os.environ.get("ADMIN_PASSWORD", password) if username == "admin" else password
                )
                user.save()
                VerificationRequest.objects.create(
                    user=user,
                    real_name=f"演示学生{index + 1}",
                    student_id=f"20260000{index + 1:02}",
                    status="pending" if username == "pending" else "approved",
                    note="合成演示资料，非真实学籍核验。",
                )
            users.append(user)
        for code, name, count, price in [
            ("zijing", "紫荆网球场", 14, 15),
            ("beiguan", "北馆网球场", 4, 120),
        ]:
            Area.objects.get_or_create(
                code=code, defaults={"name": name, "court_count": count, "reference_price": price}
            )
        for hour in range(8, 22):
            Slot.objects.get_or_create(start=f"{hour:02}:00", defaults={"end": f"{hour + 1:02}:00"})
        areas, slots = list(Area.objects.order_by("id")), list(Slot.objects.all())
        tomorrow = timezone.localdate() + timedelta(days=1)
        for day_offset in range(3):
            day = tomorrow + timedelta(days=day_offset)
            for index, kind in enumerate(["sell", "buy", "game", "sell", "game", "trade"]):
                area, slot = areas[index % 2], slots[8 + index % 4]
                owner = users[(index + day_offset) % 4]
                defaults = {
                    "starts_at": timezone.make_aware(datetime.combine(day, slot.start)),
                    "court": None if kind == "trade" else 1 + index % area.court_count,
                    "note": [
                        "临时有事，转让已预约时段，欢迎站内联系。",
                        "想在晚课后练一小时，有场地的球友联系我。",
                        "友好对拉，强度适中，一起进步。",
                    ][index % 3],
                }
                if kind == "game":
                    defaults.update(
                        mode="doubles" if index == 4 else "singles",
                        players_needed=2 if index == 4 else 1,
                        min_level=2,
                        max_level=4,
                    )
                if kind == "trade":
                    defaults["desired"] = [
                        {"area": areas[0].pk, "date": day.isoformat(), "slot": slots[12].pk}
                    ]
                Posting.objects.get_or_create(
                    owner=owner, kind=kind, area=area, date=day, slot=slot, defaults=defaults
                )
        Friendship.objects.get_or_create(
            pair_key=pair_key(users[0].pk, users[1].pk),
            defaults={"sender": users[0], "recipient": users[1], "status": "accepted"},
        )
        BehaviorRating.objects.get_or_create(
            author=users[1], target=users[0], defaults={"stars": 5}
        )
        TennisFeedback.objects.get_or_create(
            author=users[1],
            target=users[0],
            comment="正手落点比较稳定，反手在被调动时容易打短；发球可先追求成功率。",
            defaults={"strokes": {"forehand": 4, "backhand": 2, "serve": 3, "movement": 3}},
        )
        if not Message.objects.filter(sender=users[1], recipient=users[0]).exists():
            Message.objects.create(
                sender=users[1],
                recipient=users[0],
                body="明天下午一起练球吗？我约到了北馆的场地。",
                client_id=uuid4(),
            )
        if not Match.objects.exists():
            match = submit_match(
                users[0],
                {
                    "mode": "singles",
                    "team1": [users[0].pk],
                    "team2": [users[1].pk],
                    "sets": [{"a": 6, "b": 4}],
                    "winner": 1,
                    "played_on": timezone.localdate(),
                },
            )
            decide_match(match.pk, users[1], "confirmed")
        self.stdout.write(
            self.style.SUCCESS(
                "Demo ready: alice / bob / carol / dave / pending / admin. Password from DEMO_PASSWORD (admin: ADMIN_PASSWORD)."
            )
        )
