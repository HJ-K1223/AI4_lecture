"""Read-only WSGI checks. Run with production settings and a local test database."""
import io
import sys
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.wsgi import application
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage


def request(path, scheme="https", method="GET", script_name=""):
    host = settings.ALLOWED_HOSTS[0]
    status = []
    environ = {
        "REQUEST_METHOD": method, "SCRIPT_NAME": script_name, "PATH_INFO": path,
        "QUERY_STRING": "", "SERVER_NAME": host, "SERVER_PORT": "443",
        "SERVER_PROTOCOL": "HTTP/1.1", "HTTP_HOST": host,
        "HTTP_X_FORWARDED_PROTO": scheme, "wsgi.version": (1, 0),
        "wsgi.url_scheme": "http", "wsgi.input": io.BytesIO(b""),
        "wsgi.errors": io.StringIO(), "wsgi.multithread": False,
        "wsgi.multiprocess": False, "wsgi.run_once": False,
    }
    result = application(environ, lambda code, headers: status.append((code, dict(headers))))
    try:
        body = b"".join(result)
    finally:
        if hasattr(result, "close"):
            result.close()
    return int(status[0][0].split()[0]), status[0][1], body


if __name__ == "__main__":
    prefix = settings.APP_URL_PREFIX
    code, headers, body = request(prefix + "/accounts/login/")
    assert code == 200 and b"note-demo" in body
    if prefix:
        assert (prefix + "/accounts/signup/").encode() in body
        assert b'href="/accounts/' not in body
        assert request("/accounts/login/", script_name=prefix)[0] == 200
        assert request(prefix)[0] == 301
        assert settings.SESSION_COOKIE_PATH == prefix + "/"
        assert settings.CSRF_COOKIE_PATH == prefix + "/"
        assert settings.SESSION_COOKIE_NAME == "note_demo_sessionid"
        assert settings.CSRF_COOKIE_NAME == "note_demo_csrftoken"
        assert settings.SECURE_HSTS_SECONDS == 0
    assert request(prefix + "/posts/", scheme="http")[0] == 301
    code, headers, _ = request(prefix + "/posts/")
    assert code == 302 and headers["Location"].startswith(prefix + "/accounts/login/")
    asset = urlsplit(staticfiles_storage.url("css/site.css")).path
    code, headers, body = request(asset)
    assert code == 200 and b"box-sizing" in body
    assert request(prefix + "/accounts/login/", method="POST")[0] == 403
    assert request(prefix + "/unknown-page/")[0] == 404
    print("PASS: login-first WSGI, protected board, HTTPS redirect, hashed CSS, CSRF and 404")
