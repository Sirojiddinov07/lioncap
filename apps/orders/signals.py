from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.users.models import User
from .models import MasterBalance

@receiver(post_save, sender=User)
def create_master_balance(sender, instance, created, **kwargs):
    """Create balance when a new master is created"""
    if created and instance.role == 'master':
        MasterBalance.objects.get_or_create(master=instance)