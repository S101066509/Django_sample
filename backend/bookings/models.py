"""
本模組定義 Vibe Booking 系統的核心資料模型。
包含 Instructor（教練）、CourseType（課程類型）、Booking（預約）及 TimeOff（休假時段）。
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q, UniqueConstraint
from django.core.exceptions import ValidationError
from datetime import timedelta, time
import zoneinfo
from django.conf import settings

class TimeStampedModel(models.Model):
    """抽象基礎模型，自動記錄建立時間與最後更新時間。其他模型皆繼承此類別。"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Instructor(TimeStampedModel):
    """教練資料。每位教練對應一個系統使用者 (User)，並具有顯示名稱與啟用狀態。"""
    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name='instructor_profile'
    )
    display_name = models.CharField(max_length=100)
    active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.display_name

class CourseType(TimeStampedModel):
    """課程類型。目前版本僅支援 30 分鐘的課程，超出此限制會在 clean() 中拋出 ValidationError。"""
    name = models.CharField(max_length=100, db_index=True)
    duration_minutes = models.PositiveSmallIntegerField(default=30)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True, db_index=True)

    def clean(self):
        super().clean()
        if self.duration_minutes != 30:
            raise ValidationError("First version only allows duration_minutes == 30")

    def __str__(self):
        return self.name

class Booking(TimeStampedModel):
    """
    預約紀錄。記錄學生與教練之間的課程預約。
    - 開始時間限制：08:00–21:30，且只能為整點或半點。
    - 結束時間由 CourseType.duration_minutes 計算，不得超過 22:00。
    - 同一教練同一時段僅允許一筆有效預約（unique constraint）。
    - 取消採用軟刪除（status=CANCELED），不實際刪除資料列。
    """
    class Status(models.TextChoices):
        BOOKED = 'BOOKED', 'Booked'
        CANCELED = 'CANCELED', 'Canceled'

    instructor = models.ForeignKey(
        Instructor, 
        on_delete=models.PROTECT, 
        related_name='bookings'
    )
    student = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='bookings'
    )
    course_type = models.ForeignKey(
        CourseType, 
        on_delete=models.PROTECT, 
        related_name='bookings'
    )
    start_datetime = models.DateTimeField(db_index=True)
    end_datetime = models.DateTimeField()
    status = models.CharField(
        max_length=10, 
        choices=Status.choices, 
        default=Status.BOOKED, 
        db_index=True
    )

    class Meta:
        indexes = [
            models.Index(fields=['instructor', 'start_datetime']),
            models.Index(fields=['student', 'start_datetime']),
        ]
        constraints = [
            UniqueConstraint(
                fields=["instructor", "start_datetime"],
                condition=Q(status="BOOKED"),
                name="uniq_booked_slot_per_instructor"
            )
        ]

    def clean(self):
        """
        覆寫model的clean方法，進行資料驗證。
        驗證預約資料的合理性：
        1. 預約分鐘必須為整點 (0) 或半點 (30)。
        2. 預約開始時間必須在 08:00 到 21:30 之間。
        3. 根據課程類型自動計算並強制修正結束時間。
        4. 防呆檢查：結束時間不得跨日且不能超過 22:00。
        """
        super().clean()
        if not self.start_datetime:
            return

        assert settings.TIME_ZONE is not None, "TIME_ZONE must be set in settings"
        tz = zoneinfo.ZoneInfo(settings.TIME_ZONE)
        local_start = self.start_datetime.astimezone(tz)

        # 1. 分鐘必須為 0 或 30
        if local_start.minute not in (0, 30):
            raise ValidationError("Start minute must be 0 or 30")

        # 2. 開始時間必須在 08:00 到 21:30 之間
        start_time = local_start.time()
        if not (time(8, 0) <= start_time <= time(21, 30)):
            raise ValidationError("Start time must be between 08:00 and 21:30")

        # 3. 結束時間 = 開始時間 + 課程長度
        if hasattr(self, 'course_type') and self.course_type:
            expected_end = self.start_datetime + timedelta(minutes=self.course_type.duration_minutes)
            if self.end_datetime != expected_end:
                self.end_datetime = expected_end

        # 4. 結束時間不可超過 22:00
        if self.end_datetime:
            local_end = self.end_datetime.astimezone(tz)
            if local_end.date() > local_start.date() or local_end.time() > time(22, 0):
                raise ValidationError("End time must not exceed 22:00")

    def __str__(self):
        return f"{self.student.username} with {self.instructor.display_name} at {self.start_datetime}"

class TimeOff(TimeStampedModel):
    """教練休假時段。查詢可預約時段時會排除與休假區間重疊的 slot。"""
    instructor = models.ForeignKey(
        Instructor, 
        on_delete=models.PROTECT, 
        related_name='time_offs',
        null=True,
        blank=True
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    reason = models.CharField(max_length=255)

    def __str__(self):
        return f"TimeOff {self.start_datetime} to {self.end_datetime}"
