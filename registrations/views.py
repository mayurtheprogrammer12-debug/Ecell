import json
import uuid
import qrcode
import base64
import urllib.parse
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import UserRegistration
from .forms import ParticipantForm, ExhibitorForm
from payments.models import PaymentRecord

def generate_upi_qr(upi_id, payee_name, amount, transaction_note):
    # Standard UPI parameters:
    # pa: Payee address (UPI ID)
    # pn: Payee name
    # am: Amount
    # cu: Currency (INR)
    # tn: Transaction note
    # tr: Transaction reference ID (Crucial for some apps to track the payment)
    
    payee_name_encoded = urllib.parse.quote(payee_name)
    transaction_note_encoded = urllib.parse.quote(transaction_note)
    
    # tr is often required by PhonePe and GPay to uniquely identify the intent
    # mc=0000 (Generic Merchant Code) and mode=02 (Secure intent) can sometimes help with limits
    upi_url = f"upi://pay?pa={upi_id}&pn={payee_name_encoded}&am={amount}&cu=INR&tn={transaction_note_encoded}&tr={transaction_note}&mc=0000&mode=02"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return qr_base64, upi_url

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
                registration.reference_id = f"FREE-{uuid.uuid4().hex[:8].upper()}"
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
                    registration.reference_id = f"FREE-{uuid.uuid4().hex[:8].upper()}"
                    registration.save()
                    if referral_code_obj:
                        referral_code_obj.current_usage += 1
                        referral_code_obj.save()
                    return redirect('registration_success', reg_id=registration.id)

                registration.payment_status = 'PENDING'
                registration.reference_id = f"ECELL-REG-{uuid.uuid4().hex[:8].upper()}"
                registration.save()
                
                # Save Attempt
                PaymentRecord.objects.create(
                    registration=registration,
                    reference_id=registration.reference_id,
                    amount=registration.final_price,
                    payment_status='pending'
                )

                if referral_code_obj:
                    referral_code_obj.current_usage += 1
                    referral_code_obj.save()
                
                # Render payment template
                upi_id = "princevallecha@upi"
                payee_name = "PCCOE ECell"
                amount = int(registration.final_price)
                
                qr_base64, upi_url = generate_upi_qr(upi_id, payee_name, amount, registration.reference_id)
                
                context = {
                    'registration': registration,
                    'upi_id': upi_id,
                    'amount': amount,
                    'qr_base64': qr_base64,
                    'upi_url': upi_url,
                    'reference_id': registration.reference_id
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
            registration.reference_id = f"FREE-{uuid.uuid4().hex[:8].upper()}"
            registration.save()
            return redirect('registration_success', reg_id=registration.id)
    else:
        form = ExhibitorForm()
    return render(request, 'registrations/exhibitor_form.html', {'form': form})

# Not CSRF exempt because it should be submitted via a normal Django form with csrf token!
def payment_verify(request):
    if request.method == 'POST':
        reg_id = request.POST.get('reg_id')
        transaction_id = request.POST.get('transaction_id')
        screenshot = request.FILES.get('screenshot')
        
        if not reg_id:
            return HttpResponseBadRequest('Invalid registration id')

        registration = get_object_or_404(UserRegistration, id=reg_id)
        
        record = PaymentRecord.objects.filter(registration=registration, reference_id=registration.reference_id).first()
        if record:
            record.transaction_id = transaction_id
            if screenshot:
                record.screenshot = screenshot
            record.payment_status = 'pending'
            record.save()
            
        registration.payment_status = 'PENDING'
        registration.save()
            
        return redirect('registration_success', reg_id=registration.id)

    return HttpResponseBadRequest('Invalid request')

def registration_success(request, reg_id):
    registration = get_object_or_404(UserRegistration, id=reg_id)
    return render(request, 'registrations/success.html', {'registration': registration})
