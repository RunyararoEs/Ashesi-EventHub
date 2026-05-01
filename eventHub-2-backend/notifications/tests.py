from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from events.models import Event
from notifications.models import Notification
from users.models import Club

User = get_user_model()


class NotificationModelTests(TestCase):
    def setUp(self):
        self.club = Club.objects.create(
            name='Notify Club',
            description='d',
            slug='notify-club',
        )
        self.other_club = Club.objects.create(
            name='Other',
            description='d',
            slug='notify-other-club',
        )
        start = timezone.now()
        self.event = Event.objects.create(
            club=self.club,
            title='Meetup',
            slug='meetup',
            starts_at=start,
            ends_at=start + timedelta(hours=1),
        )
        self.recipient = User.objects.create_user(
            email='recv@school.edu', username='recv', password='pw'
        )
        self.actor = User.objects.create_user(
            email='actor@school.edu', username='actor', password='pw'
        )

    def test_save_sets_club_from_event(self):
        n = Notification(
            recipient=self.recipient,
            actor=self.actor,
            club=self.other_club,
            event=self.event,
            kind=Notification.Kind.EVENT_CREATED,
            title='New event',
            body='Come join',
        )
        n.save()
        n.refresh_from_db()
        self.assertEqual(n.club_id, self.club.id)

    def test_club_only_notification(self):
        n = Notification.objects.create(
            recipient=self.recipient,
            kind=Notification.Kind.EVENT_UPDATED,
            title='Club news',
            body='',
            club=self.club,
        )
        self.assertIsNone(n.event_id)
        self.assertEqual(n.club_id, self.club.id)

    def test_is_read_property(self):
        n = Notification.objects.create(
            recipient=self.recipient,
            kind=Notification.Kind.EVENT_REMINDER,
            title='Reminder',
        )
        self.assertFalse(n.is_read)
        n.read_at = timezone.now()
        n.save()
        n.refresh_from_db()
        self.assertTrue(n.is_read)

    def test_recipient_related_name(self):
        Notification.objects.create(
            recipient=self.recipient,
            kind=Notification.Kind.REGISTRATION_CONFIRMED,
            title='OK',
        )
        self.assertEqual(self.recipient.notifications.count(), 1)

    def test_actor_related_name(self):
        Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            kind=Notification.Kind.EVENT_CREATED,
            title='Hi',
        )
        self.assertEqual(self.actor.notifications_sent.count(), 1)

    def test_delete_recipient_cascades_notifications(self):
        Notification.objects.create(
            recipient=self.recipient,
            kind=Notification.Kind.EVENT_CANCELLED,
            title='Off',
        )
        self.recipient.delete()
        self.assertEqual(Notification.objects.count(), 0)
