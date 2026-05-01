"""
events/factory.py

Factory Pattern — EventRegistration Status Assignment
------------------------------------------------------
The Factory pattern defines an interface for creating an object but lets
logic inside the factory decide which value to produce. The caller asks
the factory to register a user for an event and gets back the correct
status — it never needs to know the rules that determined it.

Without this pattern, the status decision was inline in the view:
    defaults={'status': EventRegistration.Status.REGISTERED}
That hardcodes REGISTERED for every case and gives the view too much
responsibility. The factory centralises the rule so it can be changed
or extended without touching views at all.

Rules:
    - Event has no capacity set (null)              → always REGISTERED
    - Current confirmed registrations < capacity    → REGISTERED
    - Current confirmed registrations >= capacity   → WAITLIST
"""

from events.models import EventRegistration


class RegistrationFactory:
    """
    Factory that decides the correct EventRegistration status for a
    given user/event combination and creates the registration record.

    Usage:
        factory      = RegistrationFactory(event)
        reg, created = factory.get_or_create(user)
        # reg.status is REGISTERED or WAITLIST — factory decided which
    """

    def __init__(self, event):
        self.event = event

    def _determine_status(self):
        """
        Core factory logic — returns the Status the new registration
        should receive based on current capacity.
        """
        # No capacity limit set → always confirm immediately
        if self.event.capacity is None:
            return EventRegistration.Status.REGISTERED

        # Count only confirmed (non-cancelled, non-waitlist) registrations
        confirmed_count = self.event.registrations.filter(
            status=EventRegistration.Status.REGISTERED
        ).count()

        if confirmed_count < self.event.capacity:
            return EventRegistration.Status.REGISTERED
        else:
            return EventRegistration.Status.WAITLIST

    def get_or_create(self, user):
        """
        Get an existing registration or create a new one with the
        factory-determined status.

        Returns:
            (EventRegistration, created: bool)
            created is True if a new record was made, False if one
            already existed (in which case status is unchanged).
        """
        status = self._determine_status()

        reg, created = EventRegistration.objects.get_or_create(
            event=self.event,
            user=user,
            defaults={'status': status},
        )

        return reg, created
