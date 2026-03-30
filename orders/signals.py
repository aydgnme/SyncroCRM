from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from inventory.models import Stock, StockMovement
from .models import Order, OrderItem


@receiver(post_save, sender=OrderItem)
def reserve_stock_on_item_create(sender, instance, created, **kwargs):
    """
    Reserve stock when an order item is created.
    Only reserved_quantity increases — actual quantity is not deducted yet.
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
    Manage stock movements based on order status transitions.

    PENDING → CONFIRMED : Deduct real stock, release reservation.
    * → CANCELLED       : Release reservation; restore stock if already confirmed.
    """
    if not instance.pk:
        return  # New order, no status change yet

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
    """Deduct real stock and record an OUT movement for each item."""
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
            reason='Order confirmed',
            reference=order.order_number,
        )


def _cancel_order_stock(order, previous_status):
    """Release reservation on cancel. Restore real stock if order was already confirmed."""
    for item in order.items.select_related('product', 'warehouse').all():
        stock = Stock.objects.select_for_update().get(
            product=item.product,
            warehouse=item.warehouse,
        )

        if previous_status == Order.Status.PENDING:
            # Only reservation existed — real stock was never deducted
            stock.reserved_quantity -= item.quantity
            stock.save(update_fields=['reserved_quantity', 'updated_at'])

        elif previous_status == Order.Status.CONFIRMED:
            # Real stock was already deducted — restore it
            stock.quantity += item.quantity
            stock.save(update_fields=['quantity', 'updated_at'])

            StockMovement.objects.create(
                stock=stock,
                change=item.quantity,
                type=StockMovement.MovementType.ADJUSTMENT,
                reason='Order cancelled — stock restored',
                reference=order.order_number,
            )
