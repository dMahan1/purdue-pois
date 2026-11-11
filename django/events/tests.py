from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import EventSearchForm
from .models import Building, Category, Event
from .services import haversine_miles, search_events


class SeedDataTests(TestCase):
    # The test database runs every migration, including the seed data one.

    def test_seed_data_loaded(self):
        self.assertEqual(Category.objects.count(), 8)
        self.assertEqual(Building.objects.count(), 15)
        self.assertEqual(Event.objects.count(), 20)


class EventConstraintTests(TestCase):
    def setUp(self):
        self.category = Category.objects.get(name="Academic")
        self.building = Building.objects.get(code="WALC")

    def make_event(self, start, end):
        return Event.objects.create(
            title="Test event",
            category=self.category,
            building=self.building,
            start_time=start,
            end_time=end,
            organizer="Tester",
        )

    def test_end_must_be_after_start(self):
        start = timezone.now()
        # atomic() keeps the failed INSERT from breaking the rest of the test.
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_event(start, start - timedelta(hours=1))

    def test_end_equal_to_start_rejected(self):
        start = timezone.now()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make_event(start, start)

    def test_valid_event_saves(self):
        start = timezone.now()
        event = self.make_event(start, start + timedelta(hours=1))
        self.assertIsNotNone(event.pk)

    def test_cannot_delete_category_in_use(self):
        start = timezone.now()
        self.make_event(start, start + timedelta(hours=1))
        with self.assertRaises(ProtectedError):
            self.category.delete()


class SearchTests(TestCase):
    """Tests for search_events(). They use their own buildings and events
    (not the seed data), so fixing the seed coordinates won't break them."""

    def setUp(self):
        Event.objects.all().delete()  # start from an empty event table
        self.academic = Category.objects.create(name="Test Academic")
        self.social = Category.objects.create(name="Test Social")
        # "here" is HERE. NEAR is 0.0045 degrees north (~0.31 mi away).
        # FAR is ~5 miles north.
        self.here = Building.objects.create(code="T-HERE", name="Here", latitude="40.427400", longitude="-86.913200")
        self.near = Building.objects.create(code="T-NEAR", name="Near", latitude="40.431900", longitude="-86.913200")
        self.far = Building.objects.create(code="T-FAR", name="Far", latitude="40.500000", longitude="-86.913200")

        now = timezone.now()
        self.lecture = self.make("Algorithms Lecture", self.academic, self.here, now + timedelta(days=1))
        self.party = self.make("Pizza Party", self.social, self.near, now + timedelta(days=2))
        self.hike = self.make("Long Hike", self.social, self.far, now + timedelta(days=5))
        self.past = self.make("Old Event", self.academic, self.here, now - timedelta(days=3))

    def make(self, title, category, building, start):
        return Event.objects.create(
            title=title, category=category, building=building,
            start_time=start, end_time=start + timedelta(hours=1), organizer="Tester",
        )

    def titles(self, filters):
        return [e.title for e in search_events(filters)]

    def test_no_filters_lists_upcoming_soonest_first(self):
        self.assertEqual(self.titles({}), ["Algorithms Lecture", "Pizza Party", "Long Hike"])

    def test_keyword_is_case_insensitive(self):
        self.assertEqual(self.titles({"q": "pizza"}), ["Pizza Party"])

    def test_keyword_matches_organizer(self):
        self.assertEqual(len(self.titles({"q": "tester"})), 3)

    def test_category_filter(self):
        self.assertEqual(self.titles({"category": self.social}), ["Pizza Party", "Long Hike"])

    def test_date_range_includes_whole_end_day(self):
        today = timezone.localdate()
        filters = {"date_from": today + timedelta(days=2), "date_to": today + timedelta(days=5)}
        self.assertEqual(self.titles(filters), ["Pizza Party", "Long Hike"])

    def test_date_from_can_show_past_events(self):
        filters = {"date_from": timezone.localdate() - timedelta(days=4)}
        self.assertIn("Old Event", self.titles(filters))

    def test_nearby_by_building_sorted_by_distance(self):
        results = search_events({"building": self.here, "radius": 0.5})
        self.assertEqual([e.title for e in results], ["Algorithms Lecture", "Pizza Party"])
        self.assertAlmostEqual(results[0].distance, 0.0)
        self.assertAlmostEqual(results[1].distance, 0.31, places=2)

    def test_small_radius_excludes_near_building(self):
        self.assertEqual(self.titles({"building": self.here, "radius": 0.25}), ["Algorithms Lecture"])

    def test_browser_location_wins_over_building(self):
        # Standing at FAR, but HERE is picked in the drop-down: lat/lng is used.
        filters = {"lat": 40.5, "lng": -86.9132, "building": self.here, "radius": 1}
        self.assertEqual(self.titles(filters), ["Long Hike"])

    def test_no_location_means_no_distance(self):
        self.assertTrue(all(e.distance is None for e in search_events({})))

    def test_haversine_one_degree_latitude(self):
        self.assertAlmostEqual(haversine_miles(40, -86, 41, -86), 69.09, places=1)


