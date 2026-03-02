import logging
from celery import shared_task
from django.core.mail import mail_admins

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_critical_stock(self, stock_id):
    """
    Stok kritik seviyeye düştüğünde log yazar ve admin'e e-posta gönderir.
    Signal tarafından tetiklenir, Celery worker'da çalışır.
    """
    from inventory.models import Stock

    try:
        stock = Stock.objects.select_related('product', 'warehouse').get(pk=stock_id)
    except Stock.DoesNotExist:
        logger.error(f"notify_critical_stock: Stock id={stock_id} bulunamadı.")
        return

    if not stock.is_critical:
        return  # Task tetiklendiğinde stok düzelmiş olabilir

    msg = (
        f"KRİTİK STOK | {stock.product.sku} — {stock.product.name} "
        f"@ {stock.warehouse.name} | "
        f"mevcut={stock.available_quantity} / min={stock.min_level}"
    )
    logger.warning(msg)

    subject = f"[SyncroCRM] Kritik Stok: {stock.product.sku} @ {stock.warehouse.name}"
    body = (
        f"Ürün       : {stock.product.name} ({stock.product.sku})\n"
        f"Depo       : {stock.warehouse.name}\n"
        f"Kullanılabilir : {stock.available_quantity} {stock.product.unit}\n"
        f"Minimum Seviye : {stock.min_level} {stock.product.unit}\n\n"
        f"Lütfen stok yenilemesi yapınız."
    )

    try:
        mail_admins(subject, body, fail_silently=False)
    except Exception as exc:
        logger.error(f"E-posta gönderilemedi: {exc}")
        raise self.retry(exc=exc)
