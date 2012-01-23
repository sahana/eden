# -*- coding: utf-8 -*-

"""
    GIS
"""

# Expose settings to views/modules
_gis = response.s3.gis
# Store old config to know whether we need to refresh options in zz_last
_gis.old_config = session.s3.gis_config_id

# This is needed for onvalidation
# The edit_L1..edit_L5 values are per country, and are in the gis_config
# records associated with each L0 location.
if s3_has_role(MAP_ADMIN):
    _gis.edit_Lx = _gis.edit_GR = True
else:
    _gis.edit_Lx = deployment_settings.get_gis_edit_lx()
    _gis.edit_GR = deployment_settings.get_gis_edit_group()

# For Bulk Importer
s3.gis_set_default_location = gis.set_default_location

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
