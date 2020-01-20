# -*- coding: utf-8 -*-

# =============================================================================
# Tasks to be callable async &/or on a Schedule
# @ToDo: Rewrite a lot of these to use s3db_task or settings_task instead of
#        having a lot of separate tasks defined here
# =============================================================================

has_module = settings.has_module

# -----------------------------------------------------------------------------
def dummy():
    """
        Dummy Task
        - can be used to populate a table with a task_id
    """
    return

# -----------------------------------------------------------------------------
def s3db_task(function, user_id=None, **kwargs):
    """
        Generic Task
        - can be used to call any s3db.function(**kwargs)
        - saves having to create separate Tasks for many cases
    """
    if user_id:
        # Authenticate
        auth.s3_impersonate(user_id)
    # Run the Task & return the result
    result = s3db[function](**kwargs)
    db.commit()
    return result

# -----------------------------------------------------------------------------
def settings_task(taskname, user_id=None, **kwargs):
    """
        Generic Task
        - can be used to call any settings.tasks.taskname(**kwargs)
        - saves having to create separate Tasks for many cases
    """
    if user_id:
        # Authenticate
        auth.s3_impersonate(user_id)
    task = settings.get_task(taskname)
    if task:
        # Run the Task & return the result
        result = task(**kwargs)
        db.commit()
        return result

# -----------------------------------------------------------------------------
def maintenance(period = "daily"):
    """
        Run all maintenance tasks which should be done daily
        - these are read from the template
    """

    maintenance = None
    result = "NotImplementedError"

    templates = settings.get_template()
    if templates != "default":
        # Try to import maintenance routine from template
        if not isinstance(templates, (tuple, list)):
            templates = (templates,)
        for template in templates[::-1]:
            package = "applications.%s.modules.templates.%s" % (appname, template)
            name = "maintenance"
            try:
                maintenance = getattr(__import__(package, fromlist=[name]), name)
            except (ImportError, AttributeError):
                pass
            else:
                break
    if maintenance is None:
        try:
            # Fallback to default maintenance routine
            from templates.default import maintenance
        except ImportError:
            pass
    if maintenance is not None:
        if period == "daily":
            result = maintenance.Daily()()
        db.commit()

    return result

# -----------------------------------------------------------------------------
# GIS: always-enabled
# -----------------------------------------------------------------------------
def gis_download_kml(record_id, filename, session_id_name, session_id,
                     user_id=None):
    """
        Download a KML file
            - will normally be done Asynchronously if there is a worker alive

        @param record_id: id of the record in db.gis_layer_kml
        @param filename: name to save the file as
        @param session_id_name: name of the session
        @param session_id: id of the session
        @param user_id: calling request's auth.user.id or None
    """
    if user_id:
        # Authenticate
        auth.s3_impersonate(user_id)
    # Run the Task & return the result
    result = gis.download_kml(record_id, filename, session_id_name, session_id)
    db.commit()
    return result

# -----------------------------------------------------------------------------
def gis_update_location_tree(feature, user_id=None):
    """
        Update the Location Tree for a feature
            - will normally be done Asynchronously if there is a worker alive

        @param feature: the feature (in JSON format)
        @param user_id: calling request's auth.user.id or None
    """
    if user_id:
        # Authenticate
        auth.s3_impersonate(user_id)
    # Run the Task & return the result
    feature = json.loads(feature)
    path = gis.update_location_tree(feature)
    db.commit()
    return path

# -----------------------------------------------------------------------------
# Org: always-enabled
# -----------------------------------------------------------------------------
def org_site_check(site_id, user_id=None):
    """ Check the Status for Sites """

    if user_id:
        # Authenticate
        auth.s3_impersonate(user_id)

    # Check for Template-specific processing
    customise = settings.get_org_site_check()
    if customise:
        customise(site_id)
        db.commit()

# -----------------------------------------------------------------------------
tasks = {"dummy": dummy,
         "s3db_task": s3db_task,
         "settings_task": settings_task,
         "maintenance": maintenance,
         "gis_download_kml": gis_download_kml,
         "gis_update_location_tree": gis_update_location_tree,
         "org_site_check": org_site_check,
         }

# -----------------------------------------------------------------------------
# Optional Modules
# -----------------------------------------------------------------------------
if has_module("cap"):

    # -------------------------------------------------------------------------
    def cap_ftp_sync(user_id=None):
        """ Get all the FTP repositories and synchronize them """

        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)

        rows = db(s3db.sync_repository.apitype == "ftp").select()

        if rows:
            sync = current.sync
            for row in rows:
                sync.synchronize(row)

    tasks["cap_ftp_sync"] = cap_ftp_sync

