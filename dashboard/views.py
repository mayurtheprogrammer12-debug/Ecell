from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from registrations.models import UserRegistration
from referrals.models import ReferralCode

@staff_member_required
def admin_dashboard(request):
    total_registrations = UserRegistration.objects.count()
    total_participants = UserRegistration.objects.filter(registration_type='PARTICIPANT').count()
    total_exhibitors = UserRegistration.objects.filter(registration_type='EXHIBITOR').count()
    paid_registrations = UserRegistration.objects.filter(payment_status='PAID').count()
    free_registrations = UserRegistration.objects.filter(payment_status='FREE').count()
    
    # Calculate revenue based on Paid registrations
    total_revenue_dict = UserRegistration.objects.filter(payment_status='PAID').aggregate(total_revenue=Sum('final_price'))
    total_revenue = total_revenue_dict['total_revenue'] or 0

    # Ambassador Analytics
    # referral code, ambassador name, number of registrations, revenue generated
    ambassadors = []
    codes = ReferralCode.objects.all()
    for code in codes:
        registrations = UserRegistration.objects.filter(referral_code_used=code)
        num_regs = registrations.count()
        rev_gen_dict = registrations.filter(payment_status='PAID').aggregate(rev=Sum('final_price'))
        rev_gen = rev_gen_dict['rev'] or 0
        ambassadors.append({
            'code': code.referral_code,
            'name': code.ambassador_name,
            'num_regs': num_regs,
            'rev_gen': rev_gen
        })

    context = {
        'total_registrations': total_registrations,
        'total_participants': total_participants,
        'total_exhibitors': total_exhibitors,
        'paid_registrations': paid_registrations,
        'free_registrations': free_registrations,
        'total_revenue': total_revenue,
        'ambassadors': ambassadors,
    }

    return render(request, 'dashboard/dashboard.html', context)
