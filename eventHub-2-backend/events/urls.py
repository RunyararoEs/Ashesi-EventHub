from django.urls import path
from events import views

urlpatterns = [
    path('my-registrations/', views.MyRegistrationsView.as_view(), name='my-registrations'),
    path('', views.EventListView.as_view(), name='event-list'),
    path('<uuid:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('<uuid:pk>/register/', views.EventRegisterView.as_view(), name='event-register'),
    path('<uuid:pk>/clone/', views.EventCloneView.as_view(), name='event-clone'),
]