# -----------------------------------------------------------------------------
if has_module("doc"):

    # -----------------------------------------------------------------------------
    def document_create_index(document, user_id=None):

        import os
        from xlrd import open_workbook
        from pyth.plugins.rtf15.reader import Rtf15Reader
        from pyth.plugins.plaintext.writer import PlaintextWriter
        import sunburnt

        document = json.loads(document)
        table = s3db.doc_document
        id = document["id"]

        name = document["name"]
        filename = document["filename"]

        filename = "%s/%s/uploads/%s" % (os.path.abspath("applications"), \
                                        request.application, filename)

        si = sunburnt.SolrInterface(settings.get_base_solr_url())

        extension = os.path.splitext(filename)[1][1:]

        if extension == "pdf":
            data = os.popen("pdf2txt.py " + filename).read()
        elif extension == "doc":
            data = os.popen("antiword " + filename).read()
        elif extension == "xls":
            wb = open_workbook(filename)
            data=" "
            for s in wb.sheets():
                for row in range(s.nrows):
                    values = []
                    for col in range(s.ncols):
                        values.append(str(s.cell(row, col).value))
                    data = data + ",".join(values) + "\n"
        elif extension == "rtf":
            doct = Rtf15Reader.read(open(filename))
            data = PlaintextWriter.write(doct).getvalue()
        else:
            data = os.popen("strings " + filename).read()

        # The text needs to be in unicode or ascii, with no contol characters
        data = str(unicode(data, errors="ignore"))
        data = "".join(c if ord(c) >= 32 else " " for c in data)

        # Put the data according to the Multiple Fields
        # @ToDo: Also, would change this according to requirement of Eden
        document = {"id": str(id), # doc_document.id
                    "name": data, # the data of the file
                    "url": filename, # the encoded file name stored in uploads/
                    "filename": name, # the filename actually uploaded by the user
                    "filetype": extension  # x.pdf -> pdf is the extension of the file
                    }

        # Add and commit Indices
        si.add(document)
        si.commit()
        # After Indexing, set the value for has_been_indexed to True in the database
        db(table.id == id).update(has_been_indexed = True)

        db.commit()

    tasks["document_create_index"] = document_create_index

    # -----------------------------------------------------------------------------
    def document_delete_index(document, user_id=None):

        import sunburnt

        document = json.loads(document)
        table = s3db.doc_document
        id = document["id"]
        filename = document["filename"]

        si = sunburnt.SolrInterface(settings.get_base_solr_url())

        # Delete and Commit the indicies of the deleted document
        si.delete(id)
        si.commit()
        # After removing the index, set has_been_indexed value to False in the database
        db(table.id == id).update(has_been_indexed = False)

        db.commit()

    tasks["document_delete_index"] = document_delete_index

# -----------------------------------------------------------------------------
if has_module("msg"):

    # -------------------------------------------------------------------------
    def msg_process_outbox(contact_method, user_id=None):
        """
            Process Outbox
            - will normally be done Asynchronously if there is a worker alive

            @param contact_method: one from s3msg.MSG_CONTACT_OPTS
            @param user_id: calling request's auth.user.id or None
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)

        # Run the Task & return the result
        result = msg.process_outbox(contact_method)
        db.commit()
        return result

    tasks["msg_process_outbox"] = msg_process_outbox

    # -------------------------------------------------------------------------
    def msg_twitter_search(search_id, user_id=None):
        """
            Perform a Search of Twitter
            - will normally be done Asynchronously if there is a worker alive

            @param search_id: one of s3db.msg_twitter_search.id
            @param user_id: calling request's auth.user.id or None

        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)

        # Run the Task & return the result
        result = msg.twitter_search(search_id)
        db.commit()
        return result

    tasks["msg_twitter_search"] = msg_twitter_search

    # -------------------------------------------------------------------------
    def msg_process_keygraph(search_id, user_id=None):
        """
            Process Twitter Search Results with KeyGraph
            - will normally be done Asynchronously if there is a worker alive

            @param search_id: one of s3db.msg_twitter_search.id
            @param user_id: calling request's auth.user.id or None
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)

        # Run the Task & return the result
        result = msg.process_keygraph(search_id)
        db.commit()
        return result

    tasks["msg_process_keygraph"] = msg_process_keygraph

    # -------------------------------------------------------------------------
    def msg_poll(tablename, channel_id, user_id=None):
        """
            Poll an inbound channel
        """
        if user_id:
            auth.s3_impersonate(user_id)

        # Run the Task & return the result
        result = msg.poll(tablename, channel_id)
        db.commit()
        return result

    tasks["msg_poll"] = msg_poll

    # -----------------------------------------------------------------------------
    def msg_parse(channel_id, function_name, user_id=None):
        """
            Parse Messages coming in from a Source Channel
        """
        if user_id:
            auth.s3_impersonate(user_id)

        # Run the Task & return the result
        result = msg.parse(channel_id, function_name)
        db.commit()
        return result

    tasks["msg_parse"] = msg_parse

    # -------------------------------------------------------------------------
    def msg_gcm(title, uri, message, registration_ids, user_id=None):
        """ Push the data relating to google cloud messaging server """

        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)

        msg.gcm_push(title, uri, message, eval(registration_ids))

    tasks["msg_gcm"] = msg_gcm

    # -------------------------------------------------------------------------
    def notify_check_subscriptions(user_id=None):
        """
            Scheduled task to check subscriptions for updates,
            creates notify_notify tasks where updates exist.
        """
        if user_id:
            auth.s3_impersonate(user_id)

        result = s3base.S3Notifications().check_subscriptions()
        db.commit()
        return result

    tasks["notify_check_subscriptions"] = notify_check_subscriptions

    # -------------------------------------------------------------------------
    def notify_notify(resource_id, user_id=None):
        """
            Asynchronous task to notify a subscriber about resource
            updates. This task is created by notify_check_subscriptions.

            @param resource_id: the pr_subscription_resource record ID
        """
        if user_id:
            auth.s3_impersonate(user_id)

        notify = s3base.S3Notifications
        return notify.notify(resource_id)

    tasks["notify_notify"] = notify_notify

# -----------------------------------------------------------------------------
if has_module("req"):

    def req_add_from_template(req_id, user_id=None):
        """
            Add a Request from template
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)

        # Run the Task & return the result
        result = s3db.req_add_from_template(req_id)
        db.commit()
        return result

    tasks["req_add_from_template"] = req_add_from_template

