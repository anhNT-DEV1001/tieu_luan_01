from django.core.management.base import BaseCommand

from accounts.models import UserProfile


USERS = [
    {
        "full_name": "Nguyen Van Admin",
        "email": "admin@demo.local",
        "phone": "0900000001",
        "role": "admin",
        "city": "Ho Chi Minh City",
        "address": "1 Nguyen Hue",
        "metadata": {"department": "operations", "permissions": ["all"]},
    },
    {
        "full_name": "Tran Thu Staff",
        "email": "staff@demo.local",
        "phone": "0900000002",
        "role": "staff",
        "city": "Da Nang",
        "address": "12 Bach Dang",
        "metadata": {"shift": "morning", "warehouse": "central"},
    },
    {
        "full_name": "Le Minh Customer",
        "email": "customer1@demo.local",
        "phone": "0900000003",
        "role": "customer",
        "city": "Ha Noi",
        "address": "88 Ba Trieu",
        "loyalty_points": 240,
        "metadata": {"tier": "gold", "preferred_payment": "momo"},
    },
    {
        "full_name": "Pham Lan Customer",
        "email": "customer2@demo.local",
        "phone": "0900000004",
        "role": "customer",
        "city": "Can Tho",
        "address": "9 Ninh Kieu",
        "loyalty_points": 120,
        "metadata": {"tier": "silver", "preferred_payment": "cod"},
    },
]


class Command(BaseCommand):
    help = "Seed demo users for the ecommerce system."

    def handle(self, *args, **options):
        created = 0
        for payload in USERS:
            _, was_created = UserProfile.objects.get_or_create(email=payload["email"], defaults=payload)
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Seeded users. Newly created: {created}"))
