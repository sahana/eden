# -*- coding: utf-8 -*-

# =============================================================================
# Tasks to be callable async
# =============================================================================

tasks = {}

# -----------------------------------------------------------------------------
def crop_image(path, x1, y1, x2, y2, width):
    from PIL import Image
    image = Image.open(path)

    scale_factor = image.size[0] / float(width)

    points = map(int, map(lambda a: a * scale_factor, (x1, y1, x2, y2)))
    image.crop(points).save(path)

tasks["crop_image"] = crop_image

# -----------------------------------------------------------------------------)
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

tasks["gis_download_kml"] = gis_download_kml

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

tasks["gis_update_location_tree"] = gis_update_location_tree

# -----------------------------------------------------------------------------
def org_facility_geojson(user_id=None):
    """
        Export GeoJSON[P] Of Facility data

        @param user_id: calling request's auth.user.id or None
    """
    if user_id:
        # Authenticate
        auth.s3_impersonate(user_id)
    # Run the Task & return the result
    s3db.org_facility_geojson()

tasks["org_facility_geojson"] = org_facility_geojson

# -----------------------------------------------------------------------------
def sync_synchronize(repository_id, user_id=None, manual=False):
    """
        Run all tasks for a repository, to be called from scheduler
    """

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
def maintenance(period="daily"):
    """
        Run all maintenance tasks which should be done daily
        - these are read from the template
    """

    mod = "applications.%s.private.templates.%s.maintenance as maintenance" % \
                    (appname, settings.get_template())
    try:
        exec("import %s" % mod)
    except ImportError, e:
        # No Custom Maintenance available, use the default
        exec("import applications.%s.private.templates.default.maintenance as maintenance" % appname)

    if period == "daily":
        result = maintenance.Daily()()
    else:
        result = "NotImplementedError"

    db.commit()
    return result

tasks["maintenance"] = maintenance


# -----------------------------------------------------------------------------
if settings.has_module("msg"):

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
    def msg_email_poll(username, user_id):
        """
            Poll an inbound email source.

            @param username: email address of the email source to read from.
            This uniquely identifies one inbound email task.
        """
        # Run the Task & return the result
        result = msg.fetch_inbound_email(username)
        db.commit()
        return result

    tasks["msg_email_poll"] = msg_email_poll

    # -------------------------------------------------------------------------
    def msg_mcommons_poll(campaign_id, user_id=None):
        """
            Poll a Mobile Commons source for Inbound SMS.

            @param campaign_id: account name for the SMS source to read from.
            This uniquely identifies one inbound SMS task.
        """
        # Run the Task & return the result
        result = msg.mcommons_poll(campaign_id)
        db.commit()
        return result

    tasks["msg_mcommons_poll"] = msg_mcommons_poll

    # -------------------------------------------------------------------------
    def msg_twilio_poll(account, user_id=None):
        """
            Poll a Twilio source for Inbound SMS.

            @param account: account name for the SMS source to read from.
            This uniquely identifies one inbound SMS task.
        """
        # Run the Task & return the result
        result = msg.twilio_poll(account)
        db.commit()
        return result

    tasks["msg_twilio_poll"] = msg_twilio_poll

    # -----------------------------------------------------------------------------
    def msg_parse_workflow(workflow, source, user_id):
        """
            Processes the msg_log for unparsed messages.
        """
        # Run the Task & return the result
        result = msg.parse_import(workflow, source)
        db.commit()
        return result

    tasks["msg_parse_workflow"] = msg_parse_workflow

    # --------------------------------------------------------------------------
    def msg_search_subscription_notifications(frequency):
        """
            Search Subscriptions & send Notifications.
        """
        # Run the Task & return the result
        result = s3db.msg_search_subscription_notifications(frequency=frequency)
        db.commit()
        return result

    tasks["msg_search_subscription_notifications"] = msg_search_subscription_notifications

# -----------------------------------------------------------------------------
if settings.has_module("req"):

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
if settings.has_module("stats"):

    def stats_group_clean(user_id=None):
        """
            Update the stats_aggregate table by calculating all the stats_group
            records which have the dirty flag set to True
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)
        # Run the Task & return the result
        result = s3db.stats_group_clean()
        db.commit()
        return result

    tasks["stats_group_clean"] = stats_group_clean

    def stats_update_time_aggregate(data_id=None, user_id=None):
        """
            Update the stats_aggregate table for the given stats_data record

            @param data_id: the id of the stats_data record just added
            @param user_id: calling request's auth.user.id or None
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)
        # Run the Task & return the result
        result = s3db.stats_update_time_aggregate(data_id)
        db.commit()
        return result

    tasks["stats_update_time_aggregate"] = stats_update_time_aggregate

    def stats_update_aggregate_location(location_level,
                                        root_location_id,
                                        parameter_id,
                                        start_date,
                                        end_date,
                                        user_id=None):
        """
            Update the stats_aggregate table for the given location and parameter

            @param location_level: the gis level at which the data needs to be accumulated
            @param root_location_id: the id of the location
            @param paramerter_id: the parameter for which the stats are being updated
            @param start_date: the start date of the period in question
            @param end_date: the end date of the period in question
            @param user_id: calling request's auth.user.id or None
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)
        # Run the Task & return the result
        result = s3db.stats_update_aggregate_location(location_level,
                                                      root_location_id,
                                                      parameter_id,
                                                      start_date,
                                                      end_date,
                                                      )
        db.commit()
        return result

    tasks["stats_update_aggregate_location"] = stats_update_aggregate_location

# -----------------------------------------------------------------------------
# Instantiate Scheduler instance with the list of tasks
s3.tasks = tasks
s3task = s3base.S3Task()
current.s3task = s3task

# -----------------------------------------------------------------------------
# Reusable field for scheduler task links
scheduler_task_id = S3ReusableField("scheduler_task_id",
                                    "reference %s" % s3base.S3Task.TASK_TABLENAME,
                                    ondelete="CASCADE")
s3.scheduler_task_id = scheduler_task_id

# END =========================================================================
