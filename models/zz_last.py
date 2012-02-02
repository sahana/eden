# -*- coding: utf-8 -*-

# File needs to be last in order to be able to have all Tables defined

# -----------------------------------------------------------------------------
# GIS config
# ToDo: Once Event tables have moved to modules, then this should be moved
#       before 01_menu.py earlier file.
#       & then this file could be renamed as (zz_)tasks.py?
# -----------------------------------------------------------------------------
if "_config" in request.get_vars:
    # The user has just selected a config from the GIS menu
    try:
        config = int(request.get_vars._config)
    except ValueError:
        # Manually-crafted URL?
        pass
    else:
        if config != session.s3.gis_config_id:
            config = gis.set_config(config)
            if deployment_settings.has_module("event"):
                # See if this config is associated with an Event
                table = s3db.event_config
                query = (table.config_id == config)
                event = db(query).select(table.event_id,
                                         limitby=(0, 1)).first()
                if event:
                    session.s3.event = event.event_id
                else:
                    session.s3.event = None

# =============================================================================
# Tasks to be callable async
# =============================================================================
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

if deployment_settings.has_module("msg"):
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

# Instantiate Scheduler instance with the list of tasks
response.s3.tasks = tasks
s3task = s3base.S3Task()
current.s3task = s3task

# END =========================================================================
