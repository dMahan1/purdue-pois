"""
The search logic for the homepage (Requirement 2: filter + report).

All database filtering goes through the Django ORM, which sends the values
to the database as query parameters. User input is never pasted into SQL.
"""
import math
from datetime import datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone

from .models import Event

DEFAULT_RADIUS_MILES = 0.5
MILES_PER_DEGREE_LATITUDE = 69.0  # roughly constant everywhere on Earth
EARTH_RADIUS_MILES = 3958.8


def haversine_miles(lat1, lng1, lat2, lng2):
    """Great-circle distance between two points, in miles."""
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def start_of_day(day):
    """Midnight at the start of `day`, in campus time (settings.TIME_ZONE)."""
    return timezone.make_aware(datetime.combine(day, time.min))


def search_events(filters):
    """
    Return a list of events matching `filters` (the search form's cleaned_data).

    Each event gets a `.distance` attribute: miles from the search location,
    or None when no location was given.
    """
    # select_related joins category and building in the same query, so
    # showing them on each card doesn't run one extra query per event.
    events = Event.objects.select_related("category", "building")

    keyword = filters.get("q")
    if keyword:
        # Q objects combine conditions with OR. icontains = case-insensitive LIKE.
        events = events.filter(
            Q(title__icontains=keyword)
            | Q(description__icontains=keyword)
            | Q(organizer__icontains=keyword)
        )

    category = filters.get("category")
    if category:
        events = events.filter(category=category)

    # Date range. We compare start_time against datetimes (not start_time__date)
    # so each day is cut off at campus midnight.
    date_from = filters.get("date_from")
    date_to = filters.get("date_to")
    if date_from:
        events = events.filter(start_time__gte=start_of_day(date_from))
    else:
        # No start date given: hide events that are already over.
        events = events.filter(end_time__gte=timezone.now())
    if date_to:
        # "To Nov 12" includes all of Nov 12, so stop at midnight of Nov 13.
        events = events.filter(start_time__lt=start_of_day(date_to + timedelta(days=1)))

    events = events.order_by("start_time")

    # Where is "here"? The browser location wins; a chosen building is the fallback.
    lat, lng = filters.get("lat"), filters.get("lng")
    building = filters.get("building")
    if lat is None and building:
        lat, lng = float(building.latitude), float(building.longitude)

    if lat is None:
        results = list(events)
        for event in results:
            event.distance = None
        return results

    radius = filters.get("radius") or DEFAULT_RADIUS_MILES

    # Step A (SQL): keep only buildings inside
    # a square box around the center. A degree of longitude gets shorter away
    # from the equator, so its width is scaled by cos(latitude).
    lat_delta = radius / MILES_PER_DEGREE_LATITUDE
    lng_delta = radius / (MILES_PER_DEGREE_LATITUDE * math.cos(math.radians(lat)))
    events = events.filter(
        building__latitude__range=(lat - lat_delta, lat + lat_delta),
        building__longitude__range=(lng - lng_delta, lng + lng_delta),
    )

    # Step B (Python): the box's corners stick out past the circle, so compute
    # the exact distance, drop anything outside the radius, and sort nearest first.
    results = []
    for event in events:
        event.distance = haversine_miles(
            lat, lng, float(event.building.latitude), float(event.building.longitude)
        )
        if event.distance <= radius:
            results.append(event)
    results.sort(key=lambda e: (e.distance, e.start_time))
    return results
