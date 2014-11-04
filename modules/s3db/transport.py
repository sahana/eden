# -*- coding: utf-8 -*-

""" Sahana Eden Transport Model

    @copyright: 2012-14 (c) Sahana Software Foundation
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

__all__ = ("S3TransportModel",)

from gluon import *
from gluon.storage import Storage

from ..s3 import *

# =============================================================================
class S3TransportModel(S3Model):
    """
        http://eden.sahanafoundation.org/wiki/BluePrint/Transport
    """

    names = ("transport_airport",
             "transport_heliport",
             "transport_seaport",
             )

    def model(self):

        T = current.T
        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id
        super_link = self.super_link
        settings = current.deployment_settings
        db = current.db

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
        if settings.get_transport_airport_code_unique():
            code_requires = IS_EMPTY_OR(IS_NOT_IN_DB(db, "transport_airport.code"))
        else:
            code_requires = None

        tablename = "transport_airport"
        define_table(tablename,
                     super_link("site_id", "org_site"),
                     Field("name", notnull=True,
                           length=64, # Mayon Compatibility
                           label = T("Name"),
                           ),
                     # @ToDo: Add Tags or specific IATA/ICAO fields
                     Field("code", length=10,
                           # Mayon compatibility
                           #notnull=True,
                           #unique=True,
                           label = T("Code"),
                           requires = code_requires,
                           # Deployments that don't want site codes can hide them
                           #readable = False,
                           #writable = False,
                           ),
                     organisation_id(),
                     # @ToDo: Expose Elevation & Lat/Lon to Widget
                     location_id(),
                     # We should be more specific:
                     # http://en.wikipedia.org/wiki/Runway#Declared_distances
                     Field("runway_length", "integer",
                           label = T("Runway Length (m)"),
                           ),
                     Field("runway_width", "integer",
                           label = T("Runway Width (m)"),
                           ),
                     # Lookup?
                     # WFP: BASG, BL, BLA, BLAG, BLG, PM/BL
                     # http://en.wikipedia.org/wiki/Runway#Surface_type_codes
                     Field("runway_surface", #"integer",
                           label = T("Runway Surface"),
                           ),
                     # Lookup?
                     # 13TN, 3TN, C160, DC3, DC4, MH1521, PA31, SE210, L,ger
                     Field("aircraft_max_size", "text",
                           label = T("Aircraft Maximum Size"),
                           ),
                     Field("restrictions", "text",
                           label = T("Restrictions"),
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("ils", "boolean",
                           label = T("Instrument Landing System"),
                           represent=lambda bool: \
                             (bool and [T("Yes")] or [T("No")])[0],
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("lighting", "boolean",
                           label = T("Lighting"),
                           represent = lambda bool: \
                             (bool and [T("Yes")] or [T("No")])[0],
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("immigration_customs_capabilities", "text",
                           label = T("Immigration and Customs Capabilities"),
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("security_desc", "text",
                           label = T("Security Description"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Security Description"),
                                                           T("Description of perimeter fencing, security guards, security lighting."))),
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     # @ToDo: put storage type inline
                     Field("storage_capacity", "double",
                           label = T("Storage Capacity (m3)"),
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("storage_type", "integer",
                           label = T("Storage Type"),
                           requires = IS_EMPTY_OR(IS_IN_SET(storage_types)),
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     # @ToDo: put units inline
                     Field("parking_tarmac_space", "double",
                           label = T("Parking/Tarmac Space Capacity"),
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("capacity", "integer",
                           default = 1,
                           label = T("Parking/Tarmac Space Units"),
                           represent = lambda opt: \
                            transport_airport_capacity_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(transport_airport_capacity_opts, zero=None),
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     Field("helipad_info", "text",
                           label = T("Helipad Information"),
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     self.pr_person_id(
                        label = T("Information Source"),
                        # Enable in Templates as-required
                        readable = False,
                        writable = False,
                        ),
                     Field("obsolete", "boolean",
                           default = False,
                           label = T("Obsolete"),
                           represent = lambda bool: \
                             (bool and [T("Obsolete")] or [current.messages["NONE"]])[0],
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create=T("Create Airport"),
            title_display=T("Airport Details"),
            title_list=T("Airports"),
            title_update=T("Edit Airport"),
            title_upload=T("Import Airports"),
            label_list_button=T("List Airports"),
            label_delete_button=T("Delete Airport"),
            msg_record_created=T("Airport added"),
            msg_record_modified=T("Airport updated"),
            msg_record_deleted=T("Airport deleted"),
            msg_list_empty=T("No Airports currently registered"))

        configure(tablename,
                  list_fields = ["name",
                                 "location_id$lat",
                                 "location_id$lon",
                                 "location_id$elevation",
                                 "runway_length",
                                 "runway_width",
                                 "runway_surface",
                                 "aircraft_max_size",
                                 ],
                  onaccept = self.transport_airport_onaccept,
                  super_entity = "org_site",
                  )

        # ---------------------------------------------------------------------
        # Heliports
        #
        if settings.get_transport_heliport_code_unique():
            code_requires = IS_EMPTY_OR(IS_NOT_IN_DB(db, "transport_heliport.code"))
        else:
            code_requires = None

        tablename = "transport_heliport"
        define_table(tablename,
                     super_link("site_id", "org_site"),
                     Field("name", notnull=True,
                           length=64, # Mayon Compatibility
                           label = T("Name"),
                           ),
                     Field("code", length=10,
                           # Mayon compatibility
                           #notnull=True,
                           #unique=True,
                           label = T("Code"),
                           requires = code_requires,
                           # Deployments that don't want site codes can hide them
                           #readable = False,
                           #writable = False,
                           ),
                     organisation_id(),
                     location_id(),
                     Field("obsolete", "boolean",
                           default = False,
                           label = T("Obsolete"),
                           represent = lambda opt: \
                                     (opt and [T("Obsolete")] or [current.messages["NONE"]])[0],
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create=T("Create Heliport"),
            title_display=T("Heliport Details"),
            title_list=T("Heliports"),
            title_update=T("Edit Heliport"),
            title_upload=T("Import Heliports"),
            label_list_button=T("List Heliports"),
            label_delete_button=T("Delete Heliport"),
            msg_record_created=T("Heliport added"),
            msg_record_modified=T("Heliport updated"),
            msg_record_deleted=T("Heliport deleted"),
            msg_list_empty=T("No Heliports currently registered"))

        configure(tablename,
                  onaccept = self.transport_heliport_onaccept,
                  super_entity = "org_site",
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
        if settings.get_transport_seaport_code_unique():
            code_requires = IS_EMPTY_OR(IS_NOT_IN_DB(db, "transport_seaport.code"))
        else:
            code_requires = None

        tablename = "transport_seaport"
        define_table(tablename,
                     super_link("site_id", "org_site"),
                     Field("name", notnull=True,
                           length=64, # Mayon Compatibility
                           label = T("Name"),
                           ),
                     Field("code", length=10,
                           # Mayon compatibility
                           #notnull=True,
                           #unique=True,
                           label = T("Code"),
                           requires = code_requires,
                           # Deployments that don't want site codes can hide them
                           #readable = False,
                           #writable = False,
                           ),
                     Field("ownership_type", "integer",
                           default = 1,
                           label = T("Ownership"),
                           represent = lambda opt: \
                            ownership_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(ownership_opts, zero=None),
                           ),
                     Field("max_height", "double",
                           label = T("Max Height"),
                           ),
                     Field("max_height_units", "integer",
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                            unit_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(unit_opts, zero=None),
                           ),
                     Field("roll_on_off", "boolean",
                           default = False,
                           represent = lambda opt: \
                                     (opt and [T("Yes")] or [T("No")])[0],
                           label = T("Roll On Roll Off Berth"),
                           ),
                     Field("cargo_pier_depth", "double",
                           label = T("Cargo Pier Depth"),
                           ),
                     Field("cargo_pier_depth_units", "integer",
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                                       unit_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(unit_opts, zero=None),
                           ),
                     Field("oil_terminal_depth", "double",
                           label = T("Oil Terminal Depth"),
                           ),
                     Field("oil_terminal_depth_units", "integer",
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                                       unit_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(unit_opts, zero=None),
                           ),
                     Field("dry_dock", "boolean",
                           default = False,
                           label = T("Dry Dock"),
                           represent = lambda opt: \
                                     (opt and [T("Yes")] or [T("No")])[0],
                           ),
                     Field("vessel_max_length", "double",
                           label = T("Vessel Max Length"),
                           ),
                     Field("vessel_max_length_units", "integer",
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                            unit_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(unit_opts, zero=None),
                           ),
                     Field("repairs", "text",
                           label = T("Repairs"),
                           ),
                     Field ("shelter", "text",
                           label = T("Shelter"),
                           ),
                     Field("warehouse_capacity", "double",
                           label = T("Warehousing Storage Capacity"),
                           ),
                     Field("secure_storage_capacity", "double",
                           label = T("Secure Storage Capacity"),
                           ),
                     Field("customs_warehouse_capacity", "double",
                           label = T("Customs Warehousing Storage Capacity"),
                           ),
                     Field("tugs", "integer",
                           label = T("Number of Tugboats"),
                           ),
                     Field("tug_capacity", "double",
                           label = T("Tugboat Capacity"),
                           ),
                     Field("barges", "integer",
                           label = T("Number of Barges"),
                           ),
                     Field("barge_capacity", "double",
                           label = T("Barge Capacity"),
                           ),
                     Field("loading_equipment", "text",
                           label = T("Loading Equipment"),
                           ),
                     Field("customs_capacity", "text",
                           label = T("Customs Capacity"),
                           ),
                     Field("security", "text",
                           label = T("Security"),
                           ),
                     Field("high_tide_depth", "double",
                           label = T("High Tide Depth"),
                           ),
                     Field("high_tide_depth_units", "integer",
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                                       unit_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(unit_opts, zero=None),
                           ),
                     Field("low_tide_depth", "double",
                           label = T("Low Tide Depth"),
                           ),
                     Field("low_tide_depth_units", "integer",
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                                       unit_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(unit_opts, zero=None),
                           ),
                     Field("flood_depth", "double",
                           label = T("Flood Depth"),
                           ),
                     Field("flood_depth_units", "integer",
                           default = 1,
                           label = T("Units"),
                           represent = lambda opt: \
                                       unit_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(unit_opts, zero=None),
                           ),
                     organisation_id(),
                     location_id(),
                     Field("obsolete", "boolean",
                           default = False,
                           label = T("Obsolete"),
                           represent = lambda opt: \
                                     (opt and [T("Closed")] or [T("Operational")])[0],
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create=T("Create Seaport"),
            title_display=T("Seaport Details"),
            title_list=T("Seaports"),
            title_update=T("Edit Seaport"),
            title_upload=T("Import Seaports"),
            label_list_button=T("List Seaports"),
            label_delete_button=T("Delete Seaport"),
            msg_record_created=T("Seaport added"),
            msg_record_modified=T("Seaport updated"),
            msg_record_deleted=T("Seaport deleted"),
            msg_list_empty=T("No Seaports currently registered"))

        configure(tablename,
                  onaccept = self.transport_seaport_onaccept,
                  super_entity = "org_site",
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return dict()

    # -------------------------------------------------------------------------
    @staticmethod
    def transport_airport_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        current.s3db.org_update_affiliations("transport_airport", form.vars)

    # -------------------------------------------------------------------------
    @staticmethod
    def transport_heliport_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        current.s3db.org_update_affiliations("transport_heliport", form.vars)

    # -------------------------------------------------------------------------
    @staticmethod
    def transport_seaport_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        current.s3db.org_update_affiliations("transport_seaport", form.vars)

# END =========================================================================
