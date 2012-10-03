# -*- coding: utf-8 -*-

# 1st-run initialisation

# Set settings.base.prepopulate to 0 in Production
# (to save 1x DAL hit every page).
pop_list = settings.get_base_prepopulate()
if pop_list == 0:
    pop_list = []
else:
    table = db[auth.settings.table_group_name]
    # The query used here takes 2/3 the time of .count().
    if db(table.id > 0).select(table.id, limitby=(0, 1)).first():
        pop_list = []
    if not isinstance(pop_list, (list, tuple)):
        pop_list = [pop_list]

if len(pop_list) > 0:

    # =========================================================================
    # Populate default roles and permissions
    #

    # Allow debug
    import sys

    # Shortcuts
    acl = auth.permission
    sysroles = auth.S3_SYSTEM_ROLES
    create_role = auth.s3_create_role
    #update_acls = auth.s3_update_acls

    # Do not remove or change order of these 5 definitions (System Roles):
    create_role("Administrator",
                "System Administrator - can access & make changes to any data",
                uid=sysroles.ADMIN,
                system=True, protected=True)

    create_role("Authenticated",
                "Authenticated - all logged-in users",
                uid=sysroles.AUTHENTICATED,
                protected=True)

    create_role("Anonymous",
                "Unauthenticated users",
                # Allow unauthenticated users to view the list of organisations
                # so they can select an organisation when registering
                dict(t="org_organisation", uacl=acl.READ, entity="any"),
                uid=sysroles.ANONYMOUS,
                protected=True)

    # Primarily for Security Policy 2
    create_role("Editor",
                "Editor - can access & make changes to any unprotected data",
                uid=sysroles.EDITOR,
                system=True, protected=True)

    # MapAdmin
    map_admin = create_role("MapAdmin",
                            "MapAdmin - allowed access to edit the MapService Catalogue",
                            dict(c="gis", uacl=acl.ALL, oacl=acl.ALL),
                            dict(c="gis", f="location", uacl=acl.ALL, oacl=acl.ALL),
                            uid=sysroles.MAP_ADMIN,
                            system=True, protected=True)

    # OrgAdmin (policies 6, 7 and 8)
    create_role("OrgAdmin",
                "OrgAdmin - allowed to manage user roles for entity realms",
                uid=sysroles.ORG_ADMIN,
                system=True, protected=True)

    # Enable shortcuts (needed by default.py)
    system_roles = auth.get_system_roles()
    ADMIN = system_roles.ADMIN
    AUTHENTICATED = system_roles.AUTHENTICATED
    ANONYMOUS = system_roles.ANONYMOUS
    EDITOR = system_roles.EDITOR
    MAP_ADMIN = system_roles.MAP_ADMIN
    ORG_ADMIN = system_roles.ORG_ADMIN

    # =========================================================================
    # Configure Scheduled Tasks
    #

    has_module = settings.has_module
    if has_module("msg"):

        # Send Messages from Outbox
        # SMS every minute
        s3task.schedule_task("msg_process_outbox",
                             vars={"contact_method":"SMS"},
                             period=120,  # seconds
                             timeout=120, # seconds
                             repeats=0    # unlimited
                             )
        # Emails every 5 minutes
        s3task.schedule_task("msg_process_outbox",
                             vars={"contact_method":"EMAIL"},
                             period=300,  # seconds
                             timeout=300, # seconds
                             repeats=0    # unlimited
                             )
        # saved search notifications
        s3task.schedule_task("msg_search_subscription_notifications",
                             vars={"frequency":"hourly"},
                             period=3600,
                             timeout=300,
                             repeats=0
                             )
        s3task.schedule_task("msg_search_subscription_notifications",
                             vars={"frequency":"daily"},
                             period=86400,
                             timeout=300,
                             repeats=0
                             )
        s3task.schedule_task("msg_search_subscription_notifications",
                             vars={"frequency":"weekly"},
                             period=604800,
                             timeout=300,
                             repeats=0
                             )
        s3task.schedule_task("msg_search_subscription_notifications",
                             vars={"frequency":"monthly"},
                             period=2419200,
                             timeout=300,
                             repeats=0
                             )

    # Daily maintenance
    s3task.schedule_task("maintenance",
                         vars={"period":"daily"},
                         period=86400, # seconds, so 1/day
                         timeout=600,  # seconds
                         repeats=0     # unlimited
                         )

    # =========================================================================
    # Import PrePopulate data
    #

    # Override authorization
    auth.override = True

    # Load all Models to ensure all DB tables present
    s3db.load_all_models()

    if settings.get_auth_opt_in_to_email():
        table = db.pr_group
        for team in settings.get_auth_opt_in_team_list():
            table.insert(name = team, group_type = 5)

    # Synchronisation
    db.sync_config.insert() # Defaults are fine

    # Person Registry
    tablename = "pr_person"
    # Add extra indexes on search fields
    # Should work for our 3 supported databases: sqlite, MySQL & PostgreSQL
    field = "first_name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
    field = "middle_name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
    field = "last_name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))

    # GIS
    # L0 Countries
    resource = s3base.S3Resource("gis_location")
    stylesheet = os.path.join(request.folder, "static", "formats", "s3csv", "gis", "location.xsl")
    import_file = os.path.join(request.folder, "private", "templates", "locations", "countries.csv")
    File = open(import_file, "r")
    resource.import_xml(File, format="csv", stylesheet=stylesheet)
    db(db.gis_location.level == "L0").update(owned_by_group=map_admin)
    db.commit()
    # Add extra index on search field
    # Should work for our 3 supported databases: sqlite, MySQL & PostgreSQL
    tablename = "gis_location"
    field = "name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))

    # Messaging Module
    if has_module("msg"):
        # To read inbound email, set username (email address), password, etc.
        # here. Insert multiple records for multiple email sources.
        db.msg_inbound_email_settings.insert(server = "imap.gmail.com",
                                             protocol = "imap",
                                             use_ssl = True,
                                             port = 993,
                                             username = "example-username",
                                             password = "password",
                                             delete_from_server = False
                                             )
        # Need entries for the Settings/1/Update URLs to work
        db.msg_setting.insert( outgoing_sms_handler = "WEB_API" )
        db.msg_modem_settings.insert( modem_baud = 115200 )
        db.msg_api_settings.insert( to_variable = "to" )
        db.msg_smtp_to_sms_settings.insert( address="changeme" )
        db.msg_tropo_settings.insert( token_messaging = "" )
        db.msg_twitter_settings.insert( pin = "" )

    # Budget Module
    if has_module("budget"):
        db.budget_parameter.insert() # Defaults are fine

    # Climate Module
    if has_module("climate"):
        s3db.climate_first_run()

    # CAP module
    if has_module("cap"):
        s3db.cap_first_run()

    # Incident Reporting System
    if has_module("irs"):
        # Categories visible to ends-users by default
        table = db.irs_icategory
        table.insert(code = "flood")
        table.insert(code = "geophysical.landslide")
        table.insert(code = "roadway.bridgeClosure")
        table.insert(code = "roadway.roadwayClosure")
        table.insert(code = "other.buildingCollapsed")
        table.insert(code = "other.peopleTrapped")
        table.insert(code = "other.powerFailure")

    # Supply Module
    if has_module("supply"):
        db.supply_catalog.insert(name = settings.get_supply_catalog_default() )

    # Ensure DB population committed when running through shell
    db.commit()

    # =========================================================================
    # PrePopulate import (from CSV)
    #

    # Create the bulk Importer object
    bi = s3base.S3BulkImporter()

    s3.import_role = bi.import_role

    # Disable table protection
    protected = s3mgr.PROTECTED
    s3mgr.PROTECTED = []

    # Additional settings for user table imports:
    s3db.configure("auth_user",
                   onaccept = lambda form: auth.s3_approve_user(form.vars))
    s3db.add_component("auth_membership", auth_user="user_id")

    # Allow population via shell scripts
    if not request.env.request_method:
        request.env.request_method = "GET"

    _debug = settings.get_base_debug()

    grandTotalStart = datetime.datetime.now()
    for pop_setting in pop_list:
        start = datetime.datetime.now()
        bi.clear_tasks()
        # Import data specific to the prepopulate setting
        if isinstance(pop_setting, str):
            path = os.path.join(request.folder,
                                "private",
                                "templates",
                                pop_setting)
            if os.path.exists(path):
                bi.perform_tasks(path)
            else:
                print >> sys.stderr, "Unable to install data %s no valid directory found" % pop_setting
        elif pop_setting == 1:
            # Populate with the default data
            path = os.path.join(request.folder,
                                "private",
                                "templates",
                                "default")
            bi.perform_tasks(path)

        elif pop_setting == 2:
            # Populate data for the regression tests
            path = os.path.join(request.folder,
                                "private",
                                "templates",
                                "regression")
            bi.perform_tasks(path)
            print >> sys.stdout, "Installed Regression Test Data"

        elif pop_setting == 3:
            # Populate data for scalability testing
            # This is different from the repeatable imports that use csv files
            # This will generate millions of records of data for selected tables.

            # Code needs to go here to generate a large volume of test data
            pass

        elif pop_setting == 4:
            # Populate data for the user roles
            path = os.path.join(request.folder,
                                "private",
                                "templates",
                                "roles")
            bi.perform_tasks(path)
            end = datetime.datetime.now()
            duration = end - start
            print >> sys.stdout, "Installed Authorisation Roles completed in %s" % \
                                    (duration)

        elif pop_setting == 10:
            # Populate data for user specific data
            path = os.path.join(request.folder,
                                "private",
                                "templates",
                                "user")
            bi.perform_tasks(path)
            end = datetime.datetime.now()
            duration = end - start
            print >> sys.stdout, "Installed Private User Data completed in %s" % \
                                    (duration)

        elif pop_setting >= 20:
            # Populate data for a template
            # Read the folders.cfg file and extract the folder for the specific template
            file = os.path.join(request.folder,
                                "private",
                                "templates",
                                "folders.cfg")
            source = open(file, "r")
            values = source.readlines()
            source.close()
            template = ""
            for templates in values:
                # strip out the new line
                templates = templates.strip()
                if templates == "":
                    continue
                # split at the comma
                details = templates.split(",")
                if len(details) == 2:
                     # remove any spaces and enclosing double quote
                    index = details[0].strip('" ')
                    if int(index) == pop_setting:
                        directory = details[1].strip('" ')
                        path = os.path.join(request.folder,
                                            "private",
                                            "templates",
                                            directory)
                        template = directory
                        if os.path.exists(path):
                            bi.perform_tasks(path)
                        else:
                            print >> sys.stderr, "Unable to install template %s no template directory found" \
                                                    % index
            if template == "":
                print >> sys.stderr, "Unable to install a template with of an id '%s', please check 000_config and folders.cfg" \
                                        % pop_setting
            else:
                end = datetime.datetime.now()
                duration = end - start
                try:
                    # Python-2.7
                    duration = '{:.2f}'.format(duration.total_seconds()/60)
                    print >> sys.stdout, "Installed template '%s' completed in %s mins" % \
                                            (template, duration)
                except AttributeError:
                    # older Python
                    print >> sys.stdout, "Installed template '%s' completed in %s" % \
                                            (template, duration)
        grandTotalEnd = datetime.datetime.now()
        duration = grandTotalEnd - grandTotalStart
        try:
            # Python-2.7
            duration = '{:.2f}'.format(duration.total_seconds()/60)
            print >> sys.stdout, "Pre-populate task completed in %s mins" % duration
        except AttributeError:
            # older Python
            print >> sys.stdout, "Pre-populate task completed in %s" % duration
        bi.resultList = []
    for errorLine in bi.errorList:
        try:
            print >> sys.stderr, errorLine
        except:
            s3_unicode = s3base.s3_unicode
            _errorLine = ""
            for i in range(0, len(errorLine)):
                try:
                    _errorLine += s3_unicode(errorline[i])
                except:
                    pass
            print >> sys.stderr, _errorLine

    # Restore table protection
    s3mgr.PROTECTED = protected

    # Restore Auth
    auth.override = False

    # Update Location Tree (disabled during prepop)
    start = datetime.datetime.now()
    gis.update_location_tree()
    end = datetime.datetime.now()
    print >> sys.stdout, "Location Tree update completed in %s" % (end - start)

    # Update stats_aggregate (disabled during prepop)
    # - needs to be done after locations
    if has_module("stats"):
        start = datetime.datetime.now()
        s3db.stats_rebuild_aggregates()
        end = datetime.datetime.now()
        print >> sys.stdout, "Statistics data aggregation completed in %s" % (end - start)

    grandTotalEnd = datetime.datetime.now()
    duration = grandTotalEnd - grandTotalStart
    try:
        # Python-2.7
        duration = '{:.2f}'.format(duration.total_seconds()/60)
        print >> sys.stdout, "Pre-populate completed in %s mins" % duration
    except AttributeError:
        # older Python
        print >> sys.stdout, "Pre-populate completed in %s" % duration

    # Restore view
    response.view = "default/index.html"

# END =========================================================================
