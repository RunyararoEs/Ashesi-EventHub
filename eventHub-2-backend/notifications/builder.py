"""
notifications/builder.py

Builder Pattern — Notification Construction
-------------------------------------------
The Builder pattern separates the construction of a complex object
from its representation. Here, a Notification has many optional fields
(actor, club, event) and 7 distinct kinds, each with its own title and
body format. Without a builder, every place in the codebase that needs
to create a notification would have to know all those field combinations.

The NotificationBuilder lets the caller describe *what happened* in plain
terms (e.g. .for_event_created(event)) and handles all the title/body
wording and field assignment internally. The caller then calls .build()
to save and return the finished Notification object.

Usage examples (called from signals.py):
    # Notify a student their registration is confirmed
    NotificationBuilder()
        .recipient(user)
        .actor(actor_user)
        .for_registration_confirmed(event)
        .build()

    # Notify all registrants that an event was cancelled
    for reg in event.registrations.filter(status='registered'):
        NotificationBuilder()
            .recipient(reg.user)
            .actor(actor_user)
            .for_event_cancelled(event)
            .build()
"""

from notifications.models import Notification


class NotificationBuilder:
    """
    Builder for Notification objects.

    Step 1 — set the recipient (required):
        .recipient(user)

    Step 2 — optionally set who triggered the notification:
        .actor(user)

    Step 3 — call exactly one notification-type method to set
              kind, title, body, and the linked event/club:
        .for_event_created(event)
        .for_event_updated(event)
        .for_event_cancelled(event)
        .for_registration_confirmed(event)
        .for_registration_waitlist(event)
        .for_registration_cancelled(event)
        .for_event_reminder(event)

    Step 4 — build and save:
        .build()  →  returns the saved Notification instance
    """

    def __init__(self):
        # Required
        self._recipient = None

        # Optional
        self._actor = None
        self._event = None
        self._club = None

        # Set by the notification-type methods below
        self._kind = None
        self._title = None
        self._body = None

    # ── Setters ──────────────────────────────────────────────────────────────

    def recipient(self, user):
        """The user who will receive this notification."""
        self._recipient = user
        return self  # return self so calls can be chained

    def actor(self, user):
        """The user whose action triggered this notification (optional)."""
        self._actor = user
        return self

    # ── Notification type methods ─────────────────────────────────────────────
    # Each method sets kind, title, body, and the linked event/club.
    # They all return self so the chain continues to .build().

    def for_event_created(self, event):
        """A new event has been posted by a club."""
        self._event = event
        self._club = event.club
        self._kind = Notification.Kind.EVENT_CREATED
        self._title = f"New event: {event.title}"
        self._body = (
            f"{event.club.name} just posted a new event — \"{event.title}\" — "
            f"happening on {event.starts_at.strftime('%B %d, %Y at %H:%M')} "
            f"at {event.location or 'TBA'}."
        )
        return self

    def for_event_updated(self, event):
        """An existing event's details have changed."""
        self._event = event
        self._club = event.club
        self._kind = Notification.Kind.EVENT_UPDATED
        self._title = f"Event updated: {event.title}"
        self._body = (
            f"\"{event.title}\" by {event.club.name} has been updated. "
            f"Check the event page for the latest details."
        )
        return self

    def for_event_cancelled(self, event):
        """An event has been cancelled."""
        self._event = event
        self._club = event.club
        self._kind = Notification.Kind.EVENT_CANCELLED
        self._title = f"Event cancelled: {event.title}"
        self._body = (
            f"Unfortunately, \"{event.title}\" by {event.club.name} "
            f"has been cancelled."
        )
        return self

    def for_registration_confirmed(self, event):
        """A student successfully registered for an event."""
        self._event = event
        self._club = event.club
        self._kind = Notification.Kind.REGISTRATION_CONFIRMED
        self._title = f"You're registered: {event.title}"
        self._body = (
            f"Your registration for \"{event.title}\" is confirmed. "
            f"The event starts on {event.starts_at.strftime('%B %d, %Y at %H:%M')} "
            f"at {event.location or 'TBA'}. See you there!"
        )
        return self

    def for_registration_waitlist(self, event):
        """A student was placed on the waitlist for a full event."""
        self._event = event
        self._club = event.club
        self._kind = Notification.Kind.REGISTRATION_WAITLIST
        self._title = f"You're on the waitlist: {event.title}"
        self._body = (
            f"The event \"{event.title}\" is currently full. "
            f"You've been added to the waitlist and will be notified "
            f"if a spot opens up."
        )
        return self

    def for_registration_cancelled(self, event):
        """A student cancelled their registration for an event."""
        self._event = event
        self._club = event.club
        self._kind = Notification.Kind.REGISTRATION_CANCELLED
        self._title = f"Registration cancelled: {event.title}"
        self._body = (
            f"Your registration for \"{event.title}\" has been cancelled. "
            f"You can re-register on the event page if you change your mind."
        )
        return self

    def for_event_reminder(self, event):
        """A reminder sent before an event the student is registered for."""
        self._event = event
        self._club = event.club
        self._kind = Notification.Kind.EVENT_REMINDER
        self._title = f"Reminder: {event.title} is coming up"
        self._body = (
            f"Just a reminder that \"{event.title}\" by {event.club.name} "
            f"starts on {event.starts_at.strftime('%B %d, %Y at %H:%M')} "
            f"at {event.location or 'TBA'}. Don't forget!"
        )
        return self

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self):
        """
        Validate that all required fields are set, then create and
        return the saved Notification instance.
        """
        if self._recipient is None:
            raise ValueError("NotificationBuilder: recipient is required.")
        if self._kind is None:
            raise ValueError(
                "NotificationBuilder: a notification type method must be "
                "called before .build() — e.g. .for_event_created(event)"
            )

        return Notification.objects.create(
            recipient=self._recipient,
            actor=self._actor,
            event=self._event,
            club=self._club,
            kind=self._kind,
            title=self._title,
            body=self._body,
        )
