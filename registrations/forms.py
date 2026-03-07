from django import forms
from .models import UserRegistration
from referrals.models import ReferralCode

class ParticipantForm(forms.ModelForm):
    referral_code = forms.CharField(max_length=50, required=False, help_text="Optional referral code for discount")

    class Meta:
        model = UserRegistration
        fields = ['name', 'email', 'phone', 'college', 'referral_code']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'nexus@example.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+91 0000 0000'}),
            'college': forms.TextInput(attrs={'placeholder': 'Institute Name'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['referral_code'].widget.attrs.update({'placeholder': 'DISCOUNT20'})
        self.fields['name'].help_text = "Full legal name as per ID"
        self.fields['email'].help_text = "Primary communication node"
        self.fields['phone'].help_text = "Active contact sequence"
        self.fields['college'].help_text = "Institutional affiliation"
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
        fields = ['name', 'email', 'phone', 'org_name', 'description', 'website']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Venture Representative'}),
            'email': forms.EmailInput(attrs={'placeholder': 'corp@nexus.ia'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Active ID'}),
            'org_name': forms.TextInput(attrs={'placeholder': 'Venture Identity'}),
            'description': forms.Textarea(attrs={'placeholder': 'Technical Core', 'rows': 4}),
            'website': forms.URLInput(attrs={'placeholder': 'https://nexus.ia'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = "Venture Representative Name"
        self.fields['email'].help_text = "Corporate communication node"
        self.fields['phone'].help_text = "Active contact sequence"
        self.fields['org_name'].help_text = "Venture or entity designation"
        self.fields['description'].help_text = "Brief technical or business core"
        self.fields['website'].help_text = "Digital archive or portfolio"

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserRegistration.objects.filter(email=email).exists():
            raise forms.ValidationError('A registration with this email already exists.')
        return email
