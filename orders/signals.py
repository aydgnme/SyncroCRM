from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from inventory.models import Stock, StockMovement
from .models import Order, OrderItem


@receiver(post_save, sender=OrderItem)
def reserve_stock_on_item_create(sender, instance, created, **kwargs):
    """
    Sipariş kalemi oluşturulunca ilgili stokta rezervasyon başlatılır.
    Gerçek stok düşmez, sadece reserved_quantity artar.
    """
    if not created:
        return

    with transaction.atomic():
        stock = Stock.objects.select_for_update().get(
            product=instance.product,
            warehouse=instance.warehouse,
        )
        stock.reserved_quantity += instance.quantity
        stock.save(update_fields=['reserved_quantity', 'updated_at'])


@receiver(pre_save, sender=Order)
def handle_order_status_change(sender, instance, **kwargs):
    """
    Sipariş durumu değişimlerine göre stok hareketlerini yönetir.

    PENDING → CONFIRMED : Gerçek stok düşer, rezervasyon serbest kalır.
    * → CANCELLED       : Rezervasyon iade edilir, stok dokunulmaz.
    """
    if not instance.pk:
        return  # yeni sipariş, henüz status değişimi yok

    try:
        previous = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    if previous.status == instance.status:
        return

    with transaction.atomic():
        if previous.status == Order.Status.PENDING and instance.status == Order.Status.CONFIRMED:
            _confirm_order_stock(instance)

        elif instance.status == Order.Status.CANCELLED and previous.status != Order.Status.DELIVERED:
            _cancel_order_stock(instance, previous.status)


def _confirm_order_stock(order):
    """CONFIRMED: Stoktan gerçek düşüş + StockMovement kaydı."""
    for item in order.items.select_related('product', 'warehouse').all():
        stock = Stock.objects.select_for_update().get(
            product=item.product,
            warehouse=item.warehouse,
        )
        stock.quantity -= item.quantity
        stock.reserved_quantity -= item.quantity
        stock.save(update_fields=['quantity', 'reserved_quantity', 'updated_at'])

        StockMovement.objects.create(
            stock=stock,
            change=-item.quantity,
            type=StockMovement.MovementType.OUT,
            reason='Sipariş onayı',
            reference=order.order_number,
        )


def _cancel_order_stock(order, previous_status):
    """CANCELLED: Rezervasyon iade edilir. CONFIRMED ise stok geri yüklenir."""
    for item in order.items.select_related('product', 'warehouse').all():
        stock = Stock.objects.select_for_update().get(
            product=item.product,
            warehouse=item.warehouse,
        )

        if previous_status == Order.Status.PENDING:
            # Sadece rezervasyon vardı, gerçek stok düşmemişti
            stock.reserved_quantity -= item.quantity
            stock.save(update_fields=['reserved_quantity', 'updated_at'])

        elif previous_status == Order.Status.CONFIRMED:
            # Gerçek stok düşmüştü, geri yükle
            stock.quantity += item.quantity
            stock.save(update_fields=['quantity', 'updated_at'])

            StockMovement.objects.create(
                stock=stock,
                change=item.quantity,
                type=StockMovement.MovementType.ADJUSTMENT,
                reason='Sipariş iptali — stok iadesi',
                reference=order.order_number,
            )
