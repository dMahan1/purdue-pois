"""
Data migration: fills the database with starter categories, buildings and
sample events so the drop-downs and search page have something to show.

Data migrations use apps.get_model(...) instead of importing the models
directly, so they work with the model as it existed at this migration,
even if models.py changes later.
"""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.db import migrations

CATEGORIES = [
    "Academic",
    "Arts",
    "Career",
    "Club Meeting",
    "Food",
    "Other",
    "Social",
    "Sports",
]

BUILDINGS = [
    ("ARMS", "Neil Armstrong Hall of Engineering", "40.431000", "-86.914900"),
    ("BRNG", "Beering Hall", "40.425500", "-86.916000"),
    ("CREC", "France A. Cordova Recreational Sports Center", "40.428500", "-86.922000"),
    ("DSAI", "Hall of Data Science and AI", "40.428200", "-86.915700"),
    ("EE", "Electrical Engineering Building", "40.428800", "-86.911800"),
    ("ELLT", "Elliott Hall of Music", "40.428000", "-86.915300"),
    ("HAAS", "Haas Hall", "40.426600", "-86.916800"),
    ("KRAN", "Krannert Building", "40.423600", "-86.910800"),
    ("LWSN", "Lawson Computer Science Building", "40.427700", "-86.916900"),
    ("MACK", "Mackey Arena", "40.433800", "-86.916600"),
    ("MATH", "Mathematical Sciences Building", "40.426200", "-86.915600"),
    ("PHYS", "Physics Building", "40.430200", "-86.913500"),
    ("PMU", "Purdue Memorial Union", "40.424600", "-86.910900"),
    ("STEW", "Stewart Center", "40.425100", "-86.912800"),
    ("WALC", "Wilmeth Active Learning Center", "40.427400", "-86.913200"),
]

# (title, category, building code, room, days from today, start hour, hours long, organizer, description)
EVENTS = [
    ("CS Club Meetup", "Club Meeting", "LWSN", "B151", 0, 18, 1.5, "Purdue ACM", "Weekly ACM meeting with a short tech talk."),
    ("Calc II Study Session", "Academic", "MATH", "175", 1, 19, 2, "Math Help Center", "Drop-in help for series and integrals."),
    ("Resume Review Drop-in", "Career", "WALC", "1055", 1, 13, 2, "Center for Career Opportunities", "Bring a printed resume for quick feedback."),
    ("Pickup Basketball", "Sports", "CREC", "Court 3", 2, 20, 2, "Intramural Sports", "Casual games, all skill levels."),
    ("Free Pizza Friday", "Food", "PMU", "Main Lounge", 2, 12, 1, "Purdue Student Union Board", "First come, first served."),
    ("Jazz Band Concert", "Arts", "ELLT", "", 3, 19.5, 2, "Purdue Bands & Orchestras", "Fall jazz ensemble performance."),
    ("Intro to Machine Learning Talk", "Academic", "DSAI", "1001", 3, 16, 1, "Data Mine", "Beginner-friendly overview of ML."),
    ("Engineering Career Fair Prep", "Career", "ARMS", "1010", 4, 17, 1.5, "Society of Women Engineers", "Tips on talking to recruiters."),
    ("Board Game Night", "Social", "PMU", "North Ballroom", 4, 19, 3, "Purdue Gaming Club", "Bring a game or play one of ours."),
    ("Physics Colloquium", "Academic", "PHYS", "112", 5, 15.5, 1, "Department of Physics", "Guest lecture on quantum materials."),
    ("Hackathon Kickoff", "Club Meeting", "WALC", "B074", 6, 18, 2, "Purdue Hackers", "Team formation and idea pitches."),
    ("Psych Research Fair", "Academic", "BRNG", "1222", 6, 14, 2, "Department of Psychological Sciences", "Meet labs looking for undergrad RAs."),
    ("Volleyball Tournament", "Sports", "CREC", "Gym 2", 7, 10, 4, "Intramural Sports", "Sign up as a team of six."),
    ("Stats Office Hours", "Academic", "MATH", "215", 7, 15, 2, "STAT 350 TAs", "Exam review and homework help."),
    ("Mock Interviews", "Career", "KRAN", "G010", 8, 9, 3, "Krannert Career Services", "30-minute practice interviews."),
    ("Open Mic Night", "Arts", "STEW", "Fowler Hall", 9, 20, 2, "Purdue Musical Organizations", "Music, poetry and comedy."),
    ("Taco Tuesday Social", "Food", "HAAS", "Lobby", 9, 12, 1.5, "Statistics Club", "Free tacos and meet the club."),
    ("Basketball Watch Party", "Social", "MACK", "Concourse", 10, 18.5, 3, "Boilermaker Spirit Squad", "Cheer on the Boilers together."),
    ("Circuits Lab Open House", "Academic", "EE", "170", 11, 13, 2, "School of ECE", "Tour the labs and try a demo circuit."),
    ("Campus Cleanup", "Other", "STEW", "Front Steps", 12, 9, 2, "Purdue Sustainability Council", "Gloves and bags provided."),
]

CAMPUS_TZ = ZoneInfo("America/Indiana/Indianapolis")


def seed(apps, schema_editor):
    Category = apps.get_model("events", "Category")
    Building = apps.get_model("events", "Building")
    Event = apps.get_model("events", "Event")

    categories = {name: Category.objects.create(name=name) for name in CATEGORIES}

    buildings = {}
    for code, name, lat, lng in BUILDINGS:
        buildings[code] = Building.objects.create(code=code, name=name, latitude=lat, longitude=lng)

    today = date.today()
    for title, category, code, room, days, start_hour, hours, organizer, description in EVENTS:
        day = today + timedelta(days=days)
        start = datetime.combine(day, time(0, 0), tzinfo=CAMPUS_TZ) + timedelta(hours=start_hour)
        Event.objects.create(
            title=title,
            description=description,
            category=categories[category],
            building=buildings[code],
            room=room,
            start_time=start,
            end_time=start + timedelta(hours=hours),
            organizer=organizer,
        )


def unseed(apps, schema_editor): 
    apps.get_model("events", "Event").objects.all().delete()
    apps.get_model("events", "Category").objects.filter(name__in=CATEGORIES).delete()
    codes = [b[0] for b in BUILDINGS]
    apps.get_model("events", "Building").objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
