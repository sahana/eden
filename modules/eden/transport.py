# -*- coding: utf-8 -*-

""" Sahana Eden Transport Model

    @copyright: 2012 (c) Sahana Software Foundation
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

__all__ = ["S3TransportModel",
           ]

from gluon import *
from gluon.storage import Storage

from ..s3 import *

# =============================================================================
class S3TransportModel(S3Model):
    """
        http://eden.sahanafoundation.org/wiki/BluePrintTransport
    """

    names = ["transport_airport",
             "transport_seaport",
             ]

    def model(self):

        T = current.T

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Airports
        #
        tablename = "transport_airport"
        table = define_table(tablename,
                             self.super_link("site_id", "org_site"),
                             Field("name", notnull=True,
                                   length=64, # Mayon Compatibility
                                   label=T("Name")),
                             Field("code",
                                   length=10,
                                   # Deployments that don't wants office codes can hide them
                                   #readable=False,
                                   #writable=False,
                                   # Mayon compatibility
                                   # @ToDo: Deployment Setting to add validator to make these unique
                                   #notnull=True,
                                   #unique=True,
                                   label=T("Code")),
                             self.org_organisation_id(widget=S3OrganisationAutocompleteWidget(
                                default_from_profile=True)),
                             self.gis_location_id(),
                             Field("obsolete", "boolean",
                                   label=T("Obsolete"),
                                   represent=lambda bool: \
                                     (bool and [T("Obsolete")] or [current.messages.NONE])[0],
                                   default=False,
                                   readable=False,
                                   writable=False),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            title_create=T("Add Airport"),
            title_display=T("Airport Details"),
            title_list=T("Airports"),
            title_update=T("Edit Airport"),
            title_search=T("Search Facilities"),
            title_upload=T("Import Facilities"),
            subtitle_create=T("Add New Airport"),
            label_list_button=T("List Airports"),
            label_create_button=T("Add New Airport"),
            label_delete_button=T("Delete Airport"),
            msg_record_created=T("Airport added"),
            msg_record_modified=T("Airport updated"),
            msg_record_deleted=T("Airport deleted"),
            msg_list_empty=T("No Airports currently registered"))

        configure(tablename,
                  super_entity="org_site"
                  )

        # ---------------------------------------------------------------------
        # Seaports
        #
        tablename = "transport_seaport"
        table = define_table(tablename,
                             self.super_link("site_id", "org_site"),
                             Field("name", notnull=True,
                                   length=64, # Mayon Compatibility
                                   label=T("Name")),
                             Field("code",
                                   length=10,
                                   # Deployments that don't wants office codes can hide them
                                   #readable=False,
                                   #writable=False,
                                   # Mayon compatibility
                                   # @ToDo: Deployment Setting to add validator to make these unique
                                   #notnull=True,
                                   #unique=True,
                                   label=T("Code")),
                             self.org_organisation_id(widget=S3OrganisationAutocompleteWidget(
                                default_from_profile=True)),
                             self.gis_location_id(),
                             Field("obsolete", "boolean",
                                   label=T("Obsolete"),
                                   represent=lambda bool: \
                                     (bool and [T("Obsolete")] or [current.messages.NONE])[0],
                                   default=False,
                                   readable=False,
                                   writable=False),
                             s3_comments(),
                             *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            title_create=T("Add Seaport"),
            title_display=T("Seaport Details"),
            title_list=T("Seaports"),
            title_update=T("Edit Seaport"),
            title_search=T("Search Facilities"),
            title_upload=T("Import Facilities"),
            subtitle_create=T("Add New Seaport"),
            label_list_button=T("List Seaports"),
            label_create_button=T("Add New Seaport"),
            label_delete_button=T("Delete Seaport"),
            msg_record_created=T("Seaport added"),
            msg_record_modified=T("Seaport updated"),
            msg_record_deleted=T("Seaport deleted"),
            msg_list_empty=T("No Seaports currently registered"))

        configure(tablename,
                  super_entity="org_site"
                  )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                )

# END =========================================================================
