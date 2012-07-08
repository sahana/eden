# -*- coding: utf-8 -*-

""" Sahana Eden Situation Model

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3SituationModel"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3SituationModel(S3Model):
    """
    """

    names = ["sit_situation",
             "sit_trackable",
             "sit_presence",
             ]

    def model(self):

        T = current.T

        location_id = self.gis_location_id

        configure = self.configure
        super_entity = self.super_entity

        # Situation Super-Entity ----------------------------------------------
        #
        situation_types = Storage(
            irs_incident = T("Incident"),
            rms_req = T("Request"),
            pr_presence = T("Presence")
        )

        tablename = "sit_situation"
        table = super_entity(tablename, "sit_id", situation_types,
                             Field("datetime", "datetime"),
                             location_id())

        configure(tablename,
                  editable=False, deletable=False, listadd=False)

        # Trackable Types -----------------------------------------------------
        #
        # Use:
        #   - add a field with super_link("track_id", "sit_trackable")
        #   - add as super-entity in configure (super_entity=s3db.sit_trackable)
        #
        trackable_types = Storage(
            asset_asset = T("Asset"),
            pr_person = T("Person"),
            dvi_body = T("Dead Body")
        )

        tablename = "sit_trackable"
        sit_trackable = super_entity(tablename, "track_id",
                                     trackable_types,
                                     Field("track_timestmp", "datetime",
                                           readable=False,
                                           writable=False))

        configure(tablename,
                  editable=False, deletable=False, listadd=False)

        # Presence Records for trackables -------------------------------------
        #
        # Use:
        #   - will be automatically available to all trackable types
        #
        tablename = "sit_presence"
        table = self.define_table(tablename,
                                  self.super_link("track_id", sit_trackable),
                                  Field("timestmp", "datetime",
                                        label=T("Date/Time")),
                                  location_id(),
                                  Field("interlock",
                                        readable=False,
                                        writable=False),
                                  *s3_meta_fields())

        # Shared component of all trackable types
        self.add_component(table,
                            sit_trackable=self.super_key(sit_trackable))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage()

# END =========================================================================
