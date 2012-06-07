# -*- coding: utf-8 -*-

"""
    Import Modules
    Configure the Database
    Instantiate Classes
"""

# Are we running in debug mode?
s3.debug = request.vars.get("debug", None) or \
                    deployment_settings.get_base_debug()

if s3.debug:
    # Needed for s3_include_debug
    import sys
    # Reload all modules every request
    # Doesn't catch s3cfg or s3/*
    from gluon.custom_import import track_changes
    track_changes(True)

import datetime
import os
import re
import time

from gluon.dal import Row
from gluon.sqlhtml import RadioWidget

import gluon.contrib.simplejson as json

# All dates should be stored in UTC for Sync to work reliably
request.utcnow = datetime.datetime.utcnow()

########################
# Database Configuration
########################

migrate = deployment_settings.get_base_migrate()
fake_migrate = deployment_settings.get_base_fake_migrate()

if migrate:
    check_reserved = ["mysql", "postgres"]
else:
    check_reserved = None

(db_string, pool_size) = deployment_settings.get_database_string()
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
if deployment_settings.get_base_session_memcache():
    # Store sessions in Memcache
    from gluon.contrib.memcache import MemcacheClient
    cache.memcache = MemcacheClient(request,
                                    [deployment_settings.get_base_session_memcache()])
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
import s3 as s3base

# AAA
auth = s3base.AuthS3()
current.auth = auth
s3_audit = s3base.S3Audit(migrate=migrate, fake_migrate=fake_migrate)
current.s3_audit = s3_audit
s3_logged_in_person = auth.s3_logged_in_person
s3_logged_in_human_resource = auth.s3_logged_in_human_resource
aURL = auth.permission.accessible_url

# Shortcuts
s3_has_role = auth.s3_has_role
s3_has_permission = auth.s3_has_permission
s3_accessible_query = auth.s3_accessible_query

# Custom classes which extend default Gluon
crud = s3base.CrudS3()
current.crud = crud
S3DateTime = s3base.S3DateTime
S3ResourceHeader = s3base.S3ResourceHeader

from gluon.tools import Service
service = Service()

from gluon.tools import callback

# S3 Custom Validators,
# imported here into the global namespace in order
# to access them without the s3base namespace prefix
from s3.s3validators import *

# S3 Custom Utilities and Widgets
# imported here into the global namespace in order
# to access them without the s3base namespace prefix
from s3.s3utils import *
from s3.s3widgets import *
from s3.s3navigation import s3_rheader_resource
from s3.s3navigation import s3_rheader_tabs

# GIS Module
gis = s3base.GIS()
current.gis = gis

# S3RequestManager
s3.crud = Storage()
s3mgr = s3base.S3RequestManager()
current.manager = s3mgr

# MSG
msg = s3base.S3Msg()
current.msg = msg

# Charting
s3chart = s3base.S3Chart
current.chart = s3chart

# -----------------------------------------------------------------------------
def s3_clear_session():

    # S3ResourceManager last seen records (rcvars)
    s3mgr.clear_session()

    # Session-owned records
    if "owned_records" in session:
        del session["owned_records"]

    if "s3" in session:
        opts = ["hrm", "report_options", "utc_offset"]
        for o in opts:
            if o in session.s3:
                del session.s3[o]

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
