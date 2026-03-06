from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import PaymentRecord

@admin.register(PaymentRecord)
class PaymentRecordAdmin(ModelAdmin):
    list_display = ('registration', 'amount', 'status', 'razorpay_order_id', 'created_at')
    list_filter = ('status',)
    search_fields = ('razorpay_order_id', 'razorpay_payment_id', 'registration__email')
    readonly_fields = ('created_at', 'updated_at')
