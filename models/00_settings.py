# =============================================================================
#   Global settings:
#
#   Those which are typically edited during a deployment are in
#   000_config.py & their results parsed into here. Deployers
#   shouldn't typically need to edit any settings here.
# =============================================================================

# Keep all our configuration options off the main global variables

# Use response.s3 for one-off variables which are visible in views without explicit passing
s3.formats = Storage()

# Workaround for this Bug in Selenium with FF4:
#    http://code.google.com/p/selenium/issues/detail?id=1604
s3.interactive = settings.get_ui_confirm()

s3.base_url = "%s/%s" % (settings.get_base_public_url(),
                         appname)
s3.download_url = "%s/default/download" % s3.base_url

# -----------------------------------------------------------------------------
# Global variables
#
# Strings to i18n
#
# Common Labels
messages["UNKNOWN_OPT"] = "Unknown"
messages["NONE"] = "-"
messages["NOT_APPLICABLE"] = "N/A"
messages["OBSOLETE"] = "Obsolete"
messages["OPEN"] = settings.get_ui_label_open()
messages["READ"] = settings.get_ui_label_read()
messages["UPDATE"] = settings.get_ui_label_update()
messages["DELETE"] = "Delete"
messages["COPY"] = "Copy"
messages["SELECT_LOCATION"] = "Select a location"
messages["COUNTRY"] = "Country"
messages["ORGANISATION"] = "Organization"
messages["AUTOCOMPLETE_HELP"] = "Enter some characters to bring up a list of possible matches"

# CRUD Labels
s3.crud_labels = Storage(OPEN = messages.OPEN,
                         READ = messages.READ,
                         UPDATE = messages.UPDATE,
                         DELETE = messages.DELETE,
                         COPY = messages.COPY,
                         NONE = messages.NONE,
                         )

# Common Error Messages
ERROR["BAD_RECORD"] = "Record not found"
ERROR["BAD_ENDPOINT"] = "Endpoint not found"
ERROR["BAD_METHOD"] = "Unsupported method"
ERROR["BAD_FORMAT"] = "Unsupported data format"
ERROR["BAD_REQUEST"] = "Invalid request"
ERROR["BAD_SOURCE"] = "Invalid data source"
ERROR["BAD_RESOURCE"] = "Resource not found or not valid"
ERROR["INTEGRITY_ERROR"] = "Integrity error: record can not be deleted while it is referenced by other records"
ERROR["METHOD_DISABLED"] = "Method disabled"
ERROR["NO_MATCH"] = "No matching element found in the data source"
ERROR["NOT_IMPLEMENTED"] = "Not implemented"
ERROR["NOT_PERMITTED"] = "Operation not permitted"
ERROR["UNAUTHORISED"] = "Not Authorized"
ERROR["VALIDATION_ERROR"] = "Validation error"

# To get included in <HEAD>
s3.stylesheets = []
s3.external_stylesheets = []
# To get included at the end of <BODY>
s3.scripts = []
s3.scripts_modules = []
s3.js_global = []
s3.jquery_ready = []
#s3.js_foundation = None

# -----------------------------------------------------------------------------
# Languages
#
s3.l10n_languages = settings.get_L10n_languages()

# Default strings are in US English
T.current_languages = ("en", "en-us")
# Check if user has selected a specific language
if get_vars._language:
    language = get_vars._language
    session.s3.language = language
elif session.s3.language:
    # Use the last-selected language
    language = session.s3.language
elif auth.is_logged_in():
    # Use user preference
    language = auth.user.language
else:
    # Use system default
    language = settings.get_L10n_default_language()
#else:
#    # Use what browser requests (default web2py behaviour)
#    T.force(T.http_accept_language)

# IE doesn't set request.env.http_accept_language
#if language != "en":
T.force(language)

# Store for views (e.g. Ext)
if language.find("-") == -1:
    # Ext peculiarities
    if language == "vi":
        s3.language = "vn"
    elif language == "el":
        s3.language = "el_GR"
    else:
        s3.language = language
else:
    lang_parts = language.split("-")
    s3.language = "%s_%s" % (lang_parts[0], lang_parts[1].upper())

# List of Languages which use a Right-to-Left script (Arabic, Hebrew, Farsi, Urdu)
if language in ("ar", "prs", "ps", "ur"):
    s3.direction = "rtl"
else:
    s3.direction = "ltr"

# -----------------------------------------------------------------------------
# Auth
#
auth_settings = auth.settings

auth_settings.lock_keys = False

auth_settings.logging_enabled = settings.get_auth_logging()
auth_settings.expiration = 28800 # seconds

if settings.get_auth_openid():
    # Requires http://pypi.python.org/pypi/python-openid/
    try:
        from gluon.contrib.login_methods.openid_auth import OpenIDAuth
        openid_login_form = OpenIDAuth(auth)
        from gluon.contrib.login_methods.extended_login_form import ExtendedLoginForm
        auth_settings.login_form = ExtendedLoginForm(auth, openid_login_form,
                                                     signals=["oid", "janrain_nonce"])
    except ImportError:
        session.warning = "Library support not available for OpenID"

