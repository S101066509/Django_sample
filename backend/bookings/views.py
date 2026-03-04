from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction, IntegrityError
from django.utils import timezone
from datetime import datetime, time, timedelta
import zoneinfo
from django.conf import settings

from .models import Instructor, CourseType, Booking, TimeOff
from .serializers import (
    UserSerializer, InstructorSerializer, CourseTypeSerializer, BookingSerializer, UserCreateSerializer
)

from .permissions import IsOwnerOrStaff, IsStaff


# 自製登入者資訊
class UserMeView(APIView):
    """
    獲取目前登入使用者的個人資料。
    呼叫此 API 時必須夾帶有效的身分驗證 Token。
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# 繼承通用模板
class UserCreateView(generics.CreateAPIView):
    """
    使用者註冊 API (建立新帳號)。
    開放權限 (AllowAny)：不需要登入即可註冊。
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = UserCreateSerializer


# 繼承通用模板
class InstructorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    負責教練資料的查詢 API (包含列表 List 與單筆 Detail)。
    - 只允許讀取，不允許透過此 API 進行新增/修改/刪除教練。
    - 過濾掉已停用 (active=False) 的教練。
    """
    queryset = Instructor.objects.filter(active=True)
    serializer_class = InstructorSerializer
    permission_classes = [permissions.AllowAny]


# 繼承通用模板
class CourseTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    負責課程類型的查詢 API (例如：30分鐘體驗課)。
    - 只允許讀取，避免前端意外竄改課程設定。
    - 過濾掉已停用 (active=False) 的課程。
    """
    queryset = CourseType.objects.filter(active=True)
    serializer_class = CourseTypeSerializer
    permission_classes = [permissions.AllowAny]


# 自製預約時段路由
class SlotsView(APIView):
    """
    提供查詢特定教練在某個日期的可用預約時段 (Slots)。
    API 會自動排除已經被預約，或者教練正在休假的時段。
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        instructor_id = request.query_params.get('instructor_id')
        date_str = request.query_params.get('date')

        if not instructor_id or not date_str:
            return Response({
                "error": {
                    "code": "INVALID_QUERY",
                    "message": "instructor_id and date are required"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid date format, use YYYY-MM-DD"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        tz = zoneinfo.ZoneInfo(settings.TIME_ZONE)
        
        # 1. 產生 08:00 到 21:30 之間，每 30 分鐘為單位的時段列表
        slots = []
        current_time = datetime.combine(target_date, time(8, 0)).replace(tzinfo=tz)
        end_time = datetime.combine(target_date, time(22, 0)).replace(tzinfo=tz)

        while current_time < end_time:
            slots.append({
                "start": current_time,
                "end": current_time + timedelta(minutes=30),
                "available": True
            })
            current_time += timedelta(minutes=30)

        # 2. 查詢該教練當天的所有「已預約」紀錄
        day_start = datetime.combine(target_date, time.min).replace(tzinfo=tz)
        day_end = datetime.combine(target_date, time.max).replace(tzinfo=tz)

        bookings = Booking.objects.filter(
            instructor_id=instructor_id,
            start_datetime__gte=day_start,
            start_datetime__lte=day_end,
            status=Booking.Status.BOOKED
        )
        booked_starts = {b.start_datetime for b in bookings}

        # 3. 查詢該教練當天的「休假紀錄」
        timeoffs = TimeOff.objects.filter(
            instructor_id=instructor_id,
            start_datetime__lt=day_end,
            end_datetime__gt=day_start
        )

        for slot in slots:
            # 檢查該時段是否已被預約
            if slot["start"] in booked_starts:
                slot["available"] = False
                continue
            
            # 檢查該時段是否與休假重疊
            # 交集判定條件：兩個區段重疊的充要條件為 max(開始1, 開始2) < min(結束1, 結束2)
            for toff in timeoffs:
                if max(slot["start"], toff.start_datetime) < min(slot["end"], toff.end_datetime):
                    slot["available"] = False
                    break

        return Response([{
            "start": s["start"].isoformat(),
            "end": s["end"].isoformat(),
            "available": s["available"]
        } for s in slots])


# 半自製crud api
class BookingViewSet(viewsets.ModelViewSet):
    """
    預約紀錄的 CRUD API。
    - 學生只能看到並操作自己的預約。
    - 管理員可以看到所有人的預約。
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all()
        return Booking.objects.filter(student=user)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        course_type_id = data.get('course_type')
        start_datetime = data.get('start_datetime')

        try:
            course_type = CourseType.objects.get(id=course_type_id)
        except CourseType.DoesNotExist:
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Invalid course_type"}}, status=status.HTTP_400_BAD_REQUEST)

        # 為了安全，結束時間由後端依據課程類型自動計算
        try:
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
            end_dt = start_dt + timedelta(minutes=course_type.duration_minutes)
        except (ValueError, TypeError):
            return Response({"error": {"code": "VALIDATION_ERROR", "message": "Invalid start_datetime format"}}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                booking = Booking(**serializer.validated_data)
                booking.student = request.user
                booking.end_datetime = end_dt
                # 觸發 model.clean() 來執行所有的商業邏輯驗證（例如 08:00 - 21:30、0/30分限制）
                booking.full_clean()
                booking.save()
        except IntegrityError:
            return Response({
                "error": {
                    "code": "SLOT_TAKEN",
                    "message": "This slot is already booked"
                }
            }, status=status.HTTP_409_CONFLICT)

        headers = self.get_success_headers(serializer.validated_data)
        response_serializer = self.get_serializer(booking)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        """取消預約：採用軟刪除 (Soft-delete)，將狀態改為 CANCELED 而非實際刪除資料。"""
        instance = self.get_object()
        instance.status = Booking.Status.CANCELED
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
