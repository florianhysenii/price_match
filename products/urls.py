from django.urls import path
from .views import ProductListCreateView, ProductDetailView
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('products.urls')),  # Include products app URLs
]