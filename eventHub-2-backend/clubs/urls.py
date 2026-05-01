from django.urls import path
from clubs import views

urlpatterns = [
    path('', views.ClubListView.as_view(), name='club-list'),
    path('<slug:slug>/', views.ClubDetailView.as_view(), name='club-detail'),
]