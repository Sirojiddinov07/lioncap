from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm
from django.contrib.auth.decorators import user_passes_test
from django.template import loader
from django.http import HttpResponse
from django.urls import reverse




@login_required
def profile_view(request):
    """User profile view"""
    return render(request, 'users/profile.html', {'user': request.user})


@login_required
def profile_edit(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil muvaffaqiyatli yangilandi')
            return redirect('users:profile')
        else:
            messages.error(request, 'Xatolik yuz berdi. Iltimos qaytadan urinib ko\'ring.')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'users/profile_edit.html', {'form': form})


def is_admin_or_staff(user):
    return user.is_authenticated and user.role in ['admin', 'staff']


def admin_required(view_func):
    """Faqat admin va staff uchun decorator"""

    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/users/login/')

        if not is_admin_or_staff(request.user):
            messages.error(request, "Bu operatsiyani bajarish uchun sizda yetarli huquqlar mavjud emas!")
            return redirect('orders:dashboard')

        return view_func(request, *args, **kwargs)

    return wrapped_view