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

# Use session for persistent per-user variables (beware of a user having multiple tabs open!)
if not session.s3:
    session.s3 = Storage()

s3.base_url = "%s/%s" % (settings.get_base_public_url(),
                         appname)
s3.download_url = "%s/default/download" % s3.base_url

###############
# Client tests
###############
def s3_is_mobile_client(request):
    """
        Simple UA Test whether client is a mobile device
    """

    if request.env.http_x_wap_profile or request.env.http_profile:
        return True
    if request.env.http_accept and \
       request.env.http_accept.find("text/vnd.wap.wml") > 0:
        return True
    keys = ["iphone", "ipod", "android", "opera mini", "blackberry", "palm",
            "windows ce", "iemobile", "smartphone", "medi", "sk-0", "vk-v",
            "aptu", "xda-", "mtv ", "v750", "p800", "opwv", "send", "xda2",
            "sage", "t618", "qwap", "veri", "t610", "tcl-", "vx60", "vx61",
            "lg-k", "lg-l", "lg-m", "lg-o", "lg-a", "lg-b", "lg-c", "xdag",
            "lg-f", "lg-g", "sl45", "emul", "lg-p", "lg-s", "lg-t", "lg-u",
            "lg-w", "6590", "t250", "qc21", "ig01", "port", "m1-w", "770s",
            "n710", "ez60", "mt50", "g1 u", "vk40", "bird", "tagt", "pose",
            "jemu", "beck", "go.w", "jata", "gene", "smar", "g-mo", "o2-x",
            "htc_", "hei-", "fake", "qc-7", "smal", "htcp", "htcs", "craw",
            "htct", "aste", "htca", "htcg", "teli", "telm", "kgt", "mwbp",
            "kwc-", "owg1", "htc ", "kgt/", "htc-", "benq", "slid", "qc60",
            "dmob", "blac", "smt5", "nec-", "sec-", "sec1", "sec0", "fetc",
            "spv ", "mcca", "nem-", "spv-", "o2im", "m50/", "ts70", "arch",
            "qtek", "opti", "devi", "winw", "rove", "winc", "talk", "pant",
            "netf", "pana", "esl8", "pand", "vite", "v400", "whit", "scoo",
            "good", "nzph", "mtp1", "doco", "raks", "wonu", "cmd-", "cell",
            "mode", "im1k", "modo", "lg-d", "idea", "jigs", "bumb", "sany",
            "vulc", "vx70", "psio", "fly_", "mate", "pock", "cdm-", "fly-",
            "i230", "lge-", "lge/", "argo", "qc32", "n701", "n700", "mc21",
            "n500", "midp", "t-mo", "airn", "bw-u", "iac", "bw-n", "lg g",
            "erk0", "sony", "alav", "503i", "pt-g", "au-m", "treo", "ipaq",
            "dang", "seri", "mywa", "eml2", "smb3", "brvw", "sgh-", "maxo",
            "pg-c", "qci-", "vx85", "vx83", "vx80", "vx81", "pg-8", "pg-6",
            "phil", "pg-1", "pg-2", "pg-3", "ds12", "scp-", "dc-s", "brew",
            "hipt", "kddi", "qc07", "elai", "802s", "506i", "dica", "mo01",
            "mo02", "avan", "kyoc", "ikom", "siem", "kyok", "dopo", "g560",
            "i-ma", "6310", "sie-", "grad", "ibro", "sy01", "nok6", "el49",
            "rim9", "upsi", "inno", "wap-", "sc01", "ds-d", "aur ", "comp",
            "wapp", "wapr", "waps", "wapt", "wapu", "wapv", "wapy", "newg",
            "wapa", "wapi", "wapj", "wapm", "hutc", "lg/u", "yas-", "hita",
            "lg/l", "lg/k", "i-go", "4thp", "bell", "502i", "zeto", "ez40",
            "java", "n300", "n302", "mmef", "pn-2", "newt", "1207", "sdk/",
            "gf-5", "bilb", "zte-", "maui", "qc-3", "qc-2", "blaz", "r600",
            "hp i", "qc-5", "moto", "cond", "motv", "virg", "ccwa", "audi",
            "shar", "i-20", "samm", "sama", "sams", "sch-", "mot ", "http",
            "505i", "mot-", "n502", "topl", "n505", "mobi", "3gso", "wmlb",
            "ezwa", "qc12", "abac", "tdg-", "neon", "mio8", "sp01", "rozo",
            "vx98", "dait", "t600", "anyw", "tx-9", "sava", "m-cr", "tsm-",
            "mioa", "tsm5", "klon", "capi", "tsm3", "hcit", "libw", "lg50",
            "mc01", "amoi", "lg54", "ez70", "se47", "n203", "vk52", "vk53",
            "vk50", "webc", "haie", "semc", "grun", "play", "palm", "a wa",
            "anny", "prox", "o2 x", "ezze", "symb", "hs-c", "pg13", "mits",
            "kpt ", "qa-a", "501i", "pdxg", "iris", "pluc", "acoo", "soft",
            "hpip", "iac/", "iac-", "aus ", "s55/", "vx53", "vx52", "chtm",
            "meri", "merc", "your", "huaw", "cldc", "voda", "smit", "x700",
            "mozz", "lexi", "up.b", "sph-", "keji", "jbro", "wig ", "attw",
            "pire", "r380", "lynx", "anex", "vm40", "hd-m", "504i", "w3c ",
            "c55/", "w3c-", "upg1", "t218", "tosh", "acer", "hd-t", "eric",
            "hd-p", "noki", "acs-", "dbte", "n202", "tim-", "alco", "ezos",
            "dall", "leno", "alca", "asus", "m3ga", "utst", "aiko", "n102",
            "n101", "n100", "oran"]
    ua = (request.env.http_user_agent or "").lower()
    if [key for key in keys if key in ua]:
        return True
    return False

