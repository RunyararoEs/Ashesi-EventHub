from django.contrib import admin
from events.models import Event, EventRegistration

admin.site.register(Event)
admin.site.register(EventRegistration)