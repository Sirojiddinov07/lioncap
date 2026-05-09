from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from .models import MaterialIssue, ProductReceipt, MasterBalance
from apps.threads.models import Thread, ThreadTransaction
from apps.products.models import Product
from apps.users.models import User
from apps.core.constants import QualityStatus, DefectReason, CurrencyType
from ..users.views import admin_required


@login_required
def dashboard(request):
    masters = User.objects.filter(role='master')
    masters_with_debt = []
    for master in masters:
        balance, _ = MasterBalance.objects.get_or_create(master=master)
        if balance.has_debt:
            masters_with_debt.append(balance)

    context = {
        'masters_with_debt': masters_with_debt,
        'total_masters': masters.count(),
        'total_threads': Thread.objects.count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'active_debts': MaterialIssue.objects.filter(is_closed=False).count(),
        'low_stock_threads': Thread.objects.filter(current_stock__lt=10),
    }
    return render(request, 'orders/dashboard.html', context)


@login_required
def master_list(request):
    """List all masters"""
    masters = User.objects.filter(role='master')
    masters_data = []

    for master in masters:
        balance, _ = MasterBalance.objects.get_or_create(master=master)

        # Ustaning valyutasiga qarab qarzni ko'rsatish
        if master.preferred_currency == 'usd':
            payment_balance_display = f"{balance.payment_balance_usd:,.2f} USD"
            total_due_display = f"{balance.total_payment_due_usd:,.2f} USD"
            total_paid_display = f"{balance.total_payment_paid_usd:,.2f} USD"
        else:
            payment_balance_display = f"{balance.payment_balance_uzs:,.0f} so'm"
            total_due_display = f"{balance.total_payment_due_uzs:,.0f} so'm"
            total_paid_display = f"{balance.total_payment_paid_uzs:,.0f} so'm"

        masters_data.append({
            'master': master,
            'balance': balance,
            'product_debt': balance.product_debt,
            'payment_balance_display': payment_balance_display,
            'total_due_display': total_due_display,
            'total_paid_display': total_paid_display,
            'total_product_given': balance.total_product_given,
            'total_weight_given': balance.total_weight_given,
        })

    context = {
        'masters_data': masters_data,
    }
    return render(request, 'orders/master_list.html', context)


@login_required
def master_detail(request, master_id):
    master = get_object_or_404(User, id=master_id, role='master')
    balance, _ = MasterBalance.objects.get_or_create(master=master)

    active_issues = MaterialIssue.objects.filter(
        master=master, is_closed=False
    ).select_related('thread', 'expected_product').order_by('-issue_date')

    closed_issues = MaterialIssue.objects.filter(
        master=master, is_closed=True
    ).select_related('thread', 'expected_product').order_by('-issue_date')[:20]

    receipts = ProductReceipt.objects.filter(
        material_issue__master=master
    ).select_related('product').order_by('-receipt_date')[:30]

    # Valyutaga qarab to'lov ma'lumotlarini formatlash
    if master.preferred_currency == 'usd':
        total_payment_due_display = f"{balance.total_payment_due_usd:,.2f} USD"
        total_payment_paid_display = f"{balance.total_payment_paid_usd:,.2f} USD"
        payment_balance_display = f"{balance.payment_balance_usd:,.2f} USD"
    else:
        total_payment_due_display = f"{balance.total_payment_due_uzs:,.0f} so'm"
        total_payment_paid_display = f"{balance.total_payment_paid_uzs:,.0f} so'm"
        payment_balance_display = f"{balance.payment_balance_uzs:,.0f} so'm"

    context = {
        'master': master,
        'balance': balance,
        'active_issues': active_issues,
        'closed_issues': closed_issues,
        'receipts': receipts,
        'product_debt': balance.product_debt,
        'total_payment_due_display': total_payment_due_display,
        'total_payment_paid_display': total_payment_paid_display,
        'payment_balance_display': payment_balance_display,
        'total_thread_taken': balance.total_thread_taken,
        'total_product_given': balance.total_product_given,
        'total_weight_given': balance.total_weight_given,
    }
    return render(request, 'orders/master_detail.html', context)


