from django import forms
from .models import UserRegistration
from referrals.models import ReferralCode

class ParticipantForm(forms.ModelForm):
    referral_code = forms.CharField(max_length=50, required=False, help_text="Optional referral code for discount")

    class Meta:
        model = UserRegistration
        fields = ['name', 'gender', 'age', 'phone', 'email', 'city', 'college', 'referral_code']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'age': forms.NumberInput(attrs={'placeholder': 'Age'}),
            'phone': forms.TextInput(attrs={'placeholder': '+91 0000 0000'}),
            'email': forms.EmailInput(attrs={'placeholder': 'nexus@example.com'}),
            'city': forms.TextInput(attrs={'placeholder': 'City'}),
            'college': forms.TextInput(attrs={'placeholder': 'College / Organisation'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['referral_code'].widget.attrs.update({'placeholder': 'DISCOUNT20'})
        self.fields['name'].help_text = "Full legal name as per ID"
        self.fields['gender'].help_text = "Gender identity"
        self.fields['age'].help_text = "Chronological age"
        self.fields['phone'].help_text = "Active contact sequence"
        self.fields['email'].help_text = "Official communication node"
        self.fields['city'].help_text = "City of residence"
        self.fields['college'].help_text = "Institutional affiliation / Organisation"
        self.fields['referral_code'].help_text = "Optional referral code for discount"

    def clean_referral_code(self):
        code = self.cleaned_data.get('referral_code')
        if code:
            try:
                ref_obj = ReferralCode.objects.get(referral_code=code)
                if not ref_obj.is_valid:
                    raise forms.ValidationError('Referral code usage limit exceeded.')
                return ref_obj
            except ReferralCode.DoesNotExist:
                raise forms.ValidationError('Invalid referral code.')
        return None

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserRegistration.objects.filter(email=email).exists():
            raise forms.ValidationError('A registration with this email already exists.')
        return email

class ExhibitorForm(forms.ModelForm):
    class Meta:
        model = UserRegistration
        fields = ['exhibitor_category', 'name', 'age', 'gender', 'email', 'phone', 'org_name', 'description']
        widgets = {
            'exhibitor_category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'age': forms.NumberInput(attrs={'placeholder': 'Age'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'placeholder': 'corp@nexus.ia'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Contact Number'}),
            'org_name': forms.TextInput(attrs={'placeholder': 'Startup / Organization Name'}),
            'description': forms.Textarea(attrs={'placeholder': 'Basic description about business', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['exhibitor_category'].help_text = "Select Partnership Category"
        self.fields['name'].help_text = "Full Name"
        self.fields['age'].help_text = "Age"
        self.fields['gender'].help_text = "Gender"
        self.fields['email'].help_text = "Official Communication Email"
        self.fields['phone'].help_text = "Active Contact Number"
        self.fields['org_name'].help_text = "Startup or Organization Identity"
        self.fields['description'].help_text = "Core business overview"

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserRegistration.objects.filter(email=email).exists():
            raise forms.ValidationError('A registration with this email already exists.')
        return email
