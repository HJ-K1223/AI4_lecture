from .base import *
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("replace-"):
    raise ImproperlyConfigured("Production requires a random secret of at least 50 characters.")
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Set exact production ALLOWED_HOSTS.")
if not CSRF_TRUSTED_ORIGINS or any(not s.startswith("https://") for s in CSRF_TRUSTED_ORIGINS):
    raise ImproperlyConfigured("Set HTTPS CSRF_TRUSTED_ORIGINS.")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 3600
if APP_URL_PREFIX:
    # HSTS applies to the entire hostname, not just this application's path.
    SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
if os.getenv("TRUST_PROXY_HTTPS", "false").lower() == "true":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

