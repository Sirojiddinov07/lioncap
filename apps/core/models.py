from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model with common fields
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Yangilangan vaqt')

    class Meta:
        abstract = True

    def get_created_date_uz(self):
        return self.created_at.strftime('%d.%m.%Y %H:%M')

    def get_updated_date_uz(self):
        return self.updated_at.strftime('%d.%m.%Y %H:%M')
