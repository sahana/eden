# -*- coding: utf-8 -*-

"""
    Import Modules
    Configure the Database
    Instantiate Classes
"""

if settings.get_L10n_languages_readonly():
    T.is_writable = False

# Are we running in debug mode?
s3.debug = request.vars.get("debug", None) or \
                    settings.get_base_debug()

if s3.debug:
    # Reload all modules every request
    # Doesn't catch s3cfg or s3/*
    from gluon.custom_import import track_changes
    track_changes(True)

import datetime

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

########################
# Database Configuration
########################

migrate = settings.get_base_migrate()
fake_migrate = settings.get_base_fake_migrate()

if migrate:
    check_reserved = ["mysql", "postgres"]
else:
    check_reserved = None

(db_string, pool_size) = settings.get_database_string()
if db_string.find("sqlite") != -1:
    db = DAL(db_string,
             check_reserved=check_reserved,
             migrate_enabled = migrate,
             fake_migrate_all = fake_migrate)
    # on SQLite 3.6.19+ this enables foreign key support (included in Python 2.7+)
    # db.executesql("PRAGMA foreign_keys=ON")
else:
    try:
        if db_string.find("mysql") != -1:
            # Use MySQLdb where available (pymysql has given broken pipes)
            try:
                import MySQLdb
                from gluon.dal import MySQLAdapter
                MySQLAdapter.driver = MySQLdb
            except ImportError:
                # Fallback to pymysql
                pass
            if check_reserved:
                check_reserved = ["postgres"]
            db = DAL(db_string, check_reserved=check_reserved,
                     pool_size=pool_size, migrate_enabled = migrate)
        else:
            # PostgreSQL
            if check_reserved:
                check_reserved = ["mysql"]
            db = DAL(db_string, check_reserved=check_reserved,
                     pool_size=pool_size, migrate_enabled = migrate)
    except:
        db_type = db_string.split(":", 1)[0]
        db_location = db_string.split("@", 1)[1]
        raise(HTTP(503, "Cannot connect to %s Database: %s" % (db_type, db_location)))

current.db = db
db.set_folder("upload")

# Sessions Storage
if settings.get_base_session_memcache():
    # Store sessions in Memcache
    from gluon.contrib.memcache import MemcacheClient
    cache.memcache = MemcacheClient(request,
                                    [settings.get_base_session_memcache()])
    from gluon.contrib.memdb import MEMDB
    session.connect(request, response, db=MEMDB(cache.memcache))

####################################################################
# Instantiate Classes from Modules                                 #
# - store instances in current to be accessible from other modules #
####################################################################

from gluon.tools import Mail
mail = Mail()
current.mail = mail

from gluon.storage import Messages
messages = Messages(T)
current.messages = messages

# Import the S3 Framework
if update_check_needed:
    # Reload the Field definitions
    reload(s3base.s3fields)
else:
    import s3 as s3base

# Use session for persistent per-user variables
# - beware of a user having multiple tabs open!
# - don't save callables or class instances as these can't be pickled
if not session.s3:
    session.s3 = Storage()

# AAA
auth = s3base.AuthS3()
current.auth = auth

s3_audit = s3base.S3Audit(migrate=migrate, fake_migrate=fake_migrate)
current.s3_audit = s3_audit

# Use username instead of email address for logins
# - would probably require further customisation
#   to get this working within Eden
#auth.settings.username_field = True

auth.settings.hmac_key = settings.get_auth_hmac_key()
auth.define_tables(migrate=migrate, fake_migrate=fake_migrate)

# Shortcuts for models/controllers/views
s3_has_role = auth.s3_has_role
s3_has_permission = auth.s3_has_permission
s3_logged_in_person = auth.s3_logged_in_person

# CRUD
crud = s3base.CrudS3()
current.crud = crud
s3.crud = Storage()

# S3 Custom Validators and Widgets, imported here into the global
# namespace in order to access them without the s3base namespace prefix
s3_action_buttons = s3base.S3CRUD.action_buttons
s3_fullname = s3base.s3_fullname
S3ResourceHeader = s3base.S3ResourceHeader
from s3.s3navigation import s3_rheader_tabs
from s3.s3validators import *
from s3.s3widgets import *

# GIS Module
gis = s3base.GIS()
current.gis = gis

# S3RequestManager
s3mgr = s3base.S3RequestManager()
current.manager = s3mgr
s3_request = s3base.s3_request

# S3XML
s3xml = s3base.S3XML()
current.xml = s3xml

# Messaging
msg = s3base.S3Msg()
current.msg = msg

# Sync
sync = s3base.S3Sync()
current.sync = sync

# -----------------------------------------------------------------------------
def s3_clear_session():

    # S3ResourceManager last seen records (rcvars)
    s3mgr.clear_session()

    # Session-owned records
    if "owned_records" in session:
        del session["owned_records"]

    if "s3" in session:
        s3 = session.s3
        opts = ["hrm", "report_options", "utc_offset"]
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