@login_required
@admin_required
def issue_create(request):
    if request.method == 'POST':
        master_id = request.POST.get('master')
        product_id = request.POST.get('expected_product')
        note = request.POST.get('note', '')

        master = get_object_or_404(User, id=master_id, role='master')
        product = get_object_or_404(Product, id=product_id)
        product_threads = product.threads.all()

        if not product_threads.exists():
            messages.error(request, "Bu mahsulot uchun ip tarkibi belgilanmagan!")
            return redirect('orders:issue_create')

        # 1. Har bir ip turi uchun berilgan miqdorni (kg) o‘qib olamiz
        given_kg = {}
        possible_pieces = []

        for pt in product_threads:
            kg_key = f'thread_kg_{pt.thread.id}'
            kg_value = request.POST.get(kg_key)
            if not kg_value:
                messages.error(request, f"{pt.thread.name} uchun ip miqdorini kiriting!")
                return redirect('orders:issue_create')

            kg = Decimal(kg_value)
            if kg <= 0:
                messages.error(request, f"{pt.thread.name} miqdori 0 dan katta bo‘lishi kerak!")
                return redirect('orders:issue_create')

            given_kg[pt.thread.id] = kg

            # Shu ipdan necha dona mahsulot chiqishi mumkin
            pieces = int(kg // pt.quantity_per_unit)
            possible_pieces.append(pieces)

        # 2. Eng kam chiqadigan mahsulot soni = kutilayotgan mahsulot soni
        expected_quantity = min(possible_pieces) if possible_pieces else 0

        if expected_quantity <= 0:
            messages.error(request, "Kiritilgan ip miqdori bilan hech qanday mahsulot tayyorlab bo‘lmaydi!")
            return redirect('orders:issue_create')

        # 3. Kutilayotgan miqdordagi mahsulot uchun **haqiqiy kerak bo‘ladigan ip miqdori**
        #    va omborda yetarlilikni tekshirish
        required_kg = {}
        total_kg = Decimal('0')

        for pt in product_threads:
            needed = pt.quantity_per_unit * expected_quantity
            required_kg[pt.thread.id] = needed
            total_kg += needed

            # Ombor tekshiruvi (kerakli miqdor bilan, berilgan miqdor bilan emas!)
            if pt.thread.current_stock < needed:
                messages.error(
                    request,
                    f"{pt.thread.name} ipi omborda yetarli emas! Kerak: {needed:.3f} kg, Mavjud: {pt.thread.current_stock:.3f} kg"
                )
                return redirect('orders:issue_create')

        # 4. Ip berish yozuvini yaratish (umumiy ip miqdori total_kg)
        issue = MaterialIssue.objects.create(
            master=master,
            thread=None,
            quantity=total_kg,
            expected_product=product,
            expected_quantity=expected_quantity,
            note=note
        )

        # 5. Ombordan faqat kerakli miqdorda ip chiqarish (berilgan miqdor emas!)
        for pt in product_threads:
            needed = required_kg[pt.thread.id]
            thread = pt.thread
            thread.current_stock -= needed
            thread.save()

            ThreadTransaction.objects.create(
                thread=thread,
                quantity=needed,
                transaction_type='outgoing',
                related_master=master,
                note=f"Ustaga berildi: {product.name} ({expected_quantity} dona) - {thread.name} ({needed:.3f} kg)"
            )

        # 6. Usta balansini yangilash
        balance, _ = MasterBalance.objects.get_or_create(master=master)
        balance.total_thread_taken += total_kg
        balance.save()

        # 7. Xabar
        if master.preferred_currency == 'usd':
            total_payment = product.weaving_price_usd * expected_quantity
            messages.success(
                request,
                f"{expected_quantity} dona {product.name} tayyorlash uchun ip berildi.\n"
                f"Jami ip: {total_kg:.2f} kg\n"
                f"To‘lov: {total_payment:,.2f} USD"
            )
        else:
            total_payment = product.weaving_price_uzs * expected_quantity
            messages.success(
                request,
                f"{expected_quantity} dona {product.name} tayyorlash uchun ip berildi.\n"
                f"Jami ip: {total_kg:.2f} kg\n"
                f"To‘lov: {total_payment:,.0f} so‘m"
            )

        return redirect('orders:master_detail', master_id=master.id)

    context = {
        'masters': User.objects.filter(role='master'),
        'products': Product.objects.filter(is_active=True),
    }
    return render(request, 'orders/issue_form.html', context)


@login_required
@admin_required
def add_payment(request, master_id):
    master = get_object_or_404(User, id=master_id, role='master')
    balance, _ = MasterBalance.objects.get_or_create(master=master)

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        currency = request.POST.get('currency')
        note = request.POST.get('note', '')

        if amount <= 0:
            messages.error(request, "To'lov miqdori 0 dan katta bo'lishi kerak!")
            return redirect('orders:add_payment', master_id=master_id)

        # Valyutaga qarab qarzni tekshirish
        if currency == 'usd':
            if amount > balance.payment_balance_usd:
                messages.error(request,
                               f"To'lov miqdori ({amount} USD) qarzdan ({balance.payment_balance_usd:,.2f} USD) katta!")
                return redirect('orders:add_payment', master_id=master_id)
            balance.total_payment_paid_usd += amount
            balance.save()
            messages.success(request,
                             f"{amount:,.2f} USD to'lov qabul qilindi. Qolgan qarz: {balance.payment_balance_usd:,.2f} USD")
        else:
            if amount > balance.payment_balance_uzs:
                messages.error(request,
                               f"To'lov miqdori ({amount:,.0f} so'm) qarzdan ({balance.payment_balance_uzs:,.0f} so'm) katta!")
                return redirect('orders:add_payment', master_id=master_id)
            balance.total_payment_paid_uzs += amount
            balance.save()
            messages.success(request,
                             f"{amount:,.0f} so'm to'lov qabul qilindi. Qolgan qarz: {balance.payment_balance_uzs:,.0f} so'm")

        return redirect('orders:master_detail', master_id=master_id)

    context = {
        'master': master,
        'balance': balance,
        'payment_balance_uzs': balance.payment_balance_uzs,
        'payment_balance_usd': balance.payment_balance_usd,
        'preferred_currency': master.preferred_currency,
        'currencies': [('uzs', "So'm"), ('usd', 'USD')],
    }
    return render(request, 'orders/add_payment.html', context)


@login_required
@admin_required
def receipt_create(request, issue_id):
    material_issue = get_object_or_404(MaterialIssue, id=issue_id)

    # Berilgan umumiy ip miqdorini olish (quantity field'dan)
    given_weight = float(material_issue.quantity) if material_issue.quantity else 0

    # Agar quantity 0 bo'lsa, ThreadTransaction dan hisoblab olamiz (zaxira)
    if given_weight == 0:
        total_given = ThreadTransaction.objects.filter(
            related_master=material_issue.master,
            transaction_type='outgoing',
            created_at__gte=material_issue.created_at
        ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
        given_weight = float(total_given)

    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity'))
        total_weight = Decimal(request.POST.get('total_weight'))
        quality_status = request.POST.get('quality_status')
        defect_reason = request.POST.get('defect_reason', '')
        defect_description = request.POST.get('defect_description', '')
        note = request.POST.get('note', '')

        actual_weight_per_item = total_weight / quantity

        if quality_status == QualityStatus.GOOD and quantity > material_issue.current_balance_quantity:
            messages.error(
                request,
                f"Yaroqli mahsulot miqdori ({quantity} dona) qarzdan ({material_issue.current_balance_quantity} dona) katta!"
            )
            return redirect('orders:receipt_create', issue_id=issue_id)

        if float(total_weight) > given_weight:
            messages.error(
                request,
                f"Umumiy og'irlik ({total_weight} kg) berilgan ip miqdoridan ({given_weight} kg) katta!"
            )
            return redirect('orders:receipt_create', issue_id=issue_id)

        receipt = ProductReceipt.objects.create(
            material_issue=material_issue,
            product_id=product_id,
            quantity_received=quantity,
            quality_status=quality_status,
            actual_weight_per_item=actual_weight_per_item,
            defect_reason=defect_reason if quality_status != QualityStatus.GOOD else '',
            defect_description=defect_description if quality_status != QualityStatus.GOOD else '',
            note=note
        )

        if quality_status == QualityStatus.GOOD:
            currency = material_issue.master.preferred_currency
            if currency == 'usd':
                messages.success(
                    request,
                    f"{quantity} dona yaroqli mahsulot qabul qilindi. "
                    f"Umumiy og'irlik: {total_weight} kg, "
                    f"To'lov: {receipt.total_payment:,.2f} USD"
                )
            else:
                messages.success(
                    request,
                    f"{quantity} dona yaroqli mahsulot qabul qilindi. "
                    f"Umumiy og'irlik: {total_weight} kg, "
                    f"To'lov: {receipt.total_payment:,.0f} so'm"
                )
        else:
            messages.warning(request, f"{quantity} dona yaroqsiz mahsulot qabul qilindi")

        return redirect('orders:master_detail', master_id=material_issue.master.id)

    context = {
        'material_issue': material_issue,
        'products': Product.objects.filter(is_active=True),
        'current_balance': material_issue.current_balance_quantity,
        'quality_statuses': QualityStatus.choices,
        'defect_reasons': DefectReason.choices,
        'given_weight': given_weight,
    }
    return render(request, 'orders/receipt_form.html', context)


@login_required
def finished_products(request):
    receipts = ProductReceipt.objects.select_related('material_issue__master', 'product').order_by('-receipt_date')

    product_summary = {}
    for receipt in receipts:
        key = receipt.product.id
        if key not in product_summary:
            product_summary[key] = {
                'product': receipt.product,
                'good_quantity': 0,
                'defective_quantity': 0,
                'good_weight': Decimal('0'),
                'defective_weight': Decimal('0'),
            }

        if receipt.quality_status == QualityStatus.GOOD:
            product_summary[key]['good_quantity'] += receipt.quantity_received
            product_summary[key]['good_weight'] += receipt.total_weight
        else:
            product_summary[key]['defective_quantity'] += receipt.quantity_received
            product_summary[key]['defective_weight'] += receipt.total_weight

    context = {
        'receipts': receipts[:100],
        'product_summary': list(product_summary.values()),
        'total_good': sum(s['good_quantity'] for s in product_summary.values()),
        'total_defective': sum(s['defective_quantity'] for s in product_summary.values()),
    }
    return render(request, 'orders/finished_products.html', context)