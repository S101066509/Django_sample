"""
Django settings for config project.
"""
from pathlib import Path
import os
from datetime import timedelta
# 載入環境變數設定 (.env 檔案)，避免將機密資料寫死在程式碼中
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# 從環境變數讀取敏感資訊與設定，若未設定則提供預設值
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-example-key')
DEBUG = os.getenv('DJANGO_DEBUG', '0') == '1'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 第三方套件 (Third party)
    # Django Rest Framework (DRF) 核心
    'rest_framework',
    # JWT 登入驗證
    'rest_framework_simplejwt',
    # OpenAPI Swagger 自動生成 API 文件
    'drf_spectacular',
    # CORS 跨域處理 (解決前端呼叫 API 時的 CORS 阻擋問題)
    'corsheaders',
    # 本區專案的本地應用程式 (Local apps)
    'bookings.apps.BookingsConfig',
]

MIDDLEWARE = [
    # CORS 中介軟體 (必須放在盡可能上面的位置，優先處理跨域請求)
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# 允許所有來源 (跨域要求) 存取 API。在正式上線 (Production) 時應限制為只允許前端網域。
CORS_ALLOW_ALL_ORIGINS = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# 資料庫設定：從預設的 SQLite 改為 PostgreSQL，並統一由環境變數讀取連線資訊
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'vibe_booking'),
        'USER': os.getenv('DB_USER', 'vibe'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'vibe123'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5433'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'zh-hant'
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Taipei')
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================================
# 額外擴充套件設定區 (DRF, JWT, Swagger)
# ==========================================

# Django Rest Framework (DRF) 全域設定
REST_FRAMEWORK = {
    # 預設使用的身分驗證方式：改為 JWT (JSON Web Token) 驗證
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # 指定 API 文件產生器使用 Spectacular 格式
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # 客製化例外處理：將錯誤訊息統一包裝為我們寫好的 JSON 格式
    'EXCEPTION_HANDLER': 'bookings.exceptions.custom_exception_handler',
}

# JWT Token 效期設定
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60), # Access Token 1小時後過期需換發
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),    # Refresh Token 1天後過期需重新登入
}

# Swagger UI API 文件產生器相關設定
SPECTACULAR_SETTINGS = {
    'TITLE': 'Vibe Booking API',     # 顯示在文件網頁上的大大標題
    'DESCRIPTION': 'API for booking system',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,   # 隱藏產生 API Schema 的那個獨立端點自己
}
