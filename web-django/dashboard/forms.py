from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username",)


class ConnectionForm(forms.Form):
    user = forms.CharField(max_length=128)
    password = forms.CharField(max_length=1024, required=False)
    host = forms.CharField(max_length=253)
    port = forms.IntegerField(min_value=1, max_value=65535)
    database = forms.CharField(max_length=128)

    def clean_host(self):
        host = self.cleaned_data["host"].strip()
        if "/" in host or " " in host:
            raise forms.ValidationError("Enter a hostname or IP address, without a URL or path.")
        return host.lower()
