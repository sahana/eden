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
        
        storageTyp_opts = {
            1:"",
            2:T("warehousing"),
            3:T("secure storage"),
            4:T("customs warehousing")
        }
        
        operationStatus_opts = {
            1: T("Operational"),
            2: T("Closed")
        }
        
        ownership_opts = {
            1: T("Public"),
            2: T("Private")
        }
        
        heightUnit_opts = {
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
                             Field("ownershipType", "integer",
                                   requires = IS_IN_SET(ownership_opts, zero=None),
                                   default = 1,
                                   label = T("Ownership"),
                                   represent = lambda opt: \
                                   ownership_opts.get(opt, UNKNOWN_OPT)),
                             Field("operationStatus", "integer",
                                   requires = IS_IN_SET(operationStatus_opts, zero=None),
                                   default = 1,
                                   label = T("Operation Status"),
                                   represent = lambda opt: \
                                   operationStatus_opts.get(opt, UNKNOWN_OPT)),
                             Field("maxHeight", "double",
                                   label=T("Max Height")),
                             Field("maxHeightUnits", "integer",
                                   requires = IS_IN_SET(heightUnit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                   heightUnit_opts.get(opt, UNKNOWN_OPT)),
                             
                             Field("roll_OnOff", "boolean",
                                   default=False,
                                   label=T("Roll On Roll Off Berth")),
                                    
                             Field("cargoPierDepth", "double",
                                   label=T("Cargo Pier Depth")),                             
                             Field("cargoPierDepthUnits", "integer",
                                   requires = IS_IN_SET(heightUnit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                   heightUnit_opts.get(opt, UNKNOWN_OPT)),
                             
                             Field("oilTerminalDepth", "double",
                                   label=T("Oil Terminal Depth")),
                             Field("oilTerminalDepthUnits", "integer",
                                   requires = IS_IN_SET(heightUnit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                   heightUnit_opts.get(opt, UNKNOWN_OPT)),
                             
                             Field("dryDock", "boolean",
                                    default=False,
                                    label=T("Dry Dock")),
                                    
                             Field("vesselMaxLength", "double",
                                   label=T("Vessel Max Length")),
                             Field("vesselMaxLengthUnits", "integer",
                                   requires = IS_IN_SET(heightUnit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                   heightUnit_opts.get(opt, UNKNOWN_OPT)),
                             Field("seaportRepairs","text",
                                   label=T("Seaport Repairs")),
                             Field ("seaportShelter","text",
                                   label=T("Seaport Shelter")),
                             Field("wareCap", "double",     
                                   label=T("Warehousing Storage Capacity")),
                             Field("secStrCap", "double",      
                                   label=T("Secure Storage Capacity")),
                             Field("custWareCap", "double",     
                                   label=T("Customs Warehousing Storage Capacity")),
                             Field("tugNum", "integer",    
                                   label=T("Number of Tugboats")),
                             Field("tugCap", "double",     
                                   label=T("Tugboat Capacity")),
                             Field("bargeNum", "integer",     
                                   label=T("Number of Barges")),
                             Field("bargeCap", "double",     
                                   label=T("Barge Capacity")),
                             Field("seaportLoadingEquipment","text",
                                   label=T("Seaport Loading Equipment")),
                             Field("seaportCustomsCapacity","text",
                                   label=T("Seaport Customs Capacity")),
                             Field ("seaportSecurity","text",
                                   label=T("Seaport Security")),
                             Field("highTideDepth", "double",
                                   label=T("High Tide Depth")),                             
                             Field("highTideDepthUnits", "integer",
                                   requires = IS_IN_SET(heightUnit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                   heightUnit_opts.get(opt, UNKNOWN_OPT)),
                             
                             Field("lowTideDepth", "double",
                                   label=T("Low Tide Depth")),
                             Field("lowTideDepthUnits", "integer",
                                   requires = IS_IN_SET(heightUnit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                   heightUnit_opts.get(opt, UNKNOWN_OPT)),
                             
                             Field("floodDepth", "double",
                                   label=T("Flood Depth")),                             
                             Field("floodDepthUnits", "integer",
                                   requires = IS_IN_SET(heightUnit_opts, zero=None),
                                   default = 1,
                                   label = T("Units"),
                                   represent = lambda opt: \
                                   heightUnit_opts.get(opt, UNKNOWN_OPT)),
                             
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
