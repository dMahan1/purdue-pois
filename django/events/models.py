from django.db import models
from django.db.models import F, Q


class Category(models.Model):
    # unique=True also makes the database create an index on name,
    # which helps the "ORDER BY name" query that fills the drop-down.
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Building(models.Model):
    code = models.CharField(max_length=10, unique=True)  # e.g. "WALC"
    name = models.CharField(max_length=100)
    # DecimalField stores exact values, so coordinates don't pick up
    # floating-point rounding. 6 decimal places is roughly 10 cm of precision.
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    class Meta:
        ordering = ["code"]
        indexes = [
            # Supports the "nearby" bounding-box filter:
            # latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?
            models.Index(fields=["latitude", "longitude"], name="building_lat_lng_idx"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Event(models.Model):
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    # PROTECT: the database refuses to delete a category or building
    # while any event still points to it.
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    building = models.ForeignKey(Building, on_delete=models.PROTECT)
    room = models.CharField(max_length=30, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    organizer = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time"]
        indexes = [
            # Supports the default "upcoming events, soonest first" listing.
            models.Index(fields=["start_time"], name="event_start_idx"),
            # Supports "category = X AND start_time in a date range".
            models.Index(fields=["category", "start_time"], name="event_cat_start_idx"),
        ]
        constraints = [
            # Enforced by the database itself, not just by the form.
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="event_end_after_start",
            ),
        ]

    def __str__(self):
        return self.title
