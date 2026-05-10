from django.db import models
from django.core.validators import MinValueValidator
from apps.core.models import BaseModel
from apps.threads.models import Thread


class Product(BaseModel):
    name = models.CharField(max_length=100, verbose_name='Mahsulot nomi')
    code = models.CharField(max_length=50, blank=True, verbose_name='Kod')
    standard_weight = models.DecimalField(
        max_digits=10, decimal_places=3,
        validators=[MinValueValidator(0.001)],
        verbose_name="1 dona og'irligi (kg)"
    )
    weaving_price_uzs = models.DecimalField(
        max_digits=12, decimal_places=5, default=0,
        verbose_name="To'qish narxi (so'm)"
    )
    weaving_price_usd = models.DecimalField(
        max_digits=12, decimal_places=5, default=0,
        verbose_name="To'qish narxi (dollar)"
    )
    default_thread = models.ForeignKey(
        Thread, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Standart ip'
    )
    is_active = models.BooleanField(default=True, verbose_name='Faol')

    # YANGI FIELD'LAR
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name='Mahsulot rasmi'
    )
    stock_quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Ombordagi soni (dona)'
    )
    min_stock_threshold = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        verbose_name='Minimal zaxira chegarasi'
    )

    class Meta:
        verbose_name = 'Mahsulot'
        verbose_name_plural = 'Mahsulotlar'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (so'm: {self.weaving_price_uzs} | dollar: {self.weaving_price_usd})"

    @property
    def total_weight_per_unit(self):
        """1 dona mahsulotning umumiy og'irligi"""
        total = self.standard_weight
        for pt in self.threads.all():
            total += pt.quantity_per_unit
        return total

    @property
    def is_low_stock(self):
        """Zaxira kamligini tekshirish"""
        return self.stock_quantity <= self.min_stock_threshold

    @property
    def is_out_of_stock(self):
        """Mahsulot tugaganligini tekshirish"""
        return self.stock_quantity == 0


class ProductThread(BaseModel):
    """Mahsulot tarkibidagi ip va uning normasi"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='threads')
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, verbose_name='Ip turi')
    quantity_per_unit = models.DecimalField(
        max_digits=10, decimal_places=3,
        validators=[MinValueValidator(0.001)],
        verbose_name="1 dona uchun kerak bo'lgan ip miqdori (kg)"
    )

    class Meta:
        verbose_name = "Mahsulot ip tarkibi"
        verbose_name_plural = "Mahsulot ip tarkiblari"
        unique_together = ['product', 'thread']

    def __str__(self):
        return f"{self.product.name} - {self.thread.name}: {self.quantity_per_unit} kg"