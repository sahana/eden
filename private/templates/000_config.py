# -*- coding: utf-8 -*-

"""
    Machine-specific settings
    All settings which are typically edited for a specific machine should be done here

    Deployers should ideally not need to edit any other files outside of their template folder

    Note for Developers:
        /models/000_config.py is NOT in the Git repository, to avoid leaking of
        sensitive or irrelevant information into the repository.
    For changes to be committed, please also edit:
        private/templates/000_config.py
"""

# Remove this line when you have edited this file sufficiently to proceed to the web interface
FINISHED_EDITING_CONFIG_FILE = False

# Select the Template
# - which Modules are enabled
# - PrePopulate data
# - Security Policy
# - Workflows
# - Theme
# - note that you should restart your web2py after changing this setting
settings.base.template = "default"

# Database settings
# Uncomment to use a different database, other than sqlite
#settings.database.db_type = "postgres"
#settings.database.db_type = "mysql"
# Uncomment to use a different host
#settings.database.host = "localhost"
# Uncomment to use a different port
#settings.database.port = 3306
#settings.database.port = 5432
# Uncomment to select a different name for your database
#settings.database.database = "sahana"
# Uncomment to select a different username for your database
#settings.database.username = "sahana"
# Uncomment to set the password
# NB Web2Py doesn't like passwords with an @ in them
#settings.database.password = "password"
# Uncomment to use a different pool size
#settings.database.pool_size = 30
# Do we have a spatial DB available? (currently supports PostGIS. Spatialite to come.)
#settings.gis.spatialdb = True

# Base settings
#settings.base.system_name = T("Sahana Eden Humanitarian Management Platform")
#settings.base.system_name_short = T("Sahana Eden")
# Set this to the Public URL of the instance
#settings.base.public_url = "http://127.0.0.1:8000"

# Switch to "False" in Production for a Performance gain
# (need to set to "True" again when Table definitions are changed)
settings.base.migrate = True
# To just create the .table files (also requires migrate=True):
#settings.base.fake_migrate = True

# Set this to True to switch to Debug mode
# Debug mode means that uncompressed CSS/JS files are loaded
# JS Debug messages are also available in the Console
# can also load an individual page in debug mode by appending URL with
# ?debug=1
settings.base.debug = False

# Uncomment to use Content Delivery Networks to speed up Internet-facing sites
#settings.base.cdn = True

# This setting will be automatically changed _before_ registering the 1st user
settings.auth.hmac_key = "akeytochange"

# Email settings
# Outbound server
#settings.mail.server = "127.0.0.1:25"
#settings.mail.tls = True
# Useful for Windows Laptops:
#settings.mail.server = "smtp.gmail.com:587"
#settings.mail.tls = True
#settings.mail.login = "username:password"
# From Address - until this is set, no mails can be sent
#settings.mail.sender = "'Sahana' <sahana@example.org>"
# Default email address to which requests to approve new user accounts gets sent
# This can be overridden for specific domains/organisations via the auth_domain table
#settings.mail.approver = "useradmin@example.org"
# Daily Limit on Sending of emails
#settings.mail.limit = 1000

# Frontpage settings
# RSS feeds
settings.frontpage.rss = [
    {"title": "Eden",
     # Trac timeline
     "url": "http://eden.sahanafoundation.org/timeline?ticket=on&changeset=on&milestone=on&wiki=on&max=50&daysback=90&format=rss"
    },
    {"title": "Twitter",
     # @SahanaFOSS
     # Find ID via http://api.twitter.com/users/show/username.json
     "url": "http://twitter.com/statuses/user_timeline/96591754.rss"
     # Hashtag
     #url: "http://search.twitter.com/search.atom?q=%23eqnz"
    }
]

# Enable session store in Memcache to allow sharing of sessions across instances
#settings.base.session_memcache = '127.0.0.1:11211'

# Allow language files to be updated automatically
#settings.L10n.languages_readonly = False

# Fill these to allow users to Login using Facebook
# https://developers.facebook.com/apps
#settings.auth.facebook_id = ""
#settings.auth.facebook_secret = ""
# Fill these to allow users to Login using Google
# https://code.google.com/apis/console/
#settings.auth.google_id = ""
#settings.auth.google_secret = ""

# Bing API Key (for Map layers)
#settings.gis.api_bing = ""
# Google API Key (for Earth & MapMaker Layers)
# default works for localhost
#settings.gis.api_google = ""
# Yahoo API Key (for Geocoder)
#settings.gis.api_yahoo = ""
# GeoServer (Currently used by GeoExplorer. Will allow REST control of GeoServer.)
# NB Needs to be publically-accessible URL for querying via client JS
#settings.gis.geoserver_url = "http://localhost/geoserver"
#settings.gis.geoserver_username = "admin"
#settings.gis.geoserver_password = ""
# Print Service URL: http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting
#settings.gis.print_service = "/geoserver/pdf/"

# Twitter settings:
# Register an app at https://dev.twitter.com/apps
# (select Application Type: Client)
# Leave callback URL blank to allow entry of PIN for Tweepy
# - should be changed sot aht we can have one to use for Auth!
#settings.msg.twitter_oauth_consumer_key = ""
#settings.msg.twitter_oauth_consumer_secret = ""

# UI options
# Should user be prompted to save before navigating away?
#settings.ui.navigate_away_confirm = False
# Should user be prompted to confirm actions?
#settings.ui.confirm = False
# Should potentially large dropdowns be turned into autocompletes?
# (unused currently)
#settings.ui.autocomplete = True
#settings.ui.read_label = "Details"
#settings.ui.update_label = "Edit"

# Audit settings
# We Audit if either the Global or Module asks us to
# (ignore gracefully if module author hasn't implemented this)
# NB Auditing (especially Reads) slows system down & consumes diskspace
#settings.security.audit_write = False
#settings.security.audit_read = False

# =============================================================================
# Import the settings from the Template
# - note: invalid settings are ignored
#
path = template_path()
if os.path.exists(path):
    settings.exec_template(path)

# =============================================================================
# Over-rides to the Template may be done here
#

# e.g.
#settings.base.prepopulate = ["IFRC_Train"]
#settings.base.theme = "default"
#settings.L10n.default_language = "en"
#settings.security.policy = 7 # Organisation-ACLs
# Enable Additional Module(s)
#settings.modules["delphi"] = Storage(
#        name_nice = T("Delphi Decision Maker"),
#        restricted = False,
#        module_type = 10,
#    )

# After 1st_run, set this for Production to save 1x DAL hit/request
#settings.base.prepopulate = 0

# =============================================================================
# A version number to tell update_check if there is a need to refresh the
# running copy of this file
VERSION = 1

# END =========================================================================