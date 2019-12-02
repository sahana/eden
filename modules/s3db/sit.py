# -*- coding: utf-8 -*-

""" Sahana Eden Situation Model

    @copyright: 2009-2019 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("S3SituationModel",
           )

from gluon import *
from gluon.storage import Storage
from ..s3 import *
#from s3layouts import S3PopupLink

# =============================================================================
class S3SituationModel(S3Model):
    """
        Situation Super Entity & Presence tables for Trackable resources
    """

    names = ("sit_situation",
             "sit_trackable",
             "sit_presence",
             "sit_location",
             )

    def model(self):

        T = current.T

        location_id = self.gis_location_id

        configure = self.configure
        super_entity = self.super_entity

        # ---------------------------------------------------------------------
        # Situation Super-Entity
        #
        situation_types = Storage(# @ToDo: Deprecate
                                  #irs_incident = T("Incident"),
                                  rms_req = T("Request"),
                                  pr_presence = T("Presence"),
                                  )

        tablename = "sit_situation"
        super_entity(tablename, "sit_id", situation_types,
                     Field("datetime", "datetime"),
                     location_id(),
                     )

        configure(tablename,
                  deletable = False,
                  editable = False,
                  listadd = False,
                  )

        # ---------------------------------------------------------------------
        # Trackable Types
        #
        # Use:
        #   - add a field with super_link("track_id", "sit_trackable")
        #   - add as super-entity in configure (super_entity=s3db.sit_trackable)
        #
        trackable_types = Storage(asset_asset = T("Asset"),
                                  dvi_body = T("Dead Body"),
                                  event_resource = T("Event Resource"),
                                  hrm_human_resource = T("Human Resource"),
                                  pr_person = T("Person"),
                                  )

        tablename = "sit_trackable"
        super_entity(tablename, "track_id",
                     trackable_types,
                     Field("track_timestmp", "datetime",
                           readable = False,
                           writable = False,
                           ),
                     )

        configure(tablename,
                  deletable = False,
                  editable = False,
                  listadd = False,
                  )

        # Components
        self.add_components(tablename,
                            # Presence
                            sit_presence = self.super_key("sit_trackable"),
                            )

        # ---------------------------------------------------------------------
        # Presence Records for trackables
        #
        # Use:
        #   - will be automatically available to all trackable types
        #
        tablename = "sit_presence"
        self.define_table(tablename,
                          self.super_link("track_id", "sit_trackable"),
                          s3_datetime("timestmp",
                                      label = T("Date/Time"),
                                      ),
                          location_id(
                            widget = S3LocationSelector(show_address = False,
                                                        show_postcode = False,
                                                        show_latlon = True,
                                                        ),
                            ),
                          Field("direction",
                                label = T("Direction"),
                                ),
                          Field("speed",
                                label = T("Speed"),
                                ),
                          Field("accuracy",
                                label = T("Accuracy"),
                                ),
                          Field("interlock",
                                readable = False,
                                writable = False,
                                ),
                          *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {"sit_location": self.sit_location,
                }

    # ---------------------------------------------------------------------
    @staticmethod
    def sit_location(row, tablename):
        """
            Virtual Field to return the current location of a Trackable
            @ToDo: Bulk
            @ToDo: Also show Timestamp of when seen there
        """

        s3db = current.s3db
        tracker = S3Tracker()(s3db[tablename], row[tablename].id)
        location = tracker.get_location(as_rows=True).first()

        return s3db.gis_location_represent(None, row=location)

# END =========================================================================
