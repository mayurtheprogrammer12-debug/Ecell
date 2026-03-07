from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import UserRegistration

class IsPccoEFilter(admin.SimpleListFilter):
    title = 'Is PCCOE Student'
    parameter_name = 'is_pccoe'

    def lookups(self, request, model_admin):
        return (
            ('Yes', 'Yes'),
            ('No', 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Yes':
            return queryset.filter(email__endswith='@pccoepune.org')
        if self.value() == 'No':
            return queryset.exclude(email__endswith='@pccoepune.org')
        return queryset

@admin.register(UserRegistration)
class UserRegistrationAdmin(ModelAdmin):
    list_display = ('name', 'email', 'gender', 'age', 'city', 'college', 'registration_type', 'exhibitor_category', 'payment_status', 'final_price', 'referral_code_used')
    list_filter = ('registration_type', 'exhibitor_category', 'payment_status', IsPccoEFilter, 'referral_code_used', 'gender', 'city')
    search_fields = ('name', 'email', 'phone', 'college', 'org_name', 'city')
    readonly_fields = ('created_at',)
    
