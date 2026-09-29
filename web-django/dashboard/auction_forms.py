"""Validation for Auction uploads and synchronized measurement filters."""
from django import forms

from .services.auction import MAX_FILE_BYTES

COMPARISONS = [('eq', '='), ('le', '≤'), ('ge', '≥')]


class AuctionUploadForm(forms.Form):
    file = forms.FileField(label='Auction list', widget=forms.ClearableFileInput(attrs={'accept': '.xlsx,.csv'}))

    def clean_file(self):
        file = self.cleaned_data['file']
        if file.size == 0 or file.size > MAX_FILE_BYTES:
            raise forms.ValidationError('Choose a nonempty file no larger than 10 MB.')
        if not file.name.lower().endswith(('.xlsx', '.csv')):
            raise forms.ValidationError('Choose an .xlsx or .csv file.')
        return file


class AuctionFilterForm(forms.Form):
    width_op = forms.ChoiceField(choices=COMPARISONS, label='Width comparison')
    width = forms.DecimalField(min_value=0.000001, max_digits=18, decimal_places=6, label='Width (inches)')
    weight_op = forms.ChoiceField(choices=COMPARISONS, label='Weight comparison')
    weight = forms.DecimalField(min_value=0.000001, max_digits=18, decimal_places=6, label='Weight (lb)')
