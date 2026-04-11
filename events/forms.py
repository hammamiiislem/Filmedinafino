from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from .models import Event
from guard.forms import FlowbiteFormMixin

class EventForm(FlowbiteFormMixin, forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'start_date', 'end_date', 
            'registration_link', 'location'
        ]
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'location': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-gray-50 p-2.5 text-sm text-gray-900 focus:ring-blue-500 focus:border-blue-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 7-day lead time check is already in services, but we can add it here for UI feedback too
        min_start = timezone.now() + timedelta(days=7)
        self.fields['start_date'].help_text = _("Must be at least 7 days from now.")

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date and start_date < timezone.now() + timedelta(days=7):
            raise forms.ValidationError(_("Events must be submitted at least 7 days before the start date."))
        return start_date

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and end <= start:
            self.add_error('end_date', _("End date must be after start date."))
        return cleaned_data
