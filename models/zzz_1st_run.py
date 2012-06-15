# -*- coding: utf-8 -*-

# 1st-run initialisation
# designed to be called from Crontab's @reboot
# however this isn't reliable (doesn't work on Win32 Service) so still in models for now...

# Deployments can change settings live via appadmin
if len(pop_list) > 0:

    # Allow debug
    import sys

    # Load all Models to ensure all DB tables present
    s3db.load_all_models()

    # Add core data as long as at least one populate setting is on

    if deployment_settings.get_auth_opt_in_to_email():
        table = db.pr_group
        for team in deployment_settings.get_auth_opt_in_team_list():
            table.insert(name = team, group_type = 5)

    # Scheduled Tasks
    if deployment_settings.has_module("msg"):
        
        #Message Parsing Tasks for each enabled workflows 
        #for workflow in deployment_settings.get_parser_enabled():
            #workflow = int(workflow.split("_")[1])
            #s3task.schedule_task("parse_workflow",
                                 #vars={"workflow": workflow},
                                 #period=300,  # seconds
                                 #timeout=300, # seconds
                                 #repeats=0    # unlimited
                                 #)
                        
                        
                
                
        # Send Messages from Outbox
        # SMS every minute
        s3task.schedule_task("process_outbox",
                             vars={"contact_method":"SMS"},
                             period=120,  # seconds
                             timeout=120, # seconds
                             repeats=0    # unlimited
                            )
        # Emails every 5 minutes
        s3task.schedule_task("process_outbox",
                             vars={"contact_method":"EMAIL"},
                             period=300,  # seconds
                             timeout=300, # seconds
                             repeats=0    # unlimited
                            )
        # Inbound email
        # To schedule reading inbound email, uncomment and substitute the
        # username from the task definition for example-username. This example
        # shows reading email every 15 minutes. Add one task for each email
        # source.
        #s3task.schedule_task("process_inbound_email",
        #                     vars={"username":"example-username"},
        #                     period=900,  # seconds
        #                     timeout=300, # seconds
        #                     repeats=0    # unlimited
        #                    )

        
    # Person Registry
    tablename = "pr_person"
    table = db[tablename]
    # Should work for our 3 supported databases: sqlite, MySQL & PostgreSQL
    field = "first_name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
    field = "middle_name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
    field = "last_name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))

    # Synchronisation
    table = db.sync_config
    if not db(table.id > 0).select(table.id, limitby=(0, 1)).first():
       table.insert()

    # Incident Reporting System
    if deployment_settings.has_module("irs"):
        # Categories visible to ends-users by default
        table = db.irs_icategory
        if not db(table.id > 0).select(table.id, limitby=(0, 1)).first():
            table.insert(code = "flood")
            table.insert(code = "geophysical.landslide")
            table.insert(code = "roadway.bridgeClosure")
            table.insert(code = "roadway.roadwayClosure")
            table.insert(code = "other.buildingCollapsed")
            table.insert(code = "other.peopleTrapped")
            table.insert(code = "other.powerFailure")

    # Messaging Module
    if deployment_settings.has_module("msg"):
        # To read inbound email, set username (email address), password, etc.
        # here. Insert multiple records for multiple email sources.
        table = db.msg_inbound_email_settings
        if not db(table.id > 0).select(table.id, limitby=(0, 1)).first():
            table.insert(server = "imap.gmail.com",
                         protocol = "imap",
                         use_ssl = True,
                         port = 993,
                         username = "example-username",
                         password = "password",
                         delete_from_server = False
            )
        # Need entries for the Settings/1/Update URLs to work
        table = db.msg_setting
        if not db(table.id > 0).select(table.id, limitby=(0, 1)).first():
            table.insert( outgoing_sms_handler = "WEB_API" )
        table = db.msg_modem_settings
        if not db(table.id > 0).select(table.id, limitby=(0, 1)).first():
            table.insert( modem_baud = 115200 )
        table = db.msg_api_settings
        if not db(table.id > 0).select(table.id, limitby=(0, 1)).first():
            table.insert( to_variable = "to" )
        table = db.msg_smtp_to_sms_settings
        if not db(table.id > 0).select(table.id, limitby=(0, 1)).first():
            table.insert( address="changeme" )
        table = db.msg_tropo_settings
        if not db(table.id > 0).select(table.id, limitby=(0, 1)).first():
            table.insert( token_messaging = "" )
        table = db.msg_twitter_settings
        if not db(table.id > 0).select(table.id, limitby=(0, 1)).first():
            table.insert( pin = "" )

    # Budget Module
    if deployment_settings.has_module("budget"):
        table = db.budget_parameter
        if not db(table.id > 0).select(table.id, limitby=(0, 1)).first():
            table.insert() # Only defaults are fine

    # GIS Locations
    tablename = "gis_location"
    table = db[tablename]
    if not db(table.id > 0).select(table.id, limitby=(0, 1)).first():
        # L0 Countries
        import_file = os.path.join(request.folder,
                                   "private",
                                   "templates",
                                   "default",
                                   "countries.csv")
        table.import_from_csv_file(open(import_file, "r")) #, id_map=True)
        query = (db.auth_group.uuid == sysroles.MAP_ADMIN)
        map_admin = db(query).select(db.auth_group.id,
                                     limitby=(0, 1)).first().id
        db(table.level == "L0").update(owned_by_group=map_admin)
    # Should work for our 3 supported databases: sqlite, MySQL & PostgreSQL
    field = "name"
    db.executesql("CREATE INDEX %s__idx on %s(%s);" % \
        (field, tablename, field))

    # Supply Module
    if deployment_settings.has_module("supply"):
        tablename = "supply_catalog"
        table = db[tablename]
        if not db(table.id > 0).select(table.id, limitby=(0, 1)).first():
            table.insert(name = deployment_settings.get_supply_catalog_default() )

    # Climate module
    if deployment_settings.has_module("climate"):
        climate_first_run()

    # Ensure DB population committed when running through shell
    db.commit()

    # -------------------------------------------------------------------------
    # Prepopulate import (from CSV)

    # Override authorization
    auth.override = True

    # Disable table protection
    protected = s3mgr.PROTECTED
    s3mgr.PROTECTED = []

    # Additional settings for user table imports:
    s3mgr.configure("auth_user",
                    onaccept = lambda form: \
                        auth.s3_link_to_person(user=form.vars))
    s3mgr.model.add_component("auth_membership", auth_user="user_id")

    # Allow population via shell scripts
    if not request.env.request_method:
        request.env.request_method = "GET"

    _debug = deployment_settings.get_base_debug()

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
            print >> sys.stdout, "Pre-populate completed in %s mins" % duration
        except AttributeError:
            # older Python
            print >> sys.stdout, "Pre-populate completed in %s" % duration
        bi.resultList = []

    grandTotalEnd = datetime.datetime.now()
    duration = grandTotalEnd - grandTotalStart
    print >> sys.stdout, "Pre-populate completed in %s" % (duration)
    for errorLine in bi.errorList:
        print >> sys.stderr, errorLine
    # Restore table protection
    s3mgr.PROTECTED = protected

    # Restore Auth
    auth.override = False

    # Restore view
    response.view = "default/index.html"
