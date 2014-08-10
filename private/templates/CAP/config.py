# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.storage import Storage

T = current.T
settings = current.deployment_settings

"""
    Template settings

    All settings which are to configure a specific template are located here

    Deployers should ideally not need to edit any other files outside of their template folder
"""

# Pre-Populate
settings.base.prepopulate = ["CAP", "demo/users"]

# Theme (folder to use for views/layout.html)
#settings.base.theme = "default"

# GeoNames username
settings.gis.geonames_username = "eden_test"

# -----------------------------------------------------------------------------
# Messaging
# Parser
settings.msg.parser = "CAP"

def customise_msg_rss_channel_resource(r, tablename):
    s3db = current.s3db
    def onaccept(form):
        # Normal onaccept
        s3db.msg_channel_onaccept(form)
        _id = form.vars.id
        db = current.db
        table = db.msg_rss_channel
        channel_id = db(table.id == _id).select(table.channel_id,
                                                limitby=(0, 1)).first().channel_id
        # Link to Parser
        table = s3db.msg_parser
        _id = table.insert(channel_id=channel_id, function_name="parse_rss", enabled=True)
        s3db.msg_parser_enable(_id)

        async = current.s3task.async
        # Poll
        async("msg_poll", args=["msg_rss_channel", channel_id])

        # Parse
        async("msg_parse", args=[channel_id, "parse_rss"])

    s3db.configure(tablename,
                   create_onaccept = onaccept,
                   )

settings.customise_msg_rss_channel_resource = customise_msg_rss_channel_resource

# Comment/uncomment modules here to disable/enable them
# @ToDo: Have the system automatically enable migrate if a module is enabled
# Modules menu is defined in modules/eden/menu.py
settings.modules = OrderedDict([
    # Core modules which shouldn't be disabled
    ("default", Storage(
        name_nice = T("Home"),
        restricted = False, # Use ACLs to control access to this module
        access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
        module_type = None  # This item is not shown in the menu
    )),
    ("admin", Storage(
        name_nice = T("Administration"),
        #description = "Site Administration",
        restricted = True,
        access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        module_type = None  # This item is handled separately for the menu
    )),
    ("appadmin", Storage(
        name_nice = T("Administration"),
        #description = "Site Administration",
        restricted = True,
        module_type = None  # No Menu
    )),
    ("errors", Storage(
        name_nice = T("Ticket Viewer"),
        #description = "Needed for Breadcrumbs",
        restricted = False,
        module_type = None  # No Menu
    )),
    ("sync", Storage(
        name_nice = T("Synchronization"),
        #description = "Synchronization",
        restricted = True,
        access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        module_type = None  # This item is handled separately for the menu
    )),
    #("tour", Storage(
    #    name_nice = T("Guided Tour Functionality"),
    #    module_type = None,
    #)),
    ("translate", Storage(
        name_nice = T("Translation Functionality"),
        #description = "Selective translation of strings based on module.",
        module_type = None,
    )),
    ("gis", Storage(
        name_nice = T("Map"),
        #description = "Situation Awareness & Geospatial Analysis",
        restricted = True,
        module_type = 6,     # 6th item in the menu
    )),
    ("pr", Storage(
        name_nice = T("Person Registry"),
        #description = "Central point to record details on People",
        restricted = True,
        access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
        module_type = 10
    )),
    ("org", Storage(
        name_nice = T("Organizations"),
        #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
        restricted = True,
        module_type = 10
    )),
    # All modules below here should be possible to disable safely
    #("hrm", Storage(
    #    name_nice = T("Staff"),
    #    #description = "Human Resources Management",
    #    restricted = True,
    #    module_type = 2,
    #)),
    ("cap", Storage(
        name_nice = T("CAP"),
        #description = "Create & broadcast CAP alerts",
        restricted = True,
        module_type = 1,
    )),
    ("cms", Storage(
      name_nice = T("Content Management"),
      #description = "Content Management System",
      restricted = True,
      module_type = 10,
    )),
    ("doc", Storage(
        name_nice = T("Documents"),
        #description = "A library of digital resources, such as photos, documents and reports",
        restricted = True,
        module_type = 10,
    )),
    ("msg", Storage(
        name_nice = T("Messaging"),
        #description = "Sends & Receives Alerts via Email & SMS",
        restricted = True,
        # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
        module_type = None,
    )),
    ("irs", Storage(
        name_nice = T("Incidents"),
        #description = "Incident Reporting System",
        restricted = True,
        module_type = 10
    )),
    ("event", Storage(
        name_nice = T("Events"),
        #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        restricted = True,
        module_type = 10,
    )),
])
