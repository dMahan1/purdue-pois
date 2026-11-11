from django import forms

from .models import Building, Category, Event

RADIUS_CHOICES = [
    ("0.25", "0.25 mi"),
    ("0.5", "0.5 mi"),
    ("0.75", "0.75 mi"),
    ("1", "1 mi"),
    ("2", "2 mi"),
]

class EventSearchForm(forms.Form):
    """The search panel on the homepage. Submitted with GET, so every filter
    ends up in the URL (shareable, and the back button works)."""

    q = forms.CharField(label="Search", required=False, max_length=100)
 
    category = forms.ModelChoiceField(
        queryset=Category.objects.order_by("name"),
        required=False,
        empty_label="All",
    )
    building = forms.ModelChoiceField(
        queryset=Building.objects.order_by("code"),
        required=False,
        empty_label="Any",
        label="Near building",
    )

    radius = forms.TypedChoiceField(
        label="Within",
        choices=RADIUS_CHOICES,
        coerce=float,
        required=False,
        empty_value=None,
        initial="0.5",
    )
    date_from = forms.DateField(
        label="From", required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    date_to = forms.DateField(
        label="To", required=False, widget=forms.DateInput(attrs={"type": "date"})
    )

    # Filled in by the "Use my location" button (browser geolocation).
    lat = forms.FloatField(
        required=False, min_value=-90, max_value=90, widget=forms.HiddenInput
    )
    lng = forms.FloatField(
        required=False, min_value=-180, max_value=180, widget=forms.HiddenInput
    )

    def clean(self):
        # built in Form.clean func
        cleaned = super().clean()
        date_from = cleaned.get("date_from")
        date_to = cleaned.get("date_to")
        if date_from and date_to and date_to < date_from:
            self.add_error("date_to", "The end date must be on or after the start date.")
 
        if (cleaned.get("lat") is None) != (cleaned.get("lng") is None):
            raise forms.ValidationError("Location needs both latitude and longitude.")
        return cleaned

class EventForm(forms.ModelForm):
    """Model form for creating an event, prefix fields so sent data isn't """ 
    prefix = "event"

    class Meta:
        model = Event
        fields = ["title", "description", "category", "building", "room", "start_time", "end_time", "organizer"]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            'end_time': forms.DateTimeInput(attrs= {"type": "datetime-local"}, format="%Y-%m-%dT%H:%M")
        } 


