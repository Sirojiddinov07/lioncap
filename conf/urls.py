from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.orders.urls')),  # orders app asosiy
    path('users/', include('apps.users.urls')),
    path('threads/', include('apps.threads.urls')),
    path('products/', include('apps.products.urls')),
    path('reports/', include('apps.reports.urls')),
]

# # Xatolik handlerlari
# handler403 = 'bosh_kiyim_sistemi.apps.users.views.handler403'
# handler404 = 'bosh_kiyim_sistemi.apps.users.views.handler404'
# handler500 = 'bosh_kiyim_sistemi.apps.users.views.handler500'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]