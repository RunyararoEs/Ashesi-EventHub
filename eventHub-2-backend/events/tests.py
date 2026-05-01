from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from events.models import Event, EventRegistration
from users.models import Club

User = get_user_model()

//doing tests on the club code 
def _club(**kwargs):
    defaults = {
        'name': 'Test Club',
        'description': 'Desc',
        'slug': 'test-club-events',
    }
    defaults.update(kwargs)
    return Club.objects.create(**defaults)

//testing an event  
def _event_times():
    start = timezone.now()
    return start, start + timedelta(hours=2)

//
class EventModelTests(TestCase):
    def setUp(self):
        self.club = _club(slug='event-model-club')

    def test_event_str_and_club_relation(self):
        starts, ends = _event_times()
        event = Event.objects.create(
            club=self.club,
            title='Hack Night',
            slug='hack-night',
            starts_at=starts,
            ends_at=ends,
        )
        self.assertIn('Hack Night', str(event))
        self.assertIn(self.club.name, str(event))
        self.assertEqual(list(self.club.events.all()), [event])

    def test_unique_slug_per_club(self):
        starts, ends = _event_times()
        Event.objects.create(
            club=self.club,
            title='First',
            slug='same-slug',
            starts_at=starts,
            ends_at=ends,
        )
        with self.assertRaises(IntegrityError):
            Event.objects.create(
                club=self.club,
                title='Second',
                slug='same-slug',
                starts_at=starts,
                ends_at=ends,
            )

    def test_same_slug_allowed_across_clubs(self):
        other = _club(name='Other', slug='other-club-slug')
        starts, ends = _event_times()
        Event.objects.create(
            club=self.club,
            title='A',
            slug='shared',
            starts_at=starts,
            ends_at=ends,
        )
        Event.objects.create(
            club=other,
            title='B',
            slug='shared',
            starts_at=starts,
            ends_at=ends,
        )
        self.assertEqual(Event.objects.filter(slug='shared').count(), 2)

    def test_ordering_by_starts_at(self):
        base = timezone.now()
        e2 = Event.objects.create(
            club=self.club,
            title='Later',
            slug='later',
            starts_at=base + timedelta(days=2),
            ends_at=base + timedelta(days=2, hours=1),
        )
        e1 = Event.objects.create(
            club=self.club,
            title='Sooner',
            slug='sooner',
            starts_at=base,
            ends_at=base + timedelta(hours=1),
        )
        ordered = list(Event.objects.filter(club=self.club))
        self.assertEqual(ordered, [e1, e2])

    def test_delete_club_cascades_events(self):
        starts, ends = _event_times()
        Event.objects.create(
            club=self.club,
            title='X',
            slug='x',
            starts_at=starts,
            ends_at=ends,
        )
        self.club.delete()
        self.assertEqual(Event.objects.count(), 0)


class EventRegistrationTests(TestCase):
    def setUp(self):
        self.club = _club(slug='reg-club')
        starts, ends = _event_times()
        self.event = Event.objects.create(
            club=self.club,
            title='Workshop',
            slug='workshop',
            starts_at=starts,
            ends_at=ends,
        )
        self.user = User.objects.create_user(
            email='reg@school.edu', username='reguser', password='pw'
        )

    def test_one_registration_per_user_per_event(self):
        EventRegistration.objects.create(
            event=self.event, user=self.user, status=EventRegistration.Status.REGISTERED
        )
        with self.assertRaises(IntegrityError):
            EventRegistration.objects.create(
                event=self.event,
                user=self.user,
                status=EventRegistration.Status.WAITLIST,
            )

    def test_registration_str(self):
        reg = EventRegistration.objects.create(
            event=self.event, user=self.user
        )
        self.assertIn(self.user.email, str(reg))
        self.assertIn(self.event.title, str(reg))

    def test_delete_event_cascades_registrations(self):
        EventRegistration.objects.create(event=self.event, user=self.user)
        self.event.delete()
        self.assertEqual(EventRegistration.objects.count(), 0)
