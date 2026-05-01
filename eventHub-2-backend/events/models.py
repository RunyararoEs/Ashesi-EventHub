import re
import uuid

from django.conf import settings
from django.db import models


#event class that represents an event students can browse and sign up to attend
class Event(models.Model):
    #each event must have a unique id
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #each event belongs to a single club
    club = models.ForeignKey('users.Club', on_delete=models.CASCADE, related_name='events',)
    #event information such as the event title and the slug field to make it url friendly
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280)
    #description of the event and location
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)

    #include start and end times of event for scheduling purposes
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    # Factory Pattern — capacity drives the REGISTERED vs WAITLIST decision.
    # null means unlimited: the RegistrationFactory always assigns REGISTERED.
    # A positive integer caps confirmed registrations; latecomers go to WAITLIST.
    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Maximum confirmed registrations. Leave blank for unlimited.',
    )

    #in case that events are cancelled set to True but default its active
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        #order events by the time they start
        ordering = ['starts_at']
        #preventing clubs from having an event with the same slug
        constraints = [models.UniqueConstraint(fields=['club', 'slug'], name='events_event_club_slug_uniq',),]
        #access info from the database queries
        indexes = [models.Index(fields=['club', 'starts_at']), models.Index(fields=['starts_at']),]

    # ── Prototype Pattern ─────────────────────────────────────────────────────
    def clone(self, new_title=None, new_starts_at=None, new_ends_at=None):
        """
        Prototype Pattern — create a new Event by copying this one.

        The Prototype pattern creates new objects by copying (cloning) an
        existing instance rather than constructing from scratch. This is
        useful for recurring events where most fields stay the same
        (club, description, location, capacity) and only the title, slug,
        and dates need updating for the new occurrence.

        The original event is never modified. Registrations are NOT copied —
        the clone starts fresh with zero registrations, is_cancelled=False,
        and a new UUID assigned automatically by the field default.

        Args:
            new_title     (str, optional)      : Title for the clone. Defaults
                                                 to '<original title> (Copy)'.
            new_starts_at (datetime, optional) : Start time for the clone.
            new_ends_at   (datetime, optional) : End time for the clone.

        Returns:
            Event: the saved clone instance.
        """
        title = new_title or f"{self.title} (Copy)"

        # Build a slug from the new title
        base_slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:270]

        # Ensure the slug is unique within this club
        slug = base_slug
        suffix = 1
        while Event.objects.filter(club=self.club, slug=slug).exists():
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        return Event.objects.create(
            club=self.club,
            title=title,
            slug=slug,
            description=self.description,
            location=self.location,
            capacity=self.capacity,
            starts_at=new_starts_at or self.starts_at,
            ends_at=new_ends_at or self.ends_at,
            is_cancelled=False,
        )

    def __str__(self):
        return f"{self.title} ({self.club.name})"


#class for registering to events
class EventRegistration(models.Model):
    class Status(models.TextChoices):
        REGISTERED = 'registered', 'Registered'
        WAITLIST   = 'waitlist',   'Waitlist'
        CANCELLED  = 'cancelled',  'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations',)
    user  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations',)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REGISTERED,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['event', 'user'], name='events_eventregistration_event_user_uniq',),]
        indexes = [models.Index(fields=['event', 'status']),]

    def __str__(self):
        return f"{self.user} → {self.event.title} ({self.status})"
