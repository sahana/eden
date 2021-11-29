# -*- coding: utf-8 -*-

"""
    Import Modules
    Configure the Database
    Instantiate Classes
"""

if settings.get_L10n_languages_readonly():
    # Make the Language files read-only for improved performance
    T.is_writable = False

get_vars = request.get_vars

# Are we running in debug mode?
debug = settings.check_debug()

import datetime
import json

########################
# Database Configuration
########################

migrate = settings.get_base_migrate()
fake_migrate = settings.get_base_fake_migrate()

(db_type, db_string, pool_size) = settings.get_database_string()
if migrate:
    if db_type == "mysql":
        check_reserved = ["postgres"]
    elif db_type == "postgres":
        check_reserved = ["mysql"]
    else:
        check_reserved = ["mysql", "postgres"]
else:
    check_reserved = []

# Test MS SQL compatibility
#check_reserved = ["mssql"]

try:
    db = DAL(db_string,
             check_reserved = check_reserved,
             pool_size = pool_size,
             migrate_enabled = migrate,
             fake_migrate_all = fake_migrate,
             lazy_tables = not migrate,
             ignore_field_case = db_type != "postgres",
             )
except:
    db_location = db_string.split("@", 1)[1]
    raise HTTP(503, "Cannot connect to %s Database: %s" % (db_type, db_location))

current.db = db
db.set_folder("upload")

# Sessions Storage
if settings.get_base_session_db():
    # Store sessions in the database to avoid a locked session
    session.connect(request, response, db)
elif settings.get_base_session_memcache():
    # Store sessions in Memcache
    from gluon.contrib.memcache import MemcacheClient
    cache.memcache = MemcacheClient(request,
                                    [settings.get_base_session_memcache()])
    from gluon.contrib.memdb import MEMDB
    session.connect(request, response, db=MEMDB(cache.memcache))
#else:
    ## Default to filesystem
    # pass

####################################################################
# Instantiate Classes from Modules                                 #
# - store instances in current to be accessible from other modules #
####################################################################

from gluon.tools import Mail
current.mail = mail = Mail()

from gluon.storage import Messages
current.messages = messages = Messages(T)

current.ERROR = ERROR = Messages(T)

# Import the S3 Framework
import s3 as s3base # Shortcut for use, primarily, from views

# Set up logger (before any module attempts to use it!)
import s3log
s3log.S3Log.setup()

from s3 import AuthS3, S3Audit, S3Calendar, S3GIS, S3Msg, S3Sync, S3XML

# AAA
current.auth = auth = AuthS3()

# Use session for persistent per-user variables
# - beware of a user having multiple tabs open!
# - don't save callables or class instances as these can't be pickled
if not session.s3:
    session.s3 = Storage()

# Use username instead of email address for logins
# - would probably require further customisation
#   to get this fully-working within Eden as it's not a Tested configuration
#auth.settings.login_userfield = "username"

auth.settings.hmac_key = settings.get_auth_hmac_key()
auth.define_tables(migrate = migrate,
                   fake_migrate = fake_migrate,
                   )

current.audit = audit = S3Audit(migrate = migrate,
                                fake_migrate = fake_migrate,
                                )

# Shortcuts for models/controllers/views
# - removed to reduce per-request overheads & harmonise the environment in
#   models/controllers with that of Template controllers.py & customise() functions
#s3_has_role = auth.s3_has_role
#s3_has_permission = auth.s3_has_permission
#s3_logged_in_person = auth.s3_logged_in_person

# Calendar
current.calendar = S3Calendar()

# CRUD
s3.crud = Storage()

# GIS Module
current.gis = gis = S3GIS()

# S3XML
current.xml = s3xml = S3XML()

# Messaging
current.msg = msg = S3Msg()

# Sync
current.sync = sync = S3Sync()

# Frequently used S3 utilities imported into the global namespace for use by controllers
from s3 import FS, s3_action_buttons, s3_redirect_default, s3_str

# -----------------------------------------------------------------------------
def s3_clear_session():

    # CRUD last opened records (rcvars)
    from s3 import s3_remove_last_record_id
    s3_remove_last_record_id()

    # Session-owned records
    if "owned_records" in session:
        del session["owned_records"]

    if "s3" in session:
        s3 = session.s3
        opts = ("hrm",
                "report_options",
                "deduplicate",
                )
        for o in opts:
            if o in s3:
                del s3[o]

# -----------------------------------------------------------------------------
def s3_auth_on_login(form):
    """
        Actions to be performed upon successful login
            Do not redirect from here!
    """
    s3_clear_session()

# -----------------------------------------------------------------------------
def s3_auth_on_logout(user):
    """
        Actions to be performed after logout
            Do not redirect from here!
    """
    s3_clear_session()

# END =========================================================================
