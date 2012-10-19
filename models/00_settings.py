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

###############
# Client tests
###############

# Check whether browser is Mobile & store result in session
# - commented-out until we make use of it
#if session.s3.mobile is None:
#    session.s3.mobile = s3base.s3_is_mobile_client(request)
#if session.s3.browser is None:
#    session.s3.browser = s3base.s3_populate_browser_compatibility(request)

##################
# Global variables
##################

# Strings to i18n
messages["UNAUTHORISED"] = "Not authorised!"
messages["BADFORMAT"] = "Unsupported data format!"
messages["BADMETHOD"] = "Unsupported method!"
messages["BADRECORD"] = "Record not found!"
messages["INVALIDREQUEST"] = "Invalid request!"
messages["XLWT_ERROR"] = "xlwt module not available within the running Python - this needs installing for XLS output!"
messages["REPORTLAB_ERROR"] = "ReportLab module not available within the running Python - this needs installing for PDF output!"
# Common Labels
#messages["BREADCRUMB"] = ">> "
messages["UNKNOWN_OPT"] = "Unknown"
messages["NONE"] = "-"
messages["READ"] = settings.get_ui_read_label()
messages["UPDATE"] = settings.get_ui_update_label()
messages["DELETE"] = "Delete"
messages["COPY"] = "Copy"
messages["NOT_APPLICABLE"] = "N/A"
messages["ADD_PERSON"] = "Add Person"
messages["ADD_LOCATION"] = "Add Location"
messages["SELECT_LOCATION"] = "Select a location"
messages["COUNTRY"] = "Country"
messages["ORGANISATION"] = "Organization"

for u in messages:
    if isinstance(messages[u], str):
        globals()[u] = T(messages[u])

# Pass to CRUD
s3mgr.LABEL["READ"] = READ
s3mgr.LABEL["UPDATE"] = UPDATE
s3mgr.LABEL["DELETE"] = DELETE
s3mgr.LABEL["COPY"] = COPY

# To get included in <HEAD>
s3.stylesheets = []
s3.external_stylesheets = []
# To get included at the end of <BODY>
s3.scripts = []
s3.js_global = []
s3.jquery_ready = []

###########
# Languages
###########

s3.l10n_languages = settings.get_L10n_languages()

# Default strings are in US English
T.current_languages = ["en", "en-us"]
# Check if user has selected a specific language
if request.vars._language:
    language = request.vars._language
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
s3_rtl_languages = ["ur", "ar"]

if T.accepted_language in s3_rtl_languages:
    s3.rtl = True
else:
    s3.rtl = False

######
# Auth
######
_settings = auth.settings
_settings.lock_keys = False

_settings.password_min_length = 4
_settings.expiration = 28800  # seconds

_settings.facebook = settings.get_auth_facebook()
_settings.google = settings.get_auth_google()

if settings.get_auth_openid():
    # Requires http://pypi.python.org/pypi/python-openid/
    try:
        from gluon.contrib.login_methods.openid_auth import OpenIDAuth
        openid_login_form = OpenIDAuth(auth)
        from gluon.contrib.login_methods.extended_login_form import ExtendedLoginForm
        extended_login_form = ExtendedLoginForm(auth, openid_login_form,
                                                signals=["oid", "janrain_nonce"])
        auth.settings.login_form = extended_login_form
    except ImportError:
        session.warning = T("Library support not available for OpenID")

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

# Auth Messages
_messages = auth.messages

_messages.verify_email = "Click on the link %(url)s%(key)s to verify your email" % \
    dict(url="%s/default/user/verify_email/" % s3.base_url,
         key="%(key)s")
_messages.verify_email_subject = "%(system_name)s - Verify Email" % \
    {"system_name" : settings.get_system_name()}
_messages.reset_password = "%s %s/default/user/reset_password/%s %s" % \
    (T("Click on the link"),
     s3.base_url,
     "%(key)s",
     T("to reset your password"))
_messages.help_mobile_phone = T("Entering a phone number is optional, but doing so allows you to subscribe to receive SMS messages.")
# Require Admin approval for self-registered users
_settings.registration_requires_approval = settings.get_auth_registration_requires_approval()
_messages.registration_pending = settings.get_auth_registration_pending()

_messages["approve_user"] = \
"""Your action is required to approve a New User for %(system_name)s:
%(name_format)s
Please go to %(base_url)s/admin/user to approve this user.""" \
% dict(system_name = settings.get_system_name(),
       name_format = \
"""%(first_name)s %(last_name)s
%(email)s""",
       base_url = s3.base_url)

_messages["new_user"] = \
"""A New User has registered for %(system_name)s:
%(name_format)s
No action is required.""" \
% dict(system_name = settings.get_system_name(),
       name_format = \
"""%(first_name)s %(last_name)s
%(email)s""")

_messages["confirmation_email_subject"] = "%s %s" % (settings.get_system_name(),
                                                     T("access granted"))