# Allow use of LDAP accounts for login
# NB Currently this means that change password should be disabled:
#auth_settings.actions_disabled.append("change_password")
# (NB These are not automatically added to PR or to Authenticated role since they enter via the login() method not register())
#from gluon.contrib.login_methods.ldap_auth import ldap_auth
# Require even alternate login methods to register users 1st
#auth_settings.alternate_requires_registration = True
# Active Directory
#auth_settings.login_methods.append(ldap_auth(mode="ad", server="dc.domain.org", base_dn="ou=Users,dc=domain,dc=org"))
# or if not wanting local users at all (no passwords saved within DB):
#auth_settings.login_methods = [ldap_auth(mode="ad", server="dc.domain.org", base_dn="ou=Users,dc=domain,dc=org")]
# Domino
#auth_settings.login_methods.append(ldap_auth(mode="domino", server="domino.domain.org"))
# OpenLDAP
#auth_settings.login_methods.append(ldap_auth(server="directory.sahanafoundation.org", base_dn="ou=users,dc=sahanafoundation,dc=org"))

# Allow use of Email accounts for login
#auth_settings.login_methods.append(email_auth("smtp.gmail.com:587", "@gmail.com"))

# Require captcha verification for registration
#auth.settings.captcha = RECAPTCHA(request, public_key="PUBLIC_KEY", private_key="PRIVATE_KEY")

# Require Email Verification
auth_settings.registration_requires_verification = settings.get_auth_registration_requires_verification()
auth_settings.reset_password_requires_verification = True

# Require Admin approval for self-registered users
auth_settings.registration_requires_approval = settings.get_auth_registration_requires_approval()

# We don't wish to clutter the groups list with 1 per user.
auth_settings.create_user_groups = False

# We need to allow basic logins for Webservices
auth_settings.allow_basic_login = True

auth_settings.logout_onlogout = s3_auth_on_logout
auth_settings.login_onaccept = s3_auth_on_login

# Redirection URLs
auth_settings.on_failed_authorization = URL(c="default", f="user", args="not_authorized")
auth_settings.verify_email_next = URL(c="default", f="index")

if settings.has_module("vol") and \
   settings.get_auth_registration_volunteer():
    auth_settings.register_next = URL(c="vol", f="person")

auth_settings.lock_keys = True

# -----------------------------------------------------------------------------
# Mail
#
# These settings could be made configurable as part of the Messaging Module
# - however also need to be used by Auth (order issues)
sender = settings.get_mail_sender()
if sender:
    mail.settings.sender = sender
    mail.settings.server = settings.get_mail_server()
    mail.settings.tls = settings.get_mail_server_tls()
    mail_server_login = settings.get_mail_server_login()
    if mail_server_login:
        mail.settings.login = mail_server_login
    # Email settings for registration verification and approval
    auth_settings.mailer = mail

# -----------------------------------------------------------------------------
# Session
#
# Use secure session cookie over HTTPs
if request.is_https:
    session.secure()

# Pass notifications from session to response
response.error = session.error
response.confirmation = session.confirmation
response.information = session.information
response.warning = session.warning
session.error = []
session.confirmation = []
session.information = []
session.warning = []

if s3.debug:
    # Add the developer toolbar from core/tools
    s3.toolbar = s3base.s3_dev_toolbar

# -----------------------------------------------------------------------------
# CRUD
#
s3_formstyle = settings.get_ui_formstyle()
s3_formstyle_read = settings.get_ui_formstyle_read()
s3_formstyle_mobile = s3_formstyle
submit_button = T("Save")
s3_crud = s3.crud
s3_crud.formstyle = s3_formstyle
s3_crud.formstyle_read = s3_formstyle_read
s3_crud.submit_button = submit_button
# Optional class for Submit buttons
#s3_crud.submit_style = "submit-button"
s3_crud.confirm_delete = T("Do you really want to delete these records?")
s3_crud.archive_not_delete = settings.get_security_archive_not_delete()
s3_crud.navigate_away_confirm = settings.get_ui_navigate_away_confirm()

# Content Type Headers, default is application/xml for XML formats
# and text/x-json for JSON formats, other content types must be
# specified here:
s3.content_type = Storage(
    rss = "application/rss+xml", # RSS
    georss = "application/rss+xml", # GeoRSS
    kml = "application/vnd.google-earth.kml+xml", # KML
)

# JSON Formats
s3.json_formats = ["geojson", "s3json"]

# CSV Formats
s3.csv_formats = ["s3csv"]

# Datatables default number of rows per page
s3.ROWSPERPAGE = 20

# Valid Extensions for Image Upload fields
s3.IMAGE_EXTENSIONS = ["png", "PNG", "jpg", "JPG", "jpeg", "JPEG"]

# Default CRUD strings
s3.crud_strings = Storage(
    label_create = T("Add Record"),
    title_display = T("Record Details"),
    title_list = T("Records"),
    title_update = T("Edit Record"),
    title_map = T("Map"),
    title_report = T("Report"),
    title_upload = T("Import Records"),
    label_list_button = T("List Records"),
    label_delete_button = T("Delete Record"),
    msg_record_created = T("Record added"),
    msg_record_modified = T("Record updated"),
    msg_record_deleted = T("Record deleted"),
    msg_list_empty = T("No Records currently available"),
    msg_match = T("Matching Records"),
    msg_no_match = T("No Matching Records"),
    )

# END =========================================================================
