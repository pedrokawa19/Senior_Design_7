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


class HistoryFilterForm(forms.Form):
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    item = forms.CharField(required=False, max_length=128)
    party = forms.CharField(required=False, max_length=128)
    page = forms.IntegerField(required=False, min_value=1, max_value=10)
    sort_column = forms.IntegerField(required=False, min_value=0, max_value=10)
    sort_direction = forms.ChoiceField(required=False, choices=(("asc", "Ascending"), ("desc", "Descending")))
    refresh = forms.ChoiceField(required=False, choices=(("0", "No"), ("1", "Yes")))

    def clean(self):
        data = super().clean()
        if (data.get("sort_column") is not None) != bool(data.get("sort_direction")):
            raise forms.ValidationError("Choose both a sort column and direction.")
        start, end = data.get("start_date"), data.get("end_date")
        if start and end and start > end:
            raise forms.ValidationError("Start date must be on or before end date.")
        return data
