from django.core.management.base import BaseCommand

from orders.models import Order, OrderItem


class Command(BaseCommand):
    help = "Seed demo orders. Run after users and products are seeded."

    def handle(self, *args, **options):
        if Order.objects.exists():
            self.stdout.write(self.style.WARNING("Orders already seeded."))
            return

        order = Order.objects.create(
            user_id=3,
            customer_name="Le Minh Customer",
            customer_email="customer1@demo.local",
            shipping_address="88 Ba Trieu",
            shipping_city="Ha Noi",
            status=Order.OrderStatus.CONFIRMED,
            subtotal_amount=28580000,
            shipping_fee=30000,
            total_amount=28610000,
            notes="Demo order generated at bootstrap.",
            metadata={"channel": "docker-seed"},
        )
        OrderItem.objects.bulk_create(
            [
                OrderItem(order=order, product_id=1, product_name="Laptop Pro 14", sku="EL-1001", quantity=1, unit_price=26990000, line_total=26990000, product_snapshot={"category": "Electronics"}),
                OrderItem(order=order, product_id=2, product_name="Wireless Earbuds AirBeat", sku="EL-1002", quantity=1, unit_price=1590000, line_total=1590000, product_snapshot={"category": "Electronics"}),
            ]
        )
        self.stdout.write(self.style.SUCCESS("Seeded 1 demo order."))
