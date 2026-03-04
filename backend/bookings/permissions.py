from rest_framework import permissions

class IsStaff(permissions.BasePermission):
    """
    權限檢查：僅允許系統管理員（Staff）存取。
    """
    def has_permission(self, request, view) -> bool:  
        # 必須同時滿足三個條件：有使用者資訊、已登入認證、且該帳號是系統管理員
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

class IsOwnerOrStaff(permissions.BasePermission):
    """
    權限檢查：僅允許「資料擁有者（通常是學生本人）」或「系統管理員（Staff）」存取。
    這通常用於讓使用者只能看到/修改屬於自己的預約紀錄。
    """
    def has_permission(self, request, view) -> bool:  
        # API 進入點的基本檢查：只要是「已登入認證的使用者」，就能通過第一關的列表 (List) 或建立 (Create) 權限
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool: 
        # 針對「單一特定資料（例如某一筆 Booking）」的權限檢查：
        # 如果該資料有關聯到 'student'（學生），則判斷當前請求的使用者是不是該名學生，或者是不是管理員
        if hasattr(obj, 'student'):
            return obj.student == request.user or request.user.is_staff
        # 如果這個物件沒有 'student' 屬性，則為安全起見，預設只有管理員可以存取
        return request.user.is_staff
