# -*- coding: utf-8 -*-

""" Incident Reporting System - Model

    @author: Sahana Taiwan Team
    @author: Fran Boon
"""

if not deployment_settings.has_module("irs"):
    def ireport_id(**arguments):
        """
            Allow FKs to be added safely to other models in case module disabled
            - used by events module
                    & legacy assess & impact modules
        """
        return Field("ireport_id", "integer", readable=False, writable=False)
    response.s3.ireport_id = ireport_id

# END =========================================================================
