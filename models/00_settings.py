# -*- coding: utf-8 -*-

"""
    Global settings:

    Those which are typically edited during a deployment are in
    000_config.py & their results parsed into here. Deployers
    shouldn't typically need to edit any settings here.
"""

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
# Client tests

# Check whether browser is Mobile & store result in session
# - commented-out until we make use of it
#if session.s3.mobile is None:
#    session.s3.mobile = s3base.s3_is_mobile_client(request)
#if session.s3.browser is None:
#    session.s3.browser = s3base.s3_populate_browser_compatibility(request)

# -----------------------------------------------------------------------------
# Global variables

# Strings to i18n
# Common Labels
#messages["BREADCRUMB"] = ">> "
messages["UNKNOWN_OPT"] = "Unknown"
messages["NONE"] = "-"
messages["OBSOLETE"] = "Obsolete"
messages["READ"] = settings.get_ui_label_read()
messages["UPDATE"] = settings.get_ui_label_update()
messages["DELETE"] = "Delete"
messages["COPY"] = "Copy"
messages["NOT_APPLICABLE"] = "N/A"
messages["ADD_PERSON"] = "Create a Person"
messages["ADD_LOCATION"] = "Create Location"
messages["SELECT_LOCATION"] = "Select a location"
messages["COUNTRY"] = "Country"
messages["ORGANISATION"] = "Organization"
messages["AUTOCOMPLETE_HELP"] = "Enter some characters to bring up a list of possible matches"

for u in messages:
    if isinstance(messages[u], str):
        globals()[u] = T(messages[u])

# CRUD Labels
s3.crud_labels = Storage(READ=READ,
                         UPDATE=UPDATE,
                         DELETE=DELETE,
                         COPY=COPY,
                         NONE=NONE,
                         )

# Error Messages
ERROR["BAD_RECORD"] = "Record not found!"
ERROR["BAD_METHOD"] = "Unsupported method!"
ERROR["BAD_FORMAT"] = "Unsupported data format!"
ERROR["BAD_REQUEST"] = "Invalid request"
ERROR["BAD_SOURCE"] = "Invalid source"
ERROR["BAD_TEMPLATE"] = "XSLT stylesheet not found"
ERROR["BAD_RESOURCE"] = "Nonexistent or invalid resource"
ERROR["DATA_IMPORT_ERROR"] = "Data import error"
ERROR["INTEGRITY_ERROR"] = "Integrity error: record can not be deleted while it is referenced by other records"
ERROR["METHOD_DISABLED"] = "Method disabled"
ERROR["NO_MATCH"] = "No matching element found in the data source"
ERROR["NOT_IMPLEMENTED"] = "Not implemented"
ERROR["NOT_PERMITTED"] = "Operation not permitted"
ERROR["PARSE_ERROR"] = "XML parse error"
ERROR["TRANSFORMATION_ERROR"] = "XSLT transformation error"
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

# -----------------------------------------------------------------------------
# Languages

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
    s3.rtl = True
else:
    s3.rtl = False

# -----------------------------------------------------------------------------
# Auth

_settings = auth.settings
_settings.lock_keys = False

_settings.expiration = 28800  # seconds

if settings.get_auth_openid():
    # Requires http://pypi.python.org/pypi/python-openid/
    try:
        from gluon.contrib.login_methods.openid_auth import OpenIDAuth
        openid_login_form = OpenIDAuth(auth)
        from gluon.contrib.login_methods.extended_login_form import ExtendedLoginForm
        _settings.login_form = ExtendedLoginForm(auth, openid_login_form,
                                                 signals=["oid", "janrain_nonce"])
    except ImportError:
        session.warning = "Library support not available for OpenID"

