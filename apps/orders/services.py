from decimal import Decimal
from django.contrib.auth import get_user_model
from .models import MaterialIssue, ProductReceipt, MasterBalance
from apps.threads.models import Thread
from apps.products.models import Product
from apps.core.constants import QualityStatus

User = get_user_model()


class OrderService:
    """Service class for order operations"""

    @staticmethod
    def create_issue(master_id, thread_id, quantity, expected_product_id,
                     expected_quantity, note='', user=None):
        """Create a new material issue"""
        try:
            master = User.objects.get(id=master_id, role='master')
            thread = Thread.objects.get(id=thread_id)
            expected_product = Product.objects.get(id=expected_product_id)

            try:
                quantity_decimal = Decimal(str(quantity))
            except:
                return False, "Miqdor noto'g'ri formatda"

            if quantity_decimal <= 0:
                return False, "Miqdor 0 dan katta bo'lishi kerak"

            if thread.current_stock < quantity_decimal:
                return False, f"Omborda yetarli ip mavjud emas. Mavjud: {thread.current_stock} kg"

            try:
                expected_qty = int(expected_quantity)
                if expected_qty <= 0:
                    return False, "Kutilayotgan mahsulot soni 0 dan katta bo'lishi kerak"
            except ValueError:
                return False, "Kutilayotgan mahsulot soni noto'g'ri formatda"

            issue = MaterialIssue.objects.create(
                master=master,
                thread=thread,
                quantity=quantity_decimal,
                expected_product=expected_product,
                expected_quantity=expected_qty,
                note=note,
                created_by=user
            )

            # Update master balance
            balance, _ = MasterBalance.objects.get_or_create(master=master)
            balance.total_thread_taken += quantity_decimal
            balance.save()

            return True, issue

        except User.DoesNotExist:
            return False, "Usta topilmadi"
        except Thread.DoesNotExist:
            return False, "Ip topilmadi"
        except Product.DoesNotExist:
            return False, "Mahsulot topilmadi"
        except Exception as e:
            return False, f"Xatolik: {str(e)}"

    @staticmethod
    def create_receipt(material_issue_id, product_id, quantity_received,
                       quality_status, actual_weight_per_item=None,
                       defect_reason='', defect_description='', note='', user=None):
        """Create a new product receipt with quality tracking"""
        try:
            material_issue = MaterialIssue.objects.get(id=material_issue_id)
            product = Product.objects.get(id=product_id)

            if material_issue.is_closed:
                return False, "Bu berilma allaqachon yopilgan"

            try:
                quantity = int(quantity_received)
            except ValueError:
                return False, "Miqdor noto'g'ri formatda"

            if quantity <= 0:
                return False, "Miqdor 0 dan katta bo'lishi kerak"

            # Validate quantity for good products only (defective doesn't affect balance)
            if quality_status == QualityStatus.GOOD:
                if quantity > material_issue.current_balance_quantity:
                    return False, f"Yaroqli mahsulot miqdori ({quantity}) qarz miqdoridan ({material_issue.current_balance_quantity}) katta"

            # Set weight
            if actual_weight_per_item:
                try:
                    weight = Decimal(str(actual_weight_per_item))
                except:
                    weight = product.standard_weight
            else:
                weight = product.standard_weight

            receipt = ProductReceipt.objects.create(
                material_issue=material_issue,
                product=product,
                quantity_received=quantity,
                quality_status=quality_status,
                actual_weight_per_item=weight,
                defect_reason=defect_reason if quality_status != QualityStatus.GOOD else '',
                defect_description=defect_description if quality_status != QualityStatus.GOOD else '',
                note=note,
                received_by=user
            )

            return True, receipt

        except MaterialIssue.DoesNotExist:
            return False, "Ip berish topilmadi"
        except Product.DoesNotExist:
            return False, "Mahsulot topilmadi"
        except Exception as e:
            return False, f"Xatolik: {str(e)}"