class SearchFormTests(TestCase):
    def test_end_date_before_start_date_is_invalid(self):
        form = EventSearchForm({"date_from": "2026-11-12", "date_to": "2026-11-10"})
        self.assertFalse(form.is_valid())
        self.assertIn("date_to", form.errors)

    def test_lat_without_lng_is_invalid(self):
        self.assertFalse(EventSearchForm({"lat": "40.4"}).is_valid())

    def test_dropdowns_come_from_database(self):
        Category.objects.create(name="Brand New Category")
        form = EventSearchForm()
        labels = [label for _, label in form.fields["category"].choices]
        self.assertIn("Brand New Category", labels)


class HomeViewTests(TestCase):
    def test_homepage_lists_upcoming_seed_events(self):
        # Count instead of hard-coding 20: one seed event is "today at 6 PM",
        # which is already over if the tests run late in the evening.
        upcoming = Event.objects.filter(end_time__gte=timezone.now()).count()
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"{upcoming} events found")

    def test_homepage_filters_by_keyword(self):
        response = self.client.get(reverse("home"), {"q": "Jazz"})
        self.assertContains(response, "1 event found")
        self.assertContains(response, "Jazz Band Concert")

    def test_invalid_filters_show_error(self):
        response = self.client.get(reverse("home"), {"date_from": "2026-11-12", "date_to": "2026-11-10"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The end date must be on or after the start date.")

    def test_keyword_with_sql_characters_is_safe(self):
        # The ORM sends this as a parameter, so it's just text to match.
        response = self.client.get(reverse("home"), {"q": "'; DROP TABLE events_event; --"})
        self.assertContains(response, "0 events found")
        self.assertEqual(Event.objects.count(), 20)


class EventCreateTests(TestCase):
    """Tests for the Create Event pop-up (POST /events/create/)."""

    def setUp(self):
        self.category = Category.objects.get(name="Academic")
        self.building = Building.objects.get(code="WALC")
        # A day well in the future, written the way a datetime-local input sends it.
        self.day = (timezone.localdate() + timedelta(days=30)).isoformat()

    def post_data(self, **changes):
        """Valid form data; pass keyword arguments to override fields."""
        data = {
            "title": "Test Workshop",
            "description": "Learn things.",
            "category": self.category.pk,
            "building": self.building.pk,
            "room": "1055",
            "start_time": f"{self.day}T18:00",
            "end_time": f"{self.day}T19:30",
            "organizer": "Test Club",
        }
        data.update(changes)
        # EventForm uses prefix="event", so the browser sends "event-title", etc.
        return {f"event-{name}": value for name, value in data.items()}

    def test_valid_post_creates_event_and_redirects(self):
        before = Event.objects.count()
        response = self.client.post(reverse("event_create"), self.post_data())
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(Event.objects.count(), before + 1)

    def test_success_message_shown_after_redirect(self):
        response = self.client.post(reverse("event_create"), self.post_data(), follow=True)
        self.assertContains(response, "Event Created and Saved")

    def test_times_are_saved_in_campus_time(self):
        self.client.post(reverse("event_create"), self.post_data())
        event = Event.objects.get(title="Test Workshop")
        # localtime() converts the stored UTC value back to settings.TIME_ZONE.
        self.assertEqual(timezone.localtime(event.start_time).hour, 18)
        self.assertEqual(timezone.localtime(event.end_time).minute, 30)

    def test_end_before_start_is_rejected(self):
        before = Event.objects.count()
        data = self.post_data(start_time=f"{self.day}T18:00", end_time=f"{self.day}T17:00")
        response = self.client.post(reverse("event_create"), data)
        self.assertEqual(response.status_code, 200)  # page re-rendered, not redirected
        self.assertContains(response, "End time must be after start time.")
        self.assertEqual(Event.objects.count(), before)

    def test_errors_reopen_dialog_and_keep_input(self):
        data = self.post_data(title="", organizer="Keep Me")
        response = self.client.post(reverse("event_create"), data)
        self.assertTrue(response.context["open_create_dialog"])
        self.assertContains(response, '<dialog id="create-dialog" data-open>')
        self.assertContains(response, 'value="Keep Me"')
        self.assertIn("title", response.context["event_form"].errors)

    def test_unknown_category_is_rejected(self):
        before = Event.objects.count()
        response = self.client.post(reverse("event_create"), self.post_data(category=99999))
        self.assertIn("category", response.context["event_form"].errors)
        self.assertEqual(Event.objects.count(), before)

    def test_get_not_allowed(self):
        response = self.client.get(reverse("event_create"))
        self.assertEqual(response.status_code, 405)

    def test_created_event_shows_up_in_search(self):
        # The Stage 2 "before/after" demo: search, create, search again.
        search = {"q": "Test Workshop"}
        self.assertContains(self.client.get(reverse("home"), search), "0 events found")
        self.client.post(reverse("event_create"), self.post_data())
        self.assertContains(self.client.get(reverse("home"), search), "1 event found")


class CreateDialogTests(TestCase):
    def test_homepage_has_empty_create_form_closed(self):
        response = self.client.get(reverse("home"))
        self.assertFalse(response.context["open_create_dialog"])
        self.assertFalse(response.context["event_form"].is_bound)
        self.assertNotContains(response, '<dialog id="create-dialog" data-open>')

    def test_dialog_dropdowns_come_from_database(self):
        Building.objects.create(code="NEWB", name="Brand New Hall", latitude="40.4", longitude="-86.9")
        response = self.client.get(reverse("home"))
        buildings = response.context["event_form"].fields["building"].queryset
        self.assertTrue(buildings.filter(code="NEWB").exists())
        self.assertContains(response, "NEWB - Brand New Hall")
