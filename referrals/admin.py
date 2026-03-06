from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import ReferralCode

@admin.register(ReferralCode)
class ReferralCodeAdmin(ModelAdmin):
    list_display = ('referral_code', 'ambassador_name', 'discount_percentage', 'current_usage', 'max_usage', 'created_at')
    search_fields = ('referral_code', 'ambassador_name', 'ambassador_email')
    readonly_fields = ('current_usage', 'created_at')
