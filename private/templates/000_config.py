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

# Uncomment this to prevent automated test runs from remote
# settings.base.allow_testing = False

# Configure the log level ("DEBUG", "INFO", "WARNING", "ERROR" or "CRITICAL"), None = turn off logging
#settings.log.level = "WARNING"
# Uncomment to prevent writing log messages to the console (sys.stderr)
#settings.log.console = False
# Configure a log file (file name)
#settings.log.logfile = None
# Uncomment to get detailed caller information
#settings.log.caller_info = True

# Uncomment to use Content Delivery Networks to speed up Internet-facing sites
#settings.base.cdn = True

# Allow language files to be updated automatically
#settings.L10n.languages_readonly = False

# This setting should be changed _before_ registering the 1st user
# - should happen automatically if installing using supported scripts
settings.auth.hmac_key = "akeytochange"

# Minimum Password Length
#settings.auth.password_min_length = 8

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
     #"url": "https://search.twitter.com/search.rss?q=from%3ASahanaFOSS" # API v1 deprecated, so doesn't work, need to use 3rd-party service, like:
     "url": "http://www.rssitfor.me/getrss?name=@SahanaFOSS"
     # Hashtag
     #url: "http://search.twitter.com/search.atom?q=%23eqnz" # API v1 deprecated, so doesn't work, need to use 3rd-party service, like:
     #url: "http://api2.socialmention.com/search?q=%23eqnz&t=all&f=rss"
    }
]

# Uncomment to restrict to specific country/countries
#settings.gis.countries= ("LK",)

# Uncomment to enable a guided tour
#settings.base.guided_tour = True

# Instance Name - for management scripts
#settings.base.instance_name = "test"

# Bing API Key (for Map layers)
# http://www.microsoft.com/maps/create-a-bing-maps-key.aspx
#settings.gis.api_bing = ""
# Google API Key (for Earth & MapMaker Layers)
# default works for localhost
#settings.gis.api_google = ""
# Yahoo API Key (for Geocoder)
#settings.gis.api_yahoo = ""

# GeoNames username
#settings.gis.geonames_username = ""

# Fill this in to get Google Analytics for your site
#settings.base.google_analytics_tracking_id = ""

# Chat server, see: http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Chat
#settings.base.chat_server = {
#   "ip": "127.0.0.1",
#   "port": 7070,
#   "name": "servername",
#	# Default group everyone is added to
#   "groupname" : "everyone",
#   "server_db" : "openfire",
#   # These settings fallback to main DB settings if not specified
#   # Only mysql/postgres supported
#   #"server_db_type" : "mysql",
#   #"server_db_username" : "",
#   #"server_db_password": "",
#   #"server_db_port" : 3306,
#   #"server_db_ip" : "127.0.0.1",
#   }

# GeoServer (Currently used by GeoExplorer. Will allow REST control of GeoServer.)
# NB Needs to be publically-accessible URL for querying via client JS
#settings.gis.geoserver_url = "http://localhost/geoserver"
#settings.gis.geoserver_username = "admin"
#settings.gis.geoserver_password = ""
# Print Service URL: http://eden.sahanafoundation.org/wiki/BluePrintGISPrinting
#settings.gis.print_service = "/geoserver/pdf/"

# Google OAuth (to allow users to login using Google)
# https://code.google.com/apis/console/
#settings.auth.google_id = ""
#settings.auth.google_secret = ""

# Pootle server
# settings.L10n.pootle_url = "http://pootle.sahanafoundation.org/"
# settings.L10n.pootle_username = "username"
# settings.L10n.pootle_password = "*****"

# SOLR server for Full-Text Search
#settings.base.solr_url = "http://127.0.0.1:8983/solr/"

# Memcache server to allow sharing of sessions across instances
#settings.base.session_memcache = '127.0.0.1:11211'

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
# - can be a callable for custom hooks (return True to also perform normal logging, or False otherwise)
# NB Auditing (especially Reads) slows system down & consumes diskspace
#settings.security.audit_write = False
#settings.security.audit_read = False

# Performance Options
# Maximum number of search results for an Autocomplete Widget
#settings.search.max_results = 200
# Maximum number of features for a Map Layer
#settings.gis.max_features = 1000

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
#settings.base.system_name = T("Sahana TEST")
#settings.base.prepopulate = ("default", "default/users")
#settings.base.theme = "default"
#settings.L10n.default_language = "en"
#settings.security.policy = 7 # Organisation-ACLs
# Enable Additional Module(s)
#settings.modules["delphi"] = Storage(
#        name_nice = T("Delphi Decision Maker"),
#        restricted = False,
#        module_type = 10,
#    )
# Disable a module which is nromally used by the template
# - NB Only templates with adaptive menus will work nicely with this!
#del settings.modules["irs"]

# After 1st_run, set this for Production to save 1x DAL hit/request
#settings.base.prepopulate = 0

# =============================================================================
# A version number to tell update_check if there is a need to refresh the
# running copy of this file
VERSION = 1

# END =========================================================================
