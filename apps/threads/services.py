from decimal import Decimal
from .models import Thread


class ThreadService:
    """Service class for thread operations"""

    @staticmethod
    def add_stock(thread_id, quantity, price=None, note='', user=None):
        """Add stock to thread with validation"""
        try:
            thread = Thread.objects.get(id=thread_id)
            quantity_decimal = Decimal(str(quantity))

            if quantity_decimal <= 0:
                return False, "Miqdor 0 dan katta bo'lishi kerak"

            if price and Decimal(str(price)) > 0:
                thread.price_per_unit = Decimal(str(price))

            thread.add_stock(quantity_decimal, note, user)
            return True, "Muvaffaqiyatli qo'shildi"

        except Thread.DoesNotExist:
            return False, "Ip topilmadi"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Xatolik: {str(e)}"

    @staticmethod
    def remove_stock(thread_id, quantity, note='', user=None):
        """Remove stock from thread with validation"""
        try:
            thread = Thread.objects.get(id=thread_id)
            quantity_decimal = Decimal(str(quantity))

            if quantity_decimal <= 0:
                return False, "Miqdor 0 dan katta bo'lishi kerak"

            thread.remove_stock(quantity_decimal, note, user)
            return True, "Muvaffaqiyatli chiqarildi"

        except Thread.DoesNotExist:
            return False, "Ip topilmadi"
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Xatolik: {str(e)}"