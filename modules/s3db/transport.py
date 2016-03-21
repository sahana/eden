# -*- coding: utf-8 -*-

""" Sahana Eden Transport Model

    @copyright: 2012-2016 (c) Sahana Software Foundation
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

__all__ = ("S3TransportModel",
           "transport_rheader",
           )

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from ..s3layouts import S3PopupLink

# =============================================================================
class S3TransportModel(S3Model):
    """
        http://eden.sahanafoundation.org/wiki/BluePrint/Transport
    """

    names = ("transport_airport",
             "transport_heliport",
             "transport_seaport",
             "transport_border_crossing",
             "transport_border_crossing_country",
             "transport_border_control_point",
             )

    def model(self):

        T = current.T
        db = current.db
        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT
        settings = current.deployment_settings

        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id

        obsolete_options = {True: T("Closed"),
                            False: T("Operational"),
                            }

        # ---------------------------------------------------------------------
        # Airports
        #
        storage_types = {
            1: T("covered"),
            2: T("uncovered"),
        }
        airport_capacity_opts = {
            2: T("number of planes"),
            3: T("m3")
        }

        # http://en.wikipedia.org/wiki/Runway#Surface_type_codes
        runway_surface_opts = {"ASP": T("Asphalt"),
                               "BIT": T("Bitumenous asphalt or tarmac"),
                               #"BRI": T("Bricks"), (no longer in use, covered with asphalt or concrete now)
                               "CLA": T("Clay"),
                               "COM": T("Composite"),
                               "CON": T("Concrete"),
                               "COP": T("Composite"),
                               "COR": T("Coral (coral reef structures)"),
                               "GRE": T("Graded or rolled earth, grass on graded earth"),
                               "GRS": T("Grass or earth not graded or rolled"),
                               "GVL": T("Gravel"),
                               "ICE": T("Ice"),
                               "LAT": T("Laterite"),
                               "MAC": T("Macadam"),
                               "PEM": T("Partially concrete, asphalt or bitumen-bound macadam"),
                               "PER": T("Permanent surface, details unknown"),
                               "PSP": T("Marsden Matting (derived from pierced/perforated steel planking)"),
                               "SAN": T("Sand"),
                               "SMT": T("Sommerfeld Tracking"),
                               "SNO": T("Snow"),
                               "U": T("Unknown surface"),
                               }
        # SIGCAF has these:
        # http://www.humanitarianresponse.info/operations/central-african-republic/dataset/central-african-republic-aerodromes-airports-airfields
        # BASG, BL, BLA, BLAG, BLG, PM/BL
        # WFP just use Paved/Unpaved

        # SIGCAF classifications
        # We could consider using these instead?
        # http://en.wikipedia.org/wiki/Pavement_classification_number
        aircraft_size_opts = {"MH1521": "MH.1521", # 1 ton 6-seater monoplane: http://en.wikipedia.org/wiki/Max_Holste_Broussard#Specifications_.28MH.1521M.29
                              "PA31": "PA-31",     # 1.3 tons twin prop http://en.wikipedia.org/wiki/Piper_PA-31_Navajo#Specifications_.28PA-31_Navajo.29
                              "3TN": T("3 Tons"),
                              "DC3": "DC-3",       # 4 tons http://en.wikipedia.org/wiki/Douglas_DC-3#Specifications_.28DC-3A.29
                              "SE210": "SE 210",   # 8 tons http://en.wikipedia.org/wiki/Sud_Aviation_Caravelle#Specifications_.28Caravelle_III.29
                              "DC4": "DC-4",       # 10 tons http://en.wikipedia.org/wiki/Douglas_DC-4#Specifications_.28DC-4-1009.29
                              "13TN": T("13 Tons"),
                              "C160": "C-160",     # 17 tons http://en.wikipedia.org/wiki/Transall_C-160#Specifications_.28C-160.29
                              "Larger": T("Larger"),
                              }

        # Numbers are also in the XSL
        humanitarian_use_opts = {1: T("No"),
                                 2: T("Upon request"),
                                 3: T("Connection"),
                                 4: T("Hub"),
                                 9: T("Closed"),
                                 }

        if settings.get_transport_airport_code_unique():
            code_requires = IS_EMPTY_OR([IS_LENGTH(10),
                                         IS_NOT_IN_DB(db, "transport_airport.code"),
                                         ])
        else:
            code_requires = IS_EMPTY_OR(IS_LENGTH(10))

        tablename = "transport_airport"
        define_table(tablename,
                     #super_link("doc_id", "doc_entity"),
                     #super_link("pe_id", "pr_pentity"),
                     super_link("site_id", "org_site"),
                     Field("name", notnull=True,
                           length = 64, # Mayon Compatibility
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     # Code is part of the SE
                     Field("code",
                           label = T("Code"),
                           length = 10, # Mayon Compatibility
                           requires = code_requires,
                           # Enable in Templates as-required
                           readable = False,
                           writable = False,
                           ),
                     # Other codes can be added as tags if-required, but these 2 are so common that they are worth putting directly in the table
                     Field("icao", length=4,
                           label = T("ICAO"),
                           requires = IS_EMPTY_OR(IS_NOT_IN_DB(db, "transport_airport.icao")),
                           ),
                     Field("iata", length=3,
                           label = T("IATA"),
                           requires = IS_EMPTY_OR(IS_NOT_IN_DB(db, "transport_airport.iata")),
                           ),
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
                     Field("runway_surface",
                           default = "U",
                           label = T("Runway Surface"),
                           represent = lambda opt: \
                            runway_surface_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_IN_SET(runway_surface_opts),
                           ),
                     Field("aircraft_max_size",
                           label = T("Aircraft Maximum Size"),
                           represent = lambda opt: \
                            aircraft_size_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(aircraft_size_opts)
                                        ),
                           ),
                     Field("humanitarian_use", "integer",
                           label = T("Humanitarian Use"),
                           represent = lambda opt: \
                            humanitarian_use_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(humanitarian_use_opts)
                                        ),
                           ),
                     organisation_id(),
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
                           represent = lambda opt: \
                            storage_types.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(storage_types)
                                        ),
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
                            airport_capacity_opts.get(opt, UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(airport_capacity_opts)
                                        ),
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
                           represent = S3Represent(options=obsolete_options),
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
                                 "humanitarian_use",
                                 "organisation_id",
                                 "location_id$lat",
                                 "location_id$lon",
                                 "location_id$elevation",
                                 "runway_length",
                                 "runway_width",
                                 "runway_surface",
                                 "aircraft_max_size",
                                 ],
                  #onaccept = self.transport_airport_onaccept,
                  #super_entity = ("doc_entity", "pr_pentity", "org_site"),
                  super_entity = "org_site",
                  )

        # ---------------------------------------------------------------------
        # Heliports
        #
        if settings.get_transport_heliport_code_unique():
            code_requires = IS_EMPTY_OR([IS_LENGTH(10),
                                         IS_NOT_IN_DB(db, "transport_heliport.code"),
                                         ])
        else:
            code_requires = IS_EMPTY_OR(IS_LENGTH(10))

        tablename = "transport_heliport"
        define_table(tablename,
                     #super_link("doc_id", "doc_entity"),
                     #super_link("pe_id", "pr_pentity"),
                     super_link("site_id", "org_site"),
                     Field("name", notnull=True,
                           length = 64, # Mayon Compatibility
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("code",
                           label = T("Code"),
                           length = 10, # Mayon Compatibility
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
                           represent = S3Represent(options=obsolete_options),
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
                  #onaccept = self.transport_heliport_onaccept,
                  #super_entity = ("doc_entity", "pr_pentity", "org_site"),
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
            code_requires = IS_EMPTY_OR([IS_LENGTH(10),
                                         IS_NOT_IN_DB(db, "transport_seaport.code"),
                                         ])
        else:
            code_requires = IS_EMPTY_OR(IS_LENGTH(10))

        tablename = "transport_seaport"
        define_table(tablename,
                     #super_link("doc_id", "doc_entity"),
                     #super_link("pe_id", "pr_pentity"),
                     super_link("site_id", "org_site"),
                     Field("name", notnull=True,
                           length = 64, # Mayon Compatibility
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("code",
                           label = T("Code"),
                           length = 10, # Mayon Compatibility
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
                           represent = S3Represent(options=obsolete_options),
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
                  #onaccept = self.transport_seaport_onaccept,
                  #super_entity = ("doc_entity", "pr_pentity", "org_site"),
                  super_entity = "org_site",
                  )

        # ---------------------------------------------------------------------
        # Border Crossings
        #
        border_crossing_status = (("OPEN", T("Open")),
                                  ("RESTRICTED", T("Restricted")),
                                  ("CLOSED", T("Closed")),
                                  )

        tablename = "transport_border_crossing"
        define_table(tablename,
                     Field("name", notnull=True,
                           length = 64, # Mayon Compatibility
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     location_id(
                        widget = S3LocationSelector(levels = [],
                                                    show_address = False,
                                                    show_postcode = False,
                                                    show_latlon = True,
                                                    show_map = True,
                                                    ),
                     ),
                     Field("status",
                           default = "OPEN",
                           represent = S3Represent(options = dict(border_crossing_status)),
                           requires = IS_IN_SET(border_crossing_status,
                                                zero = None,
                                                sort = False,
                                                ),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # Components
        self.add_components(tablename,
                            transport_border_crossing_country = "border_crossing_id",
                            transport_border_control_point = "border_crossing_id",
                            )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create=T("Create Border Crossing"),
            title_display=T("Border Crossing Details"),
            title_list=T("Border Crossings"),
            title_update=T("Edit Border Crossing"),
            title_upload=T("Import Border Crossings"),
            label_list_button=T("List Border Crossings"),
            label_delete_button=T("Delete Border Crossing"),
            msg_record_created=T("Border Crossing added"),
            msg_record_modified=T("Border Crossing updated"),
            msg_record_deleted=T("Border Crossing deleted"),
            msg_list_empty=T("No Border Crossings currently registered"))

        # CRUD Form
        crud_form = S3SQLCustomForm("name",
                                    "location_id",
                                    S3SQLInlineComponent("border_crossing_country",
                                                         label = T("Countries"),
                                                         fields = [("", "country")],
                                                         ),
                                    "status",
                                    "comments",
                                    )

        # List Fields
        list_fields = ["name",
                       (T("Countries"), "border_crossing_country.country"),
                       "location_id",
                       "status",
                       "comments",
                       ]

        # Filter Widgets
        filter_widgets = [S3TextFilter(["name",
                                        "comments",
                                        ],
                                       label = T("Search"),
                                       ),
                          S3OptionsFilter("border_crossing_country.country",
                                          label = T("Country"),
                                          )
                          ]

        # Table Configuration
        configure(tablename,
                  crud_form = crud_form,
                  deduplicate = S3Duplicate(primary=("name",)),
                  filter_widgets = filter_widgets,
                  list_fields = list_fields,
                  )

        # Reusable field
        represent = transport_BorderCrossingRepresent(show_link=True)
        border_crossing_id = S3ReusableField("border_crossing_id", "reference %s" % tablename,
                                             label = T("Border Crossing"),
                                             represent = represent,
                                             requires = IS_ONE_OF(db, "%s.id" % tablename,
                                                                  represent,
                                                                  ),
                                             sortby = "name",
                                             comment = S3PopupLink(c="transport",
                                                                   f="border_crossing",
                                                                   tooltip=T("Create a new border crossing"),
                                                                   ),
                                             )

        # ---------------------------------------------------------------------
        # Countries involved in a border crossing
        #
        current_countries = lambda: current.gis.get_countries(key_type="code")

        tablename = "transport_border_crossing_country"
        define_table(tablename,
                     border_crossing_id(),
                     Field("country", length=2,
                           label = T("Country"),
                           represent = self.gis_country_code_represent,
                           requires = IS_EMPTY_OR(IS_IN_SET_LAZY(
                                        current_countries,
                                        zero=messages.SELECT_LOCATION,
                                        )),
                           ),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Border Control Points
        # - the Facilities at either side of the Border
        #
        tablename = "transport_border_control_point"
        define_table(tablename,
                     super_link("doc_id", "doc_entity"),
                     super_link("site_id", "org_site"),
                     #super_link("pe_id", "pr_pentity"),
                     Field("name", notnull=True,
                           length = 64, # Mayon Compatibility
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     border_crossing_id(),
                     organisation_id(),
                     location_id(),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
           label_create=T("Create Border Control Point"),
           title_display=T("Border Control Points"),
           title_list=T("Border Control Points"),
           title_update=T("Edit Border Control Point"),
           title_upload=T("Import Border Control Points"),
           label_list_button=T("List Border Control Points"),
           label_delete_button=T("Delete Border Control Point"),
           msg_record_created=T("Border Control Point added"),
           msg_record_modified=T("Border Control Point updated"),
           msg_record_deleted=T("Border Control Point deleted"),
           msg_list_empty=T("No Border Control Points currently registered"),
           )

        configure(tablename,
                  super_entity = ("doc_entity",
                                  "org_site",
                                  #"pr_pentity",
                                  ),
                  )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def transport_airport_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        # If made into a pe_id:
        #current.s3db.org_update_affiliations("transport_airport", form.vars)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def transport_heliport_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        # If made into a pe_id:
        #current.s3db.org_update_affiliations("transport_heliport", form.vars)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def transport_seaport_onaccept(form):
        """
            Update Affiliation, record ownership and component ownership
        """

        # If made into a pe_id:
        #current.s3db.org_update_affiliations("transport_seaport", form.vars)
        return

# =============================================================================
class transport_BorderCrossingRepresent(S3Represent):
    """ Representations for border_crossing_id """

    def __init__(self, show_link=False):
        """
            Constructor

            @param show_link: render as link to the border crossing
        """

        super(transport_BorderCrossingRepresent, self).__init__(
                                    lookup = "transport_border_crossing",
                                    show_link = show_link,
                                    )

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a row

            @param row: the Row
        """

        if hasattr(row, "transport_border_crossing"):
            row = row.transport_border_crossing
        representation = row.name

        if hasattr(row, "countries"):
            representation = "%s (%s)" % (representation,
                                          ", ".join(row.countries),
                                          )

        return representation

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=[]):
        """
            Custom rows lookup

            @param key: the key Field
            @param values: the values
            @param fields: unused (retained for API compatibility)
        """

        s3db = current.s3db

        btable = self.table
        ctable = s3db.transport_border_crossing_country
        left = ctable.on((ctable.border_crossing_id == btable.id) & \
                         (ctable.deleted != True))

        if len(values) == 1:
            query = (key == values[0])
        else:
            query = key.belongs(values)
        rows = current.db(query).select(btable.id,
                                        btable.name,
                                        ctable.country,
                                        left = left)
        self.queries += 1

        output = {}
        country_represent = s3db.gis_country_code_represent
        for row in rows:

            country = country_represent(row[ctable.country])

            crossing = row["transport_border_crossing"]
            crossing_id = crossing.id

            output_row = output.get(crossing_id)
            if output_row:
                countries = output_row.countries
                countries.append(country)
            else:
                crossing.countries = [country]
                output[crossing_id] = crossing

        return output.values()

# =============================================================================
def transport_rheader(r, tabs=[]):
    """ Transport module resource headers """

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None

    settings = current.deployment_settings
    s3db = current.s3db

    tablename, record = s3_rheader_resource(r)
    table = s3db.table(tablename)

    rheader = None
    rheader_fields = []

    if record:

        T = current.T

        if tablename == "transport_border_crossing":

            if not tabs:
                tabs = [(T("Details"), None),
                        (T("Control Points"), "border_control_point"),
                        ]

            rheader_fields = [["name"],
                              ["location_id"],
                              ]

        else:
            # All other entities
            # - Airports
            # - Seaports
            # - Heliports
            # - Border Control Points
            if not tabs:
                tabs = [(T("Details"), None),
                        ]

            rheader_fields = [["name"],
                              ["location_id"],
                              ]
            if settings.has_module("req"):
                tabs.extend(s3db.req_tabs(r))
            if settings.has_module("inv"):
                tabs.extend(s3db.inv_tabs(r))

        rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                         table=table,
                                                         record=record,
                                                         )
    return rheader

# END =========================================================================
