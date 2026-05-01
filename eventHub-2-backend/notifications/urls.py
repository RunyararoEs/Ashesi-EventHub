from django.urls import path
from notifications import views

urlpatterns = [
    path('mark-all-read/', views.NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<uuid:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification-read'),
]