from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from datetime import datetime, timedelta

from apps.orders.models import MaterialIssue, ProductReceipt, MasterBalance
from apps.threads.models import Thread, ThreadTransaction
from apps.products.models import Product
from apps.users.models import User
from apps.core.constants import QualityStatus


@login_required
def main_report(request):
    """Main report dashboard"""
    try:
        now = datetime.now()
        month_start = now.replace(day=1)
        last_month_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1)

        # Current month stats
        current_month_issues = MaterialIssue.objects.filter(issue_date__gte=month_start)
        current_month_receipts = ProductReceipt.objects.filter(receipt_date__gte=month_start)
        current_month_good_receipts = current_month_receipts.filter(quality_status=QualityStatus.GOOD)
        current_month_defective_receipts = current_month_receipts.filter(quality_status=QualityStatus.DEFECTIVE)

        # Last month stats
        last_month_issues = MaterialIssue.objects.filter(issue_date__gte=last_month_start, issue_date__lt=month_start)
        last_month_receipts = ProductReceipt.objects.filter(receipt_date__gte=last_month_start,
                                                            receipt_date__lt=month_start)
        last_month_good_receipts = last_month_receipts.filter(quality_status=QualityStatus.GOOD)

        context = {
            'current_month_issues_count': current_month_issues.count(),
            'current_month_issues_weight': current_month_issues.aggregate(Sum('quantity'))['quantity__sum'] or 0,
            'current_month_receipts_count': current_month_receipts.count(),
            'current_month_good_quantity': current_month_good_receipts.aggregate(Sum('quantity_received'))[
                                               'quantity_received__sum'] or 0,
            'current_month_defective_quantity': current_month_defective_receipts.aggregate(Sum('quantity_received'))[
                                                    'quantity_received__sum'] or 0,
            'current_month_good_weight': sum(float(r.total_weight) for r in current_month_good_receipts),
            'current_month_defective_weight': sum(float(r.total_weight) for r in current_month_defective_receipts),

            'last_month_issues_weight': last_month_issues.aggregate(Sum('quantity'))['quantity__sum'] or 0,
            'last_month_good_quantity': last_month_good_receipts.aggregate(Sum('quantity_received'))[
                                            'quantity_received__sum'] or 0,

            'total_masters': User.objects.filter(role='master').count(),
            'total_masters_with_debt': MasterBalance.objects.filter(total_thread_taken__gt=0).count(),
            'total_threads': Thread.objects.count(),
            'total_products': Product.objects.filter(is_active=True).count(),
            'active_debts': MaterialIssue.objects.filter(is_closed=False).count(),
        }

        # Calculate quality rate
        total_good = context['current_month_good_quantity']
        total_defective = context['current_month_defective_quantity']
        total = total_good + total_defective
        context['overall_quality_rate'] = (total_good / total * 100) if total > 0 else 0

        return render(request, 'reports/main.html', context)
    except Exception as e:
        return render(request, 'reports/main.html', {'error': str(e)})


@login_required
def masters_report(request):
    """Masters performance report"""
    try:
        masters = User.objects.filter(role='master')
        masters_data = []
        total_good_quantity = 0
        total_defective_quantity = 0
        total_good_weight = Decimal('0')
        total_defective_weight = Decimal('0')

        for master in masters:
            balance, _ = MasterBalance.objects.get_or_create(master=master)

            total_good_quantity += balance.total_product_given
            total_defective_quantity += balance.total_defective_product_given
            total_good_weight += balance.total_product_weight_given
            total_defective_weight += balance.total_defective_weight_given

            masters_data.append({
                'master': master,
                'total_thread_taken': balance.total_thread_taken,
                'total_good_quantity': balance.total_product_given,
                'total_defective_quantity': balance.total_defective_product_given,
                'total_good_weight': balance.total_product_weight_given,
                'total_defective_weight': balance.total_defective_weight_given,
                'product_debt': balance.product_debt_quantity,
                'efficiency': balance.efficiency,
                'defect_rate': balance.defect_rate,
            })

        context = {
            'masters_data': masters_data,
            'total_good_quantity': total_good_quantity,
            'total_defective_quantity': total_defective_quantity,
            'total_good_weight': total_good_weight,
            'total_defective_weight': total_defective_weight,
        }
        return render(request, 'reports/masters.html', context)
    except Exception as e:
        return render(request, 'reports/masters.html', {'error': str(e), 'masters_data': []})


@login_required
def products_report(request):
    """Products performance report"""
    try:
        products = Product.objects.filter(is_active=True)
        products_data = []
        total_good_quantity = 0
        total_defective_quantity = 0

        for product in products:
            receipts = ProductReceipt.objects.filter(product=product)
            good_receipts = receipts.filter(quality_status=QualityStatus.GOOD)
            defective_receipts = receipts.filter(quality_status=QualityStatus.DEFECTIVE)

            good_qty = good_receipts.aggregate(Sum('quantity_received'))['quantity_received__sum'] or 0
            defective_qty = defective_receipts.aggregate(Sum('quantity_received'))['quantity_received__sum'] or 0
            good_weight = sum(float(r.total_weight) for r in good_receipts)
            defective_weight = sum(float(r.total_weight) for r in defective_receipts)

            total_good_quantity += good_qty
            total_defective_quantity += defective_qty

            products_data.append({
                'product': product,
                'total_good_quantity': good_qty,
                'total_defective_quantity': defective_qty,
                'total_good_weight': good_weight,
                'total_defective_weight': defective_weight,
                'quality_rate': (good_qty / (good_qty + defective_qty) * 100) if (good_qty + defective_qty) > 0 else 0,
            })

        context = {
            'products_data': products_data,
            'total_good_quantity': total_good_quantity,
            'total_defective_quantity': total_defective_quantity,
        }
        return render(request, 'reports/products.html', context)
    except Exception as e:
        return render(request, 'reports/products.html', {'error': str(e), 'products_data': []})


@login_required
def financial_report(request):
    """Financial report"""
    try:
        thread_transactions = ThreadTransaction.objects.filter(transaction_type='incoming')
        total_thread_cost = sum(float(t.quantity) * float(t.thread.price_per_unit) for t in thread_transactions)

        receipts = ProductReceipt.objects.filter(quality_status=QualityStatus.GOOD)
        total_revenue = sum(float(r.total_weight) * float(r.product.selling_price) for r in receipts)

        total_production_cost = sum(
            float(r.total_weight) * float(r.product.production_cost) for r in receipts if r.product.production_cost)

        gross_profit = total_revenue - total_production_cost
        net_profit = total_revenue - total_production_cost - total_thread_cost
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0

        context = {
            'total_thread_cost': total_thread_cost,
            'total_production_cost': total_production_cost,
            'total_revenue': total_revenue,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'profit_margin': profit_margin,
            'receipts': receipts[:50],
        }
        return render(request, 'reports/financial.html', context)
    except Exception as e:
        return render(request, 'reports/financial.html', {'error': str(e), 'receipts': []})