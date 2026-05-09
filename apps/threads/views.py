from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Thread, ThreadTransaction, ThreadSupplierDebt, SupplierPayment
from .services import ThreadService
from apps.core.constants import TransactionType, PaymentType


class ThreadListView(LoginRequiredMixin, ListView):
    model = Thread
    template_name = 'threads/list.html'
    context_object_name = 'threads'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_stock'] = sum(t.current_stock for t in context['threads'])
        context['search_query'] = self.request.GET.get('search', '')
        return context


@login_required
def thread_incoming(request):
    """Add stock to thread (CASH only - no credit)"""
    if request.method == 'POST':
        thread_id = request.POST.get('thread')
        quantity = request.POST.get('quantity')
        price = request.POST.get('price', 0)
        note = request.POST.get('note', '')

        thread = get_object_or_404(Thread, id=thread_id)
        quantity_decimal = Decimal(str(quantity))
        price_decimal = Decimal(str(price))

        # Ipni omborga qo'shish
        thread.current_stock += quantity_decimal
        if price_decimal > 0:
            thread.price_per_unit = price_decimal
        thread.save()

        # Ip harakatini yozish
        ThreadTransaction.objects.create(
            thread=thread,
            quantity=quantity_decimal,
            transaction_type='incoming',
            note=f"Ip kirimi (naqd). {note}"
        )

        messages.success(request, f"{quantity} kg ip omborga qo'shildi")
        return redirect('threads:list')

    context = {
        'threads': Thread.objects.all(),
    }
    return render(request, 'threads/incoming.html', context)


@login_required
def add_credit_only(request):
    """Add ONLY credit (no stock addition) - for existing debts"""
    if request.method == 'POST':
        thread_id = request.POST.get('thread')
        quantity = request.POST.get('quantity')
        amount = request.POST.get('amount')
        note = request.POST.get('note', '')

        thread = get_object_or_404(Thread, id=thread_id)
        quantity_decimal = Decimal(str(quantity))
        amount_decimal = Decimal(str(amount))

        # Faqat qarz yozuvi yaratish (ip omborga qo'shilmaydi)
        ThreadSupplierDebt.objects.create(
            thread=thread,
            quantity=quantity_decimal,
            amount=amount_decimal,
            payment_type='credit',
            note=f"Faqat qarz qo'shish. {note}"
        )

        messages.success(
            request,
            f"{quantity} kg ip uchun {amount_decimal:,.0f} so'm qarz qo'shildi (omborga ip qo'shilmaydi)"
        )
        return redirect('threads:supplier_debts')

    context = {
        'threads': Thread.objects.all(),
    }
    return render(request, 'threads/add_credit.html', context)


@login_required
def supplier_debts(request):
    """Yetkazib beruvchi qarzlari ro'yxati"""
    debts = ThreadSupplierDebt.objects.filter(is_paid=False).select_related('thread')

    context = {
        'debts': debts,
        'total_debt': sum(d.remaining_amount for d in debts),
    }
    return render(request, 'threads/supplier_debts.html', context)


@login_required
def pay_supplier_debt(request, debt_id):
    """Yetkazib beruvchi qarzini to'lash"""
    debt = get_object_or_404(ThreadSupplierDebt, id=debt_id)

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        note = request.POST.get('note', '')

        if amount <= 0:
            messages.error(request, "To'lov miqdori 0 dan katta bo'lishi kerak!")
            return redirect('threads:pay_supplier_debt', debt_id=debt_id)

        if amount > debt.remaining_amount:
            messages.error(
                request,
                f"To'lov miqdori qarzdan ({debt.remaining_amount:,.0f} so'm) katta!"
            )
            return redirect('threads:pay_supplier_debt', debt_id=debt_id)

        SupplierPayment.objects.create(
            debt=debt,
            amount=amount,
            note=note,
            created_by=request.user
        )

        messages.success(
            request,
            f"{amount:,.0f} so'm to'lov qabul qilindi. Qolgan qarz: {debt.remaining_amount:,.0f} so'm"
        )
        return redirect('threads:supplier_debts')

    context = {
        'debt': debt,
        'remaining': debt.remaining_amount,
    }
    return render(request, 'threads/pay_debt.html', context)


@login_required
def transaction_list(request):
    """List all thread transactions"""
    transactions = ThreadTransaction.objects.select_related(
        'thread', 'related_master'
    ).order_by('-created_at')

    thread_id = request.GET.get('thread')
    trans_type = request.GET.get('type')

    if thread_id:
        transactions = transactions.filter(thread_id=thread_id)
    if trans_type:
        transactions = transactions.filter(transaction_type=trans_type)

    context = {
        'transactions': transactions[:100],
        'threads': Thread.objects.all(),
        'selected_thread': thread_id,
        'selected_type': trans_type,
        'transaction_types': TransactionType.choices,
    }
    return render(request, 'threads/transactions.html', context)