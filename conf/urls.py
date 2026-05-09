from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.orders.urls')),
    path('users/', include('apps.users.urls')),  # users/ prefixi bilan
    path('threads/', include('apps.threads.urls')),
    path('products/', include('apps.products.urls')),
    path('reports/', include('apps.reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    try:
        import debug_toolbar

        urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
    except ImportError:
        pass