# Store in session
# - commented-out until we make use of it
#if session.s3.mobile is None:
#    session.s3.mobile = s3_is_mobile_client(request)

def s3_populate_browser_compatibility(request):
    """
        Use WURFL for browser compatibility detection

        @ToDo: define a list of features to store
    """

    features = Storage(
        #category = ["list","of","features","to","store"]
    )

    try:
        from pywurfl.algorithms import TwoStepAnalysis
    except ImportError:
        s3_debug("pywurfl python module has not been installed, browser compatibility listing will not be populated. Download pywurfl from http://pypi.python.org/pypi/pywurfl/")
        return False
    import wurfl
    device = wurfl.devices.select_ua(unicode(request.env.http_user_agent),
                                     search=TwoStepAnalysis(wurfl.devices))

    browser = Storage()
    #for feature in device:
        #if feature[0] not in category_list:
            #category_list.append(feature[0])
    #for category in features:
        #if category in
        #browser[category] = Storage()
    for feature in device:
        if feature[0] in features and \
           feature[1] in features[feature[0]]:
            browser[feature[0]][feature[1]] = feature[2]

    return browser

# Store in session
# - commented-out until we make use of it
#if session.s3.browser is None:
#    session.s3.browser = s3_populate_browser_compatibility(request)

##################
# Global variables
##################

# Interactive view formats
s3.interactive_view_formats = ("html", "popup", "iframe")

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

for u in messages:
    if isinstance(messages[u], str):
        globals()[u] = T(messages[u])

# Pass to CRUD
s3mgr.LABEL["READ"] = READ
s3mgr.LABEL["UPDATE"] = UPDATE
s3mgr.LABEL["DELETE"] = DELETE
s3mgr.LABEL["COPY"] = COPY

# Data Export Settings
ROWSPERPAGE = 20
PRETTY_PRINT = False

# To get included in <HEAD>
s3.stylesheets = []
s3.external_stylesheets = []
# To get included at the end of <BODY>
s3_script_dir = "/%s/static/scripts/S3" % appname
s3.script_dir = s3_script_dir
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
# Mail
######

# These settings could be made configurable as part of the Messaging Module
# - however also need to be used by Auth (order issues), DB calls are overheads
# - as easy for admin to edit source here as to edit DB (although an admin panel can be nice)
mail.settings.server = settings.get_mail_server()
mail.settings.tls = settings.get_mail_server_tls()
mail_server_login = settings.get_mail_server_login()
if mail_server_login:
    mail.settings.login = mail_server_login
mail.settings.sender = settings.get_mail_sender()

######
# Auth
######
_messages = auth.messages
_settings = auth.settings
_settings.lock_keys = False

_settings.password_min_length = 4
_settings.expiration = 28800  # seconds

#auth.settings.username_field = True
_settings.hmac_key = settings.get_auth_hmac_key()
auth.define_tables(migrate=migrate,
                   fake_migrate=fake_migrate)

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

# Require captcha verification for registration
#auth.settings.captcha = RECAPTCHA(request, public_key="PUBLIC_KEY", private_key="PRIVATE_KEY")
# Require Email Verification
_settings.registration_requires_verification = settings.get_auth_registration_requires_verification()
# Email settings for registration verification
_settings.mailer = mail
_messages.verify_email = "Click on the link %(url)s%(key)s to verify your email" % \
    dict(url="%s/default/user/verify_email/" % s3.base_url,
         key="%(key)s")
_settings.on_failed_authorization = URL(c="default", f="user",
                                        args="not_authorized")

_messages.verify_email_subject = "%(system_name)s - Verify Email" % \
    {"system_name" : settings.get_system_name()}

