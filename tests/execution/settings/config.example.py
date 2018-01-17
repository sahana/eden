# Configuration file for EdenTest

# Admin password to capture web2py tickets
WEB2PY_PASSWD = "iiit123"
# Protocol (HTTP or HTTPs)
PROTO = "http"
# The server name, e.g. "localhost:8000"
SERVER = "localhost:8000"
# The web2py application name, e.g. "eden"
APPNAME = "eden"
# The browser, e.g. "Firefox" or "Chrome"
# NB requires the corresponding WebDriver to be in PATH (e.g. Geckodriver, Chromedriver)
BROWSER = "Chrome"
# The user name to test with
VALID_USER = "admin@example.com"
# The password for the test user
VALID_PASSWORD = "testing"
# HTTP Proxy (Firefox only, empty string to not use a HTTP proxy)
HTTP_PROXY = ""
# No Proxy (exemptions for HTTP Proxy)
NO_PROXY = "localhost, 127.0.0.1"
# Set Selenium Delay
DELAY = 0
# EdenTest requires admin permissions on the server being tested
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "testing"
# Smoke test start page
# - path relative to application root
SMOKETEST_START = ""
# Smoke test root
# - must be part of every visited URL
# - can be used to limit tests to a certain module
SMOKETEST_ROOT = ""
# Smoke test depth (0 = start page only)
SMOKETEST_DEPTH = 0
