# -*- coding: utf-8 -*-

"""
    GIS
"""

# For Bulk Importer
#s3.gis_set_default_location = gis.set_default_location

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

# END =========================================================================
