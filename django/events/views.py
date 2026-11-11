from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST

from .forms import EventSearchForm, EventForm
from .services import search_events

def render_home(request, event_form, open_create_dialog=False):
    # Helper to not dupe home render code
    search_form = EventSearchForm(request.GET or None)
    filters = search_form.cleaned_data if search_form.is_valid() else {}
    context = {
        "form": search_form,
        "events": search_events(filters),
        "event_form": event_form,
        "open_create_dialog": open_create_dialog,
    }
    return render(request, "events/home.html", context)

def home(request):
    # Now just calls helper to render with an empty event form for dialog boxes
    return render_home(request, EventForm())

@require_POST
def event_create(request):
    # view for creating an event, must have POST so that event necessarily gets input

    form = EventForm(request.POST)
    if form.is_valid():
        with transaction.atomic():
            form.save()
        messages.success(request, "Event Created and Saved")
        return redirect("home")
    # else return with errors
    return render_home(request, form, open_create_dialog=True)



