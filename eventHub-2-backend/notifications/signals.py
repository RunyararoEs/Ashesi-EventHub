"""
notifications/signals.py

Observer Pattern — Automatic Notification Triggering + Waitlist Promotion
--------------------------------------------------------------------------
The Observer pattern defines a one-to-many dependency: when one object
(the Subject) changes state, all its dependents (Observers) are notified
automatically.

In Django, this is implemented using signals:
  - The Subject  → Django models (Event, EventRegistration)
  - The Observers → the receiver functions below
  - The mechanism → Django's post_save signal dispatcher

When an Event or EventRegistration is saved, Django automatically calls
every receiver function connected to that model's signal. The receivers
then use the NotificationBuilder to construct and send the right
notification to the right users.

Waitlist promotion:
  When a confirmed registration is cancelled and the event has a capacity
  limit, the first person on the waitlist (by join date) is automatically
  promoted to REGISTERED. This triggers another post_save on their
  EventRegistration, which in turn fires a registration_confirmed
  notification to them automatically — no extra notification code needed.

Signals connected here:
  post_save → Event               : event_created, event_updated
  pre_save  → Event               : detect is_cancelled changing to True
  pre_save  → EventRegistration   : snapshot previous status
  post_save → EventRegistration   : confirmed, waitlist, cancelled + promotion
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from events.models import Event, EventRegistration
from notifications.builder import NotificationBuilder


# ── Helper ────────────────────────────────────────────────────────────────────

def _get_registered_users(event):
    """Return all users with an active confirmed registration for an event."""
    return [
        reg.user
        for reg in event.registrations.filter(
            status=EventRegistration.Status.REGISTERED
        ).select_related('user')
    ]


def _promote_from_waitlist(event):
    """
    Waitlist promotion — called when a confirmed spot opens up.

    Finds the earliest waitlisted registration for the event (by
    created_at) and promotes it to REGISTERED. Saving the record
    triggers post_save again, which fires a registration_confirmed
    notification to the promoted user automatically.

    Only runs when the event has a capacity set — unlimited events
    never produce a waitlist so there is nothing to promote from.
    """
    if event.capacity is None:
        return  # unlimited event, no waitlist to promote from

    next_in_line = (
        event.registrations
        .filter(status=EventRegistration.Status.WAITLIST)
        .order_by('created_at')
        .first()
    )

    if next_in_line:
        next_in_line.status = EventRegistration.Status.REGISTERED
        next_in_line.save()


# ── Event Signals ─────────────────────────────────────────────────────────────

@receiver(pre_save, sender=Event)
def capture_event_before_save(sender, instance, **kwargs):
    """
    Observer — fires BEFORE an Event is saved.

    Captures whether is_cancelled was False before the save so
    post_save can detect the moment it flips to True.
    """
    if instance.pk:
        try:
            instance._pre_save_cancelled = Event.objects.filter(
                pk=instance.pk
            ).values_list('is_cancelled', flat=True).get()
        except Event.DoesNotExist:
            instance._pre_save_cancelled = False
    else:
        instance._pre_save_cancelled = False


@receiver(post_save, sender=Event)
def handle_event_saved(sender, instance, created, **kwargs):
    """
    Observer — fires AFTER an Event is saved.

    Three cases:
    1. Brand new event → notify users interested in this club.
    2. Event just cancelled → notify all confirmed registrants.
    3. Event updated normally → notify all confirmed registrants.
    """
    if created:
        interested_users = list(
            EventRegistration.objects.filter(
                event__club=instance.club,
            ).select_related('user')
            .values_list('user', flat=True)
            .distinct()
        )

        from django.contrib.auth import get_user_model
        User = get_user_model()
        users = User.objects.filter(pk__in=interested_users)

        for user in users:
            NotificationBuilder() \
                .recipient(user) \
                .for_event_created(instance) \
                .build()
        return

    was_cancelled = getattr(instance, '_pre_save_cancelled', False)

    if instance.is_cancelled and not was_cancelled:
        # Event just got cancelled — notify confirmed registrants
        registered_users = _get_registered_users(instance)
        for user in registered_users:
            NotificationBuilder() \
                .recipient(user) \
                .for_event_cancelled(instance) \
                .build()

    elif not instance.is_cancelled:
        # Normal update — notify confirmed registrants of the change
        registered_users = _get_registered_users(instance)
        for user in registered_users:
            NotificationBuilder() \
                .recipient(user) \
                .for_event_updated(instance) \
                .build()


# ── EventRegistration Signals ─────────────────────────────────────────────────

@receiver(pre_save, sender=EventRegistration)
def capture_registration_before_save(sender, instance, **kwargs):
    """
    Observer — fires BEFORE an EventRegistration is saved.

    Snapshots the previous status so post_save can detect transitions.
    """
    if instance.pk:
        try:
            instance._pre_save_status = EventRegistration.objects.filter(
                pk=instance.pk
            ).values_list('status', flat=True).get()
        except EventRegistration.DoesNotExist:
            instance._pre_save_status = None
    else:
        instance._pre_save_status = None


@receiver(post_save, sender=EventRegistration)
def handle_registration_saved(sender, instance, created, **kwargs):
    """
    Observer — fires AFTER an EventRegistration is saved.

    Four cases:
    1. New registration → REGISTERED : notify user, spot confirmed.
    2. New registration → WAITLIST   : notify user, they are queued.
    3. Existing registration → CANCELLED : notify user, then promote
       the next person on the waitlist if the event has a capacity.
    4. Existing registration → REGISTERED (promoted from waitlist) :
       notify user their waitlist spot was confirmed.
       (This case is triggered automatically by _promote_from_waitlist.)
    """
    prev_status = getattr(instance, '_pre_save_status', None)

    if created:
        # Case 1 — new confirmed registration
        if instance.status == EventRegistration.Status.REGISTERED:
            NotificationBuilder() \
                .recipient(instance.user) \
                .for_registration_confirmed(instance.event) \
                .build()

        # Case 2 — new waitlist registration
        elif instance.status == EventRegistration.Status.WAITLIST:
            NotificationBuilder() \
                .recipient(instance.user) \
                .for_registration_waitlist(instance.event) \
                .build()

    else:
        # Case 3 — existing registration just cancelled
        if (
            instance.status == EventRegistration.Status.CANCELLED
            and prev_status != EventRegistration.Status.CANCELLED
        ):
            NotificationBuilder() \
                .recipient(instance.user) \
                .for_registration_cancelled(instance.event) \
                .build()

            # A confirmed spot just opened up — promote from waitlist
            if prev_status == EventRegistration.Status.REGISTERED:
                _promote_from_waitlist(instance.event)

        # Case 4 — promoted from WAITLIST to REGISTERED
        elif (
            instance.status == EventRegistration.Status.REGISTERED
            and prev_status == EventRegistration.Status.WAITLIST
        ):
            NotificationBuilder() \
                .recipient(instance.user) \
                .for_registration_confirmed(instance.event) \
                .build()