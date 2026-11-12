from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST, require_http_methods

from .forms import EventSearchForm, EventForm
from .models import Event
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

def redirect_home(request):
    url = reverse("home")
    if request.GET:
        url += "?" + request.GET.urlencode()
    return redirect(url)

@require_http_methods(["GET", "POST"])
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(request, "Event Updated")
            return redirect_home(request)
    else:
        form = EventForm(instance=event)
    return render(request, "events/edit.html", {"form": form, "event": event})

@require_POST
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    with transaction.atomic():
        event.delete()
    messages.success(request, "Event Deleted")
    return redirect_home(request)




