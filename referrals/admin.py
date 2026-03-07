from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import ReferralCode

@admin.register(ReferralCode)
class ReferralCodeAdmin(ModelAdmin):
    list_display = (
        'referral_code', 'ambassador_name', 'ambassador_email', 
        'discount_percentage', 'current_usage', 'max_usage', 'is_valid'
    )
    list_filter = ('created_at', 'discount_percentage')
    search_fields = ('referral_code', 'ambassador_name', 'ambassador_email')
    readonly_fields = ('created_at', 'current_usage')