_messages["confirmation_email"] = "%s %s %s %s. %s." % (T("Welcome to the"),
                                                        settings.get_system_name(),
                                                        T("Portal at"),
                                                        s3.base_url,
                                                        T("Thanks for your assistance"))

# We don't wish to clutter the groups list with 1 per user.
_settings.create_user_groups = False
# We need to allow basic logins for Webservices
_settings.allow_basic_login = True

_settings.logout_onlogout = s3_auth_on_logout
_settings.login_onaccept = s3_auth_on_login
_settings.login_next = settings.get_auth_login_next()
if settings.has_module("vol") and \
   settings.get_auth_registration_volunteer():
    _settings.register_next = URL(c="vol", f="person")

# Languages available in User Profiles
if len(s3.l10n_languages) > 1:
    _settings.table_user.language.requires = IS_IN_SET(s3.l10n_languages,
                                                       zero=None)
else:
    field = _settings.table_user.language
    field.default = s3.l10n_languages.keys()[0]
    field.readable = False
    field.writable = False

_settings.lock_keys = True

######
# Mail
######

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

#########
# Session
#########

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
system_roles = auth.get_system_roles()
ADMIN = system_roles.ADMIN
AUTHENTICATED = system_roles.AUTHENTICATED
ANONYMOUS = system_roles.ANONYMOUS
EDITOR = system_roles.EDITOR
MAP_ADMIN = system_roles.MAP_ADMIN
ORG_ADMIN = system_roles.ORG_ADMIN

if s3.debug:
    # Add the developer toolbar from modules/s3/s3utils.py
    s3.toolbar = s3base.s3_dev_toolbar

######
# CRUD
######

def s3_formstyle(id, label, widget, comment, hidden=False):
    """
        Provide the Sahana Eden Form Style

        Label above the Inputs:
        http://uxmovement.com/design-articles/faster-with-top-aligned-labels
    """

    row = []

    if hidden:
        _class = "hide"
    else:
        _class = ""

    # Label on the 1st row
    row.append(TR(TD(label, _class="w2p_fl"), TD(""), _id=id + "1", _class=_class))
    # Widget & Comment on the 2nd Row
    row.append(TR(widget, TD(comment, _class="w2p_fc"), _id=id, _class=_class))

    return tuple(row)

s3_formstyle_mobile = s3_formstyle

_crud = s3.crud
_crud.formstyle = s3_formstyle
_crud.submit_button = T("Save")
# Optional class for Submit buttons
#_crud.submit_style = "submit-button"
_crud.confirm_delete = T("Do you really want to delete these records?")

_crud.archive_not_delete = settings.get_security_archive_not_delete()
_crud.navigate_away_confirm = settings.get_ui_navigate_away_confirm()

# Web2py Crud

# Breaks refresh of List after Create: http://groups.google.com/group/web2py/browse_thread/thread/d5083ed08c685e34
#crud.settings.keepvalues = True
crud.messages.submit_button = s3.crud.submit_button
crud.settings.formstyle = s3.crud.formstyle

##################
# XML/JSON Formats
##################

s3mgr.crud = s3base.S3CRUD
s3mgr.search = s3base.S3Search

# Content Type Headers, default is application/xml for XML formats
# and text/x-json for JSON formats, other content types must be
# specified here:
s3mgr.content_type = Storage(
    tc = "application/atom+xml", # TableCast feeds
    rss = "application/rss+xml", # RSS
    georss = "application/rss+xml", # GeoRSS
    kml = "application/vnd.google-earth.kml+xml", # KML
)

# JSON Formats
s3mgr.json_formats = ["geojson", "s3json"]

# CSV Formats
s3mgr.csv_formats = ["hrf", "s3csv"]

s3mgr.ROWSPERPAGE = 20

# Valid Extensions for Image Upload fields
s3.IMAGE_EXTENSIONS = ["png", "PNG", "jpg", "JPG", "jpeg", "JPEG", "gif", "GIF", "tif", "TIF", "tiff", "TIFF", "bmp", "BMP", "raw", "RAW"]

# Default CRUD strings
ADD_RECORD = T("Add Record")
s3.crud_strings = Storage(
    title_create = ADD_RECORD,
    title_display = T("Record Details"),
    title_list = T("Records"),
    title_update = T("Edit Record"),
    title_search = T("Search Records"),
    title_map = T("Map"),
    subtitle_create = T("Add New Record"),
    label_list_button = T("List Records"),
    label_create_button = ADD_RECORD,
    label_delete_button = T("Delete Record"),
    msg_record_created = T("Record added"),
    msg_record_modified = T("Record updated"),
    msg_record_deleted = T("Record deleted"),
    msg_list_empty = T("No Records currently available"),
    msg_match = T("Matching Records"),
    msg_no_match = T("No Matching Records"),
    name_nice = T("Record"),
    name_nice_plural = T("Records"))

# END =========================================================================
