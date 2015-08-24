# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Template settings for CAP: Common Alerting Protocol
    """

    T = current.T

    settings.base.system_name = T("Sahana Alerting and Messaging Broker")
    settings.base.system_name_short = T("SAMBRO")

    # Pre-Populate
    settings.base.prepopulate = ("SAMBRO", "SAMBRO/Demo", "default/users")

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "SAMBRO"

    # The Registration functionality shouldn't be visible to the Public
    settings.security.registration_visible = False

    # GeoNames username
    settings.gis.geonames_username = "eden_test"

    # =========================================================================
    # System Settings
    # -------------------------------------------------------------------------
    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations    
    settings.security.policy = 4 # Controller-Function ACLs
    
    # Record Approval
    settings.auth.record_approval = True
    # cap_alert record requires approval before sending
    settings.auth.record_approval_required_for = ("cap_alert",)

    # =============================================================================
    # Module Settings
    # -----------------------------------------------------------------------------
    # Notifications
    
    # Template for the subject line in update notifications
    settings.msg.notify_subject = "$S %s" % T("Alert Notification")

    # -----------------------------------------------------------------------------
    # L10n (Localization) settings
    languages = OrderedDict([
        #("ar", "العربية"),
        ("dv", "ދިވެހި"), # Divehi (Maldives)
        ("en-US", "English"),
        #("es", "Español"),
        #("fr", "Français"),
        #("km", "ភាសាខ្មែរ"),        # Khmer
        #("mn", "Монгол хэл"),  # Mongolian
        ("my", "မြန်မာစာ"),        # Burmese
        #("ne", "नेपाली"),          # Nepali
        #("prs", "دری"),        # Dari
        #("ps", "پښتو"),        # Pashto
        #("tet", "Tetum"),
        #("th", "ภาษาไทย"),        # Thai
        ("tl", "Tagalog"), # Filipino
        #("vi", "Tiếng Việt"),   # Vietnamese
        #("zh-cn", "中文 (简体)"),
    ])
    settings.L10n.languages = languages
    settings.cap.languages = languages
    # Translate the cap_area name
    settings.L10n.translate_cap_area = True
    
    # -------------------------------------------------------------------------
    # Messaging
    # Parser
    settings.msg.parser = "SAMBRO"

    # -------------------------------------------------------------------------
    def customise_msg_rss_channel_resource(r, tablename):

        # @ToDo: We won't be able to automate this as we have 2 sorts, so will need the user to select manually
        # Can we add a component for the parser for S3CSV imports?

        # UX: separate menu items distinguished via get_var
        # @ToDo: Add menu entries for "Create RSS Feed for CAP" & "Create RSS Feed for CMS"
        type = current.request.get_vars.get("type", None)
        if type == "cap":
            fn = "parse_rss_2_cap"
        else:
            fn = "parse_rss_2_cms"

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
            _id = table.insert(channel_id=channel_id, function_name=fn, enabled=True)
            s3db.msg_parser_enable(_id)

            async = current.s3task.async
            # Poll
            async("msg_poll", args=["msg_rss_channel", channel_id])

            # Parse
            async("msg_parse", args=[channel_id, fn])

        s3db.configure(tablename,
                       create_onaccept = onaccept,
                       )

    settings.customise_msg_rss_channel_resource = customise_msg_rss_channel_resource

    # -------------------------------------------------------------------------
    def customise_msg_twitter_channel_resource(r, tablename):

        s3db = current.s3db
        def onaccept(form):
            # Normal onaccept
            s3db.msg_channel_onaccept(form)
            _id = form.vars.id
            db = current.db
            table = db.msg_twitter_channel
            channel_id = db(table.id == _id).select(table.channel_id,
                                                    limitby=(0, 1)).first().channel_id
            # Link to Parser
            table = s3db.msg_parser
            _id = table.insert(channel_id=channel_id, function_name="parse_tweet", enabled=True)
            s3db.msg_parser_enable(_id)

            async = current.s3task.async
            # Poll
            async("msg_poll", args=["msg_twitter_channel", channel_id])

            # Parse
            async("msg_parse", args=[channel_id, "parse_tweet"])

        s3db.configure(tablename,
                       create_onaccept = onaccept,
                       )

    settings.customise_msg_twitter_channel_resource = customise_msg_twitter_channel_resource

    # -------------------------------------------------------------------------
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
            name_nice = T("Mapping"),
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
            name_nice = T("Alerting"),
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
        ("event", Storage(
            name_nice = T("Events"),
            #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
            restricted = True,
            module_type = 10,
        )),
    ])

# END =========================================================================