# -----------------------------------------------------------------------------
if has_module("setup"):

    def setup_run_playbook(playbook,
                           tags = None,
                           hosts = None,
                           user_id = None,
                           ):
        """
            Run an Ansible Playbook
            - to Deploy a new Eden instance
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)

        # Run the Task & return the result
        result = s3db.setup_run_playbook(playbook, tags, hosts)
        #db.commit()
        return result

    tasks["setup_run_playbook"] = setup_run_playbook

    # -------------------------------------------------------------------------
    def setup_monitor_run_task(task_id, user_id=None):
        """
            Run a Monitoring Task
        """
        if user_id:
            auth.s3_impersonate(user_id)
        # Run the Task & return the result
        result = s3db.setup_monitor_run_task(task_id)
        db.commit()
        return result

    tasks["setup_monitor_run_task"] = setup_monitor_run_task

    # -------------------------------------------------------------------------
    def setup_monitor_check_email_reply(run_id, user_id=None):
        """
            Check whether we have received a reply to an Email check
        """
        if user_id:
            auth.s3_impersonate(user_id)
        # Run the Task & return the result
        result = s3db.setup_monitor_check_email_reply(run_id)
        db.commit()
        return result

    tasks["setup_monitor_check_email_reply"] = setup_monitor_check_email_reply


# -----------------------------------------------------------------------------
if has_module("stats"):

    def stats_demographic_update_aggregates(records = None,
                                            user_id = None,
                                            ):
        """
            Update the stats_demographic_aggregate table for the given
            stats_demographic_data record(s)

            @param records: JSON of Rows of stats_demographic_data records to
                            update aggregates for
            @param user_id: calling request's auth.user.id or None
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)

        # Run the Task & return the result
        result = s3db.stats_demographic_update_aggregates(records)
        db.commit()
        return result

    tasks["stats_demographic_update_aggregates"] = stats_demographic_update_aggregates

    # -------------------------------------------------------------------------
    def stats_demographic_update_location_aggregate(location_level,
                                                    root_location_id,
                                                    parameter_id,
                                                    start_date,
                                                    end_date,
                                                    user_id = None,
                                                    ):
        """
            Update the stats_demographic_aggregate table for the given location and parameter
            - called from within stats_demographic_update_aggregates

            @param location_level: gis level at which the data needs to be accumulated
            @param root_location_id: id of the location
            @param parameter_id: parameter for which the stats are being updated
            @param start_date: start date of the period in question
            @param end_date: end date of the period in question
            @param user_id: calling request's auth.user.id or None
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)

        # Run the Task & return the result
        result = s3db.stats_demographic_update_location_aggregate(location_level,
                                                                  root_location_id,
                                                                  parameter_id,
                                                                  start_date,
                                                                  end_date,
                                                                  )
        db.commit()
        return result

    tasks["stats_demographic_update_location_aggregate"] = stats_demographic_update_location_aggregate

    # --------------------e----------------------------------------------------
    # Disease: Depends on Stats
    # --------------------e----------------------------------------------------
    if has_module("disease"):

        def disease_stats_update_aggregates(records = None,
                                            all = False,
                                            user_id = None,
                                            ):
            """
                Update the disease_stats_aggregate table for the given
                disease_stats_data record(s)

                @param records: JSON of Rows of disease_stats_data records to
                                update aggregates for
                @param user_id: calling request's auth.user.id or None
            """
            if user_id:
                # Authenticate
                auth.s3_impersonate(user_id)

            # Run the Task & return the result
            result = s3db.disease_stats_update_aggregates(records, all)
            db.commit()
            return result

        tasks["disease_stats_update_aggregates"] = disease_stats_update_aggregates

        # ---------------------------------------------------------------------
        def disease_stats_update_location_aggregates(location_id,
                                                     children,
                                                     parameter_id,
                                                     dates,
                                                     user_id = None,
                                                     ):
            """
                Update the disease_stats_aggregate table for the given location and parameter
                - called from within disease_stats_update_aggregates

                @param location_id: location to aggregate at
                @param children: locations to aggregate from
                @param parameter_id: parameter to aggregate
                @param dates: dates to aggregate for
                @param user_id: calling request's auth.user.id or None
            """
            if user_id:
                # Authenticate
                auth.s3_impersonate(user_id)

            # Run the Task & return the result
            result = s3db.disease_stats_update_location_aggregates(location_id,
                                                                   children,
                                                                   parameter_id,
                                                                   dates,
                                                                   )
            db.commit()
            return result

        tasks["disease_stats_update_location_aggregates"] = disease_stats_update_location_aggregates

    # --------------------e----------------------------------------------------
    # Vulnerability: Depends on Stats
    # -------------------------------------------------------------------------
    if has_module("vulnerability"):

        def vulnerability_update_aggregates(records=None, user_id=None):
            """
                Update the vulnerability_aggregate table for the given
                vulnerability_data record(s)

                @param records: JSON of Rows of vulnerability_data records to update aggregates for
                @param user_id: calling request's auth.user.id or None
            """
            if user_id:
                # Authenticate
                auth.s3_impersonate(user_id)

            # Run the Task & return the result
            result = s3db.vulnerability_update_aggregates(records)
            db.commit()
            return result

        tasks["vulnerability_update_aggregates"] = vulnerability_update_aggregates

        # ---------------------------------------------------------------------
        def vulnerability_update_location_aggregate(#location_level,
                                                    root_location_id,
                                                    parameter_id,
                                                    start_date,
                                                    end_date,
                                                    user_id = None,
                                                    ):
            """
                Update the vulnerability_aggregate table for the given location and parameter
                - called from within vulnerability_update_aggregates

                @param location_level: gis level at which the data needs to be accumulated
                @param root_location_id: id of the location
                @param parameter_id: parameter for which the stats are being updated
                @param start_date: start date of the period in question
                @param end_date: end date of the period in question
                @param user_id: calling request's auth.user.id or None
            """
            if user_id:
                # Authenticate
                auth.s3_impersonate(user_id)

            # Run the Task & return the result
            result = s3db.vulnerability_update_location_aggregate(#location_level,
                                                                  root_location_id,
                                                                  parameter_id,
                                                                  start_date,
                                                                  end_date,
                                                                  )
            db.commit()
            return result

        tasks["vulnerability_update_location_aggregate"] = vulnerability_update_location_aggregate

# -----------------------------------------------------------------------------
if has_module("sync"):

    def sync_synchronize(repository_id, user_id=None, manual=False):
        """
            Run all tasks for a repository, to be called from scheduler
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)

        rtable = s3db.sync_repository
        query = (rtable.deleted != True) & \
                (rtable.id == repository_id)
        repository = db(query).select(limitby=(0, 1)).first()
        if repository:
            sync = s3base.S3Sync()
            status = sync.get_status()
            if status.running:
                message = "Synchronization already active - skipping run"
                sync.log.write(repository_id=repository.id,
                               resource_name=None,
                               transmission=None,
                               mode=None,
                               action="check",
                               remote=False,
                               result=sync.log.ERROR,
                               message=message)
                db.commit()
                return sync.log.ERROR
            sync.set_status(running=True, manual=manual)
            try:
                sync.synchronize(repository)
            finally:
                sync.set_status(running=False, manual=False)
        db.commit()
        return s3base.S3SyncLog.SUCCESS

    tasks["sync_synchronize"] = sync_synchronize

# -----------------------------------------------------------------------------
# Instantiate Scheduler instance with the list of tasks
s3.tasks = tasks
s3task = s3base.S3Task()
current.s3task = s3task

# -----------------------------------------------------------------------------
# Reusable field for scheduler task links
scheduler_task_id = S3ReusableField("scheduler_task_id",
                                    "reference %s" % s3base.S3Task.TASK_TABLENAME,
                                    ondelete = "CASCADE")
s3.scheduler_task_id = scheduler_task_id

# END =========================================================================