# Allow use of LDAP accounts for login
# NB Currently this means that change password should be disabled:
#_settings.actions_disabled.append("change_password")
# (NB These are not automatically added to PR or to Authenticated role since they enter via the login() method not register())
#from gluon.contrib.login_methods.ldap_auth import ldap_auth
# Require even alternate login methods to register users 1st
#_settings.alternate_requires_registration = True
# Active Directory
#_settings.login_methods.append(ldap_auth(mode="ad", server="dc.domain.org", base_dn="ou=Users,dc=domain,dc=org"))
# or if not wanting local users at all (no passwords saved within DB):
#_settings.login_methods = [ldap_auth(mode="ad", server="dc.domain.org", base_dn="ou=Users,dc=domain,dc=org")]
# Domino
#_settings.login_methods.append(ldap_auth(mode="domino", server="domino.domain.org"))
# OpenLDAP
#_settings.login_methods.append(ldap_auth(server="directory.sahanafoundation.org", base_dn="ou=users,dc=sahanafoundation,dc=org"))
# Allow use of Email accounts for login
#_settings.login_methods.append(email_auth("smtp.gmail.com:587", "@gmail.com"))

# Require captcha verification for registration
#auth.settings.captcha = RECAPTCHA(request, public_key="PUBLIC_KEY", private_key="PRIVATE_KEY")
# Require Email Verification
_settings.registration_requires_verification = settings.get_auth_registration_requires_verification()
_settings.on_failed_authorization = URL(c="default", f="user",
                                        args="not_authorized")
_settings.reset_password_requires_verification = True
_settings.verify_email_next = URL(c="default", f="index")

# Require Admin approval for self-registered users
_settings.registration_requires_approval = settings.get_auth_registration_requires_approval()

# We don't wish to clutter the groups list with 1 per user.
_settings.create_user_groups = False
# We need to allow basic logins for Webservices
_settings.allow_basic_login = True

_settings.logout_onlogout = s3_auth_on_logout
_settings.login_onaccept = s3_auth_on_login
# Now read in auth.login() to avoid setting unneccesarily in every request
#_settings.login_next = settings.get_auth_login_next()
if settings.has_module("vol") and \
   settings.get_auth_registration_volunteer():
    _settings.register_next = URL(c="vol", f="person")

# Languages available in User Profiles
#if len(s3.l10n_languages) > 1:
#    _settings.table_user.language.requires = s3base.IS_ISO639_2_LANGUAGE_CODE(sort = True,
#                                                                              translate = True,
#                                                                              zero = None,
#                                                                              )
#else:
#    field = _settings.table_user.language
#    field.default = s3.l10n_languages.keys()[0]
#    field.readable = False
#    field.writable = False

_settings.lock_keys = True

# -----------------------------------------------------------------------------
# Mail

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
    _settings.mailer = mail

# -----------------------------------------------------------------------------
# Session

# Custom Notifications
response.error = session.error
response.confirmation = session.confirmation
response.information = session.information
response.warning = session.warning
session.error = []
session.confirmation = []
session.information = []
session.warning = []

# Shortcuts for system role IDs, see modules/s3aaa.py/AuthS3
#system_roles = auth.get_system_roles()
#ADMIN = system_roles.ADMIN
#AUTHENTICATED = system_roles.AUTHENTICATED
#ANONYMOUS = system_roles.ANONYMOUS
#EDITOR = system_roles.EDITOR
#MAP_ADMIN = system_roles.MAP_ADMIN
#ORG_ADMIN = system_roles.ORG_ADMIN
#ORG_GROUP_ADMIN = system_roles.ORG_GROUP_ADMIN

if s3.debug:
    # Add the developer toolbar from modules/s3/s3utils.py
    s3.toolbar = s3base.s3_dev_toolbar

# -----------------------------------------------------------------------------
# CRUD

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
    tc = "application/atom+xml", # TableCast feeds
    rss = "application/rss+xml", # RSS
    georss = "application/rss+xml", # GeoRSS
    kml = "application/vnd.google-earth.kml+xml", # KML
)

# JSON Formats
s3.json_formats = ["geojson", "s3json"]

# CSV Formats
s3.csv_formats = ["hrf", "s3csv"]

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
