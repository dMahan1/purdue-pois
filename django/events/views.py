from django.shortcuts import render

from .forms import EventSearchForm
from .services import search_events


def home(request):
    # `request.GET or None`: with no query string the form is "unbound",
    # so it shows its defaults and no error messages.
    form = EventSearchForm(request.GET or None)

    # If the filters are invalid (e.g. end date before start date), the form
    # shows its errors and we fall back to listing all upcoming events.
    filters = form.cleaned_data if form.is_valid() else {}

    context = {
        "form": form,
        "events": search_events(filters),
    }
    return render(request, "events/home.html", context)
