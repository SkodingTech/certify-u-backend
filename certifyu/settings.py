from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if present (development convenience).
_env_file = BASE_DIR / '.env'
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if not _line or _line.startswith('#') or '=' not in _line:
            continue
        _k, _, _v = _line.partition('=')
        os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))


def _env_bool(name, default=False):
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ('1', 'true', 'yes', 'on')


def _env_list(name, default=()):
    raw = os.environ.get(name, '')
    return [x.strip() for x in raw.split(',') if x.strip()] or list(default)


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-me')

DEBUG = _env_bool('DJANGO_DEBUG', default=False)

ALLOWED_HOSTS = _env_list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'api',
    'users',
    'courses',
    'scorm',
    
    'rest_framework',
    'storages',
    'ckeditor',
    'ckeditor_uploader',
    'oauth2_provider',
    'social_django',
    'rest_framework_social_oauth2',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'certifyu.middleware.AuthRateLimitMiddleware',
]

ROOT_URLCONF = 'certifyu.urls'

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


OAUTH2_PROVIDER = {
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope', 'groups': 'Access to your groups'}
}


REST_FRAMEWORK = {
     'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework_social_oauth2.authentication.SocialAuthentication',
    ],
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ),
    
}

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'rest_framework_social_oauth2.backends.DjangoOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_REDIRECT_URL = '/'


SITE_ID = 1
SOCIALACCOUNT_LOGIN_ON_GET=True

DRFSO2_URL_NAMESPACE = 'social'
NAMESPACE = 'oauth2'

# ─────────────────────────────────────────────────────────────────────────────
# Google OAuth2 (social sign-in)
# The frontend obtains a Google access token (@react-oauth/google) and exchanges
# it at POST /auth/convert-token (drf-social-oauth2) for an app token.
# Create a Google Cloud OAuth 2.0 *Web application* client and set:
#   SOCIAL_AUTH_GOOGLE_OAUTH2_KEY     -> the client ID
#   SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET  -> the client secret
# The frontend NEXT_PUBLIC_GOOGLE_CLIENT_ID MUST be the same client ID.
# ─────────────────────────────────────────────────────────────────────────────
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile']
SOCIAL_AUTH_JSONFIELD_ENABLED = True

# Link a Google sign-in to an existing account with the same email instead of
# creating a duplicate. Safe here because Google verifies email ownership.
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

WSGI_APPLICATION = 'certifyu.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

if os.environ.get('DB_ENGINE', '').lower() == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME':     os.environ.get('DB_NAME', 'certifyu'),
            'USER':     os.environ.get('DB_USER', 'certifyuuser'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST':     os.environ.get('DB_HOST', 'localhost'),
            'PORT':     os.environ.get('DB_PORT', ''),
        }
    }

# Postgres bootstrap (run on a fresh DB host):
#   CREATE DATABASE certifyu;
#   CREATE USER certifyuuser WITH PASSWORD '<set DB_PASSWORD env var>';
#   ALTER ROLE certifyuuser SET client_encoding TO 'utf8';
#   ALTER ROLE certifyuuser SET default_transaction_isolation TO 'read committed';
#   ALTER ROLE certifyuuser SET timezone TO 'UTC';
#   GRANT ALL PRIVILEGES ON DATABASE certifyu TO certifyuuser;
#   ALTER DATABASE certifyu OWNER TO certifyuuser;

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# CORS
# In production, restrict to known frontends via env var. Falls back to
# wildcard when DJANGO_CORS_ALLOWED_ORIGINS is unset (preserves dev behaviour).
# ─────────────────────────────────────────────────────────────────────────────
INSTALLED_APPS += ['corsheaders'] if 'corsheaders' not in INSTALLED_APPS else []
_cors_origins = _env_list('DJANGO_CORS_ALLOWED_ORIGINS', default=[])
if _cors_origins:
    CORS_ALLOWED_ORIGINS = _cors_origins
    CORS_ALLOW_CREDENTIALS = True
    CORS_ORIGIN_ALLOW_ALL = False