_settings.reset_password_requires_verification = True
_messages.reset_password = "%s %s/default/user/reset_password/%s %s" % \
    (T("Click on the link"),
     s3.base_url,
     "%(key)s",
     T("to reset your password"))
_messages.help_mobile_phone = T("Entering a phone number is optional, but doing so allows you to subscribe to receive SMS messages.")
# Require Admin approval for self-registered users
_settings.registration_requires_approval = settings.get_auth_registration_requires_approval()
_messages.registration_pending = "Registration is still pending approval from Approver (%s) - please wait until confirmation received." % \
    settings.get_mail_approver()
_messages.registration_pending_approval = "Thank you for validating your email. Your user account is still pending for approval by the system administator (%s).You will get a notification by email when your account is activated." % \
    settings.get_mail_approver()
_settings.verify_email_next = URL(c="default", f="index")

# Notify Approver of new pending user registration. Action may be required.
_settings.verify_email_onaccept = auth.s3_verify_email_onaccept

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
# We don't wish to clutter the groups list with 1 per user.
_settings.create_user_groups = False
# We need to allow basic logins for Webservices
_settings.allow_basic_login = True

_settings.logout_onlogout = s3_auth_on_logout
_settings.login_onaccept = s3_auth_on_login
if settings.get_auth_registration_volunteer() and \
   settings.has_module("vol"):
    _settings.register_next = URL(c="vol", f="person")

# Default Language for authenticated users
_settings.table_user.language.default = settings.get_L10n_default_language()

# Languages available in User Profiles
field = _settings.table_user.language
if len(s3.l10n_languages) > 1:
    field.requires = IS_IN_SET(s3.l10n_languages,
                               zero=None)
else:
    field.default = s3.l10n_languages.keys()[0]
    field.readable = False
    field.writable = False

_settings.lock_keys = True

#########
# Session
#########
def s3_sessions():
    """
        Extend session to support multiple flash classes
    """

    response.error = session.error
    response.confirmation = session.confirmation
    response.information = session.information
    response.warning = session.warning
    session.error = []
    session.confirmation = []
    session.information = []
    session.warning = []

    return

# Extend the session
s3_sessions()

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
    s3.toolbar = s3_dev_toolbar

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
        _class = "hidden"
    else:
        _class = ""

    # Label on the 1st row
    row.append(TR(TD(label, _class="w2p_fl"), TD(""), _id=id + "1", _class=_class))
    # Widget & Comment on the 2nd Row
    row.append(TR(widget, TD(comment, _class="w2p_fc"), _id=id, _class=_class))

    return tuple(row)

s3_formstyle_mobile = s3_formstyle

s3.crud.formstyle = s3_formstyle
s3.crud.submit_button = T("Save")
# Optional class for Submit buttons
#s3.crud.submit_style = "submit-button"
s3.crud.confirm_delete = T("Do you really want to delete these records?")

s3.crud.archive_not_delete = settings.get_security_archive_not_delete()
s3.crud.navigate_away_confirm = settings.get_ui_navigate_away_confirm()
#s3.navigate_away_confirm = s3.crud.navigate_away_confirm

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

#######
# Menus
#######

# Import menus and layouts
from eden.layouts import *
import eden.menus as default_menus

S3MainMenu = default_menus.S3MainMenu
S3OptionsMenu = default_menus.S3OptionsMenu

current.menu = Storage(options=None, override={})
if auth.permission.format in ("html"):
    menus = "applications.%s.private.templates.%s.menus" % \
            (appname, settings.get_theme())
    try:
        exec("import %s as deployment_menus" % menus)
    except ImportError:
        pass
    else:
        if "S3MainMenu" in deployment_menus.__dict__:
            S3MainMenu = deployment_menus.S3MainMenu

        if "S3OptionsMenu" in deployment_menus.__dict__:
            S3OptionsMenu = deployment_menus.S3OptionsMenu

    main = S3MainMenu.menu()
else:
    main = None

menu = current.menu
menu["main"] = main

# Override controller menus
# @todo: replace by current.menu.override
s3_menu_dict = {}

##########
# Messages
##########
from gluon.storage import Messages
s3.messages = Messages(T)
system_name = settings.get_system_name_short()
s3.messages.confirmation_email_subject = "%s %s" % (system_name,
                                                    T("access granted"))
s3.messages.confirmation_email = "%s %s %s %s. %s." % (T("Welcome to the"),
                                                       system_name,
                                                       T("Portal at"),
                                                       s3.base_url,
                                                       T("Thanks for your assistance"))

# Valid Extensions for Image Upload fields
IMAGE_EXTENSIONS = ["png", "PNG", "jpg", "JPG", "jpeg", "JPEG", "gif", "GIF", "tif", "TIF", "tiff", "TIFF", "bmp", "BMP", "raw", "RAW"]
s3.IMAGE_EXTENSIONS = IMAGE_EXTENSIONS

# END =========================================================================
