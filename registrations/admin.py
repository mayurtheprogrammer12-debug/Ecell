from django.contrib import admin
from django.db.models import Q
from unfold.admin import ModelAdmin
from .models import UserRegistration, FreeEntryWhitelist

class IsFreeEligibleFilter(admin.SimpleListFilter):
    title = 'Is Free Eligible'
    parameter_name = 'is_free_eligible'

    def lookups(self, request, model_admin):
        return (
            ('Yes', 'Yes'),
            ('No', 'No'),
        )

    def queryset(self, request, queryset):
        # We need to filter based on both domain and specific email whitelist
        # This is a bit complex in queryset, so let's stick to the current email check 
        # but also check if email domain is in Whitelisted Domains
        
        whitelisted_domains = FreeEntryWhitelist.objects.filter(whitelist_type='DOMAIN').values_list('value', flat=True)
        whitelisted_emails = FreeEntryWhitelist.objects.filter(whitelist_type='EMAIL').values_list('value', flat=True)

        if self.value() == 'Yes':
            # Check pccoepune.org OR specific emails OR emails with whitelisted domains
            q = Q(email__endswith='@pccoepune.org') | Q(email__in=whitelisted_emails)
            for domain in whitelisted_domains:
                q |= Q(email__endswith='@' + domain)
            return queryset.filter(q)
            
        if self.value() == 'No':
            q = Q(email__endswith='@pccoepune.org') | Q(email__in=whitelisted_emails)
            for domain in whitelisted_domains:
                q |= Q(email__endswith='@' + domain)
            return queryset.exclude(q)
            
        return queryset

@admin.register(UserRegistration)
class UserRegistrationAdmin(ModelAdmin):
    list_display = ('name', 'email', 'registration_type', 'payment_status', 'round1_completed', 'selected_for_round2', 'round2_unlocked', 'final_price')
    list_filter = ('registration_type', 'payment_status', 'round1_completed', 'selected_for_round2', 'round2_unlocked', IsFreeEligibleFilter)
    search_fields = ('name', 'email', 'phone', 'college', 'org_name', 'city')
    readonly_fields = ('created_at',)

@admin.register(FreeEntryWhitelist)
class FreeEntryWhitelistAdmin(ModelAdmin):
    list_display = ('value', 'whitelist_type', 'description')
    list_filter = ('whitelist_type',)
    search_fields = ('value', 'description')
