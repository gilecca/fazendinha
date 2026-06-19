from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-feira-digital-fazendinha-key-2024')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,*', cast=Csv())

_csrf_origins = config('CSRF_TRUSTED_ORIGINS', default='')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()]

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'feira_digital.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'feira_digital.wsgi.application'
ASGI_APPLICATION = 'feira_digital.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ── Banco de dados ────────────────────────────────────────────
# Em produção, defina DATABASE_URL no ambiente (Railway gera automaticamente).
# Em desenvolvimento, usa SQLite.
_db_url = config('DATABASE_URL', default='')
if _db_url:
    DATABASES = {'default': dj_database_url.parse(_db_url, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'core.User'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ── Arquivos estáticos ────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ── Supabase ──────────────────────────────────────────────────
SUPABASE_URL = config('SUPABASE_URL', default='')
SUPABASE_SERVICE_KEY = config('SUPABASE_SERVICE_KEY', default='')
SUPABASE_BUCKET = config('SUPABASE_BUCKET', default='media')

_use_supabase = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)

STORAGES = {
    'default': {
        'BACKEND': (
            'core.storage.SupabaseStorage'
            if _use_supabase
            else 'django.core.files.storage.FileSystemStorage'
        ),
    },
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
            if not DEBUG
            else 'django.contrib.staticfiles.storage.StaticFilesStorage'
        ),
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SITE_URL = config('SITE_URL', default='http://127.0.0.1:8000').rstrip('/')

# ── Stripe ────────────────────────────────────────────────────
# Configure no .env:
#   STRIPE_SECRET_KEY=sk_test_...   (nunca exposta no frontend)
#   STRIPE_PUBLIC_KEY=pk_test_...   (pode ir no JS)
#   STRIPE_WEBHOOK_SECRET=whsec_... (gerado em Dashboard → Webhooks)
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='sk_test_COLOQUE-SUA-CHAVE-AQUI')
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='pk_test_COLOQUE-SUA-CHAVE-AQUI')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='whsec_COLOQUE-SEU-SECRET-AQUI')

# ── E-mail ────────────────────────────────────────────────────
_brevo_api_key = config('BREVO_API_KEY', default='')
_email_user    = config('EMAIL_HOST_USER', default='')
_email_pass    = config('EMAIL_HOST_PASSWORD', default='')

if _brevo_api_key:
    # API HTTP — funciona em Railway e qualquer hospedagem (sem SMTP)
    EMAIL_BACKEND = 'anymail.backends.brevo.EmailBackend'
    ANYMAIL = {'BREVO_API_KEY': _brevo_api_key}
    INSTALLED_APPS += ['anymail']
elif _email_user and _email_pass:
    # Fallback SMTP (local)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST     = config('EMAIL_HOST', default='smtp-relay.brevo.com')
    EMAIL_PORT     = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS  = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_USE_SSL  = config('EMAIL_USE_SSL', default=False, cast=bool)
    EMAIL_HOST_USER     = _email_user
    EMAIL_HOST_PASSWORD = _email_pass
    EMAIL_TIMEOUT  = 15
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = config(
    'DEFAULT_FROM_EMAIL',
    default=f'Fazendinha <{_email_user}>' if _email_user else 'Fazendinha <noreply@fazendinha.com.br>',
)

# ── Taxa de serviço ───────────────────────────────────────────
# Percentual retido da plataforma sobre cada venda do produtor.
# Ex: 10 → 10%. Altere via env SERVICE_FEE_PERCENT=10
SERVICE_FEE_PERCENT = config('SERVICE_FEE_PERCENT', default=10, cast=int)

# ── Logging ───────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'core.emails': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}
