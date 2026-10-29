import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Small dotenv reader: shell/container variables always take precedence.
env_file = BASE_DIR.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def flag(name, default=False):
    return os.environ.get(name, str(default)).lower() in {"1", "true", "yes"}


DEBUG = flag("DEBUG", True)
SECRET_KEY = os.environ.get("SECRET_KEY", "development-only-thucourt-do-not-use-in-production")
DEMO_MODE = flag("DEMO_MODE", DEBUG)
if not DEBUG and ("development" in SECRET_KEY or len(SECRET_KEY) < 32):
    raise ImproperlyConfigured("Production requires a random SECRET_KEY of at least 32 characters")
if not DEBUG and DEMO_MODE:
    raise ImproperlyConfigured("DEMO_MODE must be false in production")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "accounts",
    "courts",
    "community",
    "matches",
    "coaching",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
db_url = os.environ.get("DATABASE_URL", "")
if db_url:
    db = urlparse(db_url)
    if db.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured("DATABASE_URL must be a PostgreSQL URL")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db.path.lstrip("/"),
            "USER": unquote(db.username or ""),
            "PASSWORD": unquote(db.password or ""),
            "HOST": db.hostname,
            "PORT": db.port or 5432,
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get("SQLITE_PATH", BASE_DIR / "db.sqlite3"),
            "OPTIONS": {"timeout": 20},
        }
    }
AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "private_media"))
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CSRF_TRUSTED_ORIGINS = list(
    filter(
        None,
        os.environ.get("CSRF_TRUSTED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(
            ","
        ),
    )
)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = flag("SECURE_COOKIES", not DEBUG)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SECURE_SSL_REDIRECT = flag("SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
DATA_UPLOAD_MAX_MEMORY_SIZE = 105 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["accounts.permissions.IsVerified"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "120/hour",
        "user": "1200/hour",
        "login": "20/hour",
        "messages": "60/minute",
    },
    "EXCEPTION_HANDLER": "common.errors.exception_handler",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}
SPECTACULAR_SETTINGS = {
    "TITLE": "THUCourt API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "DESCRIPTION": "清网同行：仅认证学生可访问的网球社区。CSRF + Django Session。",
}
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = flag("CELERY_TASK_ALWAYS_EAGER", True)
CELERY_TASK_EAGER_PROPAGATES = False
CELERY_TASK_TIME_LIMIT = 180
CELERY_TASK_SOFT_TIME_LIMIT = 165
AI_PROVIDER = os.environ.get("AI_PROVIDER", "demo")
AI_BASE_URL = os.environ.get("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
AI_API_KEY = os.environ.get("AI_API_KEY", "")
AI_MODEL = os.environ.get("AI_MODEL", "")
AI_DAILY_LIMIT = int(os.environ.get("AI_DAILY_LIMIT", "10"))
AI_REMOTE_CALL_LIMIT = int(os.environ.get("AI_REMOTE_CALL_LIMIT", "1000"))
AI_PROCESSOR_LABEL = os.environ.get("AI_PROCESSOR_LABEL", "已配置的模型服务商")
WECHAT_APP_ID = os.environ.get("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.environ.get("WECHAT_APP_SECRET", "")
WECHAT_REDIRECT_URI = os.environ.get("WECHAT_REDIRECT_URI", "")
MEDIA_RETENTION_DAYS = int(os.environ.get("MEDIA_RETENTION_DAYS", "30"))
