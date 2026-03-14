from django import forms
from django.contrib.auth.models import User
from .models import UserRegistration
from referrals.models import ReferralCode

class ParticipantForm(forms.ModelForm):
    referral_code = forms.CharField(max_length=50, required=False, help_text="Optional referral code for discount")
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Set Password'}), help_text="Secure access key")
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}), help_text="Re-verify access key")

    class Meta:
        model = UserRegistration
        fields = ['name', 'gender', 'age', 'phone', 'email', 'city', 'college', 'referral_code', 'password', 'confirm_password']
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

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserRegistration.objects.filter(email=email).exists():
            raise forms.ValidationError('A registration with this email already exists.')
        return email

class ExhibitorForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Set Password'}), help_text="Secure access key")
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}), help_text="Re-verify access key")

    class Meta:
        model = UserRegistration
        fields = ['exhibitor_category', 'name', 'age', 'gender', 'email', 'phone', 'org_name', 'description', 'password', 'confirm_password']
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

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserRegistration.objects.filter(email=email).exists():
            raise forms.ValidationError('A registration with this email already exists.')
        return email

class Round1SubmissionForm(forms.ModelForm):
    class Meta:
        model = UserRegistration
        fields = ['idea_title', 'idea_description', 'idea_domain', 'idea_agreement']
        widgets = {
            'idea_title': forms.TextInput(attrs={'placeholder': 'Enter your disruptive idea title', 'class': 'premium-input'}),
            'idea_description': forms.Textarea(attrs={'placeholder': 'Describe your solution, target market, and core technology...', 'rows': 6, 'class': 'premium-input'}),
            'idea_domain': forms.TextInput(attrs={'placeholder': 'e.g. Fintech, Edtech, Sustainability...', 'class': 'premium-input'}),
            'idea_agreement': forms.CheckboxInput(attrs={'class': 'premium-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['idea_title'].label = "Project Identity"
        self.fields['idea_description'].label = "Solution Architecture"
        self.fields['idea_domain'].label = "Market Sector"
        self.fields['idea_agreement'].label = "I certify that this project is an original creation and I hold all associated intellectual property rights."
        
        for field in self.fields.values():
            field.required = True
