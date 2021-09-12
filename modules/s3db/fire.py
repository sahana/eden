# -*- coding: utf-8 -*-

""" Sahana Eden Fire Models

    @copyright: 2009-2021 (c) Sahana Software Foundation
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

__all__ = ("FireZoneModel",
           "FireStationModel",
           )

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3layouts import S3PopupLink

# =============================================================================
class FireZoneModel(S3Model):
    """
        Fire Zones: Burn Perimeter, Burnt zone, Evacuation Zone, etc
    """

    names = ("fire_zone_type",
             "fire_zone",
             )

    def model(self):

        T = current.T
        db = current.db

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # -----------------------------------------------------------
        # Fire Zone Types
        tablename = "fire_zone_type"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        ADD_ZONE_TYPE = T("Create Zone Type")
        crud_strings[tablename] = Storage(
            label_create = ADD_ZONE_TYPE,
            title_display = T("Zone Type Details"),
            title_list = T("Zone Types"),
            title_update = T("Edit Zone Type"),
            title_upload = T("Import Zone Types"),
            label_list_button = T("List Zone Types"),
            label_delete_button = T("Delete Zone Type"),
            msg_record_created = T("Zone Type added"),
            msg_record_modified = T("Zone Type updated"),
            msg_record_deleted = T("Zone Type deleted"),
            msg_list_empty = T("No Zone Types currently registered"))

        zone_type_represent = S3Represent(lookup = tablename)

        self.configure(tablename,
                       deduplicate = S3Duplicate(),
                       )

        # -----------------------------------------------------------
        # Fire Zones
        tablename = "fire_zone"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("zone_type_id", db.fire_zone_type,
                           label = T("Type"),
                           requires = IS_EMPTY_OR(
                                         IS_ONE_OF(db, "fire_zone_type.id",
                                                   zone_type_represent,
                                                   sort = True,
                                                   )),
                           represent = zone_type_represent,
                           comment = S3PopupLink(c = "fire",
                                                 f = "zone_type",
                                                 label = ADD_ZONE_TYPE,
                                                 tooltip = T("Select a Zone Type from the list or click 'Add Zone Type'"),
                                                 ),
                           ),
                     self.gis_location_id(
                       widget = S3LocationSelector(catalog_layers = True,
                                                   points = False,
                                                   polygons = True,
                                                   ),
                     ),
                     s3_comments(),
                     *s3_meta_fields())

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Zone"),
            title_display = T("Zone Details"),
            title_list = T("Zones"),
            title_update = T("Edit Zone"),
            title_upload = T("Import Zones"),
            label_list_button = T("List Zones"),
            label_delete_button = T("Delete Zone"),
            msg_record_created = T("Zone added"),
            msg_record_modified = T("Zone updated"),
            msg_record_deleted = T("Zone deleted"),
            msg_list_empty = T("No Zones currently registered"))

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

# =============================================================================
class FireStationModel(S3Model):
    """
        A Model to manage Fire Stations:
        http://eden.sahanafoundation.org/wiki/Deployments/Bombeiros
    """

    names = ("fire_station",
             )

    def model(self):

        T = current.T
        db = current.db

        messages = current.messages
        NONE = messages["NONE"]
        OBSOLETE = messages.OBSOLETE

        location_id = self.gis_location_id
        organisation_id = self.org_organisation_id

        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # =====================================================================
        # Fire Station
        #

        if current.deployment_settings.get_fire_station_code_unique():
            code_requires = IS_EMPTY_OR([IS_LENGTH(10),
                                         IS_NOT_IN_DB(db, "fire_station.code"),
                                         ])
        else:
            code_requires = IS_LENGTH(10)

        tablename = "fire_station"
        define_table(tablename,
                     super_link("pe_id", "pr_pentity"),
                     super_link("site_id", "org_site"),
                     super_link("doc_id", "doc_entity"),
                     Field("name", notnull=True,
                           length=64,           # Mayon compatibility
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     Field("code", length=10,   # Mayon compatibility
                           label = T("Code"),
                           represent = lambda v: v or NONE,
                           requires = code_requires,
                           ),
                     organisation_id(),
                     location_id(),
                     Field("phone",
                           label = T("Phone"),
                           requires = IS_EMPTY_OR(IS_PHONE_NUMBER_MULTI()),
                           ),
                     Field("email",
                           label = T("Email"),
                           requires = IS_EMPTY_OR(IS_EMAIL()),
                           ),
                     Field("website",
                           label = T("Website"),
                           represent = s3_url_represent,
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     Field("obsolete", "boolean",
                           default = False,
                           label = T("Obsolete"),
                           represent = lambda opt: OBSOLETE if opt else NONE,
                           readable = False,
                           writable = False,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        fire_station_represent = S3Represent(lookup = tablename)
        station_id = S3ReusableField("station_id", "reference %s" % tablename,
                                     label = T("Station"),
                                     ondelete = "CASCADE",
                                     represent = fire_station_represent,
                                     requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "fire_station.id",
                                                              fire_station_represent,
                                                              )),
                                     )

        # CRUD strings
        crud_strings[tablename] = Storage(
            label_create = T("Create Fire Station"),
            title_display = T("Fire Station Details"),
            title_list = T("Fire Stations"),
            title_update = T("Edit Station Details"),
            title_upload = T("Upload Fire Stations List"),
            title_map = T("Map of Fire Stations"),
            label_list_button = T("List Fire Stations"),
            label_delete_button = T("Delete Fire Station"),
            msg_record_created = T("Fire Station added"),
            msg_record_modified = T("Fire Station updated"),
            msg_record_deleted = T("Fire Station deleted"),
            msg_no_match = T("No Fire Stations could be found"),
            msg_list_empty = T("No Fire Stations currently registered"))

        # Which levels of Hierarchy are we using?
        levels = current.gis.get_relevant_hierarchy_levels()

        list_fields = ["name",
                       #"organisation_id",   # Filtered in Component views
                       #"station_type_id",
                       ]

        text_fields = ["name",
                       "code",
                       "comments",
                       #"organisation_id$name",
                       #"organisation_id$acronym",
                       ]

        #report_fields = ["name",
        #                 "organisation_id",
        #                 ]

        for level in levels:
            lfield = "location_id$%s" % level
            list_fields.append(lfield)
            #report_fields.append(lfield)
            text_fields.append(lfield)

        list_fields += [(T("Address"), "location_id$addr_street"),
                        "phone",
                        #"email",
                        ]

        # Filter widgets
        filter_widgets = [
            S3TextFilter(text_fields,
                         label = T("Search"),
                         #_class = "filter-search",
                         ),
            #S3OptionsFilter("organisation_id",
            #                #hidden = True,
            #                #label = T("Organization"),
            #                # Doesn't support l10n
            #                #represent = "%(name)s",
            #                ),
            S3LocationFilter("location_id",
                             #hidden = True,
                             #label = T("Location"),
                             levels = levels,
                             ),
            ]

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("name",),
                                                 secondary = ("organisation_id",),
                                                 ),
                       filter_widgets = filter_widgets,
                       list_fields = list_fields,
                       super_entity = ("pr_pentity", "org_site", "doc_entity"),
                       update_realm = True,
                       )

        self.set_method("fire", "station",
                        method = "vehicle_report",
                        action = self.vehicle_report,
                        )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        #
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def vehicle_report(r, **attr):
        """
            Custom method to provide a report on Vehicle Deployment Times
            - this is one of the main tools currently used to manage an Incident
        """

        rheader = attr.get("rheader", None)
        if rheader:
            rheader = rheader(r)

        station_id = r.id
        if station_id:

            T = current.T
            s3db = current.s3db
            ftable = s3db.fire_station
            atable = s3db.asset_asset
            eatable = s3db.event_asset
            itable = s3db.event_incident

            query = (ftable.id == station_id) & \
                    (ftable.site_id == atable.site_id) & \
                    (atable.type == 1) & \
                    (atable.id == eatable.asset_id) & \
                    (eatable.start_date != None) & \
                    (eatable.end_date == None)

            current.response.s3.crud_strings["event_asset"] = Storage(
                title_report = T("Vehicle Deployment Times"),
            )

            eatable.asset_id.label = T("Vehicle")

            # Add field method for minutes
            def minutes(row):
                if hasattr(row, "event_asset"):
                    row = row.event_asset
                if hasattr(row, "start_date") and row.start_date:
                    return int((r.utcnow - row.start_date).total_seconds() / 60)
                else:
                    return 0
            from gluon import Field
            eatable.minutes = Field.Method("minutes",
                                           minutes,
                                           )
            s3db.configure("event_asset",
                           extra_fields = ["start_date"],
                           )

            from s3 import S3Report
            req = r.factory(prefix = "event",
                            name = "asset",
                            args = ["report"],
                            vars = Storage(rows = "asset_id",
                                           cols = "incident_id",
                                           fact = "sum(minutes)",
                                           ),
                            )
            req.set_handler("report", S3Report())
            req.resource.add_filter(query)
            return req(rheader = rheader)

# END =========================================================================
