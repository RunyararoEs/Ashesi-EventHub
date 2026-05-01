from django.contrib import admin
from django.urls import path, include

# Adapter Pattern — auth routes now go through our adapter views,
# NOT simplejwt's views directly. Only jwt_adapter.py imports simplejwt.
from users.views import LoginView, TokenRefreshAdapterView

from eventHub import views_test_runner

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/',   LoginView.as_view(),               name='token_obtain'),
    path('api/auth/refresh/', TokenRefreshAdapterView.as_view(), name='token_refresh'),
    path('api/users/',         include('users.urls')),
    path('api/clubs/',         include('clubs.urls')),
    path('api/events/',        include('events.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('dev/tests/', views_test_runner.test_runner_page, name='test_runner'),
    path('api/dev/run-tests/', views_test_runner.run_tests_api, name='run_tests_api'),
]
