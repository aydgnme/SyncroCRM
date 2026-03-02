from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Stock


@receiver(post_save, sender=Stock)
def check_critical_stock(sender, instance, **kwargs):
    """
    Stok kaydı her güncellendiğinde kritik seviyeye düşüp düşmediğini kontrol eder.
    Kritikse Celery task'ı arka planda tetikler.
    """
    if instance.is_critical:
        from .tasks import notify_critical_stock
        notify_critical_stock.delay(instance.pk)
