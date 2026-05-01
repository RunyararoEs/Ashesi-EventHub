from django.urls import path
from users import views

urlpatterns = [
    # Auth
    path('register/', views.RegisterView.as_view(), name='register'),
    path('me/',       views.MeView.as_view(),       name='me'),

    # System admin
    path('all/',                views.UserListView.as_view(),        name='user-list'),
    path('assign-club-admin/',  views.AssignClubAdminView.as_view(), name='assign-club-admin'),

    # Transfer requests
    path('transfer-request/',                    views.TransferRequestCreateView.as_view(),  name='transfer-request-create'),
    path('transfer-request/list/',               views.TransferRequestListView.as_view(),    name='transfer-request-list'),
    path('transfer-request/<uuid:pk>/approve/',  views.TransferRequestApproveView.as_view(), name='transfer-request-approve'),
    path('transfer-request/<uuid:pk>/reject/',   views.TransferRequestRejectView.as_view(),  name='transfer-request-reject'),
]
