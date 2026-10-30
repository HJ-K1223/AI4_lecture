"""Accept WSGI hosts that either strip the registered mount path or pass it intact."""
class MountedApplication:
    def __init__(self, application, prefix):
        self.application = application
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if self.prefix:
            path = environ.get("PATH_INFO", "/")
            if path == self.prefix:
                query = environ.get("QUERY_STRING", "")
                target = self.prefix + "/" + (("?" + query) if query else "")
                start_response("301 Moved Permanently", [("Location", target), ("Content-Length", "0")])
                return [b""]
            if path.startswith(self.prefix + "/"):
                environ["PATH_INFO"] = path[len(self.prefix):]
            environ["SCRIPT_NAME"] = self.prefix
        return self.application(environ, start_response)
