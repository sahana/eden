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

    print >> sys.stdout, "Please be patient whilst the database is populated"

    # Shortcuts
    acl = auth.permission
    sysroles = auth.S3_SYSTEM_ROLES
    create_role = auth.s3_create_role
    #update_acls = auth.s3_update_acls

    # Do not remove or change order of these role definitions (System Roles):
    create_role("Administrator",
                "System Administrator - can access & make changes to any data",
                uid=sysroles.ADMIN,
                system=True,
                protected=True,
                )

    create_role("Authenticated",
                "Authenticated - all logged-in users",
                uid=sysroles.AUTHENTICATED,
                system=True,
                protected=True,
                )

    create_role("Anonymous",
                "Unauthenticated users",
                # Allow unauthenticated users to view the list of organisations
                # so they can select an organisation when registering
                dict(t="org_organisation", uacl=acl.READ),
                # Allow unauthenticated users to see the list of sites for an
                # org when registering
                dict(c="org", f="sites_for_org", uacl=acl.READ),
                uid=sysroles.ANONYMOUS,
                system=True,
                protected=True,
                )

    # Primarily for Security Policy 2
    create_role("Editor",
                "Editor - can access & make changes to any unprotected data",
                uid=sysroles.EDITOR,
                system=True,
                protected=True,
                )

    # MapAdmin
    map_admin = create_role("MapAdmin",
                            "MapAdmin - allowed access to edit the MapService Catalogue",
                            dict(c="gis", uacl=acl.ALL, oacl=acl.ALL),
                            dict(c="gis", f="location", uacl=acl.ALL, oacl=acl.ALL),
                            uid=sysroles.MAP_ADMIN,
                            system=True,
                            protected=True,
                            )

    # OrgAdmin (policies 6, 7 and 8)
    create_role("OrgAdmin",
                "OrgAdmin - allowed to manage user roles for organisation realms",
                uid=sysroles.ORG_ADMIN,
                system=True,
                protected=True,
                )

    # OrgGroupAdmin (policies 6, 7 and 8)
    create_role("OrgGroupAdmin",
                "OrgGroupAdmin - allowed to manage organisation group realms",
                uid=sysroles.ORG_GROUP_ADMIN,
                system=True,
                protected=True,
                )

    # Enable shortcuts (needed by default.py)
    system_roles = auth.get_system_roles()
    ADMIN = system_roles.ADMIN
    AUTHENTICATED = system_roles.AUTHENTICATED
    ANONYMOUS = system_roles.ANONYMOUS
    EDITOR = system_roles.EDITOR
    MAP_ADMIN = system_roles.MAP_ADMIN
    ORG_ADMIN = system_roles.ORG_ADMIN
    ORG_GROUP_ADMIN = system_roles.ORG_GROUP_ADMIN

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
        # Tweets every minute
        #s3task.schedule_task("msg_process_outbox",
        #                     vars={"contact_method":"TWITTER"},
        #                     period=120,  # seconds
        #                     timeout=120, # seconds
        #                     repeats=0    # unlimited
        #                     )

        # Subscription notifications
        s3task.schedule_task("notify_check_subscriptions",
                             period=300,
                             timeout=300,
                             repeats=0)

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
    # No location tree updates
    gis.disable_update_location_tree = True

    # Load all Models to ensure all DB tables present
    s3db.load_all_models()

    # Shortcuts
    path_join = os.path.join
    request_folder = request.folder

    if settings.get_auth_opt_in_to_email():
        table = db.pr_group
        for team in settings.get_auth_opt_in_team_list():
            table.insert(name = team, group_type = 5)

    # Synchronisation
    db.sync_config.insert() # Defaults are fine

    # Messaging Module
    if has_module("msg"):
        update_super = s3db.update_super
        # To read inbound email, set username (email address), password, etc.
        # here. Insert multiple records for multiple email sources.
        table = db.msg_email_channel
        id = table.insert(server = "imap.gmail.com",
                          protocol = "imap",
                          use_ssl = True,
                          port = 993,
                          username = "example-username",
                          password = "password",
                          delete_from_server = False
                          )
        update_super(table, dict(id=id))
        # Need entries for the Settings/1/Update URLs to work
        #table = db.msg_twitter_channel
        #id = table.insert(enabled = False, default=True)
        #update_super(table, dict(id=id))

    # Budget Module
    if has_module("budget"):
        db.budget_parameter.insert() # Defaults are fine

    # Climate Module
    if has_module("climate"):
        s3db.climate_first_run()

    # Incident Reporting System
    if has_module("irs"):
        # Categories visible to end-users by default
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
        db.supply_catalog.insert(name = settings.get_supply_catalog_default())

    # Ensure DB population committed when running through shell
    db.commit()

    # =========================================================================
    # PrePopulate import (from CSV)
    #

    # Create the bulk Importer object
    bi = s3base.S3BulkImporter()

    # Register handlers
    s3.import_feed = bi.import_feed
    s3.import_font = bi.import_font
    s3.import_image = bi.import_image
    s3.import_remote_csv = bi.import_remote_csv
    s3.import_role = bi.import_role
    s3.import_script = bi.import_script
    s3.import_user = bi.import_user
    s3.import_xml = bi.import_xml

    # Relax strict email-matching rule for import updates of person records
    email_required = settings.get_pr_import_update_requires_email()
    settings.pr.import_update_requires_email = False

    # Additional settings for user table imports:
    s3db.configure("auth_user",
                   onaccept = lambda form: auth.s3_approve_user(form.vars),
                   )
    # Now done in 00_tables.py
    #s3db.add_components("auth_user",
    #                    auth_membership="user_id",
    #                    )

    # Flag that Assets are being imported, not synced
    s3.asset_import = True

    # Allow population via shell scripts
    if not request.env.request_method:
        request.env.request_method = "GET"

    grandTotalStart = datetime.datetime.now()
    for pop_setting in pop_list:
        start = datetime.datetime.now()
        # Clear Tasklist
        bi.tasks = []
        # Import data specific to the prepopulate setting
        if pop_setting == 1:
            # Populate with the default data
            path = path_join(request_folder,
                             "modules",
                             "templates",
                             "default")
            bi.perform_tasks(path)
        else:
            path = path_join(request_folder,
                             "modules",
                             "templates",
                             pop_setting)
            if not os.path.exists(path):
                # Legacy template?
                path = path_join(request_folder,
                                 "private",
                                 "templates",
                                 pop_setting)
                if not os.path.exists(path):
                    print >> sys.stderr, "Unable to install data %s no valid directory found" % pop_setting
                    continue
            bi.perform_tasks(path)

        grandTotalEnd = datetime.datetime.now()
        duration = grandTotalEnd - grandTotalStart
        try:
            # Python 2.7
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

    # Restore setting for strict email-matching
    settings.pr.import_update_requires_email = email_required

    # Restore Auth
    auth.override = False
    # Enable location tree updates
    gis.disable_update_location_tree = False

    # Update Location Tree (disabled during prepop)
    start = datetime.datetime.now()
    gis.update_location_tree()
    end = datetime.datetime.now()
    print >> sys.stdout, "Location Tree update completed in %s" % (end - start)

    # Countries are only editable by MapAdmin
    db(db.gis_location.level == "L0").update(owned_by_group=map_admin)

    if has_module("disease"):
        # Populate disease_stats_aggregate (disabled during prepop)
        # - needs to be done after locations
        start = datetime.datetime.now()
        s3db.disease_stats_rebuild_all_aggregates()
        end = datetime.datetime.now()
        print >> sys.stdout, "Disease Statistics data aggregation completed in %s" % (end - start)

    if has_module("stats"):
        # Populate stats_demographic_aggregate (disabled during prepop)
        # - needs to be done after locations
        start = datetime.datetime.now()
        s3db.stats_demographic_rebuild_all_aggregates()
        end = datetime.datetime.now()
        print >> sys.stdout, "Demographic data aggregation completed in %s" % (end - start)

    if has_module("vulnerability"):
        # Populate vulnerability_aggregate (disabled during prepop)
        # - needs to be done after locations
        start = datetime.datetime.now()
        s3db.vulnerability_rebuild_all_aggregates()
        end = datetime.datetime.now()
        print >> sys.stdout, "Vulnerability data aggregation completed in %s" % (end - start)

    grandTotalEnd = datetime.datetime.now()
    duration = grandTotalEnd - grandTotalStart
    try:
        # Python 2.7
        duration = '{:.2f}'.format(duration.total_seconds()/60)
        print >> sys.stdout, "Pre-populate completed in %s mins" % duration
    except AttributeError:
        # older Python
        print >> sys.stdout, "Pre-populate completed in %s" % duration

    # =========================================================================
    # Indexes
    #

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
    # Add extra index on search field
    # Should work for our 3 supported databases: sqlite, MySQL & PostgreSQL
    tablename = "gis_location"
    field = "name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
    if settings.get_gis_spatialdb():
        # Add Spatial Index (PostgreSQL-only currently)
        db.executesql("CREATE INDEX gis_location_gist on %s USING GIST (the_geom);" % tablename)
        # Ensure the Planner takes this into consideration
        # Vacuum cannot run in a transaction block
        # autovacuum should be on anyway so will run ANALYZE after 50 rows inserted/updated/deleted
        #db.executesql("VACUUM ANALYZE;")

    # Restore view
    response.view = "default/index.html"

# END =========================================================================
