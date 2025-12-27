# myapp/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile  # <- correct usage


class SignUpForm(UserCreationForm):
    USER_TYPES = Profile.USER_TYPES
    user_type = forms.ChoiceField(choices=USER_TYPES, required=True)
    nid = forms.CharField(required=False)
    phone = forms.CharField(required=False)
    location = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'user_type', 'nid', 'phone', 'location')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user_type = self.cleaned_data.get('user_type')
            nid = self.cleaned_data.get('nid')
            phone = self.cleaned_data.get('phone')
            location = self.cleaned_data.get('location')
            # Inspectors require admin approval by default
            is_approved = False if user_type == 'Inspector' else True
            Profile.objects.create(user=user, user_type=user_type, nid=nid, phone=phone, location=location, is_approved=is_approved)
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['nid', 'phone', 'location']
