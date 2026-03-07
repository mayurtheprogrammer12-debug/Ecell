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
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import UserRegistration
from .forms import ParticipantForm, ExhibitorForm
from payments.models import PaymentRecord

def generate_upi_qr(upi_id, payee_name, amount, transaction_note):
    # Simplest possible UPI link
    # pa: Payee address
    # pn: Payee name (Simple, no spaces/special chars)
    # am: Amount (2 decimal places)
    # cu: Currency
    # tn: Note
    
    payee_name_simple = "PCCOE" 
    amount_formatted = "{:.2f}".format(float(amount))
    transaction_note_encoded = urllib.parse.quote(transaction_note)
    
    # We remove mc, mode, and tr to make it a 'simple' personal payment link
    # which avoids triggering 'Business Intent' security checks in some apps
    upi_url = f"upi://pay?pa={upi_id}&pn={payee_name_simple}&am={amount_formatted}&cu=INR&tn={transaction_note_encoded}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return qr_base64, upi_url

def create_auth_user(email, password, registration):
    user = User.objects.create_user(username=email, email=email, password=password)
    registration.user = user
    registration.save()
    return user

def landing_page(request):
    return render(request, 'registrations/landing.html')

def register_choice(request):
    return render(request, 'registrations/choice.html')

def register_participant(request):
    role = request.GET.get('role', 'student').upper()
    if role not in ['STUDENT', 'VISITOR', 'PARTICIPANT']:
        role = 'PARTICIPANT'
        
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            # Map role to registration type
            if role == 'VISITOR':
                registration.registration_type = 'VISITOR'
            else:
                registration.registration_type = 'PARTICIPANT'
            
            # Logic for fee
            base_price = settings.BASE_PARTICIPANT_FEE
            if role == 'VISITOR':
                # Maybe visitors have a different fee? For now assume same as participant
                # but we could adjust here.
                pass
            
            registration.base_price = base_price

            if registration.is_pccoe:
                registration.discount_amount = base_price
                registration.final_price = 0
                registration.payment_status = 'FREE'
                registration.reference_id = f"FREE-{uuid.uuid4().hex[:8].upper()}"
                registration.save()
                
                # Create User Account
                create_auth_user(registration.email, form.cleaned_data['password'], registration)
                
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
                    
                    # Create User Account
                    create_auth_user(registration.email, form.cleaned_data['password'], registration)
                    
                    if referral_code_obj:
                        referral_code_obj.current_usage += 1
                        referral_code_obj.save()
                    return redirect('registration_success', reg_id=registration.id)

                registration.payment_status = 'PENDING'
                registration.reference_id = f"ECELL-REG-{uuid.uuid4().hex[:8].upper()}"
                registration.save()
                
                # Create User Account
                create_auth_user(registration.email, form.cleaned_data['password'], registration)
                
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
                    'reference_id': registration.reference_id,
                    'role': role
                }
                return render(request, 'registrations/payment.html', context)
    else:
        form = ParticipantForm()
    
    return render(request, 'registrations/participant_form.html', {'form': form, 'role': role})

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
            
            # Create User Account
            create_auth_user(registration.email, form.cleaned_data['password'], registration)
            
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

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'registrations/login.html', {'error': 'Invalid credentials'})
    return render(request, 'registrations/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def dashboard(request):
    registration = getattr(request.user, 'registration', None)
    if not registration:
        return redirect('register_choice') # Or handle case where user is admin with no registration
    
    context = {
        'registration': registration,
    }
    return render(request, 'registrations/dashboard.html', context)

@login_required(login_url='login')
def round2_view(request):
    registration = getattr(request.user, 'registration', None)
    if not registration or not registration.selected_for_round2:
        return redirect('dashboard')
    
    return render(request, 'registrations/round2.html', {'registration': registration})
