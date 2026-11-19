"""
本模組定義 Vibe Booking 系統的 Serializers (序列化器)。
負責將 Django 模型 (Models) 轉換為 JSON 格式供 API 傳輸，
並將前端傳送來的 JSON 資料解析與驗證後，儲存至資料庫中。
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Instructor, CourseType, Booking, TimeOff
from django.db import transaction
from datetime import timedelta

class UserCreateSerializer(serializers.ModelSerializer):
    """
    負責使用者註冊 (建立新帳號) 的序列化器。
    密碼欄位設定為 write_only，避免在回傳的 API 回應中洩漏密碼。
    """
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']

    def create(self, validated_data):
        # 使用 Django 的預設機制建立使用者，這會自動幫密碼進行雜湊 (Hash) 處理
        return User.objects.create_user(**validated_data)

class UserSerializer(serializers.ModelSerializer):
    """
    負責回傳使用者資訊的序列化器。
    所有欄位皆設定為 read_only，僅供前端讀取展示用，不可透過此 API 修改。
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']
        read_only_fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff']


class InstructorSerializer(serializers.ModelSerializer):
    """教練資料的序列化器，回傳教練的基本顯示資訊。"""
    class Meta:
        model = Instructor
        fields = ['id', 'display_name', 'active', 'created_at']

class CourseTypeSerializer(serializers.ModelSerializer):
    """課程類型的序列化器，包含課程時長與描述等資訊。"""
    class Meta:
        model = CourseType
        fields = ['id', 'name', 'duration_minutes', 'description', 'active']

class BookingSerializer(serializers.ModelSerializer):
    """
    預約紀錄的序列化器。
    動態附加教練名稱 (instructor_name) 與課程名稱 (course_type_name) 以外鍵關聯的字串供前端顯示。
    """
    instructor_name = serializers.CharField(source='instructor.display_name', read_only=True)
    course_type_name = serializers.CharField(source='course_type.name', read_only=True)

    class Meta:
        model = Booking
        # The database checks the conditional unique slot atomically, including on PATCH.
        validators = []
        fields = [
            'id', 'instructor', 'instructor_name', 'course_type', 'course_type_name',
            'start_datetime', 'end_datetime', 'status', 'created_at'
        ]
        # 這些欄位是系統自動產生或計算的，不允許前端透過 API 單方面修改
        read_only_fields = ['id', 'end_datetime', 'status', 'created_at', 'instructor_name', 'course_type_name']

    def create(self, validated_data):
        return self.update(Booking(), validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.end_datetime = instance.start_datetime + timedelta(
            minutes=instance.course_type.duration_minutes
        )
        # The database enforces the unique slot constraint for concurrent requests.
        instance.full_clean(validate_constraints=False)
        instance.save()
        return instance
