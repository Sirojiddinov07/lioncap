from decimal import Decimal
import re
from django.core.exceptions import ValidationError

def validate_positive_number(value):
    """Validate that value is positive"""
    if value <= 0:
        raise ValidationError('Qiymat 0 dan katta bo\'lishi kerak')

def validate_decimal_precision(value, max_digits=12, decimal_places=3):
    """Validate decimal precision"""
    if value is None:
        return
    if isinstance(value, (int, float, Decimal)):
        str_value = str(value)
        if '.' in str_value:
            _, dec_part = str_value.split('.')
            if len(dec_part) > decimal_places:
                raise ValidationError(f'{decimal_places} xonagacha kasr qismi ruxsat etilgan')

def format_currency(value):
    """Format decimal as currency"""
    if value is None:
        return '0 so\'m'
    return f'{value:,.2f} so\'m'.replace(',', ' ')

def format_weight(value):
    """Format decimal as weight"""
    if value is None:
        return '0 kg'
    return f'{value:.3f} kg'.replace('.', ',')

def phone_number_validator(value):
    """Validate phone number format"""
    pattern = re.compile(r'^\+998\d{9}$')
    if not pattern.match(value):
        raise ValidationError('Telefon raqam +998XXXXXXXXX formatida bo\'lishi kerak')