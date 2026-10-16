import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
TESTING = os.getenv('TESTING') == '1'
SECRET_KEY = os.getenv('SECRET_KEY', '')
if not SECRET_KEY:
    if TESTING: SECRET_KEY = 'only-for-isolated-tests-not-production'
    else: raise ImproperlyConfigured('Configure SECRET_KEY no ambiente ou .env')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CSRF_TRUSTED_ORIGINS = [x for x in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if x]
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles', 'core','seo_audit','sitemaps','robots_tools','indexnow','search_console','monitoring','accounts','dashboard']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','core.middleware.TrustedProxyIPMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware','core.middleware.PrivateResponseMiddleware']
ROOT_URLCONF = 'lignet.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages','core.context.site']}}]
WSGI_APPLICATION = 'lignet.wsgi.application'
DATABASES = {'default': {'ENGINE':'django.db.backends.postgresql','NAME':os.getenv('POSTGRES_DB','lignet'),'USER':os.getenv('POSTGRES_USER','lignet'),'PASSWORD':os.getenv('POSTGRES_PASSWORD',''),'HOST':os.getenv('POSTGRES_HOST','127.0.0.1'),'PORT':os.getenv('POSTGRES_PORT','5432')}}
if TESTING: DATABASES = {'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Araguaina'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR/'staticfiles'
STATICFILES_DIRS = [BASE_DIR/'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = '/painel/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/conta/login/'
SESSION_COOKIE_SECURE = not DEBUG and not TESTING
CSRF_COOKIE_SECURE = not DEBUG and not TESTING
SECURE_SSL_REDIRECT = not DEBUG and not TESTING
SECURE_HSTS_SECONDS = 31536000 if not DEBUG and not TESTING else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SITE_URL = os.getenv('SITE_URL','https://lignetbrasil.com.br').rstrip('/')
REDIS_URL = os.getenv('REDIS_URL','redis://127.0.0.1:6379/0')
CACHES = {'default':{'BACKEND':'django.core.cache.backends.redis.RedisCache','LOCATION':REDIS_URL}}
if TESTING: CACHES = {'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache'}}
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 180
CELERY_TASK_SOFT_TIME_LIMIT = 160
CELERY_TASK_IGNORE_RESULT = True
CELERY_BEAT_SCHEDULE = {'monitor-domains':{'task':'monitoring.tasks.schedule_checks','schedule':3600.0}}
AUDIT_HOURLY_LIMIT = int(os.getenv('AUDIT_HOURLY_LIMIT','10'))
ACTION_HOURLY_LIMIT = int(os.getenv('ACTION_HOURLY_LIMIT','30'))
MAX_DOMAINS = int(os.getenv('MAX_DOMAINS','5'))
MAX_RESPONSE_BYTES = int(os.getenv('MAX_RESPONSE_BYTES','2097152'))
HTTP_TIMEOUT = int(os.getenv('HTTP_TIMEOUT','8'))
MAX_LINK_CHECKS = int(os.getenv('MAX_LINK_CHECKS','10'))
MONITOR_INTERVAL_HOURS = int(os.getenv('MONITOR_INTERVAL_HOURS','24'))
INDEXNOW_COOLDOWN_SECONDS = int(os.getenv('INDEXNOW_COOLDOWN_SECONDS','300'))
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID','')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET','')
GOOGLE_REDIRECT_URI = SITE_URL + '/integracoes/google/callback/'
TOKEN_ENCRYPTION_KEY = os.getenv('TOKEN_ENCRYPTION_KEY','')
PAGESPEED_API_KEY = os.getenv('PAGESPEED_API_KEY','')
LOGGING = {'version':1,'disable_existing_loggers':False,'handlers':{'console':{'class':'logging.StreamHandler'}},'loggers':{'lignet.audit':{'handlers':['console'],'level':'INFO','propagate':False}}}
LOGGING['loggers']['blog'] = {'handlers': ['console'], 'level': 'INFO', 'propagate': False}

DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
CELERY_BROKER_CONNECTION_TIMEOUT = 3
CELERY_TASK_PUBLISH_RETRY = False

# Enable only behind a trusted proxy that overwrites this header.
if os.getenv('TRUST_HTTPS_PROXY','false').lower() == 'true':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

TRUSTED_PROXY_IPS = [x.strip() for x in os.getenv("TRUSTED_PROXY_IPS", "").split(",") if x.strip()]

INSTALLED_APPS += ['globalping']
INSTALLED_APPS += ['blog']
BLOG_OLLAMA_URL = os.getenv('BLOG_OLLAMA_URL', 'http://127.0.0.1:11434')
BLOG_OLLAMA_MODEL = os.getenv('BLOG_OLLAMA_MODEL', 'qwen2.5:7b')
BLOG_COMFY_URL = os.getenv('BLOG_COMFY_URL', 'http://127.0.0.1:8188')
BLOG_IMAGE_CHECKPOINT = os.getenv('BLOG_IMAGE_CHECKPOINT', '')
BLOG_IMAGE_LICENSE_CONFIRMED = os.getenv('BLOG_IMAGE_LICENSE_CONFIRMED', 'false').lower() == 'true'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
GLOBALPING_REQUESTS_PER_HOUR = int(os.getenv('GLOBALPING_REQUESTS_PER_HOUR', '10'))
GLOBALPING_MAX_PROBES = int(os.getenv('GLOBALPING_MAX_PROBES', '5'))
GLOBALPING_PROBES_PER_HOUR = int(os.getenv('GLOBALPING_PROBES_PER_HOUR', '200'))
GLOBALPING_TILE_URL = os.getenv('GLOBALPING_TILE_URL', 'https://tile.openstreetmap.org/{z}/{x}/{y}.png')
GLOBALPING_TILE_ATTRIBUTION = os.getenv('GLOBALPING_TILE_ATTRIBUTION', '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors')
CELERY_BEAT_SCHEDULE['globalping-recovery'] = {'task':'globalping.tasks.expire_stalled', 'schedule':60.0}
CELERY_BEAT_SCHEDULE['globalping-cleanup'] = {'task':'globalping.tasks.cleanup', 'schedule':3600.0}
