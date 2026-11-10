from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from .models import Building, Category, Event


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
