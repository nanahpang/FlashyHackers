from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User,Group


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', )


class CreatePartialGroupForm(forms.ModelForm):
    group_name = forms.CharField(label = 'Group Name:', max_length=30, help_text='*Required.')
    #admin_name = forms.CharField(label = 'Admin Name:', max_length=30, help_text='*Required.')
    class Meta:
        model = Group
        exclude = ['admin_name']