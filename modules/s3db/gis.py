# -*- coding: utf-8 -*-

""" Sahana Eden GIS Model

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

from __future__ import division

__all__ = ("S3LocationModel",
           "S3LocationNameModel",
           "S3LocationTagModel",
           "S3LocationGroupModel",
           "S3LocationHierarchyModel",
           "S3GISConfigModel",
           "S3LayerEntityModel",
           "S3FeatureLayerModel",
           "S3MapModel",
           "S3GISThemeModel",
           "S3PoIModel",
           "S3PoIOrganisationGroupModel",
           "S3PoIFeedModel",
           "gis_location_filter",
           "gis_LocationRepresent",
           "gis_layer_represent",
           "gis_rheader",
           )

import json
import os

from collections import OrderedDict

from gluon import *
from gluon.storage import Storage

from ..s3 import *
from s3compat import BytesIO, basestring
from s3layouts import S3PopupLink

# Compact JSON encoding
SEPARATORS = (",", ":")

# =============================================================================
class S3LocationModel(S3Model):
    """
        Locations model
    """

    names = ("gis_location",
             #"gis_location_error",
             "gis_location_id",
             "gis_country_id",
             "gis_country_requires",
             "gis_country_code_represent",
             "gis_location_represent",
             "gis_location_onvalidation",
             "gis_feature_type_opts",
             )

    def model(self):

        T = current.T
        db = current.db
        messages = current.messages
        settings = current.deployment_settings
        NONE = messages["NONE"]

        # Shortcuts
        #define_table = self.define_table

        # ---------------------------------------------------------------------
        # Locations
        #
        #  A set of Coordinates &/or Address
        #
        gis_feature_type_opts = {0: T("None"),
                                 1: "Point",
                                 2: "LineString",
                                 3: "Polygon",
                                 4: "MultiPoint",
                                 5: "MultiLineString",
                                 6: "MultiPolygon",
                                 7: "GeometryCollection",
                                 #8: "CircularString",
                                 #9: "CompoundCurve",
                                 #10: "CurvePolygon",
                                 #11: "MultiCurve",
                                 #12: "MultiSurface",
                                 #13: "Curve",
                                 #14: "Surface",
                                 #15: "PolyhedralSurface",
                                 #16: "TIN",
                                 #17: "Triangle",
                                 }

        hierarchy_level_keys = current.gis.hierarchy_level_keys

        if settings.get_gis_spatialdb():
            # Add a spatial field
            # Should we do a test to confirm this? Ideally that would be done only in eden_update_check
            meta_spatial_fields = (s3_meta_fields() + (Field("the_geom", "geometry()",
                                                             readable=False, writable=False),))
        else:
            meta_spatial_fields = (s3_meta_fields())

        gis_location_represent = gis_LocationRepresent(show_link = True)

        tablename = "gis_location"
        self.define_table(tablename,
            Field("name", length=128,
                  label = T("Name"),
                  # Placenames don't have to be unique.
                  # Waypoints don't need to have a name at all.
                  requires = IS_LENGTH(128),
                  ),
            Field("level", length=2,
                  label = T("Level"),
                  represent = self.gis_level_represent,
                  requires = IS_EMPTY_OR(IS_IN_SET(hierarchy_level_keys)),
                  ),
            Field("parent", "reference gis_location", # This form of hierarchy may not work on all Databases
                  label = T("Parent"),
                  ondelete = "RESTRICT",
                  represent = gis_location_represent,
                  widget = S3LocationAutocompleteWidget(level=hierarchy_level_keys),
                  ),
            # Materialised Path
            Field("path", length=256,
                  readable = False,
                  writable = False,
                  ),
            Field("gis_feature_type", "integer", notnull=True,
                  default = 1,
                  label = T("Feature Type"),
                  represent = lambda opt: \
                    gis_feature_type_opts.get(opt,
                                              messages.UNKNOWN_OPT),
                  requires = IS_IN_SET(gis_feature_type_opts,
                                       zero=None),
                  ),
            # Points or Centroid for Polygons
            Field("lat", "double",
                  label = T("Latitude"),
                  requires = IS_EMPTY_OR(IS_LAT()),
                  comment = DIV(_class="tooltip",
                                _id="gis_location_lat_tooltip",
                                _title="%s|%s|%s|%s|%s|%s" % \
                                (T("Latitude & Longitude"),
                                 T("Latitude is North - South (Up-Down)."),
                                 T("Longitude is West - East (sideways)."),
                                 T("Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere."),
                                 T("Longitude is zero on the prime meridian (through Greenwich, United Kingdom) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas."),
                                 T("These need to be added in Decimal Degrees."))),
                  ),
            Field("lon", "double",
                  label = T("Longitude"),
                  requires = IS_EMPTY_OR(IS_LON()),
                  ),
            # Required until Shapely/Geos/GeoJSON support CIRCULARSTRING
            Field("radius", "double",
                  label = T("Radius"),
                  # Only used for CAP currently
                  readable = False,
                  writable = False,
                  comment = "m",
                  ),
            Field("wkt", "text",
                  label = "WKT (Well-Known Text)",
                  represent = self.gis_wkt_represent,
                  # Full WKT validation is done in the onvalidation callback
                  # - all we do here is allow longer fields than the default (2 ** 16)
                  # - this size handles the standard USA_L0
                  requires = IS_LENGTH(2 ** 27),
                  ),
            Field("inherited", "boolean",
                  default = False,
                  label = T("Mapped?"),
                  represent = lambda v: T("No") if v else T("Yes"),
                  writable = False,
                  ),
            # Bounding box
            Field("lat_min", "double",
                  readable = False,
                  writable = False,
                  ),
            Field("lat_max", "double",
                  readable = False,
                  writable = False,
                  ),
            Field("lon_min", "double",
                  readable = False,
                  writable = False,
                  ),
            Field("lon_max", "double",
                  readable = False,
                  writable = False,
                  ),
            # m in height above WGS84 ellipsoid (approximately sea-level).
            Field("elevation", "double",
                  readable = False,
                  writable = False,
                  ),
            # Street Address (other address fields come from hierarchy)
            Field("addr_street", "text",
                  label = T("Street Address"),
                  represent = lambda v: v or NONE,
                  ),
            Field("addr_postcode", length=128,
                  label = settings.get_ui_label_postcode(),
                  represent = lambda v: v or NONE,
                  requires = IS_LENGTH(128),
                  ),
            s3_date("start_date",
                    label = T("Start Date"),
                    ),
            s3_date("end_date",
                    label = T("End Date"),
                    ),
            s3_comments(),
            Field("L5",
                  represent = lambda v: v or NONE,
                  readable = False,
                  writable = False,
                  ),
            Field("L4",
                  represent = lambda v: v or NONE,
                  readable = False,
                  writable = False,
                  ),
            Field("L3",
                  represent = lambda v: v or NONE,
                  readable = False,
                  writable = False,
                  ),
            Field("L2",
                  represent = lambda v: v or NONE,
                  readable = False,
                  writable = False,
                  ),
            Field("L1",
                  represent = lambda v: v or NONE,
                  readable = False,
                  writable = False,
                  ),
            Field("L0",
                  #label=current.messages.COUNTRY,
                  represent = lambda v: v or NONE,
                  readable = False,
                  writable = False,
                  ),
            *meta_spatial_fields,
            on_define = lambda table: \
                [# Doesn't set parent properly when field is defined inline as the table isn't yet in db
                 table._create_references(),

                 # Default the owning role to Authenticated. This can be used to allow the site
                 # to control whether authenticated users get to create / update locations, or
                 # just read them. Having an owner and using ACLs also allows us to take away
                 # privileges from generic Authenticated users for particular locations (like
                 # hierarchy or region locations) by changing the owner on those locations, e.g.
                 # to MapAdmin.
                 table.owned_by_group.set_attributes(default = current.session.s3.system_roles.AUTHENTICATED),

                 # Can't be defined in-line as otherwise get a circular reference
                 table.parent.set_attributes(requires = IS_EMPTY_OR(
                                               IS_ONE_OF(db, "gis_location.id",
                                                         gis_location_represent,
                                                         # @ToDo: If level is known, filter on higher than that?
                                                         # If strict, filter on next higher level?
                                                         filterby="level",
                                                         filter_opts=hierarchy_level_keys,
                                                         orderby="gis_location.name"))),
                 ]
            )

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = messages.ADD_LOCATION,
            title_display = T("Location Details"),
            title_list = T("Locations"),
            title_update = T("Edit Location"),
            title_upload = T("Import Locations"),
            label_list_button = T("List Locations"),
            label_delete_button = T("Delete Location"),
            msg_record_created = T("Location added"),
            msg_record_modified = T("Location updated"),
            msg_record_deleted = T("Location deleted"),
            msg_list_empty = T("No Locations currently available"))

        # Reusable field to include in other table definitions
        location_id = S3ReusableField("location_id", "reference %s" % tablename,
                                      label = T("Location"),
                                      ondelete = "RESTRICT",
                                      represent = gis_location_represent,
                                      requires = IS_EMPTY_OR(IS_LOCATION()),
                                      sortby = "name",
                                      widget = S3LocationSelector(show_address = True,
                                                                  ),
                                      # Alternate simple Autocomplete (e.g. used by pr_person_presence)
                                      #requires = IS_EMPTY_OR(IS_LOCATION()),
                                      #widget = S3LocationAutocompleteWidget(),
                                      )

        represent = S3Represent(lookup=tablename, translate=True)
        country_requires = IS_EMPTY_OR(IS_ONE_OF(db, "gis_location.id",
                                                 represent,
                                                 filterby = "level",
                                                 filter_opts = ["L0"],
                                                 sort=True))
        country_id = S3ReusableField("location_id", "reference %s" % tablename,
                                     label = messages.COUNTRY,
                                     ondelete = "RESTRICT",
                                     represent = represent,
                                     requires = country_requires,
                                     sortby = "name",
                                     widget = S3MultiSelectWidget(multiple=False),
                                     )

        list_fields = ["id",
                       "name",
                       "level",
                       "L0",
                       "L1",
                       "L2",
                       "L3",
                       "L4",
                       "inherited",
                       #"lat",
                       #"lon",
                       "start_date",
                       "end_date",
                       ]
        position = 2
        if settings.get_L10n_translate_gis_location():
            list_fields.insert(position, "name.name_l10n")
            position += 1
        if settings.get_L10n_name_alt_gis_location():
            list_fields.insert(position, "name_alt.name_alt")

        self.configure(tablename,
                       context = {"location": "parent",
                                  },
                       deduplicate = self.gis_location_duplicate,
                       list_fields = list_fields,
                       list_orderby = "gis_location.name",
                       onaccept = self.gis_location_onaccept,
                       onvalidation = self.gis_location_onvalidation,
                       )

        # Custom Method for S3LocationAutocompleteWidget
        self.set_method("gis", "location",
                        method = "search_ac",
                        action = self.gis_search_ac)

        # Components
        self.add_components(tablename,
                            # Tags
                            gis_location_tag = {"name": "tag",
                                                "joinby": "location_id",
                                                },
                            # Names
                            gis_location_name = {"name": "name",
                                                 "joinby": "location_id",
                                                 },
                            # Alternate Names
                            gis_location_name_alt = {"name": "name_alt",
                                                     "joinby": "location_id",
                                                     },
                            # Child Locations
                            #gis_location = {"joinby": "parent",
                            #                "multiple": False,
                            #                },

                            # Regions
                            org_region_country = {"name": "region",
                                                  "joinby": "location_id",
                                                  },

                            # Sites
                            org_site = "location_id",

                            # Tenures
                            stdm_tenure = "location_id",
                            )

        # ---------------------------------------------------------------------
        # Error
        # - needed for COT support
        #
        # tablename = "gis_location_error"
        # define_table(tablename,
                        # location_id(),
                        ##Circular 'Error' around Lat/Lon (in m).
                        # Field("ce", "integer",
                            # writable=False,
                            # readable=False),
                        ##Linear 'Error' for the Elevation (in m).
                        # Field("le", "integer",
                            # writable=False,
                            # readable=False),
                        # s3_comments(),
                        # *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {"gis_location_id": location_id,
                "gis_country_id": country_id,
                "gis_country_requires": country_requires,
                "gis_country_code_represent": self.gis_country_code_represent,
                "gis_location_represent": gis_location_represent,
                "gis_location_onvalidation": self.gis_location_onvalidation,
                "gis_feature_type_opts": gis_feature_type_opts,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_country_code_represent(code):
        """ FK representation """

        if not code:
            return current.messages["NONE"]

        return current.gis.get_country(code, key_type="code") or \
               current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_location_onaccept(form):
        """
            On Accept for GIS Locations (after DB I/O)
        """

        auth = current.auth
        form_vars_get = form.vars.get
        location_id = form_vars_get("id")

        if form_vars_get("path") and current.response.s3.bulk:
            # Don't import path from foreign sources as IDs won't match
            db = current.db
            db(db.gis_location.id == location_id).update(path = None)

        if not auth.override and \
           not auth.rollback:
            # Update the Path (async if-possible)
            # (skip during prepop)
            feature = json.dumps({"id": location_id,
                                  "level": form_vars_get("level", False),
                                  })
            current.s3task.run_async("gis_update_location_tree",
                                     args = [feature],
                                     )

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_location_onvalidation(form):
        """
            On Validation for GIS Locations (before DB I/O)
        """

        T = current.T
        db = current.db
        gis = current.gis
        auth = current.auth
        response = current.response
        settings = current.deployment_settings
        s3 = response.s3

        form_vars = form.vars
        vars_get = form_vars.get

        level = vars_get("level", None)
        parent = vars_get("parent", None)
        lat = vars_get("lat", None)
        lon = vars_get("lon", None)
        addr_street = vars_get("addr_street", None)

        bulk = s3.bulk

        if addr_street and lat is None and lon is None and bulk:

            geocoder = settings.get_gis_geocode_imported_addresses()
            if geocoder:
                # Geocode imported addresses
                postcode = vars_get("postcode", None)
                # Build Path (won't be populated yet). Note get_parents will not
                # construct the path during prepopulate. Updating the location
                # tree is deferred til after the prepopulate data is loaded.
                if parent:
                    Lx_ids = gis.get_parents(parent, ids_only=True)
                    if Lx_ids:
                        Lx_ids.append(parent)
                    else:
                        Lx_ids = [parent]
                else:
                    Lx_ids = None
                results = gis.geocode(addr_street, postcode, Lx_ids)
                if isinstance(results, basestring):
                    # Error
                    if settings.get_gis_ignore_geocode_errors():
                        # Just Warn
                        current.log.warning("Geocoder: %s" % results)
                    elif auth.override and \
                         not settings.get_gis_check_within_parent_boundaries():
                        # Just Warn
                        current.log.warning("Geocoder: %s" % results)
                    else:
                        # Make this check mandatory
                        form.errors["addr_street"] = results
                        return
                else:
                    form_vars.lon = lon = results["lon"]
                    form_vars.lat = lat = results["lat"]

        if lon:
            if lon > 180:
                # Map Selector wrapped
                form_vars.lon = lon = lon - 360
            elif lon < -180:
                # Map Selector wrapped
                form_vars.lon = lon = lon + 360

        # 'MapAdmin' has permission to edit hierarchy locations, no matter what
        # 000_config or the ancestor country's gis_config has.
        MAP_ADMIN = auth.s3_has_role(current.session.s3.system_roles.MAP_ADMIN)
        if not MAP_ADMIN:
            if level:
                editable = level != "L0"
                if editable and level in gis.hierarchy_level_keys:
                    if level == "L1" and not parent:
                        response.error = error = T("L1 locations need to be within a Country")
                        form.errors["level"] = error
                        return
                    # Check whether the country config allows us to edit this location
                    # id doesn't exist for create forms and parent is a quicker check anyway when available
                    child = parent or current.request.vars.get("id", None)
                    editable = gis_hierarchy_editable(level, child)
                if not editable and not s3.synchronise_uuids: # Allow Editing of UUIDs during Sync
                    response.error = T("Sorry, only users with the MapAdmin role are allowed to edit these locations")
                    form.errors["level"] = T("This level is not open for editing.")
                    return

        if parent:
            table = db.gis_location
            _parent = db(table.id == parent).select(table.level,
                                                    limitby=(0, 1)).first()

        # Check Parents are in sane order
        if level and parent and _parent:
            # Check that parent is of a higher level
            if level[1:] < _parent.level[1:]:
                response.error = "%s: %s" % (T("Parent level should be higher than this record's level. Parent level is"),
                                             gis.get_location_hierarchy()[_parent.level])
                form.errors["level"] = T("Level is higher than parent's")
                return
        strict = gis.get_strict_hierarchy()
        if strict:
            if level == "L0":
                # Parent is impossible
                parent = ""
            elif not parent:
                # Parent is mandatory
                response.error = "%s: %s" % \
                    (T("Parent needs to be set for locations of level"),
                    gis.get_location_hierarchy()[level])
                form.errors["parent"] = T("Parent needs to be set")
                return
            elif not level:
                # Parents needs to be of level max_hierarchy
                max_hierarchy = gis.get_max_hierarchy_level()
                if _parent.level != max_hierarchy:
                    response.error = "%s: %s" % \
                        (T("Specific locations need to have a parent of level"),
                        gis.get_location_hierarchy()[max_hierarchy])
                    form.errors["parent"] = T("Parent needs to be of the correct level")
                    return
            else:
                # Check that parent is of exactly next higher order
                if (int(level[1:]) - 1) != int(_parent.level[1:]):
                    response.error = "%s: %s" % \
                        (T("Locations of this level need to have a parent of level"),
                        gis.get_location_hierarchy()["L%i" % (int(level[1:]) - 1)])
                    form.errors["parent"] = T("Parent needs to be of the correct level")
                    return

        if level != "L0":
            # Check within permitted bounds
            # (avoid incorrect data entry)
            # Points only for now
            if not "gis_feature_type" in form_vars or (form_vars.gis_feature_type == "1"):
                #if lat not in (None, "") and lon not in (None, ""):
                if lat and lon:
                    name = form_vars.name
                    if parent and settings.get_gis_check_within_parent_boundaries():
                        # Check within Bounds of the Parent if possible.
                        # Rough (Bounding Box)
                        # During prepopulate, the location tree update is
                        # disabled. This is what propagates location and bounds
                        # down the hierarchy so the parent may not have bounds.
                        # Prepopulate data should be prepared to be correct.
                        lat_min, lon_min, lat_max, lon_max, parent_name = \
                                        gis.get_parent_bounds(parent=parent)
                        if (lat > lat_max) or (lat < lat_min):
                            lat_error = T("Latitude %(lat)s is invalid, should be between %(lat_min)s & %(lat_max)s") % \
                                {"lat": lat, "lat_min": lat_min, "lat_max": lat_max}
                            form.errors["lat"] = lat_error
                        if (lon > lon_max) or (lon < lon_min):
                            lon_error = T("Longitude %(lon)s is invalid, should be between %(lon_min)s & %(lon_max)s") % \
                                {"lon": lon, "lon_min": lon_min, "lon_max": lon_max}
                            form.errors["lon"] = lon_error
                        if form.errors:
                            if name:
                                error = T("Sorry location %(location)s appears to be outside the area of parent %(parent)s.") % \
                                    {"location": name, "parent": parent_name}
                            else:
                                error = T("Sorry location appears to be outside the area of parent %(parent)s.") % \
                                    {"parent": parent_name}
                            response.error = error
                            current.log.error(error)
                            return

                        # @ToDo: Precise (GIS function)
                        # (if using PostGIS then don't do a separate BBOX check as this is done within the query)

                    else:
                        # Check bounds for the Instance
                        config = gis.get_config()
                        if config.lat_min is not None:
                            lat_min = config.lat_min
                        else:
                            lat_min = -90
                        if config.lon_min is not None:
                            lon_min = config.lon_min
                        else:
                            lon_min = -180
                        if config.lat_max is not None:
                            lat_max = config.lat_max
                        else:
                            lat_max = 90
                        if config.lon_max is not None:
                            lon_max = config.lon_max
                        else:
                            lon_max = 180
                        if (lat > lat_max) or (lat < lat_min):
                            if name:
                                error = T("Sorry location %(location)s appears to be outside the area supported by this deployment.") % \
                                    {"location": name}
                            else:
                                error = T("Sorry location appears to be outside the area supported by this deployment.")
                            response.error = error
                            current.log.error(error)
                            lat_error =  T("Latitude %(lat)s is invalid, should be between %(lat_min)s & %(lat_max)s") % \
                                {"lat": lat, "lat_min": lat_min, "lat_max": lat_max}
                            form.errors["lat"] = lat_error
                            current.log.error(lat_error)
                            return
                        elif (lon > lon_max) or (lon < lon_min):
                            if name:
                                error = T("Sorry location %(location)s appears to be outside the area supported by this deployment.") % \
                                    {"location": name}
                            else:
                                error = T("Sorry location appears to be outside the area supported by this deployment.")
                            response.error = error
                            current.log.error(error)
                            lon_error = T("Longitude %(lon)s is invalid, should be between %(lon_min)s & %(lon_max)s") % \
                                {"lon": lon, "lon_min": lon_min, "lon_max": lon_max}
                            form.errors["lon"] = lon_error
                            current.log.error(lon_error)
                            return

        # Add the WKT, bounds (& Centroid for Polygons)
        gis.wkt_centroid(form)

        # The original record
        record = form.record

        if form_vars.wkt and not form_vars.wkt[:3] == "POI":

            # Only POINTs can be inherited (but not POLYGONs)
            form_vars.inherited = False


        elif bulk:
            # Bulk import: can not check for wkt change here because
            # wkt not loaded during imports for better performance =>
            # instead, check whether import item has lat and lon:
            if form_vars.lat not in (None, "") and \
               form_vars.lon not in (None, ""):
                form_vars.inherited = False

        elif record and hasattr(record, "inherited") and record.inherited:
            # Have we provided more accurate data?
            if hasattr(record, "wkt") and form_vars.wkt != record.wkt:
                form_vars.inherited = False

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_location_duplicate(item):
        """
          This callback will be called when importing location records it will look
          to see if the record being imported is a duplicate.

          @param item: An S3ImportItem object which includes all the details
                       of the record being imported

          If the record is a duplicate then it will set the item method to update

          Rules for finding a duplicate:
           - If there is no level, then deduplicate based on the address
           - Look for a record with the same name, ignoring case
           - If no match, also check name_l10n
           - If parent exists in the import, the same parent
           - If start_date exists in the import, the same start_date
           - If end_date exists in the import, the same end_date

            @ToDo: Check soundex? (only good in English)
                   http://eden.sahanafoundation.org/ticket/481
                   - make a deployment_setting for relevant function?
        """

        data = item.data
        name = data.get("name")

        if not name:
            return

        level = data.get("level")
        if not level:
            address = data.get("addr_street")
            if not address:
                # Don't deduplicate precise locations as hard to ensure these have unique names
                return
            table = item.table
            query = (table.addr_street == address) & \
                    (table.deleted != True)
            postcode = data.get("addr_postcode")
            if postcode:
                query &= (table.addr_postcode == postcode)
            parent = data.get("parent")
            if parent:
                query &= (table.parent == parent)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
            return

        # Don't try to update Countries
        MAP_ADMIN = current.auth.s3_has_role(current.session.s3.system_roles.MAP_ADMIN)
        if level == "L0":
            item.method = None
            if not MAP_ADMIN:
                item.skip = True
            return

        def skip(level, location_id):
            if not MAP_ADMIN:
                return not gis_hierarchy_editable(level, location_id)
            return False

        table = item.table

        settings = current.deployment_settings
        if settings.get_database_type() == "postgres":
            # None is last
            orderby = ~table.end_date
        else:
            # None is 1st
            orderby = table.end_date

        code = settings.get_gis_lookup_code()
        if code:
            # The name is a Code
            kv_table = current.s3db.gis_location_tag
            query = (kv_table.tag == code) & \
                    (kv_table.value == name) & \
                    (kv_table.location_id == table.id)
            duplicate = current.db(query).select(table.id,
                                                 table.name,
                                                 table.level,
                                                 orderby=orderby,
                                                 limitby=(0, 1)).first()

            if duplicate:
                # @ToDo: Import Log
                #current.log.debug("Location PCode Match")
                data.name = duplicate.name # Don't update the name with the code
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
                item.skip = skip(duplicate.level, duplicate.id)
                return

        parent = data.get("parent")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # @ToDo: check the the lat and lon if they exist?
        #lat = "lat" in data and data.lat
        #lon = "lon" in data and data.lon

        # Try the Name
        # @ToDo: Hook for possible duplicates vs definite?
        #query = (table.name.lower().like('%%%s%%' % name.lower()))

        if current.deployment_settings.get_database_type() == "postgres":
            # Python lower() only works properly on Unicode strings not UTF-8 encoded strings
            # Oddity:
            # Python lower() converts the TR char İ to i (Correctly, according to http://www.fileformat.info/info/unicode/char/0130/index.htm)
            # PostgreSQL LOWER() on Windows doesn't convert it, although this seems to be a locale issue:
            # http://stackoverflow.com/questions/18507589/the-lower-function-on-international-characters-in-postgresql
            # Works fine on Debian servers if the locale is a .UTF-8 before the Postgres cluster is created
            query = (table.name.lower() == s3_unicode(name).lower().encode("utf8")) & \
                    (table.level == level)
        else :
            query = (table.name.lower() == name.lower()) & \
                    (table.level == level)

        if parent:
            query &= (table.parent == parent)
        if end_date:
            query &= (table.end_date == end_date)
        if start_date:
            query &= ((table.start_date == start_date) | \
                      (table.end_date == None))

        duplicate = current.db(query).select(table.id,
                                             table.level,
                                             orderby=orderby,
                                             limitby=(0, 1)).first()
        if duplicate:
            # @ToDo: Import Log
            #current.log.debug("Location Match")
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE
            item.skip = skip(duplicate.level, duplicate.id)
            return

        elif current.deployment_settings.get_L10n_translate_gis_location():
            # See if this a name_l10n
            ltable = current.s3db.gis_location_name
            query = (ltable.name_l10n == name) & \
                    (ltable.location_id == table.id) & \
                    (table.level == level)
            if parent:
                query &= (table.parent == parent)
            if end_date:
                query &= (table.end_date == end_date)
            if start_date:
                query &= (table.start_date == start_date)

            duplicate = current.db(query).select(table.id,
                                                 table.name,
                                                 table.level,
                                                 orderby=orderby,
                                                 limitby=(0, 1)).first()
            if duplicate:
                # @ToDo: Import Log
                #current.log.debug("Location l10n Match")
                data.name = duplicate.name # Don't update the name
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
                item.skip = skip(duplicate.level, duplicate.id)
            else:
                # @ToDo: Import Log
                #current.log.debug("No Match", name)
                pass

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_level_represent(level):
        if not level:
            return current.messages["NONE"]
        elif level == "L0":
            return current.messages.COUNTRY
        else:
            gis = current.gis
            config = gis.get_config()
            if config.default_location_id:
                # Single country deployment so we can provide a nice name reliably
                # @ToDo: Maybe not any longer
                return gis.get_all_current_levels(level)
            else:
                # The representation of a level can vary per-record (since it varies per country),
                # however we have no way of knowing the country here, so safest not to give a wrong answer.
                return level

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_wkt_represent(wkt, max_length=30):
        if not wkt:
            # Blank WKT field
            return None
        elif len(wkt) > max_length:
            return "%s(...)" % wkt[0:wkt.index("(")]
        else:
            return wkt

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_search_ac(r, **attr):
        """
            JSON search method for S3LocationAutocompleteWidget
            - adds hierarchy support

            @param r: the S3Request
            @param attr: request attributes
        """

        output = None
        response = current.response
        resource = r.resource
        table = r.resource.table
        settings = current.deployment_settings

        # Query comes in pre-filtered to accessible & deletion_status
        # Respect response.s3.filter
        resource.add_filter(response.s3.filter)

        # Filter out old Locations
        # @ToDo: Allow override
        resource.add_filter(table.end_date == None)

        _vars = current.request.get_vars

        limit = int(_vars.limit or 0)

        # JQueryUI Autocomplete uses "term"
        # old JQuery Autocomplete uses "q"
        # what uses "value"?
        value = _vars.term or _vars.value or _vars.q or None

        if not value:
            r.error(400, "Missing query variable")

        # We want to do case-insensitive searches
        # (default anyway on MySQL/SQLite, but not PostgreSQL)
        value = s3_unicode(value).lower().strip()

        search_l10n = None
        translate = None
        name_alt = settings.get_L10n_name_alt_gis_location()

        loc_select = _vars.get("loc_select", None)
        if loc_select:
            # S3LocationSelectorWidget
            # @todo: obsolete?
            fields = ["id",
                      "name",
                      ]
        else:
            # S3LocationAutocompleteWidget
            # Vulnerability Search
            fields = ["id",
                      "name",
                      "level",
                      "L1",
                      "L2",
                      "L3",
                      "L4",
                      "L5",
                      ]
            multi_country = len(current.deployment_settings.get_gis_countries()) != 1
            if multi_country:
                fields.append("L0")
            if settings.get_L10n_translate_gis_location():
                search_l10n = True
                language = current.session.s3.language
                if language != current.deployment_settings.get_L10n_default_language():
                    translate = True
                    fields.append("path")

        children = _vars.get("children", None)
        if children:
            if children == "null":
                children = None
            else:
                children = int(children)

        level = _vars.get("level", None)
        if level:
            if level == "null":
                level = None
            elif "|" in level:
                level = level.split("|")
            else:
                level = str.upper(level)

        if children:
            # LocationSelector
            children = current.gis.get_children(children, level=level)
            children = children.find(lambda row: \
                                     row.name and value in str.lower(row.name))
            output = children.json()
            response.headers["Content-Type"] = "application/json"
            return output

        query = FS("name").lower().like(value + "%")
        field2 = _vars.get("field2", None)
        if field2:
            # S3LocationSelectorWidget's s3_gis_autocomplete_search
            # addr_street
            # @todo: obsolete?
            fieldname = str.lower(field2)
            fields.append(fieldname)
            query |= FS(fieldname).lower().like(value + "%")
        elif loc_select:
            fields.append("level")
            fields.append("parent")
        else:
            if search_l10n:
                query |= FS("name.name_l10n").lower().like(value + "%")
                fields.append("name.name_l10n")
            if name_alt:
                query |= FS("name_alt.name_alt").lower().like(value + "%")
                fields.append("name_alt.name_alt")

        resource.add_filter(query)

        if level:
            # LocationSelector or Autocomplete
            if isinstance(level, list):
                query = (table.level.belongs(level))
            elif level == "NULLNONE":
                # S3LocationSelectorWidget's s3_gis_autocomplete_search
                # @todo: obsolete?
                query = (table.level == None)
            elif level == "NOTNONE":
                # Vulnerability Search
                query = (table.level != None)
            else:
                query = (table.level == level)
        else:
            # Filter out poor-quality data, such as from Ushahidi
            query = (table.level != "XX")

        resource.add_filter(query)

        parent = _vars.get("parent", None)
        if parent:
            # LocationSelector
            query = (table.parent == int(parent))
            resource.add_filter(query)

        MAX_SEARCH_RESULTS = current.deployment_settings.get_search_max_results()
        if (not limit or limit > MAX_SEARCH_RESULTS) and \
           resource.count() > MAX_SEARCH_RESULTS:
            output = json.dumps([
                {"label": s3_str(current.T("There are more than %(max)s results, please input more characters.") % \
                    {"max": MAX_SEARCH_RESULTS})}
                ], separators=SEPARATORS)

        elif loc_select:
            # LocationSelector
            # @ToDo: Deprecate
            from s3.s3export import S3Exporter
            output = S3Exporter().json(resource,
                                       start=0,
                                       limit=limit,
                                       fields=fields,
                                       orderby=table.name)
        else:
            # S3LocationAutocompleteWidget
            # Vulnerability Search
            rows = resource.select(fields=fields,
                                   start=0,
                                   limit=limit,
                                   orderby="gis_location.name")["rows"]
            if translate:
                # Lookup Translations
                s3db = current.s3db
                l10n_table = s3db.gis_location_name
                l10n_query = (l10n_table.deleted == False) & \
                             (l10n_table.language == language)
                ids = []
                for row in rows:
                    path = row["gis_location.path"]
                    if not path:
                        path = current.gis.update_location_tree(row["gis_location"])
                    ids += path.split("/")
                # Remove Duplicates
                ids = set(ids)
                l10n_query &= (l10n_table.location_id.belongs(ids))
                limitby = (0, len(ids))
                l10n = current.db(l10n_query).select(l10n_table.location_id,
                                                     l10n_table.name_l10n,
                                                     limitby = limitby,
                                                     ).as_dict(key="location_id")
            items = []
            iappend = items.append
            for row in rows:
                item = {"id" : row["gis_location.id"],
                        }
                level = row.get("gis_location.level", None)
                if level:
                    item["level"] = level
                if translate:
                    path = row["gis_location.path"]
                    ids = path.split("/")
                    loc = l10n.get(int(ids.pop()), None)
                    if loc:
                        item["name"] = loc["name_l10n"]
                    else:
                        item["name"] = row["gis_location.name"]
                else:
                    item["name"] = row["gis_location.name"]
                L5 = row.get("gis_location.L5", None)
                if L5 and level != "L5":
                    if translate:
                        loc = l10n.get(int(ids.pop()), None)
                        if loc:
                            item["L5"] = loc["name_l10n"]
                        else:
                            item["L5"] = L5
                    else:
                        item["L5"] = L5
                L4 = row.get("gis_location.L4", None)
                if L4 and level != "L4":
                    if translate:
                        loc = l10n.get(int(ids.pop()), None)
                        if loc:
                            item["L4"] = loc["name_l10n"]
                        else:
                            item["L4"] = L4
                    else:
                        item["L4"] = L4
                L3 = row.get("gis_location.L3", None)
                if L3 and level != "L3":
                    if translate:
                        loc = l10n.get(int(ids.pop()), None)
                        if loc:
                            item["L3"] = loc["name_l10n"]
                        else:
                            item["L3"] = L3
                    else:
                        item["L3"] = L3
                L2 = row.get("gis_location.L2", None)
                if L2 and level != "L2":
                    if translate:
                        loc = l10n.get(int(ids.pop()), None)
                        if loc:
                            item["L2"] = loc["name_l10n"]
                        else:
                            item["L2"] = L2
                    else:
                        item["L2"] = L2
                L1 = row.get("gis_location.L1", None)
                if L1 and level != "L1":
                    if translate:
                        loc = l10n.get(int(ids.pop()), None)
                        if loc:
                            item["L1"] = loc["name_l10n"]
                        else:
                            item["L1"] = L1
                    else:
                        item["L1"] = L1
                L0 = row.get("gis_location.L0", None)
                if L0 and level != "L0":
                    if translate:
                        loc = l10n.get(int(ids.pop()), None)
                        if loc:
                            item["L0"] = loc["name_l10n"]
                    else:
                        item["L0"] = L0

                _name_alt = row.get("gis_location_name_alt.name_alt", None)
                _name_l10n = row.get("gis_location_name.name_l10n", None)
                if isinstance(_name_alt, basestring):
                    # Convert into list
                    _name_alt = [ _name_alt ]
                if isinstance(_name_l10n, basestring):
                    _name_l10n = [ _name_l10n ]

                alternate = dict(item)
                location_names = []
                l = len(value)

                if _name_alt:
                    location_names += _name_alt
                if _name_l10n:
                    location_names += _name_l10n

                # Check for matches in other(if any) names
                alternate.pop("name", None)
                for name in location_names:
                    _alternate = dict(alternate)
                    if name[:l].lower() == value:
                        # Insert other possible names, if matched
                        _alternate["name"] = name
                        # Populate match information
                        s3_set_match_strings(_alternate, value)
                        iappend(_alternate)

                if item["name"][:l].lower() == value:
                    # Include Actual name also, if matched
                    s3_set_match_strings(item, value)
                    iappend(item)

            output = json.dumps(items, separators=SEPARATORS)

        response.headers["Content-Type"] = "application/json"
        return output

# =============================================================================
class S3LocationNameModel(S3Model):
    """
        Location Names model
        - local/alternate names for Locations
    """

    names = ("gis_location_name",
             "gis_location_name_alt",
             )

    def model(self):

        T = current.T
        configure = self.configure
        define_table = self.define_table
        location_id = self.gis_location_id

        # ---------------------------------------------------------------------
        # Local Names
        #
        tablename = "gis_location_name"
        define_table(tablename,
                     location_id(empty = False,
                                 ondelete = "CASCADE",
                                 ),
                     s3_language(empty = False),
                     Field("name_l10n",
                           label = T("Local Name"),
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("location_id",
                                                       "language",
                                                       ),
                                            ),
                  )

        # ---------------------------------------------------------------------
        # Alternate Names
        #
        # @ToDo: Include these in Search
        #
        tablename = "gis_location_name_alt"
        define_table(tablename,
                     location_id(empty = False,
                                 ondelete = "CASCADE",
                                 ),
                     Field("name_alt",
                           label = T("Alternate Name"),
                           ),
                     Field("old_name", "boolean",
                           default = False,
                           label = T("Old?"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_comments(),
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("location_id",
                                                       "name_alt",
                                                       ),
                                            ),
                  )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3LocationTagModel(S3Model):
    """
        Location Tags model
        - flexible Key-Value component attributes to Locations
    """

    names = ("gis_location_tag",
             "gis_country_opts",
             )

    def model(self):

        T = current.T

        # ---------------------------------------------------------------------
        # Location Tags
        # - Key-Value extensions
        # - can be used to identify a Source (GPS, Imagery, Wikipedia, etc)
        # - can be used to add extra attributes (e.g. Area, Population)
        # - can link Locations to other Systems, such as:
        #   * ISO2
        #   * ISO3
        #   * OpenStreetMap (although their IDs can change over time)
        #   * UN P-Codes
        #   * GeoNames
        #   * Wikipedia URL
        #   * Christchurch 'prupi'(Property reference in the council system) &
        #                  'gisratingid' (Polygon reference of the rating unit)
        # - can be a Triple Store for Semantic Web support
        #
        tablename = "gis_location_tag"
        self.define_table(tablename,
                          self.gis_location_id(empty = False,
                                               ondelete = "CASCADE",
                                               ),
                          # key is a reserved word in MySQL
                          Field("tag",
                                label = T("Key"),
                                ),
                          Field("value",
                                label = T("Value"),
                                ),
                          s3_comments(),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("location_id",
                                                            "tag",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {"gis_country_opts": self.gis_country_opts,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_country_opts(countries):
        """
            Provide the options for a Search widget
            - countries is a list of ISO2 codes
            - normally provided via settings.get_gis_countries()
        """

        db = current.db
        table = db.gis_location
        ttable = db.gis_location_tag
        query = (ttable.tag == "ISO2") & \
                (ttable.value.belongs(countries)) & \
                (ttable.location_id == table.id)
        opts = db(query).select(table.id,
                                table.name,
                                orderby=table.name)
        od = OrderedDict()
        for opt in opts:
            od[opt.id] = opt.name
        return od

# =============================================================================
class S3LocationGroupModel(S3Model):
    """
        Location Groups model
        - currently unused
    """

    names = ("gis_location_group",
             "gis_location_group_member",
             )

    def model(self):

        T = current.T

        location_id = self.gis_location_id

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Location Groups
        #
        tablename = "gis_location_group"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           ),
                     # Optional Polygon for the overall Group
                     location_id(empty = False,
                                 ondelete = "CASCADE",
                                 ),
                     s3_comments(),
                     *s3_meta_fields())

        self.add_components(tablename,
                            gis_location_group_member = "location_group_id",
                            )

        # ---------------------------------------------------------------------
        # Location Group Membership
        #
        tablename = "gis_location_group_member"
        define_table(tablename,
                     Field("location_group_id", "reference gis_location_group",
                           label = T("Location Group"),
                           ondelete = "RESTRICT",
                           ),
                     location_id(empty = False,
                                 ondelete = "CASCADE",
                                 ),
                     s3_comments(),
                     *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3LocationHierarchyModel(S3Model):
    """
        Location Hierarchy model
    """

    names = ("gis_hierarchy",
             "gis_hierarchy_form_setup",
             )

    def model(self):

        T = current.T

        # =====================================================================
        # GIS Hierarchy
        #
        # uuid=SITE_DEFAULT = Site default settings
        #

        tablename = "gis_hierarchy"
        self.define_table(tablename,
                          self.gis_country_id(),
                          Field("L1",
                                default = "State / Province",
                                ),
                          Field("L2",
                                default = "County / District",
                                ),
                          Field("L3",
                                default = "City / Town / Village",
                                ),
                          Field("L4",
                                # Default: off
                                default = "",
                                ),
                          Field("L5",
                                # Default: off
                                default = "",
                                ),
                          # Do all levels of the hierarchy need to be filled-out?
                          Field("strict_hierarchy", "boolean",
                                default = False,
                                # Currently not fully used
                                readable = False,
                                writable = False,
                                ),
                          # Do we minimally need a parent for every non-L0 location?
                          Field("location_parent_required", "boolean",
                                default = False,
                                # Currently completely unused
                                readable = False,
                                writable = False,
                                ),
                          Field("edit_L1", "boolean",
                                default = True),
                          Field("edit_L2", "boolean",
                                default = True),
                          Field("edit_L3", "boolean",
                                default = True),
                          Field("edit_L4", "boolean",
                                default = True),
                          Field("edit_L5", "boolean",
                                default = True),
                          *s3_meta_fields())

        ADD_HIERARCHY = T("Create Location Hierarchy")
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = ADD_HIERARCHY,
            title_display = T("Location Hierarchy"),
            title_list = T("Location Hierarchies"),
            title_update = T("Edit Location Hierarchy"),
            label_list_button = T("List Location Hierarchies"),
            label_delete_button = T("Delete Location Hierarchy"),
            msg_record_created = T("Location Hierarchy added"),
            msg_record_modified = T("Location Hierarchy updated"),
            msg_record_deleted = T("Location Hierarchy deleted"),
            msg_list_empty = T("No Location Hierarchies currently defined")
        )

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary=("location_id",)),
                       onvalidation = self.gis_hierarchy_onvalidation,
                       )

        # Pass names back to global scope (s3.*)
        return {"gis_hierarchy_form_setup": self.gis_hierarchy_form_setup,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_hierarchy_form_setup():
        """ Prepare the gis_hierarchy form """

        T = current.T
        table = current.db.gis_hierarchy
        table.L1.label = T("Hierarchy Level 1 Name (e.g. State or Province)")
        table.L1.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Location Hierarchy Level 1 Name"),
                T("Term for the primary within-country administrative division (e.g. State or Province).")))
        table.L2.label = T("Hierarchy Level 2 Name (e.g. District or County)")
        table.L2.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Location Hierarchy Level 2 Name"),
                T("Term for the secondary within-country administrative division (e.g. District or County).")))
        table.L3.label = T("Hierarchy Level 3 Name (e.g. City / Town / Village)")
        table.L3.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Location Hierarchy Level 3 Name"),
                T("Term for the third-level within-country administrative division (e.g. City or Town).")))
        table.L4.label = T("Hierarchy Level 4 Name (e.g. Neighbourhood)")
        table.L4.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Location Hierarchy Level 4 Name"),
                T("Term for the fourth-level within-country administrative division (e.g. Village, Neighborhood or Precinct).")))
        table.L5.label = T("Hierarchy Level 5 Name")
        table.L5.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Location Hierarchy Level 5 Name"),
                T("Term for the fifth-level within-country administrative division (e.g. a voting or postcode subdivision). This level is not often used.")))
        table.strict_hierarchy.label = T("Is this a strict hierarchy?")
        table.strict_hierarchy.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Is this a strict hierarchy?"),
                T("Select this if all specific locations need a parent at the deepest level of the location hierarchy. For example, if 'district' is the smallest division in the hierarchy, then all specific locations would be required to have a district as a parent.")))
        table.location_parent_required.label = T("Must a location have a parent location?")
        table.location_parent_required.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Must a location have a parent location?"),
                T("Select this if all specific locations need a parent location in the location hierarchy. This can assist in setting up a 'region' representing an affected area.")))
        edit_Ln_tip_1 = T("Set True to allow editing this level of the location hierarchy by users who are not MapAdmins.")
        edit_Ln_tip_2 = T("This is appropriate if this level is under construction. To prevent accidental modification after this level is complete, this can be set to False.")
        max_allowed_level_num = current.gis.max_allowed_level_num
        for n in range(1, max_allowed_level_num):
            field = "edit_L%d" % n
            table[field].label = T("Edit Level %d Locations?") % n
            table[field].comment = DIV(
                        _class="tooltip",
                        _title="%s|%s|%s" % (
                            T("Is editing level L%d locations allowed?") % n,
                            edit_Ln_tip_1,
                            edit_Ln_tip_2
                            )
                        )

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_hierarchy_onvalidation(form):
        """
            If strict, hierarchy names must not have gaps.
        """

        form_vars = form.vars

        if form_vars.strict_hierarchy:
            gis = current.gis
            hierarchy_level_keys = gis.hierarchy_level_keys
            level_names = [form_vars[key] if key in form_vars else None
                           for key in hierarchy_level_keys]
            # L0 is always missing because its label is hard-coded

            gaps = ["L%d" % n for n in range(1, gis.max_allowed_level_num)
                              if not level_names[n] and level_names[n + 1]]
            if gaps:
                hierarchy_gap = current.T("A strict location hierarchy cannot have gaps.")
                for gap in gaps:
                    form.errors[gap] = hierarchy_gap

# =============================================================================
class S3GISConfigModel(S3Model):
    """
        GIS Config model: Web Map Context
        - Site config
        - Personal config
        - OU config (Organisation &/or Team)
    """

    names = ("gis_config",
             "gis_menu",
             "gis_marker",
             "gis_projection",
             "gis_config_id",
             "gis_marker_id",
             "gis_projection_id",
             "gis_config_form_setup",
             )

    def model(self):

        T = current.T
        db = current.db
        gis = current.gis

        location_id = self.gis_location_id

        settings = current.deployment_settings

        # Shortcuts
        add_components = self.add_components
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # =====================================================================
        # GIS Markers (Icons)
        tablename = "gis_marker"
        define_table(tablename,
                     Field("name", length=64, notnull=True, unique=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ]
                           ),
                     # If-needed, then Symbology should be here
                     #symbology_id(),
                     Field("image", "upload",
                           autodelete = False,
                           custom_retrieve = gis_marker_retrieve,
                           custom_retrieve_file_properties = gis_marker_retrieve_file_properties,
                           label = T("Image"),
                           length = current.MAX_FILENAME_LENGTH,
                           represent = lambda filename: \
                               (filename and [DIV(IMG(_src=URL(c="static",
                                                               f="img",
                                                               args=["markers",
                                                                     filename]),
                                                      _height=40))] or [""])[0],
                           # upload folder needs to be visible to the download() function as well as the upload
                           uploadfolder = os.path.join(current.request.folder,
                                                       "static",
                                                       "img",
                                                       "markers"),
                           widget = S3ImageCropWidget((50, 50)),
                           ),
                     # We could get size client-side using Javascript's Image() class, although this is unreliable!
                     Field("height", "integer", # In Pixels, for display purposes
                           writable = False,
                           ),
                     Field("width", "integer",
                           writable = False,
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_MARKER = T("Create Marker")
        crud_strings[tablename] = Storage(
            label_create = ADD_MARKER,
            title_display = T("Marker Details"),
            title_list = T("Markers"),
            title_update = T("Edit Marker"),
            label_list_button = T("List Markers"),
            label_delete_button = T("Delete Marker"),
            msg_record_created = T("Marker added"),
            msg_record_modified = T("Marker updated"),
            msg_record_deleted = T("Marker deleted"),
            msg_list_empty = T("No Markers currently available"))

        # Reusable field to include in other table definitions
        # @ToDo: Widget to include icons in dropdown: http://jqueryui.com/selectmenu/#custom_render
        marker_represent = gis_MarkerRepresent()
        marker_id = S3ReusableField("marker_id", "reference %s" % tablename,
                                    label = T("Marker"),
                                    ondelete = "SET NULL",
                                    represent = marker_represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "gis_marker.id",
                                                          "%(name)s",
                                                          zero=T("Use default"))),
                                    sortby = "name",
                                    widget = S3SelectWidget(icons=self.gis_marker_options),
                                    comment=S3PopupLink(c = "gis",
                                                        f = "marker",
                                                        #vars = {"child": "marker_id",
                                                        #        "parent": "symbology"},
                                                        label = ADD_MARKER,
                                                        title = T("Marker"),
                                                        tooltip = "%s|%s|%s" % (T("Defines the icon used for display of features on interactive map & KML exports."),
                                                                                T("A Marker assigned to an individual Location is set if there is a need to override the Marker assigned to the Feature Class."),
                                                                                T("If neither are defined, then the Default Marker is used.")),
                                                        ),
                                    )

        # Components
        #add_components(tablename,
        #               gis_layer_entity = {"link": "gis_style",
        #                                   "joinby": "marker_id",
        #                                   "key": "layer_id",
        #                                   "actuate": "hide",
        #                                   "autocomplete": "name",
        #                                   "autodelete": False,
        #                                   },
        #               )

        configure(tablename,
                  deduplicate = S3Duplicate(),
                  onvalidation = self.gis_marker_onvalidation,
                  )

        # =====================================================================
        # GIS Projections
        tablename = "gis_projection"
        proj4js = T("%(proj4js)s definition") % {"proj4js": "Proj4js"}
        define_table(tablename,
                     Field("name", length=64, notnull=True, unique=True,
                           label = T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     Field("epsg", "integer", notnull=True,
                           label = "EPSG",
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("maxExtent", length=64, notnull=True,
                           label = T("Maximum Extent"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Maximum Extent"),
                                                           T("The Maximum valid bounds, in projected coordinates"))),
                           # @ToDo: Add a specialised validator
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           ),
                     Field("proj4js",
                           label = proj4js,
                           comment = DIV(_class="stickytip",
                                         _title="%s|%s" % (proj4js,
                                                           T("String used to configure Proj4js. Can be found from %(url)s") % {"url": A("http://spatialreference.org",
                                                                                                                                        _href="http://spatialreference.org",
                                                                                                                                        _target="_blank")})),
                           ),
                     Field("units", notnull=True,
                           label = T("Units"),
                           requires = IS_IN_SET(["m", "degrees"],
                                                zero=None),
                           ),
                     *s3_meta_fields())

        # CRUD Strings
        ADD_PROJECTION = T("Create Projection")
        crud_strings[tablename] = Storage(
            label_create = ADD_PROJECTION,
            title_display = T("Projection Details"),
            title_list = T("Projections"),
            title_update = T("Edit Projection"),
            label_list_button = T("List Projections"),
            label_delete_button = T("Delete Projection"),
            msg_record_created = T("Projection added"),
            msg_record_modified = T("Projection updated"),
            msg_record_deleted = T("Projection deleted"),
            msg_list_empty = T("No Projections currently defined"))

        # Reusable field to include in other table definitions
        represent = S3Represent(lookup=tablename)
        projection_id = S3ReusableField("projection_id", "reference %s" % tablename,
                                        sortby="name",
                                        requires = IS_EMPTY_OR(
                                                    IS_ONE_OF(db, "gis_projection.id",
                                                              represent)),
                                        represent = represent,
                                        label = T("Projection"),
                                        comment=S3PopupLink(c = "gis",
                                                            f = "projection",
                                                            label = ADD_PROJECTION,
                                                            title = T("Projection"),
                                                            tooltip = "%s|%s|%s" % (T("The system supports 2 projections by default:"),
                                                                                    T("Spherical Mercator (900913) is needed to use OpenStreetMap/Google/Bing base layers."),
                                                                                    T("WGS84 (EPSG 4236) is required for many WMS servers.")),
                                                            ),
                                        ondelete = "RESTRICT")

        configure(tablename,
                  deduplicate = S3Duplicate(primary=("epsg",)),
                  deletable = False,
                  )

        # =====================================================================
        # GIS Config
        #
        # uuid==SITE_DEFAULT => Site default settings
        #
        # @ToDo: Settings that apply will be the Site Settings modified
        #        according to any active Event or Region config and any OU or
        #        Personal config found

        org_group_label = settings.get_org_groups()
        org_site_label = settings.get_org_site_label()
        teams_label = settings.get_hrm_teams()

        pe_types = {1: T("Person"),
                    2: T(teams_label),
                    4: T(org_site_label),
                    7: T("Organization"),
                    9: "SITE_DEFAULT",
                    }
        if settings.get_org_branches():
            pe_types[6] = T("Branch")
        if org_group_label:
            pe_types[8] = T(org_group_label)

        tablename = "gis_config"
        define_table(tablename,
                     # Name displayed in the GIS config menu.
                     Field("name"),

                     # pe_id for Personal/OU configs
                     super_link("pe_id", "pr_pentity"),
                     # Gets populated onvalidation
                     Field("pe_type", "integer",
                           requires = IS_EMPTY_OR(IS_IN_SET(pe_types)),
                           readable = False,
                           writable = False,
                           ),
                     # Default:
                     # If a person has multiple saved configs then this decides
                     # which is the one to use
                     Field("pe_default", "boolean",
                           default = False,
                           ),

                     # Region field
                     location_id("region_location_id",
                                 requires = IS_EMPTY_OR(IS_LOCATION(level=gis.hierarchy_level_keys)),
                                 widget = S3LocationAutocompleteWidget(),
                                 ),

                     # CRUD Settings
                     # Default Location
                     location_id("default_location_id",
                                 requires = IS_EMPTY_OR(IS_LOCATION()),
                                 widget = S3LocationAutocompleteWidget(),
                                 ),
                     # Map Settings
                     Field("zoom", "integer",
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(1, 20)),
                           ),
                     Field("lat", "double",
                           requires = IS_EMPTY_OR(IS_LAT()),
                           ),
                     Field("lon", "double",
                           requires = IS_EMPTY_OR(IS_LON()),
                           ),
                     projection_id(#empty=False,
                                   # Nice if we could get this set to epsg field
                                   #default=900913
                                   ),
                     #symbology_id(),
                     # Overall Bounding Box for sanity-checking inputs
                     Field("lat_min", "double",
                           # @ToDo: Remove default once we have cascading working
                           default = -90,
                           requires = IS_EMPTY_OR(IS_LAT()),
                           ),
                     Field("lat_max", "double",
                           # @ToDo: Remove default once we have cascading working
                           default = 90,
                           requires = IS_EMPTY_OR(IS_LAT()),
                           ),
                     Field("lon_min", "double",
                           # @ToDo: Remove default once we have cascading working
                           default = -180,
                           requires = IS_EMPTY_OR(IS_LON()),
                           ),
                     Field("lon_max", "double",
                           # @ToDo: Remove default once we have cascading working
                           default = 180,
                           requires = IS_EMPTY_OR(IS_LON()),
                           ),

                     # This should be turned off for Offline deployments or expensive SatComms, such as BGAN
                     Field("geocoder", "boolean"),
                     Field("wmsbrowser_url"),
                     Field("wmsbrowser_name",
                           default = "Web Map Service",
                           ),
                     # Note: This hasn't yet been changed for any instance
                     # Do we really need it to be configurable?
                     Field("zoom_levels", "integer",
                           # @ToDo: Remove default once we have cascading working
                           default = 22,
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(1, 30)),
                           readable = False,
                           writable = False,
                           ),

                     Field("image", "upload",
                           autodelete = False,
                           custom_retrieve = gis_marker_retrieve,
                           custom_retrieve_file_properties = gis_marker_retrieve_file_properties,
                           label = T("Image"),
                           length = 255,
                           represent = lambda filename: \
                               (filename and [DIV(IMG(_src=URL(c="static",
                                                               f="cache",
                                                               args=["jpg",
                                                                     filename]),
                                                      _height=40))] or [""])[0],
                           # upload folder needs to be visible to the download() function as well as the upload
                           uploadfolder = os.path.join(current.request.folder,
                                                       "static",
                                                       "cache",
                                                       "jpg"),
                           # Enable in-templates as-required
                           #readable = False,
                           #writable = False,
                           #widget = S3ImageCropWidget((820, 410)),
                           ),
                     # Whether the config should be merged with the default config
                     Field("merge", "boolean",
                           default = True,
                           ),
                     # Whether the config is just temporary for taking a screenshot
                     Field("temp", "boolean",
                           default = False,
                           readable = False,
                           writable = False,
                           ),
                     *s3_meta_fields())

        # Reusable field - used by Events & Scenarios
        represent = S3Represent(lookup=tablename)
        config_id = S3ReusableField("config_id", "reference %s" % tablename,
                                    label = T("Map Profile"),
                                    ondelete = "CASCADE",
                                    represent = represent,
                                    requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "gis_config.id",
                                                          represent)),
                                    )

        crud_strings[tablename] = Storage(
            label_create = T("Create Map Profile"),
            title_display = T("Map Profile"),
            title_list = T("Map Profiles"),
            title_update = T("Edit Map Profile"),
            label_list_button = T("List Map Profiles"),
            label_delete_button = T("Delete Map Profile"),
            msg_record_created = T("Map Profile added"),
            msg_record_modified = T("Map Profile updated"),
            msg_record_deleted = T("Map Profile deleted"),
            msg_list_empty = T("No Map Profiles currently defined")
        )

        configure(tablename,
                  create_next = URL(c="gis", f="config",
                                    args=["[id]", "layer_entity"]),
                  deduplicate = S3Duplicate(),
                  # These are amended as-required in the controller
                  list_fields = ["name",
                                 "pe_id",
                                 ],
                  onaccept = self.gis_config_onaccept,
                  ondelete = self.gis_config_ondelete,
                  onvalidation = self.gis_config_onvalidation,
                  orderby = "gis_config.name",
                  )

        # Components
        add_components(tablename,
                       # Layers
                       gis_layer_entity = {"link": "gis_layer_config",
                                           "joinby": "config_id",
                                           "key": "layer_id",
                                           "actuate": "hide",
                                           "autocomplete": "name",
                                           "autodelete": False,
                                           },
                       # Styles
                       gis_style = "config_id",
                       )

        if settings.get_security_map() and not \
           current.auth.s3_has_role("MapAdmin"):
            configure(tablename,
                      deletable = False,
                      )

        # =====================================================================
        # GIS Menu Entries
        #
        # Entries in here decide whether a GIS menu appears for a user & which
        # entries are included within it.
        #
        # If the pe_id field is blank then it applies to everyone
        #
        # Initially we just check the Person's
        # @ToDo: Check for OUs too

        tablename = "gis_menu"
        define_table(tablename,
                     config_id(empty = False),
                     super_link("pe_id", "pr_pentity"),
                     *s3_meta_fields())

        # Initially will be populated only when a Personal config is created
        # CRUD Strings
        # crud_strings[tablename] = Storage(
            # label_create = T("Add Menu Entry"),
            # title_display = T("Menu Entry Details"),
            # title_list = T("Menu Entries"),
            # title_update = T("Edit Menu Entry"),
            # label_list_button = T("List Menu Entries"),
            # label_delete_button = T("Delete Menu Entry"),
            # msg_record_created = T("Menu Entry added"),
            # msg_record_modified = T("Menu Entry updated"),
            # msg_record_deleted = T("Menu Entry deleted"),
            # msg_list_empty = T("No Menu Entries currently defined"))

        # Pass names back to global scope (s3.*)
        return {"gis_config_form_setup": self.gis_config_form_setup,
                "gis_config_id": config_id,
                "gis_marker_id": marker_id,
                "gis_projection_id": projection_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_form_setup():
        """ Prepare the gis_config form """

        T = current.T
        table = current.db.gis_config

        # Defined here since Component (of Persons)
        # @ToDo: Need tooltips for projection, geocoder, zoom levels,
        # cluster distance, and cluster threshold.
        label = T("Name")
        table.name.label = label
        table.name.represent = lambda v: v or ""
        table.name.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                label,
                T("If this configuration is displayed on the GIS config menu, give it a name to use in the menu. The name for a personal map configuration will be set to the user's name.")))
        field = table.pe_id
        field.label = T("Person or OU")
        field.readable = field.writable = True
        field.represent = current.s3db.pr_PersonEntityRepresent(show_label=False)
        field.widget = S3PentityAutocompleteWidget(
            types=("pr_person", "pr_group", "org_organisation"))
        label = T("Default?")
        table.pe_default.label = label
        table.pe_default.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                label,
                T("If there are multiple configs for a person, which should be their default?")))

        table.region_location_id.label = T("Region")
        table.region_location_id.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Region Location"),
                T("A location that specifies the geographic area for this region. This can be a location from the location hierarchy, or a 'group location', or a location that has a boundary for the area.")))
        label = T("Default Location")
        table.default_location_id.label = label
        table.default_location_id.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                label,
                T("Use this to set the starting location for the Location Selector.")))
        table.lat.label = T("Map Center Latitude")
        table.lat.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s|%s" % (
                T("Latitude of Map Center"),
                T("The map will be displayed initially with this latitude at the center."),
                T("Latitude is North-South (Up-Down)."),
                T("Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere.")))
        table.lon.label = T("Map Center Longitude")
        table.lon.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s|%s" % (
                T("Longitude of Map Center"),
                T("The map will be displayed initially with this longitude at the center."),
                T("Longitude is West - East (sideways)."),
                T("Longitude is zero on the prime meridian (through Greenwich, United Kingdom) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas.")))
        label = T("Web Map Service Browser Name")
        table.wmsbrowser_name.label = label
        table.wmsbrowser_name.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                label,
                T("Title to show for the Web Map Service panel in the Tools panel.")))
        label = T("Web Map Service Browser URL")
        table.wmsbrowser_url.label = label
        table.wmsbrowser_url.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s" % (
                label,
                T("The URL for the GetCapabilities page of a Web Map Service (WMS) whose layers you want available via the Browser panel on the Map."),
                T("The form of the URL is http://your/web/map/service?service=WMS&request=GetCapabilities where your/web/map/service stands for the URL path to the WMS.")))
        table.geocoder.label = T("Use Geocoder for address lookups?")
        label = T("Minimum Location Latitude")
        table.lat_min.label = label
        table.lat_min.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s" % (
                label,
                T("Latitude of far southern end of the region of interest."),
                T("Used to check that latitude of entered locations is reasonable. May be used to filter lists of resources that have locations.")))
        label = T("Maximum Location Latitude")
        table.lat_max.label = label
        table.lat_max.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s" % (
                label,
                T("Latitude of far northern end of the region of interest."),
                T("Used to check that latitude of entered locations is reasonable. May be used to filter lists of resources that have locations.")))
        label = T("Minimum Location Longitude")
        table.lon_min.label = label
        table.lon_min.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s" % (
                label,
                T("Longitude of far western end of the region of interest."),
                T("Used to check that longitude of entered locations is reasonable. May be used to filter lists of resources that have locations.")))
        label = T("Maximum Location Longitude")
        table.lon_max.label = label
        table.lon_max.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s" % (
                label,
                T("Longitude of far eastern end of the region of interest."),
                T("Used to check that longitude of entered locations is reasonable. May be used to filter lists of resources that have locations.")))
        table.zoom_levels.label = T("Zoom Levels")
        table.zoom.label = T("Map Zoom")
        table.zoom.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Zoom"),
                T("How much detail is seen. A high Zoom level means lot of detail, but not a wide area. A low Zoom level means seeing a wide area, but not a high level of detail.")))

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_onvalidation(form):
        """
            Set the pe_type
        """

        form_vars = form.vars
        if form_vars.uuid == "SITE_DEFAULT":
            form_vars.pe_type = 9
        elif "pe_id" in form_vars:
            pe_id = form_vars.pe_id
            if pe_id:
                # Populate the pe_type
                db = current.db
                s3db = current.s3db
                table = s3db.pr_pentity
                query = (table.pe_id == pe_id)
                pe = db(query).select(table.instance_type,
                                      limitby=(0, 1)).first()
                if pe:
                    pe_type = pe.instance_type
                    if pe_type == "pr_person":
                        form_vars.pe_type = 1
                    elif pe_type == "pr_group":
                        form_vars.pe_type = 2
                    elif pe_type == "org_office":
                        form_vars.pe_type = 4
                    elif pe_type == "org_group":
                        form_vars.pe_type = 8
                    elif pe_type == "org_organisation":
                        if current.deployment_settings.get_org_branches():
                            # Check if we're a branch
                            otable = s3db.org_organisation
                            btable = s3db.org_organisation_branch
                            query = (otable.pe_id == pe_id) & \
                                    (btable.branch_id == otable.id)
                            branch = db(query).select(btable.id,
                                                      limitby=(0, 1)).first()
                            if branch:
                                form_vars.pe_type = 6
                            else:
                                form_vars.pe_type = 7
                        else:
                            form_vars.pe_type = 7
        elif "config" in current.request.args:
            # Personal Config
            form_vars.pe_type = 1

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_onaccept(form):
        """
            If this is the cached config, clear the cache.
            If this is this user's personal config, clear the config
            Check that there is only 1 default for each PE
            If this is an OU config, then add to GIS menu

            If this has a region location, protect that location from accidental
            editing (e.g. if it is used as a default location for any resources in
            the region) but making it only editable by a MapAdmin.
        """

        db = current.db
        auth = current.auth

        form_vars = form.vars
        config_id = form_vars.id
        pe_id = form_vars.get("pe_id", None)
        if pe_id:
            user = auth.user
            if user and user.pe_id == pe_id:
                # Clear the current config
                current.response.s3.gis.config = None
            if form_vars.pe_default:
                # Ensure no other records for this PE are marked as default
                table = db.gis_config
                query = (table.pe_id == pe_id) & \
                        (table.id != config_id)
                db(query).update(pe_default=False)
            # Add to GIS Menu
            db.gis_menu.update_or_insert(config_id=config_id,
                                         pe_id=pe_id)
        else:
            config = current.response.s3.gis.config
            if config and config.id == config_id:
                # This is the currently active config, so clear our cache
                config = None

        # Prepop records should be owned by MapAdmin.
        # That makes Authenticated no longer an owner, so they only get whatever
        # is permitted by uacl (usually READ).
        if auth.override:
            db(db.gis_config.id == config_id).update(
                owned_by_group = current.session.s3.system_roles.MAP_ADMIN)

        # Locations which are referenced by Map Configs should be owned by MapAdmin.
        # That makes Authenticated no longer an owner, so they only get whatever
        # is permitted by uacl (usually READ).
        if form_vars.region_location_id:
            db(db.gis_location.id == form_vars.region_location_id).update(
                owned_by_group = current.session.s3.system_roles.MAP_ADMIN)

        if not form_vars.get("temp", None) and not auth.override:
            settings = current.deployment_settings
            screenshot = settings.get_gis_config_screenshot()
            if screenshot is not None:
                # Save a screenshot
                width = screenshot[0]
                height = screenshot[1]
                filename = current.gis.get_screenshot(config_id,
                                                      False,
                                                      height,
                                                      width)
                db(db.gis_config.id == config_id).update(image=filename)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_ondelete(row):
        """
            If the currently-active config was deleted, clear the cache
        """

        s3 = current.response.s3
        if s3.gis.config and s3.gis.config.id == row.id:
            s3.gis.config = None

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_marker_options(options):
        """
            Function which takes a list of k/v option tuples and adds an
            icon URL for S3SelectMenu()
        """

        marker_ids = []
        mappend = marker_ids.append
        for o in options:
            mappend(o[0])
        # Do a bulk lookup
        mtable = current.s3db.gis_marker
        markers = current.db(mtable.id.belongs(marker_ids)).select(mtable.id,
                                                                   mtable.image,
                                                                   mtable.height,
                                                                   mtable.width,
                                                                   )
        markers_lookup = {}
        base_url = "/%s/static/img/markers/" % current.request.application
        for m in markers:
            markers_lookup[str(m.id)] = ("%s%s" % (base_url, m.image),
                                         m.height,
                                         m.width,
                                         )

        new_options = []
        oappend = new_options.append
        for (k, v) in options:
            i = markers_lookup.get(k, None)
            opt = (k, v, i)
            oappend(opt)

        return new_options

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_marker_onvalidation(form):
        """
            Record the size of an Image upon Upload
            Don't wish to resize here as we'd like to use full resolution for printed output
        """

        form_vars = form.vars
        image = form_vars.image
        if image is None:
            encoded_file = form_vars.get("imagecrop-data", None)
            if not encoded_file:
                # No Image => CSV import of resources which just need a ref
                return
            import base64
            import uuid
            metadata, encoded_file = encoded_file.split(",")
            filename = metadata.split(";")[0]
            f = Storage()
            f.filename = uuid.uuid4().hex + filename
            f.file = BytesIO(base64.b64decode(encoded_file))
            form_vars.image = image = f

        elif isinstance(image, str):
            # Image = String => Update not a Create, so file not in form
            return

        extension = image.filename.rfind(".")
        extension = image.filename[extension + 1:].lower()
        if extension == "jpg":
            extension = "jpeg"
        if extension not in ("bmp", "gif", "jpeg", "png"):
            form.errors.image = current.T("Uploaded file(s) are not Image(s). Supported image formats are '.png', '.jpg', '.bmp', '.gif'.")
            return

        native = False
        try:
            from PIL import Image
        except ImportError:
            try:
                import Image
            except ImportError:
                # Native Python version
                native = True
                import struct

        if native:
            # Fallbacks
            width = height = -1
            stream = image.file
            if extension == "bmp":
                if stream.read(2) == "BM":
                    stream.read(16)
                    width, height = struct.unpack("<LL", stream.read(8))
            elif extension == "gif":
                if stream.read(6) in ("GIF87a", "GIF89a"):
                    stream = stream.read(5)
                    if len(stream) == 5:
                        width, height = \
                            tuple(struct.unpack("<HHB", stream)[:-1])
            elif extension == "jpeg":
                if stream.read(2) == "\xFF\xD8":
                    while True:
                        (marker, code, length) = \
                            struct.unpack("!BBH", stream.read(4))
                        if marker != 0xFF:
                            break
                        elif code >= 0xC0 and code <= 0xC3:
                            width, height = \
                                tuple(reversed(struct.unpack("!xHH",
                                                             stream.read(5))))
                        else:
                            stream.read(length - 2)
            elif extension == "png":
                if stream.read(8) == "\211PNG\r\n\032\n":
                    stream.read(4)
                    if stream.read(4) == "IHDR":
                        width, height = struct.unpack("!LL", stream.read(8))
        else:
            # Use PIL
            try:
                im = Image.open(image.file)
            except:
                width = height = -1
            else:
                width, height = im.size

        if width < 1 or height < 1:
            form.errors.image = current.T("Invalid image!")
            return

        if width > 50 or height > 50:
            if native:
                form.errors.image = current.T("Maximum size 50x50!")
                return
            # Resize the Image
            im.thumbnail((50, 50) , Image.ANTIALIAS)
            width, height = im.size
            #im.save(image.file)
            current.session.warning = current.T("File has been resized")

        image.file.seek(0)

        form_vars.width = width
        form_vars.height = height

# =============================================================================
class gis_MarkerRepresent(S3Represent):
    """
        Represent a Marker by it's picture
    """

    def __init__(self):

        super(gis_MarkerRepresent, self).__init__(lookup="gis_marker",
                                                  fields=["image"])

    def represent_row(self, row):
        """
            Represent a Row
            @param row: The Row
        """
        represent = DIV(IMG(_src=URL(c="static", f="img",
                                     args=["markers", row.image]),
                            _height=40))
        return represent

# ==============================================================================
class S3LayerEntityModel(S3Model):
    """
        Model for Layer SuperEntity
        - used to provide a common link table for:
            Layers <> Configs (applicable to Vectors & Rasters)
                for Enabled/Visible
            Layers <> Styles (applicable to Vectors)
                for Marker/GPS Symbol, Opacity, Style, Popup Format, Clustering
    """

    names = ("gis_layer_entity",
             "gis_layer_config",
             "gis_style",
             "gis_layer_config_onaccept",
             "gis_style_postprocess",
             )

    def model(self):

        T = current.T

        # Shortcuts
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # =====================================================================
        #  Layer Entity

        # @ToDo: Scanned images
        layer_types = Storage(gis_layer_arcrest = T("ArcGIS REST Layer"),
                              gis_layer_bing = T("Bing Layer"),
                              gis_layer_coordinate = T("Coordinate Layer"),
                              gis_layer_empty = T("No Base Layer"),
                              gis_layer_feature = T("Feature Layer"),
                              gis_layer_geojson = T("GeoJSON Layer"),
                              gis_layer_georss = T("GeoRSS Layer"),
                              gis_layer_google = T("Google Layer"),
                              gis_layer_gpx = T("GPX Layer"),
                              gis_layer_js = T("JS Layer"),
                              gis_layer_kml = T("KML Layer"),
                              gis_layer_mgrs = T("MGRS Layer"),
                              gis_layer_openstreetmap = T("OpenStreetMap Layer"),
                              gis_layer_openweathermap = T("OpenWeatherMap Layer"),
                              gis_layer_shapefile = T("Shapefile Layer"),
                              gis_layer_theme = T("Theme Layer"),
                              gis_layer_tms = T("TMS Layer"),
                              gis_layer_wfs = T("WFS Layer"),
                              gis_layer_wms = T("WMS Layer"),
                              gis_layer_xyz = T("XYZ Layer"),
                              )

        tablename = "gis_layer_entity"
        self.super_entity(tablename, "layer_id", layer_types,
                          name_field()(),
                          desc_field()(),
                          #role_required(),       # Single Role
                          ##roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                          )

        crud_strings[tablename] = Storage(
            label_create = T("Create Layer"),
            title_display = T("Layer Details"),
            title_list = T("Layers"),
            title_update = T("Edit Layer"),
            label_list_button = T("List Layers"),
            label_delete_button = T("Delete Layer"),
            msg_record_created = T("Layer added"),
            msg_record_modified = T("Layer updated"),
            msg_record_deleted = T("Layer deleted"),
            msg_list_empty=T("No Layers currently defined")
            )

        # Components
        self.add_components(tablename,
                            # Configs
                            gis_config = {"link": "gis_layer_config",
                                          "pkey": "layer_id",
                                          "joinby": "layer_id",
                                          "key": "config_id",
                                          "actuate": "hide",
                                          "autocomplete": "name",
                                          "autodelete": False,
                                          },
                            # Styles
                            gis_style = "layer_id",
                            # Posts
                            cms_post = {"link": "cms_post_layer",
                                        "pkey": "layer_id",
                                        "joinby": "layer_id",
                                        "key": "post_id",
                                        },
                            )

        layer_id = self.super_link("layer_id", "gis_layer_entity",
                                   label = T("Layer"),
                                   represent = gis_layer_represent,
                                   readable = True,
                                   writable = True,
                                   )

        # =====================================================================
        #  Layer Config link table

        tablename = "gis_layer_config"
        self.define_table(tablename,
                     layer_id,
                     self.gis_config_id(empty = False),
                     Field("enabled", "boolean",
                           default = True,
                           label = T("Available in Viewer?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("visible", "boolean",
                           default = True,
                           label = T("On by default?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("dir", length=64,
                           label = T("Folder"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Folder"),
                                                           T("If you enter a foldername then the layer will appear in this folder in the Map's layer switcher. A sub-folder can be created by separating names with a '/'"))),
                           requires = IS_LENGTH(64),
                           ),
                     Field("base", "boolean",
                           default = False,
                           label = T("Default Base layer?"),
                           represent = s3_yes_no_represent,
                           ),
                     *s3_meta_fields())

        # Default to the Layer -> Config view
        # since there are many diff layers
        # - override for single Config -> Layer
        crud_strings[tablename] = Storage(
            label_create = T("Add Profile Configuration for this Layer"),
            title_display = T("Profile Configuration"),
            title_list = T("Profile Configurations"),
            title_update = T("Edit Profile Configuration"),
            label_list_button = T("List Profiles configured for this Layer"),
            label_delete_button = T("Remove Profile Configuration for Layer"),
            msg_record_created = T("Profile Configured"),
            msg_record_modified = T("Profile Configuration updated"),
            msg_record_deleted = T("Profile Configuration removed"),
            msg_list_empty = T("No Profiles currently have Configurations for this Layer")
            )

        self.configure(tablename,
                       onaccept = self.gis_layer_config_onaccept,
                       )

        # ---------------------------------------------------------------------
        # GIS Styles
        # - can be linked to a layer/record_id
        # - can be a component of a layer_config
        # - @ToDo: can be standalone, named styles for re-use (link vs copy)

        # Style is a JSON object with the following structure
        # (only the starred elements are currently parsed)
        # @ToDo: Support elements in a common section (such as prop, graphic)
        # @ToDo: Import/Export SLD
        #Style = [{
        #   prop: string,       //* Attribute used to activate this style rule (otherwise defaults to 'value')
        #   cat: string,        //* Absolute Value used to style the element
        #   low: float,         //* Low value of the range of values used for this style rule
        #   high: float,        //* High value of the range of values used for this style rule
        #   label: string,      //* Optional label for the Category/Range (falls back to cat or 'low - high')
        #   externalGraphic: string, //* Marker to load from /static/path/to/marker.png
        #   fill: string,       //*
        #   fillOpacity: float, //*
        #   stroke: string,     //* (will default to fill, if not set)
        #   strokeLinecap: string, Stroke cap type: "butt", "round", "square"
        #   strokeDashstyle: string, //* Encodes a dash pattern as a series of numbers separated by spaces. Odd-indexed numbers (first, third, etc) determine the length in pxiels to draw the line, and even-indexed numbers (second, fourth, etc) determine the length in pixels to blank out the line.
        #   strokeOpacity: float,
        #   strokeWidth: float or int, //* OpenLayers wants int, SLD wants float
        #   label: string,      //* Attribute used to label the element
        #   show_label: boolean, //* Whether or not to label the element
        #   graphic: string,    //* Shape: "circle", "square", "star", "x", "cross", "triangle"
        #   size: integer,,     //* Radius of the Shape
        #   popup: {},
        #}]

        tablename = "gis_style"
        define_table(tablename,
                     # Optionally give the style a Name/Description
                     #name_field()(),
                     #desc_field()(),
                     # Optionally restrict to a specific Config
                     self.gis_config_id(
                        comment = DIV(_class="tooltip",
                                      _title=T("Leave this blank to apply to all Profiles")
                                      ),
                        ),
                     # Optionally link to a specific Layer
                     # Component not Instance
                     self.super_link("layer_id", "gis_layer_entity"),
                     # Optionally restrict to a specific Record
                     Field("record_id", "integer",
                           label = T("Record"),
                           requires = IS_EMPTY_OR(IS_INT_IN_RANGE(1, None)),
                           ),
                     Field("aggregate", "boolean",
                           default = False,
                           label = T("Aggregate"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Aggregate"),
                                                           T("Is this style for use when the layer is displaying aggregated data?"))),
                           ),
                     # Allow selection of a marker
                     # @ToDo: write style onaccept?
                     self.gis_marker_id(),
                     Field("gps_marker",
                           label = T("GPS Marker"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("GPS Marker"),
                                                           T("Defines the icon used for display of features on handheld GPS."))),
                           # This is the list of GPS Markers for Garmin devices
                          requires = IS_EMPTY_OR(
                                        IS_IN_SET(current.gis.gps_symbols(),
                                                  zero=T("Use default")))
                           ),
                     gis_opacity()(),
                     Field("popup_format",
                           label = T("Popup Format"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Popup Format"),
                                                           T("Used in onHover Tooltip & Cluster Popups to differentiate between types."))),
                           ),
                     Field("cluster_distance", "integer",
                           default = 20,
                           label = T("Cluster Distance"),
                           requires = IS_INT_IN_RANGE(1, 51),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Cluster Distance"),
                                                           T("The number of pixels apart that features need to be before they are clustered."))),
                           ),
                     Field("cluster_threshold", "integer",
                           default = 2,
                           label = T("Cluster Threshold"),
                           requires = IS_INT_IN_RANGE(0, 10),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Cluster Threshold"),
                                                           T("The minimum number of features to form a cluster. 0 to disable."))),
                           ),
                     Field("style", "json",
                           label = T("Style"),
                           # @ToDo: Validate that a record-specific style just has a single entry in the array
                           requires = IS_EMPTY_OR(
                                        IS_JSONS3(error_message="Style invalid")),
                           ),
                     # @ToDo: SLD XML which can be used by a GeoServer co-app:
                     # http://docs.geoserver.org/stable/en/user/restconfig/rest-config-api.html#styles
                     # Not currently possible to convert between JSON <> XML automatically without losing details
                     #Field("sld", "text"),
                     *s3_meta_fields())

        # Reusable field
        #represent = S3Represent(lookup=tablename)
        #style_id = S3ReusableField("style_id", "reference %s" % tablename,
        #                           label = T("Map Style"),
        #                           ondelete = "CASCADE",
        #                           represent = represent,
        #                           requires = IS_ONE_OF(db, "gis_style.id",
        #                                                represent),
        #                           )

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Map Style"),
            title_display = T("Map Style"),
            title_list = T("Map Styles"),
            title_update = T("Edit Map Style"),
            label_list_button = T("List Map Styles"),
            label_delete_button = T("Delete Map Style"),
            msg_record_created = T("Map Style added"),
            msg_record_modified = T("Map Style updated"),
            msg_record_deleted = T("Map Style deleted"),
            msg_list_empty = T("No Map Styles currently defined")
        )

        # ---------------------------------------------------------------------
        # Pass names back to global scope (s3.*)
        return {"gis_layer_types": layer_types,
                # Run from config() controller when saving state
                "gis_layer_config_onaccept": self.gis_layer_config_onaccept,
                "gis_style_postprocess": self.gis_style_postprocess,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_config_onaccept(form):
        """
            If this is the default base layer then remove this flag from all
            others in this config.
        """

        form_vars = form.vars
        base = form_vars.base
        if base == "False":
            base = False
        enabled = form_vars.enabled
        if enabled == "False":
            enabled = False

        if base and enabled:
            db = current.db
            ctable = db.gis_config
            ltable = db.gis_layer_config
            query = (ltable.id == form_vars.id) & \
                    (ltable.config_id == ctable.id)
            config = db(query).select(ctable.id,
                                      limitby=(0, 1)).first()
            if config:
                # Set all others in this config as not the default Base Layer
                query  = (ltable.config_id == config.id) & \
                         (ltable.base == True) & \
                         (ltable.id != form_vars.id)
                db(query).update(base = False)

    # ---------------------------------------------------------------------
    @staticmethod
    def gis_style_postprocess(form):
        """
            Extract the style from a LocationSelectorWidget2
            & create/update the style record
        """

        # Collect the Style
        colour = current.request.post_vars.colour
        if not colour:
            return

        # Format the style
        def rgb2hex(r, g, b):
            """
                Given an rgb or rgba sequence of 0-1 floats, return the hex string
            """
            return "%02x%02x%02x" % (r, g, b)

        try:
            parts = colour.split("(", 1)[1][:-1].split(",")
        except:
            current.log.error("invalid colour: %s" % colour)
            return

        fill = rgb2hex(int(parts[0]), int(parts[1]), int(parts[2]))
        style = {"fill": fill}
        if len(parts) == 4:
            opacity = float(parts[3])
            style["fillOpacity"] = opacity
        else:
            opacity = 1

        db = current.db
        s3db = current.s3db

        # Which Layer(s) should we add to?
        # @ToDo: Support for different controller/function than the table
        c, f = str(form.table).split("_", 1)
        ftable = s3db.gis_layer_feature
        query = (ftable.deleted != True) & \
                (ftable.controller == c) & \
                (ftable.function == f) & \
                (ftable.individual == True)
        rows = db(query).select(ftable.layer_id)

        # Insert/Update the Style record(s)
        stable = s3db.gis_style
        record_id = form.vars.id
        for row in rows:
            layer_id = row.layer_id
            query = (stable.layer_id == layer_id) & \
                    (stable.record_id == record_id)
            exists = db(query).select(stable.id,
                                      limitby=(0, 1)).first()
            if exists:
                exists.update_record(opacity = opacity,
                                     style = style)
            else:
                stable.insert(layer_id = layer_id,
                              record_id = record_id,
                              opacity = opacity,
                              style = style,
                              )

# =============================================================================
class S3FeatureLayerModel(S3Model):
    """
        Model for Feature Layers
        - used to select a set of Features for either Display on a Map
          or Export as XML: S3XML.gis_encode()
          (for transformation to GeoJSON/KML/GPX)
    """

    names = ("gis_layer_feature",)

    def model(self):

        T = current.T

        # =====================================================================
        # Feature Layers

        tablename = "gis_layer_feature"
        self.define_table(tablename,
                          # Instance
                          self.super_link("layer_id", "gis_layer_entity"),
                          name_field()(),
                          desc_field()(),
                          # REST Query added to Map JS to call back to server
                          Field("controller",
                                label = T("Controller"),
                                requires = IS_NOT_EMPTY(),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s /" % (T("Controller"),
                                                                  T("Part of the URL to call to access the Features"))),
                                ),
                          Field("function",
                                label = T("Function"),
                                requires = IS_NOT_EMPTY(),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s /" % (T("Function"),
                                                                  T("Part of the URL to call to access the Features"))),
                                ),
                          Field("filter",
                                label = T("Filter"),
                                comment = DIV(_class="stickytip",
                                              _title="%s|%s" % (T("Filter"),
                                                                "%s: <a href='http://eden.sahanafoundation.org/wiki/S3XRC/RESTfulAPI/URLFormat#BasicQueryFormat' target='_blank'>Wiki</a>" % \
                                                                T("Uses the REST Query Format defined in"))),
                                ),
                          Field("aggregate", "boolean",
                                default = False,
                                label = T("Aggregate"),
                                represent = s3_yes_no_represent,
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Aggregate"),
                                                                T("Instead of showing individual features, aggregate by Location Hierarchy"))),
                                ),
                          # @ToDo: Deprecate (replaced by popup_format)
                          Field("popup_label",
                                #label = T("Popup Label"),
                                readable = False,
                                writable = False,
                                #comment = DIV(_class="tooltip",
                                #              _title="%s|%s" % (T("Popup Label"),
                                #                                T("Used in onHover Tooltip & Cluster Popups to differentiate between types."))),
                                ),
                          # @ToDo: Deprecate (replaced by popup_format)
                          Field("popup_fields", "list:string",
                                # Want to be able to prepop layers with this empty to prevent popups from showing
                                #default = "name",
                                #label = T("Popup Fields"),
                                readable = False,
                                writable = False,
                                #comment = DIV(_class="tooltip",
                                #              _title="%s|%s" % (T("Popup Fields"),
                                #                                T("Used to build onHover Tooltip & 1st field also used in Cluster Popups to differentiate between records."))),
                                ),
                          # NB To use complex attributes, use the full-format, e.g. "~.location_id$gis_feature_type"
                          Field("attr_fields", "list:string",
                                label = T("Attributes"),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Attributes"),
                                                                T("Used to populate feature attributes which can be used for Styling and Popups."))),
                                ),
                          # @ToDo: Rename as no longer really 'style'
                          Field("style_default", "boolean",
                                default = False,
                                label = T("Default"),
                                represent = s3_yes_no_represent,
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Default"),
                                                                T("Whether calls to this resource which don't specify the layer should use this configuration as the default one"))),
                                ),
                          Field("individual", "boolean",
                                default = False,
                                label = T("Style Features Individually?"),
                                represent = s3_yes_no_represent,
                                ),
                          Field("points", "boolean",
                                default = False,
                                label = T("Points"),
                                represent = s3_yes_no_represent,
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Points"),
                                                                T("Whether the resource should be mapped just using Points and not Polygons"))),
                                ),
                          Field("trackable", "boolean",
                                default = False,
                                label = T("Trackable"),
                                represent = s3_yes_no_represent,
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Trackable"),
                                                                T("Whether the resource should be tracked using S3Track rather than just using the Base Location"))),
                                ),
                          Field("use_site", "boolean",
                                default = False,
                                label = T("Use Site?"),
                                comment = DIV(_class="tooltip",
                                              _title="%s|%s" % (T("Use Site?"),
                                                                T("Select this if you need this resource to be mapped from site_id instead of location_id."))),
                                ),
                          gis_refresh()(),
                          cluster_attribute()(),
                          s3_role_required(),    # Single Role
                          #s3_roles_permitted(), # Multiple Roles (needs implementing in modules/s3gis.py)
                          *s3_meta_fields())

        # CRUD Strings
        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Create Feature Layer"),
            title_display = T("Feature Layer Details"),
            title_list = T("Feature Layers"),
            title_update = T("Edit Feature Layer"),
            label_list_button = T("List Feature Layers"),
            label_delete_button = T("Delete Feature Layer"),
            msg_record_created = T("Feature Layer added"),
            msg_record_modified = T("Feature Layer updated"),
            msg_record_deleted = T("Feature Layer deleted"),
            msg_list_empty = T("No Feature Layers currently defined"))

        self.configure(tablename,
                       deduplicate = self.gis_layer_feature_deduplicate,
                       list_fields = ["id",
                                      "name",
                                      "description",
                                      "controller",
                                      "function",
                                      "filter",
                                      "attr_fields",
                                      "style_default",
                                      #"individual",
                                      #"trackable",
                                      ],
                       onaccept = self.gis_layer_feature_onaccept,
                       super_entity = "gis_layer_entity",
                       )

        # Pass names back to global scope (s3.*)
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_feature_onaccept(form):
        """
            Ensure that only a single layer for each controller/function
            is set as Default
        """

        layer_id = form.vars.id
        formvars = form.vars

        c = formvars.get("controller")
        f = formvars.get("function")
        default = formvars.get("style_default")

        if default and c and f and layer_id:
            # Ensure no other records for this controller/function are marked
            # as default
            db = current.db
            table = db.gis_layer_feature
            query = (table.controller == c) & \
                    (table.function == f) & \
                    (table.id != layer_id)
            db(query).update(style_default = False)

        # Normal Layer onaccept
        gis_layer_onaccept(form)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_feature_deduplicate(item):

        # Match if controller, function, filter and name are identical
        table = item.table
        data = item.data
        query = (table.name == data.name)
        controller = data.controller
        if controller:
            query &= (table.controller.lower() == controller.lower())
        function = data.function
        if function:
            query &= (table.function.lower() == function.lower())
        layer_filter = data.filter
        if layer_filter:
            query &= (table.filter == layer_filter)

        duplicate = current.db(query).select(table.id,
                                             limitby=(0, 1)).first()
        if duplicate:
            item.id = duplicate.id
            item.method = item.METHOD.UPDATE

# =============================================================================
class S3MapModel(S3Model):
    """ Models for Maps """

    names = ("gis_cache",
             "gis_cache2",
             "gis_feature_query",
             "gis_layer_arcrest",
             "gis_layer_bing",
             "gis_layer_coordinate",
             "gis_layer_empty",
             "gis_layer_geojson",
             "gis_layer_georss",
             "gis_layer_google",
             "gis_layer_gpx",
             "gis_layer_js",
             "gis_layer_kml",
             "gis_layer_mgrs",
             "gis_layer_openstreetmap",
             "gis_layer_openweathermap",
             "gis_layer_shapefile",
             "gis_layer_tms",
             "gis_layer_wfs",
             "gis_layer_wms",
             "gis_layer_xyz",
             )

    def model(self):

        T = current.T

        request = current.request
        folder = request.folder

        layer_id = lambda: self.super_link("layer_id", "gis_layer_entity")
        projection_id = self.gis_projection_id

        configure = self.configure
        define_table = self.define_table

        MAX_FILENAME_LENGTH = current.MAX_FILENAME_LENGTH

        messages = current.messages
        NONE  = messages["NONE"]
        TRANSPARENT = T("Transparent?")
        BASE_LAYER = T("Base Layer?")
        LOCATION = T("Location")
        FORMAT = T("Format")
        TYPE = T("Type")

        # ---------------------------------------------------------------------
        # GIS Feature Queries
        #
        # Store results of Feature Queries in a temporary table to allow
        # BBOX queries, Clustering, Refresh, Client-side Filtering, etc
        #
        tablename = "gis_feature_query"
        define_table(tablename,
                     Field("name", length=128, notnull=True,
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     Field("lat", "double",
                           requires = IS_LAT(),
                           ),
                     Field("lon", "double",
                           requires = IS_LON(),
                           ),
                     Field("popup_url"),
                     Field("popup_label"),
                     # Optional Marker
                     Field("marker_url"),
                     Field("marker_height", "integer"),
                     Field("marker_width", "integer"),
                     # or Shape/Size/Colour
                     Field("shape",
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(["circle",
                                                   "square",
                                                   "star",
                                                   "x",
                                                   "cross",
                                                   "triangle",
                                                   ]))
                           ),
                     Field("size", "integer"),
                     Field("colour",
                           requires = IS_EMPTY_OR(IS_HTML_COLOUR()),
                           widget = S3ColorPickerWidget(),
                           ),
                     gis_opacity()(),
                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # GPS Waypoints
        #tablename = "gis_waypoint"
        #define_table(tablename,
        #             Field("name", length=128, notnull=True,
        #                   label = T("Name"),
        #                   ),
        #             Field("description", length=128,
        #                   label = DESCRIPTION,
        #                   ),
        #             Field("category", length=128,
        #                   label = T("Category"),
        #                   ),
        #             location_id(),
        #             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # GPS Tracks (stored as 1 record per point)
        #tablename = "gis_trackpoint"
        #define_table(tablename,
        #             location_id(),
        #             #track_id(),        # link to the uploaded file?
        #             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # ArcGIS REST
        #
        # If exporting data via the Query interface use WHERE 1=1
        # Can then convert to GeoJSON using:
        # ogr2ogr -f GeoJSON standard.geojson proprietary.json" OGRGeoJSON
        #
        arc_img_formats = ("png", "png8", "png24", "jpg", "pdf", "bmp", "gif", "svg", "svgz", "emf", "ps", "png32")

        tablename = "gis_layer_arcrest"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("url",
                           label = LOCATION,
                           requires = IS_NOT_EMPTY(),
                           comment = DIV(_class="stickytip",
                                         _title="%s|%s" % (LOCATION,
                                                           "%s:%s" % (T("This should be an export service URL, see"),
                                                                      A("http://sampleserver1.arcgisonline.com/ArcGIS/SDK/REST/export.html",
                                                                        _href="http://sampleserver1.arcgisonline.com/ArcGIS/SDK/REST/export.html",
                                                                        _target="_blank"))))
                           ),
                     Field("layers", "list:integer",
                           default = [0],
                           label = T("Layers"),
                           ),
                     Field("base", "boolean",
                           default = False,
                           label = BASE_LAYER,
                           represent = s3_yes_no_represent,
                           ),
                     Field("transparent", "boolean",
                           default = True,
                           label = TRANSPARENT,
                           represent = s3_yes_no_represent,
                           ),
                     Field("img_format", length=32,
                           default = "png",
                           label = FORMAT,
                           requires = IS_EMPTY_OR(IS_IN_SET(arc_img_formats)),
                           ),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # Bing tiles
        #
        bing_layer_types = ("aerial", "road", "hybrid")

        tablename = "gis_layer_bing"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("type", length=16,
                           label = TYPE,
                           requires = IS_IN_SET(bing_layer_types),
                           ),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # Coordinate grid
        #
        tablename = "gis_layer_coordinate"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # Empty (no baselayer, so can display just overlays)
        #
        tablename = "gis_layer_empty"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # GeoJSON
        #
        tablename = "gis_layer_geojson"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("url",
                           label = LOCATION,
                           represent = lambda url: \
                            url and A(url, _href=url) or NONE,
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     Field("file", "upload",
                           autodelete = False,
                           #custom_retrieve = gis_marker_retrieve,
                           #custom_retrieve_file_properties = gis_marker_retrieve_file_properties,
                           #custom_store?
                           label = T("File"),
                           length = MAX_FILENAME_LENGTH,
                           represent = self.gis_layer_geojson_file_represent,
                           requires = IS_EMPTY_OR(
                                        IS_UPLOAD_FILENAME(extension="geojson"),
                                        null = "", # Distinguish from Prepop
                                        ),
                           # upload folder needs to be visible to the download() function as well as the upload
                           uploadfolder = os.path.join(folder,
                                                       "static",
                                                       "cache",
                                                       "geojson"),
                           ),
                     projection_id(# Nice if we could get this set to epsg field
                                   #default = 4326,
                                   empty = False,
                                   ),
                     gis_refresh()(),
                     cluster_attribute()(),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  create_next = URL(args=["[id]", "style"]),
                  deduplicate = S3Duplicate(),
                  onaccept = self.gis_layer_geojson_onaccept,
                  onvalidation = self.gis_layer_file_onvalidation,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # GeoRSS
        #
        tablename = "gis_layer_georss"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("url",
                           label = LOCATION,
                           represent = lambda url: \
                            url and A(url, _href=url) or NONE,
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     Field("data",
                           label = T("Data"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s|%s" % (T("Data"),
                                                              T("Optional. The name of an element whose contents should be put into Popups."),
                                                              T("If it is a URL leading to HTML, then this will downloaded."))),
                           ),
                     Field("image",
                           label = T("Image"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Image"),
                                                           T("Optional. The name of an element whose contents should be a URL of an Image file put into Popups."))),
                           ),
                     gis_refresh()(),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("url",),
                                            ignore_case = False,
                                            ),
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # Google tiles
        #
        google_layer_types = ("satellite", "maps", "hybrid", "terrain",
                              "mapmaker", "mapmakerhybrid",
                              "earth", "streetview")

        tablename = "gis_layer_google"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("type", length=16,
                           label = TYPE,
                           requires = IS_IN_SET(google_layer_types),
                           ),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # GPX - GPS eXchange format
        #
        tablename = "gis_layer_gpx"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("track", "upload",
                           autodelete=True,
                           label = T("GPS Track File"),
                           length = MAX_FILENAME_LENGTH,
                           requires = IS_UPLOAD_FILENAME(extension="gpx"),
                           # upload folder needs to be visible to the download() function as well as the upload
                           uploadfolder = os.path.join(folder,
                                                       "uploads",
                                                       "tracks"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("GPS Track"),
                                                           T("A file in GPX format taken from a GPS."),
                                                           #T("Timestamps can be correlated with the timestamps on the photos to locate them on the map.")
                                                          )),
                           ),
                     Field("waypoints", "boolean",
                           default = True,
                           label = T("Display Waypoints?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("tracks", "boolean",
                           default = True,
                           label = T("Display Tracks?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("routes", "boolean",
                           default = False,
                           label = T("Display Routes?"),
                           represent = s3_yes_no_represent,
                           ),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # JS
        # - raw JavaScript code for advanced users
        # @ToDo: Move to a Plugin (more flexible)
        #
        tablename = "gis_layer_js"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("code", "text",
                           default = "var myNewLayer = new OpenLayers.Layer.XYZ();\nmap.addLayer(myNewLayer);",
                           label = T("Code"),
                           ),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # KML
        #
        tablename = "gis_layer_kml"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("url",
                           label = LOCATION,
                           represent = lambda url: \
                            url and A(url, _href=url) or NONE,
                           requires = IS_EMPTY_OR(IS_URL()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (LOCATION,
                                                           T("The URL to access the service."))),
                           ),
                     Field("file", "upload",
                           autodelete = False,
                           #custom_retrieve = gis_marker_retrieve,
                           #custom_retrieve_file_properties = gis_marker_retrieve_file_properties,
                           #custom_store?
                           label = T("File"),
                           length = MAX_FILENAME_LENGTH,
                           represent = self.gis_layer_kml_file_represent,
                           requires = IS_EMPTY_OR(
                                        IS_UPLOAD_FILENAME(extension="kml"),
                                        null = "", # Distinguish from Prepop
                                        ),
                           # upload folder needs to be visible to the download() function as well as the upload
                           uploadfolder = os.path.join(folder,
                                                       "static",
                                                       "cache",
                                                       "kml"),
                           ),
                     Field("title",
                           default = "name",
                           label = T("Title"),
                           comment = T("The attribute within the KML which is used for the title of popups."),
                           ),
                     Field("body",
                           default = "description",
                           label = T("Body"),
                           comment = T("The attribute(s) within the KML which are used for the body of popups. (Use a space between attributes)"),
                           ),
                     gis_refresh()(),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("url",),
                                            ignore_case = False,
                                            ),
                  onaccept = self.gis_layer_kml_onaccept,
                  onvalidation = self.gis_layer_file_onvalidation,
                  super_entity="gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # MGRS
        #
        tablename = "gis_layer_mgrs"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("url",
                           label = LOCATION,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (LOCATION,
                                                           T("The URL to access the service."))),
                           ),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # OpenStreetMap tiles
        #
        # @ToDo: Provide a catalogue of standard layers which are fully-defined
        #        in static & can just have name over-ridden, as well as
        #        fully-custom layers.
        #
        tablename = "gis_layer_openstreetmap"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("url1",
                           label = LOCATION,
                           requires = IS_NOT_EMPTY(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (LOCATION,
                                                           T("The URL to access the service."))),
                           ),
                     Field("url2",
                           label = T("Secondary Server (Optional)"),
                           ),
                     Field("url3",
                           label = T("Tertiary Server (Optional)"),
                           ),
                     Field("base", "boolean",
                           default = True,
                           label = BASE_LAYER,
                           represent = s3_yes_no_represent,
                           ),
                     Field("attribution",
                           label = T("Attribution"),
                           ),
                     Field("zoom_levels", "integer",
                           default = 19,
                           label = T("Zoom Levels"),
                           requires = IS_INT_IN_RANGE(1, 30),
                           ),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("url1",),
                                            ignore_case = False,
                                            ),
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # OpenWeatherMap
        #
        openweathermap_layer_types = ("station", "city")

        tablename = "gis_layer_openweathermap"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("type", length=16,
                           label = TYPE,
                           requires = IS_IN_SET(openweathermap_layer_types),
                           ),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # Shapefiles
        #
        gis_feature_type_opts = self.gis_feature_type_opts

        tablename = "gis_layer_shapefile"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     source_name_field()(),
                     source_url_field()(),
                     Field("shape", "upload",
                           autodelete = True,
                           label = T("ESRI Shape File"),
                           length = MAX_FILENAME_LENGTH,
                           requires = IS_UPLOAD_FILENAME(extension="zip"),
                           # upload folder needs to be visible to the download() function as well as the upload
                           uploadfolder = os.path.join(folder,
                                                       "uploads",
                                                       "shapefiles"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("ESRI Shape File"),
                                                           T("An ESRI Shapefile (zipped)"),
                                                           )),
                           ),
                     Field("gis_feature_type", "integer",
                           label = T("Feature Type"),
                           represent = lambda opt: \
                           gis_feature_type_opts.get(opt,
                                                     messages.UNKNOWN_OPT),
                           requires = IS_EMPTY_OR(
                                        IS_IN_SET(gis_feature_type_opts,
                                                  zero=None)),
                           # Auto-populated by reading Shapefile
                           writable = False,
                           ),
                     # @ToDo: Can we auto-populate this from the layer?
                     projection_id(# Nice if we could get this set to epsg field without having to do a DB lookup
                                   #default = 4326,
                                   empty = False,
                                   ),
                     Field("filter",
                           label = T("REST Filter"),
                           comment = DIV(_class="stickytip",
                                         _title="%s|%s" % (T("REST Filter"),
                                                           "%s: <a href='http://eden.sahanafoundation.org/wiki/S3XRC/RESTfulAPI/URLFormat#BasicQueryFormat' target='_blank'>Trac</a>" % \
                                                            T("Uses the REST Query Format defined in"))),
                           ),
                     # @ToDo: Switch type to "json" & Test
                     Field("data", "text",
                           label = T("Attributes"),
                           represent = lambda v: v or NONE,
                           # Auto-populated by reading Shapefile
                           readable = False,
                           writable = False,
                           ),
                     # @ToDo
                     #gis_refresh()(),
                     cluster_attribute()(),
                     s3_role_required(), # Single Role
                     *s3_meta_fields())

        configure(tablename,
                  create_onaccept = self.gis_layer_shapefile_onaccept,
                  # Match if name is identical (not ideal):
                  deduplicate = S3Duplicate(ignore_case=False),
                  #update_onaccept = self.gis_layer_shapefile_onaccept_update,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # TMS
        #
        tablename = "gis_layer_tms"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("url",
                           label = LOCATION,
                           requires = IS_NOT_EMPTY(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (LOCATION,
                                                           T("The URL to access the service."))),
                           ),
                     Field("url2",
                           label = T("Secondary Server (Optional)"),
                           ),
                     Field("url3",
                           label = T("Tertiary Server (Optional)"),
                           ),
                     Field("layername",
                           label = T("Layer Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("img_format",
                           label = FORMAT,
                           ),
                     Field("attribution",
                           label = T("Attribution"),
                           ),
                     Field("zoom_levels", "integer",
                           default = 19,
                           label = T("Zoom Levels"),
                           requires = IS_INT_IN_RANGE(1, 30),
                           ),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # WFS
        #
        tablename = "gis_layer_wfs"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     source_name_field()(),
                     source_url_field()(),
                     Field("url",
                           label = LOCATION,
                           requires = IS_NOT_EMPTY(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (LOCATION,
                                                           T("Mandatory. The base URL to access the service. e.g. http://host.domain/geoserver/wfs?"))),
                           ),
                     Field("featureType",
                           label = T("Feature Type"),
                           requires = IS_NOT_EMPTY(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Feature Type"),
                                                           T("Mandatory. In GeoServer, this is the Layer Name. Within the WFS getCapabilities, this is the FeatureType Name part after the colon(:)."))),
                           ),
                     Field("featureNS",
                           label = T("Feature Namespace"),
                           requires = IS_EMPTY_OR(IS_URL()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Feature Namespace"),
                                                           T("Optional. In GeoServer, this is the Workspace Namespace URI (not the name!). Within the WFS getCapabilities, the workspace is the FeatureType Name part before the colon(:)."))),
                           ),
                     Field("title",
                           default = "name",
                           label = T("Title"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Title"),
                                                           T("The attribute which is used for the title of popups."))),
                           ),
                     Field("username",
                           label = T("Username"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Username"),
                                                           T("Optional username for HTTP Basic Authentication."))),
                           ),
                     Field("password",
                           label = T("Password"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Password"),
                                                           T("Optional password for HTTP Basic Authentication."))),
                           ),
                     Field("geometryName",
                           default = "the_geom",
                           label = T("Geometry Name"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Geometry Name"),
                                                           T("Optional. The name of the geometry column. In PostGIS this defaults to 'the_geom'."))),
                           ),
                     Field("wfs_schema",
                           label = T("Schema"),
                           requires = IS_EMPTY_OR(IS_URL()),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Schema"),
                                                           T("Optional. The name of the schema. In Geoserver this has the form http://host_name/geoserver/wfs/DescribeFeatureType?version=1.1.0&;typename=workspace_name:layer_name."))),
                           ),
                     projection_id(# Nice if we could get this set to epsg field
                                   #default = 4326,
                                   empty = False,
                                   ),
                     Field("version",
                           default = "1.1.0",
                           label = T("Version"),
                           requires = IS_IN_SET(["1.0.0", "1.1.0", "2.0.0"],
                                                zero=None),
                           ),
                     gis_refresh()(default=0), # Default to Off as 'External Source' which is uneditable
                      cluster_attribute()(),
                     #Field("editable", "boolean", default=False, label=T("Editable?")),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  deduplicate = S3Duplicate(primary = ("url",
                                                       "featureType",
                                                       ),
                                            ignore_case = False,
                                            ),
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # WMS
        #
        wms_img_formats = ("image/jpeg", "image/jpeg;mode=24bit", "image/png",
                           "image/gif", "image/bmp", "image/tiff",
                           "image/svg+xml")

        tablename = "gis_layer_wms"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     source_name_field()(),
                     source_url_field()(),
                     Field("url",
                           label = LOCATION,
                           requires = IS_NOT_EMPTY(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (LOCATION,
                                                           T("Mandatory. The base URL to access the service. e.g. http://host.domain/geoserver/wms?"))),
                           ),
                     Field("version", length=32,
                           default = "1.1.1",
                           label = T("Version"),
                           requires = IS_IN_SET(["1.1.1", "1.3.0"], zero=None),
                           ),
                     Field("base", "boolean",
                           default = False,
                           label = BASE_LAYER,
                           represent = s3_yes_no_represent,
                           ),
                     Field("transparent", "boolean",
                           default = True,
                           label = TRANSPARENT,
                           represent = s3_yes_no_represent,
                           ),
                     gis_opacity()(),
                     Field("map", length=32,
                           label = T("Map"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Map"),
                                                           T("Optional selection of a MapServer map."))),
                           requires = IS_LENGTH(32),
                           ),
                     Field("layers",
                           label = T("Layers"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     Field("username",
                           label = T("Username"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Username"),
                                                           T("Optional username for HTTP Basic Authentication."))),
                           ),
                     Field("password",
                           label = T("Password"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Password"),
                                                           T("Optional password for HTTP Basic Authentication."))),
                           ),
                     Field("img_format", length=32,
                           default = "image/png",
                           label = FORMAT,
                           requires = IS_EMPTY_OR(IS_IN_SET(wms_img_formats)),
                           ),
                     # NB This is a WMS-server-side style NOT an internal JSON style
                     Field("style", length=32,
                           label = T("Style"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Style"),
                                                           T("Optional selection of an alternate style."))),
                           requires = IS_LENGTH(32),
                           ),
                     Field("bgcolor", length=32,
                           label = T("Background Color"),
                           requires = IS_EMPTY_OR(IS_HTML_COLOUR()),
                           widget = S3ColorPickerWidget(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Background Color"),
                                                           T("Optional selection of a background color."))),
                           ),
                     Field("tiled", "boolean",
                           default = False,
                           label = T("Tiled"),
                           represent = s3_yes_no_represent,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s|%s" % (T("Tiled"),
                                                              T("Tells GeoServer to do MetaTiling which reduces the number of duplicate labels."),
                                                              T("Note that when using geowebcache, this can be set in the GWC config."))),
                           ),
                     Field("buffer", "integer",
                           default = 0,
                           label = T("Buffer"),
                           requires = IS_INT_IN_RANGE(0, 10),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Buffer"),
                                                           T("The number of tiles around the visible map to download. Zero means that the 1st page loads faster, higher numbers mean subsequent panning is faster."))),
                           ),
                     Field("queryable", "boolean",
                           default = True,
                           label = T("Queryable?"),
                           represent = s3_yes_no_represent,
                           ),
                     Field("legend_url",
                           label = T("Legend URL"),
                           represent = lambda v: v or NONE,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Legend URL"),
                                                           T("Address of an image to use for this Layer in the Legend. This allows use of a controlled static image rather than querying the server automatically for what it provides (which won't work through GeoWebCache anyway)."))),
                           ),
                     #Field("legend_format",
                     #      label = T("Legend Format"),
                     #      requires = IS_EMPTY_OR(IS_IN_SET(gis_layer_wms_img_formats)),
                     #      ),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # XYZ
        # - e.g. used by OSM community for JOSM/Potlatch
        #
        # @ToDo: Support Overlays with Opacity
        #
        tablename = "gis_layer_xyz"
        define_table(tablename,
                     layer_id(),
                     name_field()(),
                     desc_field()(),
                     Field("url",
                           label = LOCATION,
                           requires = IS_NOT_EMPTY(),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (LOCATION,
                                                           T("The URL to access the service."))),
                           ),
                     Field("url2",
                           label = T("Secondary Server (Optional)"),
                           ),
                     Field("url3",
                           label = T("Tertiary Server (Optional)"),
                           ),
                     Field("img_format",
                           label = FORMAT,
                           ),
                     Field("attribution",
                           label = T("Attribution"),
                           ),
                     Field("zoom_levels", "integer",
                           default = 19,
                           label = T("Zoom Levels"),
                           requires = IS_INT_IN_RANGE(1, 30),
                           ),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        configure(tablename,
                  onaccept = gis_layer_onaccept,
                  super_entity = "gis_layer_entity",
                  )

        # ---------------------------------------------------------------------
        # GIS Cache
        # ---------------------------------------------------------------------
        # Store downloaded GeoRSS feeds in the DB
        # - to allow refresh timer, BBOX queries, unified approach to Markers & Popups
        #
        tablename = "gis_cache"
        define_table(tablename,
                     Field("title"),
                     Field("description"),
                     Field("link"),      # Used by GeoRSS
                     Field("data"),
                     Field("image"),
                     Field("lat", "double"),
                     Field("lon", "double"),
                     Field("marker"),    # Used by KML
                     Field("source",
                           requires = IS_EMPTY_OR(IS_URL()),
                           ),
                     *s3_meta_fields())

        # Store downloaded KML feeds on the filesystem
        # @ToDo: Migrate to DB instead (using above gis_cache)
        #
        tablename = "gis_cache2"
        define_table(tablename,
                     Field("name", length=128, notnull=True, unique=True,
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(128),
                                       ],
                           ),
                     Field("file", "upload",
                           autodelete = True,
                           custom_retrieve = self.gis_cache2_retrieve,
                           # upload folder needs to be visible to the download() function as well as the upload
                           length = MAX_FILENAME_LENGTH,
                           uploadfolder = os.path.join(folder,
                                                       "uploads",
                                                       "gis_cache"),
                           ),
                     *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_cache2_retrieve(filename, path=None):
        """
            custom_retrieve to override web2py DAL's standard retrieve,
            as that checks filenames for uuids, so doesn't work with
            pre-populated files in static
        """

        if not path:
            path = current.db.gis_cache2.file.uploadfolder

        f = open(os.path.join(path, filename), "rb")
        return (filename, f)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_file_onvalidation(form):
        """
            Check we have either a URL or a file
        """

        form_vars = form.vars
        doc = form_vars.file

        if doc is None:
            # If this is a prepop, then file not in form
            # Interactive forms with empty doc has this as "" not None
            return

        if not hasattr(doc, "file") and not doc and not form_vars.url:
            msg = current.T("Either file upload or URL required.")
            form.errors.file = msg
            form.errors.url = msg

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_geojson_file_represent(filename):
        """ File representation """

        if filename:
            try:
                # Check whether file exists and extract the original
                # file name from the stored file name
                orig_filename = current.db.gis_layer_geojson.file.retrieve(filename)[0]
            except IOError:
                return current.T("File not found")
            else:
                return A(orig_filename,
                         _href = URL(c = "static",
                                     f = "cache",
                                     args = ["geojson", filename],
                                     ),
                         )
        else:
            return current.messages["NONE"]

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_geojson_onaccept(form):
        """
            If we have a file, then set the URL to point to it
        """

        layer_id = form.vars.id

        table = current.s3db.gis_layer_geojson
        record = current.db(table.id == layer_id).select(table.id,
                                                         table.file,
                                                         limitby = (0, 1),
                                                         ).first()
        if record and record.file:
            # Use the filename to build the URL
            record.update_record(url = URL(c = "static",
                                           f = "cache",
                                           args = ["geojson", record.file],
                                           ),
                                 # Set refresh to 0 (static file)
                                 refresh = 0,
                                 )

        # Normal Layer onaccept
        gis_layer_onaccept(form)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_kml_file_represent(filename):
        """ File representation """

        if filename:
            try:
                # Check whether file exists and extract the original
                # file name from the stored file name
                orig_filename = current.db.gis_layer_kml.file.retrieve(filename)[0]
            except IOError:
                return current.T("File not found")
            else:
                return A(orig_filename,
                         _href = URL(c = "static",
                                     f = "cache",
                                     args = ["kml", filename],
                                     ),
                         )
        else:
            return current.messages["NONE"]

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_kml_onaccept(form):
        """
            If we have a file, then set the URL to point to it
        """

        layer_id = form.vars.id

        table = current.s3db.gis_layer_kml
        record = current.db(table.id == layer_id).select(table.id,
                                                         table.file,
                                                         limitby = (0, 1),
                                                         ).first()
        if record and record.file:
            # Use the filename to build the URL
            record.update_record(url = URL(c = "static",
                                           f = "cache",
                                           args = ["kml", record.file],
                                           ),
                                 # Set refresh to 0 (static file)
                                 refresh = 0,
                                 )

        # Normal Layer onaccept
        gis_layer_onaccept(form)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_shapefile_onaccept(form):
        """
            Convert the Uploaded Shapefile to GeoJSON for display on the map
        """

        shapefile_id = form.vars.id
        db = current.db
        tablename = "gis_layer_shapefile_%s" % shapefile_id
        if tablename in db:
            # Table already defined, so can quit here
            return
        try:
            from osgeo import ogr
        except ImportError:
            current.response.error = current.T("Python GDAL required for Shapefile support!")
            # NB We could include this instead: https://code.google.com/p/pyshp/
        else:
            # Retrieve the file & projection
            table = db.gis_layer_shapefile
            ptable = db.gis_projection
            query = (table.id == shapefile_id) & \
                    (ptable.id == table.projection_id)
            row = db(query).select(table.shape,
                                   ptable.epsg,
                                   limitby=(0, 1)).first()
            try:
                shapefile = table.shape.retrieve(row.gis_layer_shapefile.shape)
            except:
                current.log.error("No Shapefile found in layer %s!" % shapefile_id)
                return
            (fileName, fp) = shapefile
            layerName = fileName.rsplit(".", 1)[0] # strip the .zip extension

            # Copy the current working directory to revert back to later
            cwd = os.getcwd()
            # Create the working directory
            TEMP = os.path.join(cwd, "temp")
            if not os.path.exists(TEMP): # use web2py/temp
                import tempfile
                TEMP = tempfile.gettempdir()
            tempPath = os.path.join(TEMP, "Shapefiles")
            if not os.path.exists(tempPath):
                try:
                    os.mkdir(tempPath)
                except OSError:
                    current.log.error("Unable to create temp folder %s!" % tempPath)
                    return
            # Set the current working directory
            os.chdir(tempPath)

            # Unzip the file
            import zipfile
            myfile = zipfile.ZipFile(fp)
            for ext in ("dbf", "prj", "sbn", "sbx", "shp", "shx"):
                fileName = "%s.%s" % (layerName, ext)
                try:
                    infile = myfile.read(fileName)
                except KeyError:
                    current.log.error("%s.zip doesn't contain a file %s" % (layerName, fileName))
                else:
                    f = open(fileName, "wb")
                    f.write(infile)
                    f.close()
            myfile.close()
            fp.close()

            projection = row["gis_projection.epsg"]
            # @ToDo:
            #if !projection:
            #     # Read from .prj file (if-present)
            if projection != 4326:
                # Set up reprojections
                reproject = True
                from osgeo import osr
                inSpatialRef = osr.SpatialReference()
                inSpatialRef.ImportFromEPSG(projection)
                outSpatialRef = osr.SpatialReference()
                outSpatialRef.ImportFromEPSG(4326)
                coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
            else:
                reproject = False

            # Handle dates
            from dateutil import parser
            parse_date = parser.parse

            # Use OGR to read Shapefile
            shapefile = "%s.shp" % layerName
            ds = ogr.Open(shapefile)
            if ds is None:
                current.response.error = current.T("Couldn't open %s!") % shapefile
                # Revert back to the working directory as before.
                os.chdir(cwd)
                return
            lyr = ds.GetLayerByName(layerName)
            lyr.ResetReading()

            spatialdb = current.deployment_settings.get_gis_spatialdb()

            # Get the Data Model
            geom_type = lyr.GetGeomType() # All features within a Shapefile share a common geometry
            wkbPoint = ogr.wkbPoint
            OFTInteger = ogr.OFTInteger
            OFTReal = ogr.OFTReal
            OFTDate = ogr.OFTDate
            OFTDateTime = ogr.OFTDateTime
            OFTTime = ogr.OFTTime
            lyr_defn = lyr.GetLayerDefn()
            nFields = lyr_defn.GetFieldCount()
            GetFieldDefn = lyr_defn.GetFieldDefn
            fields = []
            append = fields.append
            for i in range(nFields):
                field_defn = GetFieldDefn(i)
                fname = field_defn.GetName()
                if fname.lower() == "id":
                    fname = "id_orig"
                elif fname.lower() == "lat":
                    fname = "lat_orig"
                elif fname.lower() == "lon":
                    fname = "lon_orig"
                else:
                    try:
                        db.check_reserved_keyword(fname)
                    except SyntaxError:
                        fname = "%s_orig" % fname
                ftype = field_defn.GetType()
                if ftype == OFTInteger:
                    ftype = "integer"
                elif ftype == OFTReal:
                    ftype = "double"
                elif ftype == OFTDate:
                    ftype = "date"
                elif ftype == OFTDateTime:
                    ftype = "datetime"
                elif ftype == OFTTime:
                    ftype = "time"
                else:
                    # Assume String (ogr.OFTString/OFTWideString)
                    ftype = "string"
                append((fname, ftype))

            # Get the Data
            features = []
            append = features.append
            for feature in lyr:
                f = {}
                # Get the Attributes
                for i in range(nFields):
                    fname = fields[i][0]
                    ftype = fields[i][1]
                    value = feature.GetField(i)
                    if ftype in ("date", "datetime"):
                        f[fname] = parse_date(value)
                    else:
                        f[fname] = value

                # Get the Geometry
                geom = feature.GetGeometryRef()
                if geom is None:
                    lat = lon = wkt = None
                else:
                    if reproject:
                        geom.Transform(coordTransform)
                    if geom_type == wkbPoint:
                        lon = geom.GetX()
                        lat = geom.GetY()
                        wkt = "POINT(%f %f)" % (lon, lat)
                    else:
                        wkt = geom.ExportToWkt()
                        centroid = geom.Centroid()
                        lon = centroid.GetX()
                        lat = centroid.GetY()
                        # @ToDo: Bounds?
                f["lat"] = lat
                f["lon"] = lon
                f["wkt"] = wkt
                if spatialdb:
                    f["the_geom"] = wkt
                f["layer_id"] = shapefile_id
                append(f)

            # Close the shapefile
            ds = None

            # Revert back to the working directory as before.
            os.chdir(cwd)

            # Convert table structure to JSON
            data = json.dumps(fields)
            # Update the record
            db(table.id == shapefile_id).update(gis_feature_type = geom_type,
                                                data = data,
                                                )

            # Create Database table to store these features in
            Fields = [Field("lat", "float"),
                      Field("lon", "float"),
                      Field("wkt", "text"),
                      Field("layer_id", table),
                      ]
            append = Fields.append
            for field in fields:
                append(Field(field[0], field[1]))
            if spatialdb:
                # Add a spatial field
                append(Field("the_geom", "geometry()"))
            db._migrate_enabled = True
            db.define_table(tablename, *Fields)
            dbtable = db[tablename]
            db._migrate_enabled = False
            # Clear old data if-any
            dbtable.truncate()
            # Populate table with data
            for feature in features:
                dbtable.insert(**feature)

        # Normal Layer onaccept
        gis_layer_onaccept(form)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_shapefile_onaccept_update(form):
        """
            @ToDo: Check if the file has changed & run the normal onaccept if-so
        """

        S3MapModel.gis_layer_shapefile_onaccept(form)

# =============================================================================
class S3GISThemeModel(S3Model):
    """
        Thematic Mapping model

        @ToDo: Deprecate since we now have this functionality available for normal feature layers?
    """

    names = ("gis_layer_theme",
             "gis_theme_data",
             "gis_layer_theme_id",
             )

    def model(self):

        T = current.T
        db = current.db

        define_table = self.define_table

        # =====================================================================
        # Theme Layer
        #

        tablename = "gis_layer_theme"
        define_table(tablename,
                     self.super_link("layer_id", "gis_layer_entity"),
                     name_field()(unique = True),
                     desc_field()(),
                     # @ToDo:
                     #self.stats_parameter_id(),
                     Field("date", "datetime",
                           label = T("Date"),
                           ),
                     s3_role_required(),       # Single Role
                     #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                     *s3_meta_fields())

        self.configure(tablename,
                       super_entity = "gis_layer_entity",
                       )

        # Components
        self.add_components(tablename,
                            # Configs
                            gis_config = {"link": "gis_layer_config",
                                          "pkey": "layer_id",
                                          "joinby": "layer_id",
                                          "key": "config_id",
                                          "actuate": "hide",
                                          "autocomplete": "name",
                                          "autodelete": False,
                                          },
                            gis_theme_data = "layer_theme_id",
                            )

        represent = S3Represent(lookup=tablename)
        layer_theme_id = S3ReusableField("layer_theme_id", "reference %s" % tablename,
                                         label = "Theme Layer",
                                         ondelete = "CASCADE",
                                         represent = represent,
                                         requires = IS_ONE_OF(db,
                                                              "gis_layer_theme.id",
                                                              represent
                                                              ),
                                         )

        # Custom Method to generate a style
        self.set_method("gis", "layer_theme",
                        method = "style",
                        action = self.gis_theme_style)

        # =====================================================================
        # GIS Theme Data
        #
        # @ToDo: Replace this with gis_location_tag?
        #        - layer just selects a tag to filter on?
        #

        tablename = "gis_theme_data"
        define_table(tablename,
                     layer_theme_id(),
                     self.gis_location_id(
                         requires = IS_LOCATION(level=("L1", "L2", "L3", "L4")),
                         widget = S3LocationAutocompleteWidget(),
                     ),
                     Field("value",
                           label = T("Value"),
                           ),
                     *s3_meta_fields())

        current.response.s3.crud_strings[tablename] = Storage(
            label_create = T("Add Data to Theme Layer"),
            title_display = T("Theme Data"),
            title_list = T("Theme Data"),
            title_update = T("Edit Theme Data"),
            title_upload = T("Import Data for Theme Layer"),
            label_list_button = T("List Data in Theme Layer"),
            label_delete_button = T("Delete Data from Theme layer"),
            msg_record_created = T("Data added to Theme Layer"),
            msg_record_modified = T("Theme Data updated"),
            msg_record_deleted = T("Theme Data deleted"),
            msg_list_empty = T("No Data currently defined for this Theme Layer")
        )

        # Pass names back to global scope (s3.*)
        return {"gis_layer_theme_id": layer_theme_id,
                }

    # ---------------------------------------------------------------------
    @staticmethod
    def gis_theme_style(r, **attr):
        """
            Custom method to create a Style for a Theme Layer
            - splits data into 5 quintiles
            - uses Colorbrewer to create a 5-class colorblind-safe printer-friendly Sequential scheme

            @ToDo: Divergent colour scheme option
            @ToDo: Select # of classes
            @ToDo: Select full range of colour schemes
            @ToDo: Alternate class breaks mechanisms (pretty breaks, etc)
        """

        classes = 5
        nature = "sequential"

        db = current.db
        table = db.gis_theme_data
        rows = db(table.layer_theme_id == r.id).select(table.value)
        values = [float(row.value) for row in rows]
        q = []
        qappend = q.append
        for i in range(classes - 1):
            qappend(1.0 / classes * (i + 1))
        breaks = current.s3db.stats_quantile(values, q)
        # Make mutable
        breaks = list(breaks)
        values_min = min(values)
        values_max = max(values)
        breaks.insert(0, values_min)
        breaks.append(values_max)

        if nature == "sequential":
            # PuRd
            colours = ["F1EEF6", "D7B5D8", "DF65B0", "DD1C77", "980043"]
        elif nature == "divergent":
            # BrBG
            colours = ["A6611A", "DFC27D", "F5F5F5", "80CDC1", "018571"]

        style = []
        sappend = style.append
        for i in range(classes):
            sappend({"low": breaks[i],
                     "high": breaks[i + 1],
                     "fill": colours[i]
                     })

        current.response.headers["Content-Type"] = "application/json"
        return json.dumps(style)

# =============================================================================
class S3PoIModel(S3Model):
    """
        Data Model for PoIs (Points of Interest)
    """

    names = ("gis_poi_type",
             #"gis_poi_type_tag",
             "gis_poi",
             "gis_poi_id",
             )

    def model(self):

        db = current.db
        T = current.T
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # PoI Category
        #
        # @ToDo: Optionally restrict by Feature Type?
        #
        tablename = "gis_poi_type"
        define_table(tablename,
                     Field("name",
                           label = T("Name"),
                           requires = IS_NOT_EMPTY(),
                           ),
                     self.gis_marker_id(),
                     s3_comments(),
                     *s3_meta_fields())

        represent = S3Represent(lookup=tablename, translate=True)
        poi_type_id = S3ReusableField("poi_type_id", "reference %s" % tablename,
                                      label = T("Type"),
                                      ondelete = "SET NULL",
                                      represent = represent,
                                      requires = IS_EMPTY_OR(
                                        IS_ONE_OF(db, "gis_poi_type.id",
                                                  represent)),
                                      sortby = "name",
                                      )

        self.configure(tablename,
                       deduplicate = S3Duplicate(),
                       onaccept = self.gis_poi_type_onaccept,
                       )

        crud_strings[tablename] = Storage(
            label_create = T("Create PoI Type"),
            title_display = T("PoI Type Details"),
            title_list = T("PoI Types"),
            title_update = T("Edit PoI Type"),
            title_upload = T("Import PoI Types"),
            label_list_button = T("List PoI Types"),
            label_delete_button = T("Delete PoI Type"),
            msg_record_created = T("PoI Type added"),
            msg_record_modified = T("PoI Type updated"),
            msg_record_deleted = T("PoI Type deleted"),
            msg_list_empty = T("No PoI Types currently available"))

        # ---------------------------------------------------------------------
        # PoI
        #
        tablename = "gis_poi"
        define_table(tablename,
                     poi_type_id(),
                     Field("name",
                           label = T("Title"),
                           #requires = IS_NOT_EMPTY(),
                           ),
                     s3_comments(comment = None,
                                 label = T("Description"),
                                 ),
                     self.gis_location_id(
                         ondelete = "CASCADE",
                         requires = IS_LAT_LON("gis_poi_location_id"),
                         # @ToDo: S3PoIWidget() to allow other resources to pickup the passed Lat/Lon/WKT
                         widget = S3LocationLatLonWidget(),
                     ),
                     # Enable in Templates as-required
                     self.org_organisation_id(readable = False,
                                              writable = False,
                                              ),
                     # Enable in Templates as-required
                     self.pr_person_id(readable = False,
                                       writable = False,
                                       ),
                     *s3_meta_fields())

        crud_strings[tablename] = Storage(
            label_create = T("Create Point of Interest"),
            title_display = T("Point of Interest Details"),
            title_list = T("Points of Interest"),
            title_update = T("Edit Point of Interest"),
            title_upload = T("Import Points of Interest"),
            label_list_button = T("List Points of Interest"),
            label_delete_button = T("Delete Point of Interest"),
            msg_record_created = T("Point of Interest added"),
            msg_record_modified = T("Point of Interest updated"),
            msg_record_deleted = T("Point of Interest deleted"),
            msg_list_empty = T("No Points of Interest currently available"))

        represent = S3Represent(lookup=tablename)
        poi_id = S3ReusableField("poi_id", "reference %s" % tablename,
                                 label = T("Point of Interest"),
                                 ondelete = "RESTRICT",
                                 represent = represent,
                                 requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db, "gis_poi.id",
                                                          represent)
                                                ),
                                 sortby = "name",
                                 )

        self.configure(tablename,
                       onaccept = self.gis_poi_onaccept,
                       )

        # Components
        self.add_components(tablename,
                            # Organisation Groups (Coalitions/Networks)
                            org_group = {"link": "gis_poi_group",
                                         "joinby": "poi_id",
                                         "key": "group_id",
                                         "actuate": "hide",
                                         },
                            # Format for InlineComponent/filter_widget
                            gis_poi_group = "poi_id",
                            )

        # Pass names back to global scope (s3.*)
        return {"gis_poi_id": poi_id,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_poi_onaccept(form):
        """
            If the Comments are a Style then create a gis_style record for this
            and blank the comment. Used for s3csv imports as we have no components & can't use an import_prep as we don't know the record_id
        """

        form_vars = form.vars
        comments = form_vars.get("comments")
        if not comments:
            # Nothing to do
            return

        value = comments.replace("'", "\"")
        try:
            style = json.loads(value)
        except:
            # Not a style
            return

        db = current.db
        s3db = current.s3db

        # Lookup the PoI Type
        table = s3db.gis_poi_type
        poi_type = db(table.id == form_vars.poi_type_id).select(table.name,
                                                                limitby=(0, 1)
                                                                ).first()
        try:
            poi_type = poi_type.name
        except AttributeError:
            # Bail
            return

        # Lookup the Layer
        table = s3db.gis_layer_feature
        query = (table.controller == "gis") & \
                (table.function == "poi") & \
                ((table.filter == None) | \
                 (table.filter == "poi_type.name__typeof=%s" % poi_type))
        postgres = current.deployment_settings.get_database_type() == "postgres"
        if postgres:
            # None is last
            orderby = table.filter
        else:
            # None is 1st
            orderby = ~table.filter
        layer = db(query).select(table.layer_id,
                                 table.filter,
                                 limitby=(0, 1),
                                 orderby = orderby,
                                 ).first()
        try:
            layer_id = layer.layer_id
        except AttributeError:
            # No layer to style
            current.log.warning("Couldn't find a layer to use for this PoI Style")
            return

        # Create a Style record
        record_id = form_vars.id
        table = s3db.gis_style
        table.insert(layer_id = layer_id,
                     record_id = record_id,
                     style = style,
                     )

        # Cleanup the Comments
        db(db.gis_poi.id == record_id).update(comments = None)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_poi_type_onaccept(form):
        """
            Update Style for the PoIs layer

            @ToDo: deployment_setting to add a new Feature Layer for new PoI types
        """

        db = current.db
        s3db = current.s3db

        # Read all PoI Types and their Markers
        ptable = s3db.gis_poi_type
        mtable = s3db.gis_marker
        query = (ptable.deleted == False) & \
                (mtable.id == ptable.marker_id)
        rows = db(query).select(ptable.name,
                                mtable.image,
                                )

        # Build Style File
        style = []
        sappend = style.append
        for row in rows:
            marker = row["gis_marker.image"]
            if marker:
                cat = {"prop": "poi_type_id",
                       "cat": row["gis_poi_type.name"],
                       "externalGraphic": "img/markers/%s" % marker
                       }
                sappend(cat)

        # Find correct Layer record
        ltable = s3db.gis_layer_feature
        query = (ltable.controller == "gis") & \
                (ltable.function == "poi") & \
                (ltable.filter == None) & \
                (ltable.deleted == False)
        row = db(query).select(ltable.layer_id,
                               limitby=(0, 1)
                               ).first()
        if row:
            layer_id = row.layer_id
        else:
            # Create It
            f_id = ltable.insert(controller = "gis",
                                 function = "poi",
                                 attr_fields = ["name", "poi_type_id"],
                                 name = "PoIs",
                                 )
            record = {"id": f_id}
            s3db.update_super(ltable, record)
            layer_id = record["layer_id"]

        # Find correct Style record
        stable = s3db.gis_style
        query = (stable.layer_id == layer_id) & \
                (stable.record_id == None)
        styles = db(query).select(stable.id,
                                  stable.config_id,
                                  )
        none_excluded = False
        if len(styles) > 1:
            # Exclude all rows for different Map Configs
            config = current.gis.get_config()
            config_id = config.id
            styles.exclude(lambda row: (row.config_id == config_id) & \
                                       (row.config_id != None))

        if len(styles) > 1:
            # Exclude all rows for the default Map Config
            # (thus leaving just our own)
            styles.exclude(lambda row: row.config_id == None)
            none_excluded = True

        if len(styles) == 1:
            # Update it
            _style = styles.first()
            _style.update_record(style = style)

        elif len(styles) == 0:
            # Create It
            data = {"layer_id": layer_id,
                    "popup_format": "{name} ({poi_type_id})",
                    "style": style,
                    }
            if none_excluded:
                data["config_id"] = config_id
            stable.insert(**data)

        else:
            # Can't differentiate
            current.log.warning("Unable to update GIS PoI Style as there are multiple possible")

# =============================================================================
class S3PoIOrganisationGroupModel(S3Model):
    """
        PoI Organisation Group Model

        This model allows PoIs to link to Organisation Groups
    """

    names = ("gis_poi_group",
             )

    def model(self):

        #T = current.T

        # ---------------------------------------------------------------------
        # PoIs <> Organisation Groups - Link table
        #
        tablename = "gis_poi_group"
        self.define_table(tablename,
                          self.gis_poi_id(empty = False,
                                          ondelete = "CASCADE",
                                          ),
                          self.org_group_id(empty = False,
                                            ondelete = "CASCADE",
                                            ),
                          *s3_meta_fields())

        self.configure(tablename,
                       deduplicate = S3Duplicate(primary = ("poi_id",
                                                            "group_id",
                                                            ),
                                                 ),
                       )

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
class S3PoIFeedModel(S3Model):
    """ Data Model for PoI feeds """

    names = ("gis_poi_feed",)

    def model(self):

        # ---------------------------------------------------------------------
        # Store last update time for a PoI feed
        #
        tablename = "gis_poi_feed"
        self.define_table(tablename,
                          self.gis_location_id(),
                          Field("tablename"),
                          Field("last_update", "datetime"),
                          *s3_meta_fields())

        # Pass names back to global scope (s3.*)
        return {}

# =============================================================================
def name_field():
    return S3ReusableField("name", length=64, notnull=True,
                           #unique=True,
                           label = current.T("Name"),
                           requires = [IS_NOT_EMPTY(),
                                       IS_LENGTH(64),
                                       ],
                           )

# =============================================================================
def desc_field():
    return S3ReusableField("description", "text",
                           label = current.T("Description"),
                           represent = lambda v: v or current.messages["NONE"],
                           widget = s3_comments_widget,
                           )

# =============================================================================
def source_name_field():
    return S3ReusableField("source_name",
                           label = current.T("Source Name"),
                           represent = lambda v: v or current.messages["NONE"],
                           )

# =============================================================================
def source_url_field():
    return S3ReusableField("source_url",
                           label = current.T("Source URL"),
                           represent = lambda v: v or current.messages["NONE"],
                           requires = IS_EMPTY_OR(IS_URL(mode="generic")),
                           )

# =============================================================================
def gis_opacity():
    """
        Used by gis_style, gis_layer_wms & gis_feature_query
    """
    T = current.T
    OPACITY = T("Opacity")
    return S3ReusableField("opacity", "double",
                           default = 1.0,
                           label = OPACITY,
                           requires = IS_FLOAT_IN_RANGE(0, 1),
                           widget = S3SliderWidget(0.01, "float"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (OPACITY,
                                                           T("Left-side is fully transparent (0), right-side is opaque (1.0)."))),
                           )

# =============================================================================
def gis_refresh():
    return S3ReusableField("refresh", "integer",
                           default = 900,       # 15 minutes
                           label = current.T("Refresh Rate (seconds)"),
                           requires = IS_INT_IN_RANGE(0, 86400),    # 0 seconds - 24 hours
                           )

# =============================================================================
def cluster_attribute():
    T = current.T
    CLUSTER_ATTRIBUTE = T("Cluster Attribute")
    return S3ReusableField("cluster_attribute",
                           label = CLUSTER_ATTRIBUTE,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (CLUSTER_ATTRIBUTE,
                                                           T("The attribute used to determine which features to cluster together (optional).")))
                           )

# =============================================================================
def gis_layer_onaccept(form):
    """
        Process the enable checkbox
    """

    enable = current.request.post_vars.enable

    if enable:
        # Find the Default config
        db = current.db
        s3db = current.s3db
        ctable = s3db.gis_config
        query = (ctable.uuid == "SITE_DEFAULT")
        config = db(query).select(ctable.id,
                                  limitby=(0, 1)).first()
        if not config:
            return
        config_id = config.id
        layer_id = form.vars.layer_id
        # Update or Insert?
        ltable = s3db.gis_layer_config
        query = (ltable.config_id == config_id) & \
                (ltable.layer_id == layer_id)
        record = db(query).select(ltable.id,
                                  limitby=(0, 1)).first()
        if record:
            db(query).update(enabled=True)
        else:
            ltable.insert(config_id = config_id,
                          layer_id = layer_id,
                          enabled = True)

# =============================================================================
def gis_hierarchy_editable(level, location_id):
    """
        Returns the edit_<level> value from the parent country hierarchy.

        Used by gis_location_onvalidation()

        @param id: the id of the location or an ancestor - used to find
                   the ancestor country location.
    """

    country = current.gis.get_parent_country(location_id)

    s3db = current.s3db
    table = s3db.gis_hierarchy
    fieldname = "edit_%s" % level

    # Read the system default
    query = (table.uuid == "SITE_DEFAULT")
    if country:
        # Try the Location's Country, but ensure we have the fallback available in a single query
        query |= (table.location_id == country)
        limitby = (0, 2)
    else:
        limitby = (0, 1)
    rows = current.db(query).select(table[fieldname],
                                    table.uuid,
                                    limitby=limitby,
                                    cache=s3db.cache)
    if len(rows) > 1:
        # Remove the Site Default
        excluded = lambda row: row.uuid == "SITE_DEFAULT"
        rows.exclude(excluded)
    row = rows.first()
    editable = row[fieldname]

    return editable

# =============================================================================
def gis_location_filter(r):
    """
        Filter resources to those for a specified location
        @ToDo: Migrate to Context
    """

    lfilter = current.session.s3.location_filter
    if not lfilter:
        return

    db = current.db
    s3db = current.s3db
    gtable = s3db.gis_location
    query = (gtable.id == lfilter)
    row = db(query).select(gtable.id,
                           gtable.name,
                           gtable.level,
                           gtable.path,
                           limitby=(0, 1)).first()
    if row and row.level:
        resource = r.resource
        if resource.name == "organisation":
            selector = "organisation.country"
            if row.level != "L0":
                code = current.gis.get_parent_country(row, key_type="code")
            else:
                ttable = s3db.gis_location_tag
                query = (ttable.tag == "ISO2") & \
                        (ttable.location_id == row.id)
                tag = db(query).select(ttable.value,
                                       limitby=(0, 1)).first()
                code = tag.value
            location_filter = (FS(selector) == code)
        elif resource.name == "project":
            # Go via project_location link table
            selector = "location.location_id$%s" % row.level
            location_filter = (FS(selector) == row.name)
        else:
            # Normal case: resource with location_id
            selector = "%s.location_id$%s" % (resource.name, row.level)
            location_filter = (FS(selector) == row.name)
        resource.add_filter(location_filter)

# =============================================================================
class gis_LocationRepresent(S3Represent):
    """ Representation of Locations """

    def __init__(self,
                 show_link = False,
                 multiple = False,
                 address_only = False,
                 sep = None,
                 show_name = False, # Show name in location for level==None when sep is used
                 controller = None, # Override default controller for s3_viewMap() lookup of Popup
                 func = None,       # Override default function for s3_viewMap() lookup of Popup
                 ):

        settings = current.deployment_settings
        # Translation uses gis_location_name & not T()
        translate = settings.get_L10n_translate_gis_location()
        language = current.session.s3.language
        if language == settings.get_L10n_default_language():
            translate = False
        # Iframe height(Link)
        self.iheight = settings.get_gis_map_selector_height()
        address_only = address_only or \
                       settings.get_gis_location_represent_address_only()
        show_marker_icon = True if address_only == "icon" else False
        self.address_only = address_only
        self.show_marker_icon = show_marker_icon
        self.sep = sep
        if sep:
            self.multi_country = len(settings.get_gis_countries()) != 1
        self.show_name = show_name
        self.controller = controller
        self.func = func

        super(gis_LocationRepresent,
              self).__init__(lookup = "gis_location",
                             show_link = show_link,
                             translate = translate,
                             multiple = multiple)

    # -------------------------------------------------------------------------
    def link(self, k, v, row=None):
        """
            Represent a (key, value) as hypertext link.

            @param k: the key
            @param v: the representation of the key
            @param row: the row with this key (unused here)
        """

        if k is None:
            return "-"

        settings = current.deployment_settings
        iheight = settings.get_gis_map_selector_height()
        popup = settings.get_gis_popup_location_link()
        if self.controller:
            opts = ",'%s'" % self.controller
            func = self.func
            if func:
                opts = "%s,'%s'" % (opts, self.func)
        else:
            opts = ''
        return A(v,
                 _style="cursor:pointer;cursor:hand",
                 _onclick="s3_viewMap(%i,%i,'%s'%s);return false" % (k,
                                                                     iheight,
                                                                     popup,
                                                                     opts
                                                                     ),
                 )

    # -------------------------------------------------------------------------
    @staticmethod
    def lat_lon_format(coord):
        """
            Represent a coordinate (latitude or longitude) according to a
            format provided from deployment_settings.
        """

        degrees = abs(coord)
        minutes = (degrees - int(degrees)) * 60
        seconds = (minutes - int(minutes)) * 60

        # truncate (floor) degrees and minutes
        degrees, minutes = (int(coord), int(minutes))

        latlonformat = current.deployment_settings.get_L10n_lat_lon_format()
        formatted = latlonformat.replace("%d", "%d" % degrees) \
                                .replace("%m", "%d" % minutes) \
                                .replace("%s", "%lf" % seconds) \
                                .replace("%f", "%lf" % coord)
        return formatted

    # -------------------------------------------------------------------------
    def lat_lon_represent(self, row):
        lat = row.lat
        lon = row.lon
        if lat is not None and lon is not None:
            if lat > 0:
                lat_suffix = "N"
            else:
                lat_suffix = "S"
                lat = -lat
            if lon > 0:
                lon_suffix = "E"
            else:
                lon_suffix = "W"
                lon = -lon
            text = "%s %s, %s %s" % (self.lat_lon_format(lat),
                                     lat_suffix,
                                     self.lat_lon_format(lon),
                                     lon_suffix)
            return text

    # -------------------------------------------------------------------------
    def lookup_rows(self, key, values, fields=None):
        """
            Custom lookup method for Location(GIS) rows.Parameters
            key and fields are not used, but are kept for API
            compatiblity reasons.

            @param values: the gis_location IDs
        """

        db = current.db
        s3db = current.s3db
        ltable = s3db.gis_location
        count = len(values)
        sep = self.sep
        translate = self.translate

        # Initialized here to keep the init lightweight
        fields = [ltable.id,
                  ltable.name,
                  ltable.level,
                  ltable.path,
                  ltable.L0,
                  ltable.L1,
                  ltable.L2,
                  ltable.L3,
                  ltable.L4,
                  ltable.L5,
                  ]
        if sep:
            # Separator to place between all elements in the hierarchy
            gis_fields = fields
        elif self.address_only and not self.show_marker_icon:
            gis_fields = fields + [ltable.parent,
                                   ltable.addr_street,
                                   ltable.addr_postcode,
                                   ]
        else:
            gis_fields = fields + [ltable.parent,
                                   ltable.addr_street,
                                   ltable.addr_postcode,
                                   ltable.inherited,
                                   ltable.lat,
                                   ltable.lon,
                                   ]
        if count == 1:
            query = (ltable.id == values[0])
        else:
            query = (ltable.id.belongs(values))

        rows = db(query).select(limitby = (0, count),
                                *gis_fields)
        location_ids = []
        paths = self.paths = {}
        if sep or translate:
            for row in rows:
                path = row.path
                if not path:
                    path = current.gis.update_location_tree(row)
                split_path = path.split("/")
                paths[row.id] = split_path
                location_ids += split_path
            location_ids = set(location_ids)

        if translate:
            table = s3db.gis_location_name
            query = (table.deleted == False) & \
                    (table.language == current.session.s3.language)
            count = len(location_ids)
            if count == 1:
                query &= (table.location_id == location_ids.pop())
            else:
                query &= (table.location_id.belongs(location_ids))
            self.l10n = db(query).select(table.location_id,
                                         table.name_l10n,
                                         limitby = (0, count),
                                         ).as_dict(key="location_id")
        return rows

    # -------------------------------------------------------------------------
    def alt_represent_row(self, row):
        """
            Different Entry point for S3LocationSelector(intends to use represent_row)
            - Lookup L10n, path
            - then call represent_row
        """

        sep = self.sep
        translate = self.translate
        self.paths = {}

        if sep or translate:
            path = row.path
            if not path:
                path = current.gis.update_location_tree(row)
            split_path = path.split("/")
            self.paths[row.id] = split_path
            location_ids = set(split_path)

        # Lookup l10n
        if translate:
            table = current.s3db.gis_location_name
            query = (table.deleted == False) & \
                    (table.language == current.session.s3.language)
            count = len(location_ids)
            if count == 1:
                query &= (table.location_id == row.id)
            else:
                query &= (table.location_id.belongs(location_ids))
            self.l10n = current.db(query).select(table.location_id,
                                                 table.name_l10n,
                                                 limitby = (0, count),
                                                 ).as_dict(key="location_id")
        return self.represent_row(row)

    # -------------------------------------------------------------------------
    def represent_row(self, row):
        """
            Represent a single Row
            - assumes that Path & Lx have been populated correctly by
              gis.update_location_tree()

            @param row: the gis_location Row
        """

        sep = self.sep
        translate = self.translate
        ids = self.paths.get(row.id)

        if translate:
            l10n = self.l10n
            loc = l10n.get(row.id)
            if loc:
                name = loc["name_l10n"]
            else:
                name = row.name or ""
        else:
            name = row.name or ""

        level = row.level
        if sep:
            if level == "L0":
                return name
            # Remove the last ID as this is 'name'
            ids.pop()
            if self.show_name or level is not None:
                locations = [name]
            else:
                locations = []
            lappend = locations.append
            L5 = row.L5
            if L5 and level != "L5":
                if translate:
                    loc = l10n.get(int(ids.pop()), None)
                    if loc:
                        L5 = loc["name_l10n"]
                lappend(L5)
            L4 = row.L4
            if L4 and level != "L4":
                if translate:
                    loc = l10n.get(int(ids.pop()), None)
                    if loc:
                        L4 = loc["name_l10n"]
                lappend(L4)
            L3 = row.L3
            if L3 and level != "L3":
                if translate:
                    loc = l10n.get(int(ids.pop()), None)
                    if loc:
                        L3 = loc["name_l10n"]
                lappend(L3)
            L2 = row.L2
            if L2 and level != "L2":
                if translate:
                    loc = l10n.get(int(ids.pop()), None)
                    if loc:
                        L2 = loc["name_l10n"]
                lappend(L2)
            L1 = row.L1
            if L1 and level != "L1":
                if translate:
                    loc = l10n.get(int(ids.pop()), None)
                    if loc:
                        L1 = loc["name_l10n"]
                lappend(L1)
            if self.multi_country:
                L0 = row.L0
                if L0:
                    if translate:
                        loc = l10n.get(int(ids.pop()), None)
                        if loc:
                            L0 = loc["name_l10n"]
                    lappend(L0)
            if locations:
                represent = sep.join(locations)
            else:
                # Fallback to name even if show_name is False
                represent = name
        else:
            if level == "L0":
                represent = "%s (%s)" % (name, current.messages.COUNTRY)
            elif level in ("L1", "L2", "L3", "L4", "L5"):
                # Lookup the hierarchy for labels
                s3db = current.s3db
                L0_name = row.L0
                if L0_name:
                    if row.path:
                        path = row.path
                    else:
                        # Not yet been built, so do it now
                        path = current.gis.update_location_tree(row)
                    path = path.split("/")
                    L0_id = path[0]
                    level_name = current.gis.get_location_hierarchy(level,
                                                                    L0_id)
                else:
                    # Fallback to system default
                    level_name = current.gis.get_location_hierarchy(level)

                represent = name
                if level_name:
                    represent = "%s (%s)" % (represent, level_name)
                if row.parent:
                    # @ToDo: Don't assume no missing levels in PATH
                    parent_level = "L%s" % (int(level[1]) - 1)
                    # @ToDo: Support translate=True
                    parent_name = row[parent_level]
                    if parent_name:
                        represent = "%s, %s" % (represent, parent_name)
            else:
                # Specific location:
                # Don't duplicate the Resource Name
                # Street address or lat/lon as base
                has_lat_lon = row.get("lat") is not None and \
                              row.get("lon") is not None
                represent = ""
                if row.addr_street:
                    # Get the 1st line of the street address.
                    represent = row.addr_street.splitlines()[0]
                if row.addr_postcode:
                    represent = "%s, %s" % (represent, row.addr_postcode)
                if (not represent) and \
                   (not self.address_only) and \
                   (row.inherited == False) and \
                   has_lat_lon:
                    represent = self.lat_lon_represent(row)
                if row.parent:
                    if row.path:
                        path = row.path
                    else:
                        # Not yet been built, so do it now
                        path = current.gis.update_location_tree(row)
                    path = path.split("/")
                    path_len = len(path)
                    if path_len > 1:
                        # @ToDo: Don't assume no missing levels in PATH
                        parent_level = "L%s" % (path_len - 2)
                        # @ToDo: Support translate=True
                        parent_name = row[parent_level]
                        if parent_name:
                            if represent:
                                represent = "%s, %s" % (represent, parent_name)
                            else:
                                represent = parent_name
                if not represent:
                    represent = name or "ID: %s" % row.id

                if has_lat_lon and self.show_marker_icon:
                    if not self.show_link:
                        popup = current.deployment_settings.get_gis_popup_location_link()
                        script = '''s3_viewMap(%i,%i,'%s');return false''' % (row.id,
                                                                              self.iheight,
                                                                              popup)
                    else:
                        # Already inside a link with onclick-script
                        script = None
                    represent = SPAN(s3_unicode(represent),
                                     ICON("map-marker",
                                          _title=self.lat_lon_represent(row),
                                          _onclick=script,
                                          ),
                                     _class="gis-display-feature",
                                     )
                    return represent

        return s3_str(represent)

# =============================================================================
def gis_layer_represent(layer_id, row=None, show_link=True):
    """ Represent a Layer  """

    if row:
        db = current.db
        s3db = current.s3db
        ltable = s3db.gis_layer_entity
    elif not layer_id:
        return current.messages["NONE"]
    else:
        db = current.db
        s3db = current.s3db
        ltable = s3db.gis_layer_entity
        row = db(ltable.layer_id == layer_id).select(ltable.name,
                                                     ltable.layer_id,
                                                     ltable.instance_type,
                                                     limitby = (0, 1),
                                                     ).first()

    try:
        instance_type = row.instance_type
    except AttributeError:
        return current.messages.UNKNOWN_OPT

    instance_type_nice = ltable.instance_type.represent(instance_type)

    represent = "%s (%s)" % (row.name, instance_type_nice)

    if show_link:
        table = s3db[instance_type]
        query = (table.layer_id == row.layer_id)
        try:
            id = db(query).select(table.id,
                                  limitby = (0, 1),
                                  ).first().id
        except AttributeError:
            # Not found?
            return represent
        c, f = instance_type.split("_", 1)
        represent = A(represent,
                      _href=URL(c=c, f=f,
                                args=[id],
                                extension="", # removes the .aaData extension in paginated views!
                                ),
                      )

    return represent

# =============================================================================
def gis_marker_retrieve(filename, path=None):
    """
        custom_retrieve to override web2py DAL's standard retrieve,
        as that checks filenames for uuids, so doesn't work with
        pre-populated files in static
    """

    if not path:
        # NB This is also used by gis_config (& not gis_layer_geojson) but path
        #    always seems to be supplied so no issues so far
        path = current.db.gis_marker.image.uploadfolder

    if "/" in filename:
        _path, filename = filename.split("/")
        image = open(os.path.join(path, _path, filename), "rb")
    else:
        image = open(os.path.join(path, filename), "rb")
    return (filename, image)

# =============================================================================
def gis_marker_retrieve_file_properties(filename, path=None):
    """
        Custom method to override web2py DAL's standard
        retrieve_file_properties, as that checks filenames
        for uuids, so doesn't work with pre-populated files
        in static. This method is required for XML exports.
    """

    if not path:
        # NB This is also used by gis_config (& not gis_layer_geojson) but path
        #    always seems to be supplied so no issues so far
        path = current.db.gis_marker.image.uploadfolder

    # @ToDo: should probably use os.sep here rather than "/"
    if "/" in filename:
        _path = filename.split("/", 1)
        if len(_path) > 1:
            _path, filename = _path
        else:
            _path, filename = "", filename
        path = os.path.join(path, _path)
    return {"path": path, "filename": filename}

# =============================================================================
def gis_rheader(r, tabs=None):
    """ GIS page headers """

    settings = current.deployment_settings

    if r.representation != "html":
        # RHeaders only used in interactive views
        return None
    record = r.record
    if record is None:
        # List or Create form: rheader makes no sense here
        return None

    table = r.table
    resourcename = r.name
    T = current.T

    if resourcename == "location":
        tabs = [(T("Location Details"), None),
                (T("Key Value pairs"), "tag"),
                (T("Import from OpenStreetMap"), "import_poi"),
                ]
        # Insert the tabs based on Deployment settings
        position = 1
        if settings.get_L10n_translate_gis_location():
            tabs.insert(position, (T("Local Names"), "name"))
            position += 1
        if settings.get_L10n_name_alt_gis_location():
            tabs.insert(position, (T("Alternate Names"), "name_alt"))

        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name,
                               ),
                            TR(TH("%s: " % T("Level")),
                               record.level,
                               ),
                            ), rheader_tabs)

    elif resourcename == "config":
        # Tabs
        if not tabs:
            tabs = [(T("Profile Details"), None),
                    (T("Layers"), "layer_entity"),
                    (T("Styles"), "style"),
                    ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        context = ""
        if record.uuid == "SITE_DEFAULT":
            context = T("Default")
        else:
            # Check both the OU & Region contexts
            s3db = current.s3db
            pe_id = record.pe_id
            if pe_id:
                auth = current.auth
                # Is this the user's personal config?
                if auth.user and auth.user.pe_id == pe_id:
                    context = T("Personal")
                else:
                    context = s3db.pr_pentity_represent(pe_id)

            region_location_id = record.region_location_id
            if region_location_id:
                location_represent = gis_LocationRepresent()(region_location_id)
                if context:
                    context = T("%(pe)s in %(location)s") % {
                                    "pe": context,
                                    "location": location_represent,
                                    }
                else:
                    context = location_represent

        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name,
                               ),
                            TR(TH("%s: " % T("Context")),
                               context,
                               ),
                            ), rheader_tabs)

    elif resourcename == "marker":
        # Tabs
        if not tabs:
            tabs = [(T("Basic Details"), None),
                    (T("Layers"), "layer_entity"),
                    ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                                record.name),
                            ), rheader_tabs)

    elif resourcename == "layer_feature" or \
         resourcename == "layer_georss" or \
         resourcename == "layer_geojson" or \
         resourcename == "layer_kml" or \
         resourcename == "layer_wfs":
        # Tabs
        if not tabs:
            # @ToDo: Move to InlineComponents
            tabs = [(T("Layer Details"), None),
                    (T("Profiles"), "config"),
                    (T("Styles"), "style"),
                    ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        if record.description:
            description = TR(TH("%s: " % table.description.label),
                             record.description)
        else:
            description = ""

        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name,
                            ),
                            description,
                            ), rheader_tabs)

    elif resourcename == "layer_entity":
        # Tabs
        if not tabs:
            tabs = [(T("Layer Details"), None), # @ToDo: Make this the layer instance not entity
                    (T("Profiles"), "config"),
                    (T("Styles"), "style"),
                    ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        if record.description:
            description = TR(TH("%s: " % table.description.label),
                             record.description)
        else:
            description = ""

        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name,
                            ),
                            description,
                            ), rheader_tabs)

    elif resourcename == "layer_openstreetmap" or \
         resourcename == "layer_bing" or \
         resourcename == "layer_empty" or \
         resourcename == "layer_google" or \
         resourcename == "layer_openweathermap" or \
         resourcename == "layer_tms" or \
         resourcename == "layer_wms" or \
         resourcename == "layer_xyz" or \
         resourcename == "layer_arcrest" or \
         resourcename == "layer_coordinate" or \
         resourcename == "layer_gpx" or \
         resourcename == "layer_js" :
        # Tabs
        if not tabs:
            tabs = [(T("Layer Details"), None),
                    (T("Profiles"), "config"),
                    ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        if record.description:
            description = TR(TH("%s: " % table.description.label),
                             record.description)
        else:
            description = ""

        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name,
                            ),
                            description,
                            ), rheader_tabs)

    elif resourcename == "layer_shapefile":
        # Tabs
        if not tabs:
            tabs = [(T("Layer Details"), None),
                    (T("Profiles"), "config"),
                    (T("Styles"), "style"),
                    # @ToDo: Not showing as not a component yet
                    #(T("Data"), "data"),
                    ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        if record.description:
            description = TR(TH("%s: " % table.description.label),
                             record.description)
        else:
            description = ""

        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name,
                            ),
                            description,
                            ), rheader_tabs)
    elif resourcename == "layer_theme":
        # Tabs
        if not tabs:
            tabs = [(T("Layer Details"), None),
                    (T("Profiles"), "config"),
                    (T("Data"), "theme_data"),
                    ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        if record.description:
            description = TR(TH("%s: " % table.description.label),
                             record.description)
        else:
            description = ""

        rheader = DIV(TABLE(TR(TH("%s: " % table.name.label),
                               record.name,
                            ),
                            description,
                            ), rheader_tabs)
    else:
        rheader = None

    return rheader

# END =========================================================================
