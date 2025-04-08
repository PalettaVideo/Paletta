from django.contrib import admin
from .models import Order, OrderDetail

class OrderDetailInline(admin.TabularInline):
    model = OrderDetail
    extra = 0
    readonly_fields = ('added_at',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'library', 'total_price', 'order_date', 'payment_status')
    list_filter = ('payment_status', 'order_date', 'library')
    search_fields = ('user__email', 'id')
    readonly_fields = ('order_date',)
    inlines = [OrderDetailInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'library')

@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'video', 'resolution', 'price', 'download_status')
    list_filter = ('download_status', 'resolution', 'added_at')
    search_fields = ('video__title', 'order__id')
    readonly_fields = ('added_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('order', 'video') 