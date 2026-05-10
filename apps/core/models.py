from datetime import datetime

from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=False, blank=True, null=True, verbose_name='Yaratilgan vaqt')
    updated_at = models.DateTimeField(auto_now=False, blank=True, null=True, verbose_name='Yangilangan vaqt')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()
        super().save(*args, **kwargs)
