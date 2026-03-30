import logging
from celery import shared_task
from django.core.mail import mail_admins

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_critical_stock(self, stock_id):
    """
    Log a warning and email admins when a stock record falls below the minimum level.
    Triggered by a signal; runs in the Celery worker.
    """
    from inventory.models import Stock

    try:
        stock = Stock.objects.select_related('product', 'warehouse').get(pk=stock_id)
    except Stock.DoesNotExist:
        logger.error(f"notify_critical_stock: Stock id={stock_id} not found.")
        return

    if not stock.is_critical:
        # Stock may have been replenished before the task ran
        return

    msg = (
        f"CRITICAL STOCK | {stock.product.sku} — {stock.product.name} "
        f"@ {stock.warehouse.name} | "
        f"available={stock.available_quantity} / min={stock.min_level}"
    )
    logger.warning(msg)

    subject = f"[SyncroCRM] Critical Stock: {stock.product.sku} @ {stock.warehouse.name}"
    body = (
        f"Product        : {stock.product.name} ({stock.product.sku})\n"
        f"Warehouse      : {stock.warehouse.name}\n"
        f"Available      : {stock.available_quantity} {stock.product.unit}\n"
        f"Minimum Level  : {stock.min_level} {stock.product.unit}\n\n"
        f"Please reorder stock as soon as possible."
    )

    try:
        mail_admins(subject, body, fail_silently=False)
    except Exception as exc:
        logger.error(f"Failed to send critical stock email: {exc}")
        raise self.retry(exc=exc)
