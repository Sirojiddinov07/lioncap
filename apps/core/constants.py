from django.db import models

class DebtType(models.TextChoices):
    PRODUCT = 'product', 'Tayyor mahsulot soni'

class QualityStatus(models.TextChoices):
    GOOD = 'good', 'Yaroqli'
    DEFECTIVE = 'defective', 'Yaroqsiz'
    REPAIRABLE = 'repairable', 'Qayta tiklanadigan'

class TransactionType(models.TextChoices):
    INCOMING = 'incoming', 'Kirim'
    OUTGOING = 'outgoing', 'Chiqim'
    RETURN = 'return', 'Qaytarilgan'
    WRITE_OFF = 'write_off', 'Hisobdan chiqarish'

class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Administrator'
    STAFF = 'staff', 'Omborchi'
    MASTER = 'master', 'Usta'

class DefectReason(models.TextChoices):
    SEWING = 'sewing', 'Tikish xatosi'
    FABRIC = 'fabric', 'Mato nuqsoni'
    SIZE = 'size', 'O\'lcham xatosi'
    CUTTING = 'cutting', 'Kesish xatosi'
    OTHER = 'other', 'Boshqa sabab'

class CurrencyType(models.TextChoices):
    UZS = 'uzs', "So'm"
    USD = 'usd', 'Dollar'

class PaymentType(models.TextChoices):
    CASH = 'cash', 'Naqd'
    CREDIT = 'credit', 'Qarz'