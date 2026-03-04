"""
Django Admin 後台管理設定。
將系統中的核心 Model 註冊到 /admin/ 後台，方便管理員直接進行資料的查看與操作。
"""
from django.contrib import admin
from .models import Instructor, CourseType, Booking, TimeOff


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    """教練管理介面"""
    list_display = ('id', 'display_name', 'user', 'active', 'created_at')
    list_filter = ('active',)
    search_fields = ('display_name', 'user__username')


@admin.register(CourseType)
class CourseTypeAdmin(admin.ModelAdmin):
    """課程類型管理介面"""
    list_display = ('id', 'name', 'duration_minutes', 'active', 'created_at')
    list_filter = ('active',)
    search_fields = ('name',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """預約紀錄管理介面"""
    list_display = ('id', 'student', 'instructor', 'course_type', 'start_datetime', 'end_datetime', 'status', 'created_at')
    list_filter = ('status', 'instructor')
    search_fields = ('student__username', 'instructor__display_name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TimeOff)
class TimeOffAdmin(admin.ModelAdmin):
    """教練休假管理介面"""
    list_display = ('id', 'instructor', 'start_datetime', 'end_datetime', 'reason', 'created_at')
    list_filter = ('instructor',)
    search_fields = ('reason', 'instructor__display_name')
