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
        http://eden.sahanafoundation.org/wiki/BluePrint/Transport
    """

    names = ["transport_airport",
             "transport_seaport",
             ]

    def model(self):

        T = current.T
        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # ---------------------------------------------------------------------
        # Airports
        #
        storage_types = {
            1: T("covered"),
            2: T("uncovered"),
        }
        transport_airport_capacity_opts = {
            1: "",
            2: T("number of planes"),
            3: T("m3")
        }

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
                             Field("restrictions", "text",
                                   label=T("Restrictions")),
                             Field("ils", "boolean",
                                   represent=lambda bool: \
                                     (bool and [T("Yes")] or [T("No")])[0],
                                   label=T("Instrument Landing System")),
                             Field("lighting", "boolean",
                                   represent=lambda bool: \
                                     (bool and [T("Yes")] or [T("No")])[0],
                                   label=T("Lighting")),
                             Field("immigration_customs_capabilities", "text",
                                   label=T("Immigration and Customs Capabilities")),
                             Field("aircraft_max_size", "text",
                                   label=T("Aircraft Maximum Size")),
                             Field("security_desc", "text",
                                   label=T("Security Description"),
                                   comment=DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Security Description"),
                                                                   T("Description of perimeter fencing, security guards, security lighting.")))),
                             # @ToDo: put storage type inline
                             Field("storage_capacity", "double",
                                   label=T("Storage Capacity (m3)")),
                             Field("storage_type", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(storage_types)),
                                   label=T("Storage Type")),
                             # @ToDo: put units inline 
                             Field("parking_tarmac_space", "double",
                                   label=T("Parking/Tarmac Space Capacity")),
                             Field("capacity", "integer",
                                   label = T("Parking/Tarmac Space Units"),
                                   requires = IS_IN_SET(transport_airport_capacity_opts, zero=None),
                                   default = 1,
                                   represent = lambda opt: \
                                    transport_airport_capacity_opts.get(opt, UNKNOWN_OPT)),
                             Field("helipad_info", "text",
                                   label=T("Helipad Information")),
                             self.pr_person_id(label=T("Information Source")),
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

        ownership_opts = {
            1: T("Public"),
            2: T("Private")
        }

        unit_opts = {
            1: T("ft"),
            2: T("m")
        }

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

                             Field("ownership_type", "integer",
                                   requires = IS_IN_SET(ownership_opts, zero=None),
                                   default = 1,
                                   label = T("Ownership"),
                                   represent = lambda opt: \
                                    ownership_opts.get(opt, UNKNOWN_OPT)),
                             Field("max_height", "double",
                                   label=T("Max Height")),
                             Field("max_height_units", "integer",
                                   requires = IS_IN_SET(unit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                    unit_opts.get(opt, UNKNOWN_OPT)),
                             Field("roll_on_off", "boolean",
                                   default=False,
                                   represent=lambda bool: \
                                     (bool and [T("Yes")] or [T("No")])[0],
                                   label=T("Roll On Roll Off Berth")),
                             Field("cargo_pier_depth", "double",
                                   label=T("Cargo Pier Depth")),                             
                             Field("cargo_pier_depth_units", "integer",
                                   requires = IS_IN_SET(unit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                    unit_opts.get(opt, UNKNOWN_OPT)),
                             Field("oil_terminal_depth", "double",
                                   label=T("Oil Terminal Depth")),
                             Field("oil_terminal_depth_units", "integer",
                                   requires = IS_IN_SET(unit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                    unit_opts.get(opt, UNKNOWN_OPT)),
                             Field("dry_dock", "boolean",
                                   default=False,
                                   represent=lambda bool: \
                                     (bool and [T("Yes")] or [T("No")])[0],
                                   label=T("Dry Dock")),
                             Field("vessel_max_length", "double",
                                   label=T("Vessel Max Length")),
                             Field("vessel_max_length_units", "integer",
                                   requires = IS_IN_SET(unit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                    unit_opts.get(opt, UNKNOWN_OPT)),
                             Field("repairs", "text",
                                   label=T("Repairs")),
                             Field ("shelter", "text",
                                   label=T("Shelter")),
                             Field("warehouse_capacity", "double",     
                                   label=T("Warehousing Storage Capacity")),
                             Field("secure_storage_capacity", "double",      
                                   label=T("Secure Storage Capacity")),
                             Field("customs_warehouse_capacity", "double",     
                                   label=T("Customs Warehousing Storage Capacity")),
                             Field("tugs", "integer",    
                                   label=T("Number of Tugboats")),
                             Field("tug_capacity", "double",     
                                   label=T("Tugboat Capacity")),
                             Field("barges", "integer",     
                                   label=T("Number of Barges")),
                             Field("barge_capacity", "double",     
                                   label=T("Barge Capacity")),
                             Field("loading_equipment", "text",
                                   label=T("Loading Equipment")),
                             Field("customs_capacity", "text",
                                   label=T("Customs Capacity")),
                             Field ("security", "text",
                                   label=T("Security")),
                             Field("high_tide_depth", "double",
                                   label=T("High Tide Depth")),                             
                             Field("high_tide_depth_units", "integer",
                                   requires = IS_IN_SET(unit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                    unit_opts.get(opt, UNKNOWN_OPT)),
                             Field("low_tide_depth", "double",
                                   label=T("Low Tide Depth")),
                             Field("low_tide_depth_units", "integer",
                                   requires = IS_IN_SET(unit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                    unit_opts.get(opt, UNKNOWN_OPT)),
                             Field("flood_depth", "double",
                                   label=T("Flood Depth")),                             
                             Field("flood_depth_units", "integer",
                                   requires = IS_IN_SET(unit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                    unit_opts.get(opt, UNKNOWN_OPT)),

                             self.org_organisation_id(widget=S3OrganisationAutocompleteWidget(
                                default_from_profile=True)),
                             self.gis_location_id(),
                             Field("obsolete", "boolean",
                                   label=T("Obsolete"),
                                   represent=lambda bool: \
                                     (bool and [T("Closed")] or [T("Operational")])[0],
                                   default=False,
                                   ),
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
