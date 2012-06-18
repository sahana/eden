# -*- coding: utf-8 -*-

# =============================================================================
# Tasks to be callable async
# =============================================================================

tasks = {}

# -----------------------------------------------------------------------------
def download_kml(record_id, filename, user_id=None):
    """
        Download a KML file
            - will normally be done Asynchronously if there is a worker alive

        @param record_id: id of the record in db.gis_layer_kml
        @param filename: name to save the file as
        @param user_id: calling request's auth.user.id or None
    """
    if user_id:
        # Authenticate
        auth.s3_impersonate(user_id)
    # Run the Task
    result = gis.download_kml(record_id, filename)
    return result

tasks["download_kml"] = download_kml

# -----------------------------------------------------------------------------
if settings.has_module("msg"):

    # -------------------------------------------------------------------------
    def process_outbox(contact_method, user_id=None):
        """
            Process Outbox
                - will normally be done Asynchronously if there is a worker alive

            @param contact_method: one from s3msg.MSG_CONTACT_OPTS
            @param user_id: calling request's auth.user.id or None
        """
        if user_id:
            # Authenticate
            auth.s3_impersonate(user_id)
        # Run the Task
        result = msg.process_outbox(contact_method)
        return result

    tasks["process_outbox"] = process_outbox

    # -------------------------------------------------------------------------
    def process_inbound_email(username):
        """
            Poll an inbound email source.

            @param username: email address of the email source to read from.
            This uniquely identifies one inbound email task.
        """
        # Run the Task
        result = msg.fetch_inbound_email(username)
        return result

    tasks["process_inbound_email"] = process_inbound_email

    # -----------------------------------------------------------------------------
    def parse_workflow(workflow):
        """
        Processes the msg_log for unparsed messages.
        """
        # Run the Task
        result = msg.parse_import(workflow)
        return result
        
    tasks["parse_workflow"] = parse_workflow
    
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
# Instantiate Scheduler instance with the list of tasks
s3.tasks = tasks
s3task = s3base.S3Task()
current.s3task = s3task

# END =========================================================================
