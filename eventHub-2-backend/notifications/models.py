import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    #code for in-website notifications for events
    #types of notifications :
    #-event created 
    #-event updated 
    #-event cancelled
    #-confirmation for registration
    #-waitlisted for event
    #-cancellation of registration 
    #remineer of events
    class Kind(models.TextChoices):
        EVENT_CREATED = 'event_created', 'New event'
        EVENT_UPDATED = 'event_updated', 'Event updated'
        EVENT_CANCELLED = 'event_cancelled', 'Event cancelled'
        REGISTRATION_CONFIRMED = 'registration_confirmed', 'Registration confirmed'
        REGISTRATION_WAITLIST = 'registration_waitlist', 'Added to waitlist'
        REGISTRATION_CANCELLED = 'registration_cancelled', 'Registration cancelled'
        EVENT_REMINDER = 'event_reminder', 'Event reminder'

    #unique ID for each notification 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #user receiving the notification 
    recipient = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', )
   
    #check who caused the notification 
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_sent',
    )
    #linking notification to the club 
    club = models.ForeignKey(
        'users.Club',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
    )
    #linking notification to the event
    event = models.ForeignKey( 'events.Event', on_delete=models.SET_NULL,  null=True, blank=True, related_name='notifications',)
    #enumerated the kind of notifcation 
    kind = models.CharField(max_length=40, choices=Kind.choices)
    
    #title for preview of the notifications
    title = models.CharField(max_length=255)
    #the main message of the notification 
    body = models.TextField(blank=True)

    #checj when the notifcation was read
    read_at = models.DateTimeField(null=True, blank=True)
    #timestamp for when the notication was created 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        #ordering notifcations based on the recent one 
        ordering = ['-created_at']
        indexes = [models.Index(fields=['recipient', '-created_at']), models.Index(fields=['recipient', 'read_at']),]

    def save(self, *args, **kwargs):
        # Keep club aligned with the event’s club when an event is linked (for queries and tests).
        if self.event_id:
            self.club_id = self.event.club_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} → {self.recipient}"

    @property
    def is_read(self):
        return self.read_at is not None
