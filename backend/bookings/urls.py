from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserMeView, InstructorViewSet, CourseTypeViewSet, SlotsView, BookingViewSet, UserCreateView
)

router = DefaultRouter()
router.register(r'instructors', InstructorViewSet, basename='instructor')
router.register(r'course-types', CourseTypeViewSet, basename='course-type')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('users/register/', UserCreateView.as_view(), name='user-register'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/me/', UserMeView.as_view(), name='user-me'),
    path('slots/', SlotsView.as_view(), name='slots'),
    path('', include(router.urls)),
]
