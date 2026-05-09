from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from apps.orders.models import MasterBalance

@receiver(post_save, sender=User)
def create_master_balance(sender, instance, created, **kwargs):
    """Create balance record when a new master user is created"""
    if created and instance.role == 'master':
        MasterBalance.objects.get_or_create(master=instance)