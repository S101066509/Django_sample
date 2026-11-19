from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Booking, CourseType, Instructor, TimeOff


class BookingWriteTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(username="student")
        coach = User.objects.create_user(username="coach")
        self.instructor = Instructor.objects.create(user=coach, display_name="Coach")
        self.course = CourseType.objects.create(name="Lesson")
        self.start = datetime(2030, 1, 3, 10, tzinfo=ZoneInfo(settings.TIME_ZONE))
        self.client.force_authenticate(self.student)

    def reserve(self):
        return self.client.post(reverse("booking-list"), {
            "instructor": self.instructor.pk,
            "course_type": self.course.pk,
            "start_datetime": self.start.isoformat(),
        }, format="json")

    def test_cannot_create_during_leave(self):
        TimeOff.objects.create(instructor=self.instructor, start_datetime=self.start,
                               end_datetime=self.start + timedelta(hours=1))
        self.assertEqual(self.reserve().status_code, 400)
        self.assertFalse(Booking.objects.exists())

    def test_reschedule_recalculates_end_and_checks_leave(self):
        self.assertEqual(self.reserve().status_code, 201)
        booking = Booking.objects.get()
        url = reverse("booking-detail", args=[booking.pk])
        new_start = self.start + timedelta(hours=1)
        result = self.client.patch(url, {"start_datetime": new_start.isoformat()}, format="json")
        self.assertEqual(result.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.end_datetime, new_start + timedelta(minutes=30))
        TimeOff.objects.create(instructor=self.instructor, start_datetime=self.start,
                               end_datetime=new_start)
        result = self.client.patch(url, {"start_datetime": self.start.isoformat()}, format="json")
        self.assertEqual(result.status_code, 400)
        booking.refresh_from_db()
        self.assertEqual(booking.start_datetime, new_start)

    def test_duplicate_booking_returns_conflict(self):
        self.assertEqual(self.reserve().status_code, 201)
        duplicate = self.reserve()
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.data["error"]["code"], "SLOT_TAKEN")