else:
    CORS_ORIGIN_ALLOW_ALL = True  # dev fallback

# CSRF trusted origins — Django 4 requires explicit scheme.
CSRF_TRUSTED_ORIGINS = _env_list(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    default=['https://cms.certify-u.com', 'https://certify-u.com',
             'https://www.certify-u.com', 'https://server.certify-u.com'],
)

# ─────────────────────────────────────────────────────────────────────────────
# Production-only hardening (gated on DEBUG to keep local dev usable)
# ─────────────────────────────────────────────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')  # behind nginx
    SECURE_SSL_REDIRECT = _env_bool('DJANGO_SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days; raise to 1y after burn-in
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False  # opt in once HSTS_SECONDS is at ≥1y
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_BROWSER_XSS_FILTER = True  # legacy header; harmless to set
    X_FRAME_OPTIONS = 'DENY'
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'

# ─────────────────────────────────────────────────────────────────────────────
# Upload size limits (course materials + SCORM packages are larger than default)
# ─────────────────────────────────────────────────────────────────────────────
DATA_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024   # 25 MB form payload
FILE_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024   # 25 MB before spilling to disk
DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000             # bumped for multi-row admin pages

# ─────────────────────────────────────────────────────────────────────────────
# Logging — write tracebacks to a rotating file so prod errors aren't lost.
# (Replaces "no error visibility" with at least file-based logs until a real
# observability stack is wired up.)
# ─────────────────────────────────────────────────────────────────────────────
_log_dir = os.environ.get('DJANGO_LOG_DIR', '/var/log/certifyu')
try:
    Path(_log_dir).mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError):
    _log_dir = '/tmp'  # fall back to /tmp if /var/log isn't writable

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'standard'},
        'errfile': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(_log_dir, 'errors.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'level': 'WARNING',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {'handlers': ['console', 'errfile'], 'level': 'INFO',
                   'propagate': False},
        'django.request': {'handlers': ['console', 'errfile'], 'level': 'ERROR',
                           'propagate': False},
        'django.security': {'handlers': ['console', 'errfile'], 'level': 'WARNING',
                            'propagate': False},
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Default throttling on the OAuth token endpoint (best-effort, in-memory).
# Backed by Django's local cache so it only protects per-process; for serious
# brute-force defence put a WAF / Cloudflare rule in front.
# ─────────────────────────────────────────────────────────────────────────────
REST_FRAMEWORK_THROTTLE_RATES = {
    'anon': '60/min',
    'user': '600/min',
    'login': '20/min',
}

# CSP (loose, kept compatible with ckeditor + S3 static — tighten later)
# Not enforced via middleware here; left as a reminder/follow-up.


# ─────────────────────────────────────────────────────────────────────────────
# Cache — filesystem-backed so it's shared across gunicorn workers (the
# default LocMem cache is per-process, which means the rate limiter
# under-counts with multiple workers).
# ─────────────────────────────────────────────────────────────────────────────
_cache_dir = os.environ.get('DJANGO_CACHE_DIR', '/var/cache/certifyu')
try:
    Path(_cache_dir).mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError):
    _cache_dir = '/tmp/certifyu-cache'
    Path(_cache_dir).mkdir(parents=True, exist_ok=True)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': _cache_dir,
        'TIMEOUT': 300,
        'OPTIONS': {'MAX_ENTRIES': 10000},
    },
}


CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': None,
    },
}
CKEDITOR_UPLOAD_PATH = "uploads/"

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


AWS_ACCESS_KEY_ID     = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'certifyu')
AWS_S3_CUSTOM_DOMAIN = '%s.s3-ap-south-1.amazonaws.com' % (AWS_STORAGE_BUCKET_NAME)
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_LOCATION = 'static'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'web/static/'),
]
if os.environ.get('USE_LOCAL_STORAGE', '').lower() in ('1', 'true', 'yes'):
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
else:
    STATIC_URL = 'https://%s/%s/' % (AWS_S3_CUSTOM_DOMAIN, AWS_LOCATION)
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_DEFAULT_ACL = 'public-read'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'





