from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

"""
總路由 (Root URLconf)
這裡是所有 HTTP 請求進入 Django 系統的「第一道大門 (一級路由)」。
負責把網址的前綴字指派給對應的應用程式或功能模組去處理。
"""
urlpatterns = [
    # Django 內建的後台管理系統路由，網址為 /admin/
    path('admin/', admin.site.urls),
    
    # 我們的核心 API 路由。
    # 所有開頭是 /api/ 的請求，都會被「轉交」給 bookings/urls.py 裡面去進行第二層解析 (二級路由)
    path('api/', include('bookings.urls')),
    
    # ============================================
    # OpenAPI (Swagger & ReDoc) 自動文件產生器路由
    # ============================================
    # 產出機器讀得懂的 Swagger Schema (通常是 JSON 格式)，這是文件的資料來源
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # 根據上面的 Schema 產生出人類可讀、可互動操作的 Swagger UI (常用的測試文件)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # 另一種文件呈現風格 (ReDoc)，適合用來產出靜態的、像說明書般美觀的 API 文件
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
