from django import forms
from .models import UserRegistration
from referrals.models import ReferralCode

class ParticipantForm(forms.ModelForm):
    referral_code = forms.CharField(max_length=50, required=False, help_text="Optional referral code for discount")

    class Meta:
        model = UserRegistration
        fields = ['name', 'email', 'phone', 'college']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 bg-gray-50 text-black', 'placeholder': 'John Doe'}),
            'email': forms.EmailInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 bg-gray-50 text-black', 'placeholder': 'john@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 bg-gray-50 text-black', 'placeholder': '+91 9876543210'}),
            'college': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 bg-gray-50 text-black', 'placeholder': 'PCCOE Pune'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['referral_code'].widget.attrs.update({'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 bg-gray-50 text-black', 'placeholder': 'DISCOUNT20'})

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
            'name': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 bg-gray-50 text-black'}),
            'email': forms.EmailInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 bg-gray-50 text-black'}),
            'phone': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 bg-gray-50 text-black'}),
            'org_name': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 bg-gray-50 text-black'}),
            'description': forms.Textarea(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 bg-gray-50 text-black', 'rows': 4}),
            'website': forms.URLInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-3 bg-gray-50 text-black'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserRegistration.objects.filter(email=email).exists():
            raise forms.ValidationError('A registration with this email already exists.')
        return email
