from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Stock


@receiver(post_save, sender=Stock)
def check_critical_stock(sender, instance, **kwargs):
    """
    After every Stock save, check whether the level has fallen below the minimum.
    If critical, dispatch a Celery task to notify admins.
    """
    if instance.is_critical:
        from .tasks import notify_critical_stock
        notify_critical_stock.delay(instance.pk)
