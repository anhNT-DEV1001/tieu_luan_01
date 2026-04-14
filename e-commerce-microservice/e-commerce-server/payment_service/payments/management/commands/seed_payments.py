from django.core.management.base import BaseCommand
from django.utils import timezone

from payments.models import Payment


class Command(BaseCommand):
    help = "Seed demo payments. Run after orders are seeded."

    def handle(self, *args, **options):
        payment, created = Payment.objects.get_or_create(
            transaction_code="PAYDEMO0001",
            defaults={
                "order_id": 1,
                "payer_name": "Le Minh Customer",
                "amount": 28610000,
                "currency": "VND",
                "method": Payment.PaymentMethod.MOMO,
                "status": Payment.PaymentStatus.PAID,
                "gateway_response": {"provider": "momo", "seeded": True},
                "paid_at": timezone.now(),
            },
        )
        state = "created" if created else "already exists"
        self.stdout.write(self.style.SUCCESS(f"Demo payment {state}: {payment.transaction_code}"))
