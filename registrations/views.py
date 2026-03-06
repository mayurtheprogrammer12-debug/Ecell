import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import UserRegistration
from .forms import ParticipantForm, ExhibitorForm
from payments.models import PaymentRecord
from payments.razorpay_client import create_razorpay_order, verify_razorpay_payment

def landing_page(request):
    return render(request, 'registrations/landing.html')

def register_choice(request):
    return render(request, 'registrations/choice.html')

def register_participant(request):
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.registration_type = 'PARTICIPANT'
            
            # Logic for fee
            base_price = settings.BASE_PARTICIPANT_FEE
            registration.base_price = base_price

            if registration.is_pccoe:
                registration.discount_amount = base_price
                registration.final_price = 0
                registration.payment_status = 'FREE'
                registration.save()
                return redirect('registration_success', reg_id=registration.id)
            else:
                discount_amount = 0
                referral_code_obj = form.cleaned_data.get('referral_code')
                if referral_code_obj:
                    registration.referral_code_used = referral_code_obj
                    discount_percentage = referral_code_obj.discount_percentage
                    discount_amount = (base_price * discount_percentage) / 100
                
                registration.discount_amount = discount_amount
                registration.final_price = base_price - discount_amount
                
                # Apply safe guard
                if registration.final_price <= 0:
                    registration.final_price = 0
                    registration.payment_status = 'FREE'
                    registration.save()
                    if referral_code_obj:
                        referral_code_obj.current_usage += 1
                        referral_code_obj.save()
                    return redirect('registration_success', reg_id=registration.id)

                registration.payment_status = 'PENDING'
                
                # Razorpay Order Create
                try:
                    order = create_razorpay_order(registration.final_price)
                    registration.razorpay_order_id = order['id']
                except Exception as e:
                    print(f"Razorpay Order Error: {e}. Using mock order.")
                    registration.razorpay_order_id = "order_mock_1234"
                    
                registration.save()
                
                # Save Attempt
                PaymentRecord.objects.create(
                    registration=registration,
                    razorpay_order_id=registration.razorpay_order_id,
                    amount=registration.final_price
                )

                if referral_code_obj:
                    referral_code_obj.current_usage += 1
                    referral_code_obj.save()
                
                # Render payment template
                context = {
                    'registration': registration,
                    'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                    'amount': int(registration.final_price * 100)
                }
                return render(request, 'registrations/payment.html', context)
    else:
        form = ParticipantForm()
    
    return render(request, 'registrations/participant_form.html', {'form': form})

def register_exhibitor(request):
    if request.method == 'POST':
        form = ExhibitorForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.registration_type = 'EXHIBITOR'
            registration.payment_status = 'FREE'
            registration.final_price = 0
            registration.save()
            return redirect('registration_success', reg_id=registration.id)
    else:
        form = ExhibitorForm()
    return render(request, 'registrations/exhibitor_form.html', {'form': form})

@csrf_exempt
def payment_verify(request):
    if request.method == 'POST':
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        
        reg_id = request.POST.get('reg_id') # Pass reg_id through form as hidden field to safely identify
        
        if not reg_id:
            # Fallback based on order_id
            registration = UserRegistration.objects.filter(razorpay_order_id=razorpay_order_id).first()
        else:
            registration = UserRegistration.objects.filter(id=reg_id).first()
            
        if not registration:
            return HttpResponseBadRequest('Invalid registration')

        if verify_razorpay_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
            registration.payment_status = 'PAID'
            registration.razorpay_payment_id = razorpay_payment_id
            registration.razorpay_signature = razorpay_signature
            registration.save()
            
            record = PaymentRecord.objects.filter(razorpay_order_id=razorpay_order_id).first()
            if record:
                record.status = 'SUCCESS'
                record.razorpay_payment_id = razorpay_payment_id
                record.razorpay_signature = razorpay_signature
                record.save()
                
            return redirect('registration_success', reg_id=registration.id)
        else:
            registration.payment_status = 'FAILED'
            registration.save()
            
            record = PaymentRecord.objects.filter(razorpay_order_id=razorpay_order_id).first()
            if record:
                record.status = 'FAILED'
                record.error_message = 'Signature verification failed'
                record.save()
                
            return render(request, 'registrations/payment_failed.html', {'registration': registration})

    return HttpResponseBadRequest('Invalid request')

def registration_success(request, reg_id):
    registration = get_object_or_404(UserRegistration, id=reg_id)
    return render(request, 'registrations/success.html', {'registration': registration})
