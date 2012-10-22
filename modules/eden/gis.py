# -*- coding: utf-8 -*-

""" Sahana Eden GIS Model

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

__all__ = ["S3LocationModel",
           "S3LocationNameModel",
           "S3LocationTagModel",
           "S3LocationGroupModel",
           "S3LocationHierarchyModel",
           "S3GISConfigModel",
           "S3LayerEntityModel",
           "S3FeatureLayerModel",
           "S3MapModel",
           "S3GISThemeModel",
           "S3POIFeedModel",
           "gis_location_filter",
           "gis_location_represent",
           "gis_location_lx_represent",
           "gis_layer_represent",
           "gis_rheader",
           ]

import os

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.dal import Row, Rows
from gluon.storage import Storage
from ..s3 import *
from eden.layouts import S3AddResourceLink

# =============================================================================
class S3LocationModel(S3Model):
    """
        Locations model
    """

    names = ["gis_location",
             #"gis_location_error",
             "gis_location_id",
             "gis_country_id",
             "gis_countries_id",
             "gis_location_onvalidation",
             ]

    def model(self):

        T = current.T
        db = current.db
        gis = current.gis

        messages = current.messages

        # Shortcuts
        add_component = self.add_component
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Locations
        #
        #  A set of Coordinates &/or Address
        #
        gis_feature_type_opts = {
            0:T("None"),
            1:"Point",
            2:"LineString",
            3:"Polygon",
            4:"MultiPoint",
            5:"MultiLineString",
            6:"MultiPolygon",
            7:"GeometryCollection",
            }

        hierarchy_level_keys = gis.hierarchy_level_keys

        if current.deployment_settings.get_gis_spatialdb():
            # Add a spatial field
            # Should we do a test to confirm this? Ideally that would be done only in eden_update_check
            meta_spatial_fields = (s3_lx_fields() + s3_meta_fields() + (Field("the_geom", "geometry()"),))
        else:
            meta_spatial_fields = (s3_lx_fields() + s3_meta_fields())

        tablename = "gis_location"
        table = define_table(tablename,
                             Field("name", length=128,
                                   # Placenames don't have to be unique.
                                   # Waypoints don't need to have a name at all.
                                   #requires = IS_NOT_EMPTY()
                                   label = T("Name")),
                             Field("level", length=2,
                                   label = T("Level"),
                                   requires = IS_NULL_OR(IS_IN_SET(hierarchy_level_keys)),
                                   represent = self.gis_level_represent),
                             Field("parent", "reference gis_location", # This form of hierarchy may not work on all Databases
                                   label = T("Parent"),
                                   represent = self.gis_location_represent,
                                   widget=S3LocationAutocompleteWidget(level=hierarchy_level_keys),
                                   ondelete = "RESTRICT"),
                             # Materialised Path
                             Field("path", length=256,
                                   readable=False, writable=False),
                             Field("gis_feature_type", "integer",
                                   default=1, notnull=True,
                                   requires = IS_IN_SET(gis_feature_type_opts,
                                                        zero=None),
                                   represent = lambda opt: gis_feature_type_opts.get(opt,
                                                                                     messages.UNKNOWN_OPT),
                                   label = T("Feature Type")),
                             # Points or Centroid for Polygons
                             Field("lat", "double",
                                   label = T("Latitude"),
                                   requires = IS_NULL_OR(IS_LAT()),
                                   comment = DIV(_class="tooltip",
                                                 _id="gis_location_lat_tooltip",
                                                 _title="%s|%s|%s|%s|%s|%s" % \
                                                 (T("Latitude & Longitude"),
                                                  T("Latitude is North-South (Up-Down)."),
                                                  T("Longitude is West-East (sideways)."),
                                                  T("Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere."),
                                                  T("Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas."),
                                                  T("These need to be added in Decimal Degrees."))),
                                  ),
                             Field("lon", "double",
                                    label = T("Longitude"),
                                    requires = IS_NULL_OR(IS_LON()),
                                    comment = A(T("Conversion Tool"),
                                                _style="cursor:pointer;",
                                                _title=T("You can use the Conversion Tool to convert from either GPS coordinates or Degrees/Minutes/Seconds."),
                                                _id="gis_location_converter-btn"),
                                  ),
                             Field("wkt", "text",
                                   # Full WKT validation is done in the onvalidation callback
                                   # - all we do here is allow longer fields than the default (2 ** 16)
                                   requires = IS_LENGTH(2 ** 24),
                                   represent = gis.abbreviate_wkt,
                                   label = "WKT (Well-Known Text)"),
                             Field("inherited", "boolean",
                                   label = T("Inherited?"),
                                   default = False,
                                   writable = False,
                                   represent = lambda opt: \
                                    T("Yes") if opt == True else T("No")),
                             # Bounding box
                             Field("lat_min", "double",
                                   readable=False, writable=False),
                             Field("lat_max", "double",
                                   readable=False, writable=False),
                             Field("lon_min", "double",
                                   readable=False, writable=False),
                             Field("lon_max", "double",
                                   readable=False, writable=False),
                             # m in height above WGS84 ellipsoid (approximately sea-level).
                             Field("elevation", "double",
                                   readable=False, writable=False),
                             # Street Address (other address fields come from hierarchy)
                             Field("addr_street", "text",
                                   label = T("Street Address")),
                             Field("addr_postcode", length=128,
                                   label = T("Postcode")),
                             s3_comments(),
                             format=gis_location_represent,
                             *meta_spatial_fields)

        # Default the owning role to Authenticated. This can be used to allow the site
        # to control whether authenticated users get to create / update locations, or
        # just read them. Having an owner and using ACLs also allows us to take away
        # privileges from generic Authenticated users for particular locations (like
        # hierarchy or region locations) by changing the owner on those locations, e.g.
        # to MapAdmin.
        table.owned_by_group.default = current.session.s3.system_roles.AUTHENTICATED

        # Can't be defined in-line as otherwise get a circular reference
        table.parent.requires = IS_NULL_OR(
                                    IS_ONE_OF(db, "gis_location.id",
                                              gis_location_represent,
                                              # @ToDo: If level is known, filter on higher than that?
                                              # If strict, filter on next higher level?
                                              filterby="level",
                                              filter_opts=hierarchy_level_keys,
                                              orderby="gis_location.name"))

        # CRUD Strings
        ADD_LOCATION = messages.ADD_LOCATION
        crud_strings[tablename] = Storage(
            title_create = ADD_LOCATION,
            title_display = T("Location Details"),
            title_list = T("Locations"),
            title_update = T("Edit Location"),
            title_search = T("Search Locations"),
            title_upload = T("Import Locations"),
            subtitle_create = T("Add New Location"),
            label_list_button = T("List Locations"),
            label_create_button = ADD_LOCATION,
            label_delete_button = T("Delete Location"),
            msg_record_created = T("Location added"),
            msg_record_modified = T("Location updated"),
            msg_record_deleted = T("Location deleted"),
            msg_list_empty = T("No Locations currently available"))

        # Reusable field to include in other table definitions
        location_id = S3ReusableField("location_id", table,
                                      sortby = "name",
                                      label = T("Location"),
                                      represent = gis_location_represent,
                                      widget = S3LocationSelectorWidget(),
                                      requires = IS_NULL_OR(IS_LOCATION_SELECTOR()),
                                      # Alternate simple Autocomplete (e.g. used by pr_person_presence)
                                      #requires = IS_NULL_OR(IS_LOCATION()),
                                      #widget = S3LocationAutocompleteWidget(),
                                      ondelete = "RESTRICT")

        country_id = S3ReusableField("country_id", table,
                                     sortby = "name",
                                     label = messages.COUNTRY,
                                     requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "gis_location.id",
                                                              self.country_represent,
                                                              filterby = "level",
                                                              filter_opts = ["L0"],
                                                              sort=True)),
                                     represent = self.country_represent,
                                     ondelete = "RESTRICT")

        countries_id = S3ReusableField("countries_id", "list:reference gis_location",
                                       label = T("Countries"),
                                       requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "gis_location.id",
                                                              self.country_represent,
                                                              filterby = "level",
                                                              filter_opts = ["L0"],
                                                              sort=True,
                                                              multiple=True)),
                                       represent = self.countries_represent,
                                       ondelete = "RESTRICT")

        self.configure(tablename,
                        onvalidation=self.gis_location_onvalidation,
                        onaccept=self.gis_location_onaccept,
                        deduplicate=self.gis_location_deduplicate,
                        list_fields = ["id",
                                       "name",
                                       "level",
                                       #"parent",
                                       "L0",
                                       "L1",
                                       "L2",
                                       "L3",
                                       "L4",
                                       "lat",
                                       "lon"
                                       ]
                        )

        # Tags as component of Locations
        add_component("gis_location_tag",
                      gis_location=dict(joinby="location_id",
                                        name="tag"))

        # Names as component of Locations
        add_component("gis_location_name",
                      gis_location=dict(joinby="location_id",
                                        name="name"))

        # Locations as component of Locations ('Parent')
        #add_component(table, joinby=dict(gis_location="parent"),
        #              multiple=False)

        # ---------------------------------------------------------------------
        # Error
        # - needed for COT support
        #
        # tablename = "gis_location_error"
        # table = define_table(tablename,
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

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                    gis_location_id = location_id,
                    gis_country_id = country_id,
                    gis_countries_id = countries_id,
                    gis_location_onvalidation = self.gis_location_onvalidation,
                )

    # ---------------------------------------------------------------------
    @staticmethod
    def country_represent(id, row=None):
        """ FK representation """

        if row:
            return row.name
        elif not id:
            return current.messages.NONE

        db = current.db
        table = db.gis_location
        r = db(table.id == id).select(table.name,
                                      limitby = (0, 1)).first()
        try:
            return r.name
        except:
            return current.messages.UNKNOWN_OPT

    # ---------------------------------------------------------------------
    @staticmethod
    def countries_represent(locations, row=None):
        """ FK representation """

        if isinstance(locations, Rows):
            try:
                locations = [r.name for r in locations]
                return ", ".join(locations)
            except:
                locations = [r.id for r in locations]
        if not isinstance(locations, list):
            locations = [locations]
        db = current.db
        table = db.gis_location
        query = table.id.belongs(locations)
        rows = db(query).select(table.name)
        return S3LocationModel.countries_represent(rows)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_location_onaccept(form):
        """
            On Accept for GIS Locations (after DB I/O)
        """

        if not current.auth.override:
            # Update the Path (async if-possible)
            # (skip during prepop)
            vars = form.vars
            feature = json.dumps(dict(id=vars.id,
                                      level=vars.get("level", False),
                                      ))
            current.s3task.async("gis_update_location_tree",
                                 args=[feature])
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_location_onvalidation(form):

        """
            On Validation for GIS Locations (before DB I/O)
        """

        T = current.T
        db = current.db
        gis = current.gis
        request = current.request
        response = current.response

        MAP_ADMIN = current.auth.s3_has_role(current.session.s3.system_roles.MAP_ADMIN)

        record_error = T("Sorry, only users with the MapAdmin role are allowed to edit these locations")
        field_error = T("Please select another level")

        # Shortcuts
        vars = form.vars
        level = "level" in vars and vars.level
        parent = "parent" in vars and vars.parent
        lat = "lat" in vars and vars.lat
        lon = "lon" in vars and vars.lon
        if lon:
            if lon > 180:
                # Map Selector wrapped
                vars.lon = lon = lon - 360
            elif lon < -180:
                # Map Selector wrapped
                vars.lon = lon = lon + 360
        id = "id" in request.vars and request.vars.id

        # 'MapAdmin' has permission to edit hierarchy locations, no matter what
        # 000_config or the ancestor country's gis_config has.
        if not MAP_ADMIN:
            if level and (level == "L0" or (level in gis.location_hierarchy_keys and \
                                            not gis.get_edit_level(level, id))):
                response.error = record_error
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

        # Check within permitted bounds
        # (avoid incorrect data entry)
        # Points only for now
        if not "gis_feature_type" in vars or (vars.gis_feature_type == "1"):
            #if lat not in (None, "") and lon not in (None, ""):
            if lat and lon:
                name = vars.name
                if parent:
                    # Check within Bounds of the Parent
                    # Rough (Bounding Box)
                    min_lat, min_lon, max_lat, max_lon, parent_name = gis.get_bounds(parent=parent)
                    if (lat > max_lat) or (lat < min_lat):
                        lat_error =  "%s: %s & %s" % (T("Latitude should be between"),
                                                      min_lat, max_lat)
                        form.errors["lat"] = lat_error
                    if (lon > max_lon) or (lon < min_lon):
                        lon_error = "%s: %s & %s" % (T("Longitude should be between"),
                                                     min_lon, max_lon)
                        form.errors["lon"] = lon_error
                    if form.errors:
                        if name:
                            base_error = T("Sorry location %(location)s appears to be outside the area of parent %(parent)s.") % \
                                dict(location=name, parent=parent_name)
                        else:
                            base_error = T("Sorry location appears to be outside the area of parent %(parent)s.") % \
                                dict(parent=parent_name)
                        response.error = base_error
                        s3_debug(base_error)
                        return

                    # @ToDo: Precise (GIS function)
                    # (if using PostGIS then don't do a separate BBOX check as this is done within the query)

                else:
                    # Check bounds for the Instance
                    config = gis.get_config()
                    if config.min_lat is not None:
                        min_lat = config.min_lat
                    else:
                        min_lat = -90
                    if config.min_lon is not None:
                        min_lon = config.min_lon
                    else:
                        min_lon = -180
                    if config.max_lat is not None:
                        max_lat = config.max_lat
                    else:
                        max_lat = 90
                    if config.max_lon is not None:
                        max_lon = config.max_lon
                    else:
                        max_lon = 180
                    if name:
                        base_error = T("Sorry location %(location)s appears to be outside the area supported by this deployment.") % dict(location=name)
                    else:
                        base_error = T("Sorry location appears to be outside the area supported by this deployment.")
                    lat_error =  "%s: %s & %s" % (T("Latitude should be between"),
                                                  str(min_lat), str(max_lat))
                    lon_error = "%s: %s & %s" % (T("Longitude should be between"),
                                                 str(min_lon), str(max_lon))
                    if (lat > max_lat) or (lat < min_lat):
                        response.error = base_error
                        s3_debug(base_error)
                        form.errors["lat"] = lat_error
                        return
                    elif (lon > max_lon) or (lon < min_lon):
                        response.error = base_error
                        s3_debug(base_error)
                        form.errors["lon"] = lon_error
                        return

        # Add the bounds (& Centroid for Polygons)
        gis.wkt_centroid(form)

        if form.record:
            inherited = form.record.inherited
            if inherited:
                # Have we provided more accurate data?
                if lat != form.record.lat or lon != form.record.lon:
                    vars.inherited = False
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_location_deduplicate(job):
        """
          This callback will be called when importing location records it will look
          to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - Look for a record with the same name, ignoring case
                and, if level exists in the import, the same level
                and, if parent exists in the import, the same parent

            @ToDo: Use codes that we know are unique

            @ToDo: Check soundex? (only good in English)
                   http://eden.sahanafoundation.org/ticket/481
        """

        if job.tablename == "gis_location":
            table = job.table
            data = job.data
            name = "name" in data and data.name or None
            level = "level" in data and data.level or None
            parent = "parent" in data and data.parent or None

            if not name:
                return

            # Don't try to update Countries
            if level and level == "L0":
                job.method = None
                return

            # @ToDo: check the the lat and lon if they exist?
            #lat = "lat" in data and data.lat
            #lon = "lon" in data and data.lon

            # Try the Name
            # @ToDo: Hook for possible duplicates vs definite?
            #query = (table.name.lower().like('%%%s%%' % name.lower()))
            query = (table.name.lower() == name.lower())
            if parent:
                query = query & (table.parent == parent)
            if level:
                query = query & (table.level == level)

            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_level_represent(level):
        if not level:
            return current.messages.NONE
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

# =============================================================================
class S3LocationNameModel(S3Model):
    """
        Location Names model
        - local/alternate names for Locations

        @ToDo: Change lookup to be a full set of languages,
               not just those we are using in the interface
    """

    names = ["gis_location_name"]

    def model(self):

        T = current.T
        l10n_languages = current.response.s3.l10n_languages

        # ---------------------------------------------------------------------
        # Local Names
        #
        tablename = "gis_location_name"
        table = self.define_table(tablename,
                                  self.gis_location_id(),
                                  Field("language",
                                        label = T("Language"),
                                        requires = IS_IN_SET(l10n_languages),
                                        represent = lambda opt: \
                                            l10n_languages.get(opt,
                                                               current.messages.UNKNOWN_OPT)),
                                  Field("name_l10n",
                                        label = T("Name")),
                                  s3_comments(),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                )

# =============================================================================
class S3LocationTagModel(S3Model):
    """
        Location Tags model
        - flexible Key-Value component attributes to Locations
    """

    names = ["gis_location_tag",
             "gis_country_opts",
            ]

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
        table = self.define_table(tablename,
                                  self.gis_location_id(),
                                  # key is a reserved word in MySQL
                                  Field("tag", label=T("Key")),
                                  Field("value", label=T("Value")),
                                  s3_comments(),
                                  *s3_meta_fields())

        self.configure(tablename,
                       deduplicate=self.gis_location_tag_deduplicate)

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                    gis_country_opts = self.gis_country_opts,
                )

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

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_location_tag_deduplicate(job):
        """
           If the record is a duplicate then it will set the job method to update
        """

        if job.tablename == "gis_location_tag":
            table = job.table
            data = job.data
            tag = "tag" in data and data.tag or None
            location = "location_id" in data and data.location_id or None

            if not tag or not location:
                return

            query = (table.tag.lower() == tag.lower()) & \
                    (table.location_id == location)

            _duplicate = current.db(query).select(table.id,
                                                  limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.method = job.METHOD.UPDATE

# =============================================================================
class S3LocationGroupModel(S3Model):
    """
        Location Groups model
        - currently unused
    """

    names = ["gis_location_group",
             "gis_location_group_member",
            ]

    def model(self):

        T = current.T
        db = current.db

        location_id = self.gis_location_id

        define_table = self.define_table

        # ---------------------------------------------------------------------
        # Location Groups
        #
        tablename = "gis_location_group"
        table = define_table(tablename,
                             Field("name",
                                   label = T("Name")),
                             # Optional Polygon for the overall Group
                             location_id(),
                             s3_comments(),
                             *s3_meta_fields())

        self.add_component("gis_location_group_member",
                           gis_location_group="location_group_id")

        # ---------------------------------------------------------------------
        # Location Group Membership
        #
        tablename = "gis_location_group_member"
        table = define_table(tablename,
                             Field("location_group_id",
                                   db.gis_location_group,
                                   label = T("Location Group"),
                                   ondelete = "RESTRICT"),
                             location_id(),
                             s3_comments(),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                )

# =============================================================================
class S3LocationHierarchyModel(S3Model):
    """
        Location Hierarchy model
    """

    names = ["gis_hierarchy",
             "gis_hierarchy_form_setup",
             ]

    def model(self):

        T = current.T

        # =====================================================================
        # GIS Hierarchy
        #
        # uuid=SITE_DEFAULT = Site default settings
        #

        tablename = "gis_hierarchy"
        table = self.define_table(tablename,
                                  self.gis_country_id("location_id"),
                                  Field("L1", default = "State / Province"),
                                  Field("L2", default = "County / District"),
                                  Field("L3", default = "City / Town / Village"),
                                  Field("L4", default = ""),   # Default: off
                                  Field("L5", default = ""),   # Default: off
                                  # Do all levels of the hierarchy need to be filled-out?
                                  Field("strict_hierarchy", "boolean",
                                        # Currently not fully used
                                        readable = False,
                                        writable = False,
                                        default=False),
                                  # Do we minimally need a parent for every non-L0 location?
                                  Field("location_parent_required", "boolean",
                                        # Currently completely unused
                                        readable = False,
                                        writable = False,
                                        default=False),
                                  Field("edit_L1", "boolean", default=True),
                                  Field("edit_L2", "boolean", default=True),
                                  Field("edit_L3", "boolean", default=True),
                                  Field("edit_L4", "boolean", default=True),
                                  Field("edit_L5", "boolean", default=True),
                                  *s3_meta_fields())

        ADD_HIERARCHY = T("Add Location Hierarchy")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_HIERARCHY,
            title_display = T("Location Hierarchy"),
            title_list = T("Location Hierarchies"),
            title_update = T("Edit Location Hierarchy"),
            title_search = T("Search Location Hierarchies"),
            subtitle_create = T("Add New Location Hierarchy"),
            label_list_button = T("List Location Hierarchies"),
            label_create_button = ADD_HIERARCHY,
            label_delete_button = T("Delete Location Hierarchy"),
            msg_record_created = T("Location Hierarchy added"),
            msg_record_modified = T("Location Hierarchy updated"),
            msg_record_deleted = T("Location Hierarchy deleted"),
            msg_list_empty = T("No Location Hierarchies currently defined")
        )

        self.configure(tablename,
                       onvalidation=self.gis_hierarchy_onvalidation,
                       )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                gis_hierarchy_form_setup = self.gis_hierarchy_form_setup,
                )

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
                            T("Is editing level L%d locations allowed?" % n),
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

        vars = form.vars

        if vars.strict_hierarchy:
            gis = current.gis
            hierarchy_level_keys = gis.hierarchy_level_keys
            level_names = [vars[key] if key in vars else None
                           for key in hierarchy_level_keys]
            # L0 is always missing because its label is hard-coded
            gaps = filter(None, map(lambda n:
                                        not level_names[n] and
                                        level_names[n + 1] and
                                        "L%d" % n,
                                    range(1, gis.max_allowed_level_num)))
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

    names = ["gis_config",
             "gis_menu",
             "gis_marker",
             "gis_projection",
             "gis_symbology",
             "gis_config_id",
             "gis_marker_id",
             "gis_projection_id",
             "gis_symbology_id",
             "gis_config_form_setup",
             ]

    def model(self):

        T = current.T
        db = current.db
        gis = current.gis

        location_id = self.gis_location_id

        NONE = current.messages.NONE

        # Shortcuts
        add_component = self.add_component
        configure = self.configure
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table
        super_link = self.super_link

        # =====================================================================
        # GIS Markers (Icons)
        tablename = "gis_marker"
        table = define_table(tablename,
                             Field("name", length=64,
                                   notnull=True, unique=True,
                                   label = T("Name")),
                             Field("image", "upload", autodelete=True,
                                   label = T("Image"),
                                   # upload folder needs to be visible to the download() function as well as the upload
                                   uploadfolder = os.path.join(current.request.folder,
                                                               "static",
                                                               "img",
                                                               "markers"),
                                   custom_retrieve = self.gis_marker_retrieve,
                                   represent = lambda filename: \
                                      (filename and [DIV(IMG(_src=URL(c="static",
                                                                      f="img",
                                                                      args=["markers", filename]),
                                                             _height=40))] or [""])[0]),
                             Field("height", "integer", writable=False), # In Pixels, for display purposes
                             Field("width", "integer", writable=False),  # We could get size client-side using Javascript's Image() class, although this is unreliable!
                             *s3_meta_fields())

        # CRUD Strings
        ADD_MARKER = T("Add Marker")
        crud_strings[tablename] = Storage(
            title_create = ADD_MARKER,
            title_display = T("Marker Details"),
            title_list = T("Markers"),
            title_update = T("Edit Marker"),
            title_search = T("Search Markers"),
            subtitle_create = T("Add New Marker"),
            label_list_button = T("List Markers"),
            label_create_button = ADD_MARKER,
            label_delete_button = T("Delete Marker"),
            msg_record_created = T("Marker added"),
            msg_record_modified = T("Marker updated"),
            msg_record_deleted = T("Marker deleted"),
            msg_list_empty = T("No Markers currently available"))

        # Reusable field to include in other table definitions
        marker_id = S3ReusableField("marker_id", table, sortby="name",
                                    requires = IS_NULL_OR(IS_ONE_OF(db, "gis_marker.id", "%(name)s", zero=T("Use default"))),
                                    represent = self.gis_marker_represent,
                                    label = T("Marker"),
                                    comment=S3AddResourceLink(c="gis",
                                                              f="marker",
                                                              label=ADD_MARKER,
                                                              title=T("Marker"),
                                                              tooltip="%s|%s|%s" % (T("Defines the icon used for display of features on interactive map & KML exports."),
                                                                                    T("A Marker assigned to an individual Location is set if there is a need to override the Marker assigned to the Feature Class."),
                                                                                    T("If neither are defined, then the Default Marker is used."))),
                                    ondelete = "SET NULL")

        # Components
        # Layers
        add_component("gis_layer_entity",
                      gis_marker=Storage(
                                    link="gis_layer_symbology",
                                    joinby="marker_id",
                                    key="layer_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        configure(tablename,
                  onvalidation=self.gis_marker_onvalidation,
                  deduplicate=self.gis_marker_deduplicate)

        # =====================================================================
        # GIS Projections
        tablename = "gis_projection"
        table = define_table(tablename,
                             Field("name", length=64,
                                   notnull=True, unique=True,
                                   label = T("Name")),
                             Field("epsg", "integer",
                                   notnull=True, label="EPSG",
                                   requires = IS_NOT_EMPTY()),
                             Field("maxExtent", length=64, notnull=True,
                                   label = T("maxExtent"),
                                   # @ToDo: Add a specialised validator
                                   requires = IS_NOT_EMPTY()),
                             Field("maxResolution", "double", notnull=True,
                                   label = T("maxResolution"),
                                   # @ToDo: Add a specialised validator
                                   requires = IS_NOT_EMPTY()),
                             Field("units", notnull=True,
                                   label = T("Units"),
                                   requires = IS_IN_SET(["m", "degrees"],
                                                        zero=None)),
                             *s3_meta_fields())

        # CRUD Strings
        ADD_PROJECTION = T("Add Projection")
        crud_strings[tablename] = Storage(
            title_create = ADD_PROJECTION,
            title_display = T("Projection Details"),
            title_list = T("Projections"),
            title_update = T("Edit Projection"),
            title_search = T("Search Projections"),
            subtitle_create = T("Add New Projection"),
            label_list_button = T("List Projections"),
            label_create_button = ADD_PROJECTION,
            label_delete_button = T("Delete Projection"),
            msg_record_created = T("Projection added"),
            msg_record_modified = T("Projection updated"),
            msg_record_deleted = T("Projection deleted"),
            msg_list_empty = T("No Projections currently defined"))

        # Reusable field to include in other table definitions
        projection_id = S3ReusableField("projection_id", table,
                                        sortby="name",
                                        requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                        "gis_projection.id",
                                                                        "%(name)s")),
                                        represent = lambda id: \
                                            (id and [db(db.gis_projection.id == id).select(db.gis_projection.name,
                                                                                           limitby=(0, 1)).first().name] or [NONE])[0],
                                        label = T("Projection"),
                                        comment=S3AddResourceLink(c="gis",
                                                                  f="projection",
                                                                  label=ADD_PROJECTION,
                                                                  title=T("Projection"),
                                                                  tooltip="%s|%s|%s" % (T("The system supports 2 projections by default:"),
                                                                                        T("Spherical Mercator (900913) is needed to use OpenStreetMap/Google/Bing base layers."),
                                                                                        T("WGS84 (EPSG 4236) is required for many WMS servers."))),
                                        ondelete = "RESTRICT")

        configure(tablename,
                  deduplicate=self.gis_projection_deduplicate,
                  deletable=False)

        # =====================================================================
        # GIS Symbology
        # - currently unused
        tablename = "gis_symbology"
        table = define_table(tablename,
                             Field("name", length=32,
                                   notnull=True, unique=True),
                             marker_id(label = T("Default Marker"),
                                       empty=False),
                             *s3_meta_fields())

        ADD_SYMBOLOGY = T("Add Symbology")
        crud_strings[tablename] = Storage(
            title_create = ADD_SYMBOLOGY,
            title_display = T("Symbology"),
            title_list = T("Symbologies"),
            title_update = T("Edit Symbology"),
            title_search = T("Search Symbologies"),
            subtitle_create = T("Add New Symbology"),
            label_list_button = T("List Symbologies"),
            label_create_button = ADD_SYMBOLOGY,
            label_delete_button = T("Delete Symbology"),
            msg_record_created = T("Symbology added"),
            msg_record_modified = T("Symbology updated"),
            msg_record_deleted = T("Symbology deleted"),
            msg_list_empty = T("No Symbologies currently defined")
        )

        # Reusable field to include in other table definitions
        symbology_id = S3ReusableField("symbology_id", table,
                                       sortby="name",
                                       requires = IS_NULL_OR(
                                                    IS_ONE_OF(db, "gis_symbology.id",
                                                              "%(name)s")),
                                       represent = lambda id: \
                                        (id and [db(db.gis_symbology.id == id).select(db.gis_symbology.name,
                                                                                      limitby=(0, 1)).first().name] or [NONE])[0],
                                       label = T("Symbology"),
                                       ondelete = "SET NULL")

        # Components
        # Layers
        add_component("gis_layer_entity",
                      gis_symbology=Storage(
                                    link="gis_layer_symbology",
                                    joinby="symbology_id",
                                    key="layer_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # Markers
        add_component("gis_marker",
                      gis_symbology=Storage(
                                    link="gis_layer_symbology",
                                    joinby="symbology_id",
                                    key="marker_id",
                                    actuate="replace",
                                    autocomplete="name",
                                    autodelete=False))

        configure(tablename,
                  deduplicate=self.gis_symbology_deduplicate)

        # =====================================================================
        # GIS Config
        #
        # uuid==SITE_DEFAULT => Site default settings
        #
        # @ToDo: Settings that apply will be the Site Settings modified
        #        according to any active Event or Region config and any OU or
        #        Personal config found

        pe_types = {
                    1: "person",
                    2: "group",
                    4: "facility",
                    6: "branch",
                    7: "organisation",
                    9: "SITE_DEFAULT",
                }

        tablename = "gis_config"
        table = define_table(tablename,
                             # Name displayed in the GIS config menu.
                             Field("name"),

                             # pe_id for Personal/OU configs
                             super_link("pe_id", "pr_pentity"),
                             # Gets populated onvalidation
                             Field("pe_type", "integer",
                                   requires = IS_NULL_OR(IS_IN_SET(pe_types)),
                                   readable=False,
                                   writable=False,
                                   ),
                             # @ToDo: Allows selection of which OU a person's config should inherit from for disambiguation
                             # - needs implementing in gis.set_config()
                             # - needs a method in gis_config_form_setup() to populate the dropdown from the OUs (in this person's Path for this person's,  would have to be a dynamic lookup for Admins)
                             Field("pe_path", "integer",
                                   readable=False,
                                   writable=False,
                                   ),

                             # Region field
                             location_id("region_location_id",
                                         widget = S3LocationAutocompleteWidget(),
                                         requires = IS_NULL_OR(IS_LOCATION(level=gis.hierarchy_level_keys))),

                             # CRUD Settings
                             # Default Location
                             location_id("default_location_id",
                                         widget = S3LocationAutocompleteWidget(),
                                         requires = IS_NULL_OR(IS_LOCATION())),
                             Field("geocoder", "boolean",
                                   # This would be turned off for Offline deployments or expensive SatComms, such as BGAN
                                   #readable=False,
                                   #writable=False,
                                   # @ToDo: Remove default once we have cascading working
                                   default=True),
                             # Overall Bounding Box for sanity-checking inputs
                             Field("min_lat", "double",
                                   # @ToDo: Remove default once we have cascading working
                                   default=-90,
                                   requires = IS_NULL_OR(IS_LAT())),
                             Field("max_lat", "double",
                                   # @ToDo: Remove default once we have cascading working
                                   default=90,
                                   requires = IS_NULL_OR(IS_LAT())),
                             Field("min_lon", "double",
                                   # @ToDo: Remove default once we have cascading working
                                   default=-180,
                                   requires = IS_NULL_OR(IS_LON())),
                             Field("max_lon", "double",
                                   # @ToDo: Remove default once we have cascading working
                                   default=180,
                                   requires = IS_NULL_OR(IS_LON())),

                             # Map Settings
                             Field("zoom", "integer",
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(1, 20))),
                             Field("lat", "double",
                                   requires = IS_NULL_OR(IS_LAT())),
                             Field("lon", "double",
                                   requires = IS_NULL_OR(IS_LON())),
                             projection_id(
                                   #empty=False,
                                   # Nice if we could get this set to epsg field
                                   #default=900913
                                   ),
                             symbology_id(),
                             Field("wmsbrowser_url"),
                             Field("wmsbrowser_name",
                                   # @ToDo: Remove default once we have cascading working
                                   default="Web Map Service"),
                             # OpenStreetMap settings:
                             # Register your app by logging in to www.openstreetmap.org & then selecting 'oauth settings'
                             Field("osm_oauth_consumer_key"),
                             Field("osm_oauth_consumer_secret"),
                             # Note: This hasn't yet been changed for any instance
                             # Do we really need it to be configurable?
                             Field("zoom_levels", "integer",
                                   requires = IS_NULL_OR(IS_INT_IN_RANGE(1, 30)),
                                   readable=False,
                                   writable=False,
                                   # @ToDo: Remove default once we have cascading working
                                   default = 22),

                             *s3_meta_fields())

        # Reusable field - used by Events & Scenarios
        config_id = S3ReusableField("config_id", table,
                                    #readable=False,
                                    #writable=False,
                                    requires = IS_ONE_OF(db,
                                                         "gis_config.id",
                                                         "%(name)s"),
                                    represent = self.gis_config_represent,
                                    label = T("Map Configuration"),
                                    ondelete = "CASCADE")

        ADD_CONFIG = T("Add Map Configuration")
        crud_strings[tablename] = Storage(
            title_create = ADD_CONFIG,
            title_display = T("Map Configuration"),
            title_list = T("Map Configurations"),
            title_update = T("Edit Map Configuration"),
            title_search = T("Search Map Configurations"),
            subtitle_create = T("Add New Map Configuration"),
            label_list_button = T("List Map Configurations"),
            label_create_button = ADD_CONFIG,
            label_delete_button = T("Delete Map Configuration"),
            msg_record_created = T("Map Configuration added"),
            msg_record_modified = T("Map Configuration updated"),
            msg_record_deleted = T("Map Configuration deleted"),
            msg_list_empty = T("No Map Configurations currently defined")
        )

        # Components
        # Layers
        add_component("gis_layer_entity",
                      gis_config=Storage(
                                    link="gis_layer_config",
                                    joinby="config_id",
                                    key="layer_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        configure(tablename,
                  deduplicate=self.gis_config_deduplicate,
                  onvalidation=self.gis_config_onvalidation,
                  onaccept=self.gis_config_onaccept,
                  create_next=URL(args=["[id]", "layer_entity"]),
                  ondelete=self.gis_config_ondelete,
                  subheadings = {
                       T("Map Settings"): "zoom",
                       T("Form Settings"): "default_location_id",
                   },
                  list_fields = ["id",
                                 "name",
                                 "pe_id",
                                 "region_location_id",
                                 "default_location_id",
                               ])

        if current.deployment_settings.get_security_map() and not \
           current.auth.s3_has_role("MapAdmin"):
            configure(tablename,
                      deletable=False)

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
        table = define_table(tablename,
                             config_id(),
                             super_link("pe_id", "pr_pentity"),
                             *s3_meta_fields())

        # Initially will be populated only when a Personal config is created
        # CRUD Strings
        # ADD_MENU = T("Add Menu Entry")
        # crud_strings[tablename] = Storage(
            # title_create = ADD_MENU,
            # title_display = T("Menu Entry Details"),
            # title_list = T("Menu Entries"),
            # title_update = T("Edit Menu Entry"),
            # title_search = T("Search Menu Entries"),
            # subtitle_create = T("Add New Menu Entry"),
            # label_list_button = T("List Menu Entries"),
            # label_create_button = ADD_MENU,
            # label_delete_button = T("Delete Menu Entry"),
            # msg_record_created = T("Menu Entry added"),
            # msg_record_modified = T("Menu Entry updated"),
            # msg_record_deleted = T("Menu Entry deleted"),
            # msg_list_empty = T("No Menu Entries currently defined"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                gis_config_form_setup = self.gis_config_form_setup,
                gis_config_id = config_id,
                gis_marker_id = marker_id,
                gis_projection_id = projection_id,
                gis_symbology_id = symbology_id,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_form_setup():
        """ Prepare the gis_config form """

        T = current.T
        table = current.db.gis_config

        # Defined here since Component (of Persons)
        # @ToDo: Need tooltips for projection, symbology, geocoder, zoom levels,
        # cluster distance, and cluster threshold.
        table.name.label = T("Name")
        table.name.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Name"),
                T("If this configuration is displayed on the GIS config menu, give it a name to use in the menu. The name for a personal map configuration will be set to the user's name.")))
        field = table.pe_id
        field.label = T("Person or OU")
        field.readable = True
        field.writable = True
        field.represent = lambda id: current.s3db.pr_pentity_represent(id, show_label=False)
        field.widget = S3AutocompleteWidget("pr", "pentity")
        table.region_location_id.label = T("Region")
        table.default_location_id.label = T("Default Location")
        table.default_location_id.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Default Location"),
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
        table.wmsbrowser_name.label = T("Web Map Service Browser Name")
        table.wmsbrowser_name.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Web Map Service Browser Name"),
                T("Title to show for the Web Map Service panel in the Tools panel.")))
        table.wmsbrowser_url.label = T("Web Map Service Browser URL")
        table.wmsbrowser_url.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s" % (
                T("Web Map Service Browser URL"),
                T("The URL for the GetCapabilities page of a Web Map Service (WMS) whose layers you want available via the Browser panel on the Map."),
                T("The form of the URL is http://your/web/map/service?service=WMS&request=GetCapabilities where your/web/map/service stands for the URL path to the WMS.")))
        table.osm_oauth_consumer_key.label = T("OpenStreetMap OAuth Consumer Key")
        table.osm_oauth_consumer_key.comment = DIV(
            _class="stickytip",
            _title="%s|%s|%s" % (
                T("OpenStreetMap OAuth Consumer Key"),
                T("In order to be able to edit OpenStreetMap data from within %(name_short)s, you need to register for an account on the OpenStreet server.") % \
                    dict(name_short=current.deployment_settings.get_system_name_short()),
                T("Go to %(url)s, sign up & then register your application. You can put any URL in & you only need to select the 'modify the map' permission.") % \
                    dict(url=A("http://www.openstreetmap.org",
                         _href="http://www.openstreetmap.org",
                         _target="blank"))))
        table.osm_oauth_consumer_secret.label = T("OpenStreetMap OAuth Consumer Secret")
        table.geocoder.label = T("Use Geocoder for address lookups?")
        table.min_lat.label = T("Minimum Location Latitude")
        table.min_lat.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s" % (
                T("Minimum Location Latitude"),
                T("Latitude of far southern end of the region of interest."),
                T("Used to check that latitude of entered locations is reasonable. May be used to filter lists of resources that have locations.")))
        table.max_lat.label = T("Maximum Location Latitude")
        table.max_lat.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s" % (
                T("Maximum Location Latitude"),
                T("Latitude of far northern end of the region of interest."),
                T("Used to check that latitude of entered locations is reasonable. May be used to filter lists of resources that have locations.")))
        table.min_lon.label = T("Minimum Location Longitude")
        table.min_lon.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s" % (
                T("Minimum Location Longitude"),
                T("Longitude of far western end of the region of interest."),
                T("Used to check that longitude of entered locations is reasonable. May be used to filter lists of resources that have locations.")))
        table.max_lon.label = T("Maximum Location Longitude")
        table.max_lon.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s" % (
                T("Maximum Location Longitude"),
                T("Longitude of far eastern end of the region of interest."),
                T("Used to check that longitude of entered locations is reasonable. May be used to filter lists of resources that have locations.")))
        table.zoom_levels.label = T("Zoom Levels")
        table.zoom.label = T("Map Zoom")
        table.zoom.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Zoom"),
                T("How much detail is seen. A high Zoom level means lot of detail, but not a wide area. A low Zoom level means seeing a wide area, but not a high level of detail.")))
        table.region_location_id.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Region Location"),
                T("A location that specifies the geographic area for this region. This can be a location from the location hierarchy, or a 'group location', or a location that has a boundary for the area.")))

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_deduplicate(item):
        """
          This callback will be called when importing Marker records it will look
          to see if the record being imported is a duplicate.

          @param item: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

        """

        if item.tablename == "gis_config" and \
            "name" in item.data:
            # Match by name (all-lowercase)
            table = item.table
            name = item.data.name
            query = (table.name.lower() == name.lower())
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_represent(id):
        """
            Represent a Configuration
        """

        if not id:
            return current.messages.NONE

        db = current.db
        table = db.gis_config
        query = (table.id == id)
        record = db(query).select(table.name,
                                  limitby=(0, 1)).first()
        try:
            return record.name
        except:
            return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_onvalidation(form):
        """
            Check region values. Add name for personal & site configs.

            If this a region location is set, protect that location from accidental
            editing (e.g. if it is used as a default location for any resources in
            the region) but making it only editable by a MapAdmin.
        """

        db = current.db
        s3db = current.s3db
        vars = form.vars

        if vars.uuid == "SITE_DEFAULT":
            vars.pe_type = 9
        elif "pe_id" in vars:
            pe_id = vars.pe_id
            if pe_id:
                # Populate the pe_type
                table = s3db.pr_pentity
                query = (table.pe_id == pe_id)
                pe = db(query).select(table.instance_type,
                                      limitby=(0, 1)).first()
                if pe:
                    pe_type = pe.instance_type
                    if pe_type == "pr_person":
                        vars.pe_type = 1
                    elif pe_type == "pr_group":
                        vars.pe_type = 2
                    elif pe_type == "org_office":
                        vars.pe_type = 4
                    elif pe_type == "org_organisation":
                        # Check if we're a branch
                        otable = s3db.org_organisation
                        btable = s3db.org_organisation_branch
                        query = (otable.pe_id == pe_id) & \
                                (btable.branch_id == otable.id)
                        branch = db(query).select(btable.id,
                                                  limitby=(0, 1)).first()
                        if branch:
                            vars.pe_type = 6
                        else:
                            vars.pe_type = 7

        # If there's a region location, set its owned by role to MapAdmin.
        # That makes Authenticated no longer an owner, so they only get whatever
        # is permitted by uacl (currently that is set to READ).
        if "region_location_id" in vars and vars.region_location_id:
            MAP_ADMIN = current.session.s3.system_roles.MAP_ADMIN
            table = db.gis_location
            query = (table.id == vars.region_location_id)
            db(query).update(owned_by_group = MAP_ADMIN)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_onaccept(form):
        """
            If this is the cached config, clear the cache.

            If this is this user's personal config, clear the config
            If this is an OU config, then add to GIS menu
        """

        try:
            update = False
            id = form.vars.id
            pe_id = form.request_vars.pe_id
            if pe_id:
                if pe_id == current.auth.user.pe_id:
                    # Clear the current config
                    current.response.s3.gis.config = None
                # Add to GIS Menu
                table = current.db.gis_menu
                table.update_or_insert(config_id=id,
                                       pe_id=pe_id)
            else:
                config = current.response.s3.gis.config
                if config and config.id == id:
                    # This is the currently active config, so clear our cache
                    config = None
        except:
            # AJAX Save of Viewport from Map
            pass

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_ondelete(row):
        """
            If the currently-active config was deleted, clear the cache
        """

        s3 = current.response.s3
        if s3.gis.config and \
           s3.gis.config.id == row.id:
                s3.gis.config = None

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_marker_represent(id):
        """
            Represent a Marker by it's picture
        """

        if not id:
            return current.messages.NONE

        if isinstance(id, Row):
            record = id
        else:
            db = current.db
            table = db.gis_marker
            record = db(table.id == id).select(table.image,
                                               limitby=(0, 1)).first()
        try:
            represent = DIV(IMG(_src=URL(c="static", f="img",
                                         args=["markers", record.image]),
                                _height=40))
        except:
            return current.messages.UNKNOWN_OPT

        return represent

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_marker_onvalidation(form):
        """
            Record the size of an Image upon Upload
            Don't wish to resize here as we'd like to use full resolution for printed output
        """

        vars = form.vars
        image = vars.image
        if isinstance(image, str):
            # This is an update not a create, so file not in form
            return

        try:
            from PIL import Image
        except ImportError:
            import Image

        im = Image.open(image.file)
        (width, height) = im.size
        vars.image.file.seek(0)

        vars.width = width
        vars.height = height

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_marker_deduplicate(item):
        """
          This callback will be called when importing Marker records it will look
          to see if the record being imported is a duplicate.

          @param item: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

        """

        if item.tablename == "gis_marker" and \
            "name" in item.data:
            # Match by name (all-lowercase)
            table = item.table
            name = item.data.name
            query = (table.name.lower() == name.lower())
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_marker_retrieve(filename, path=None):
        """
            custom_retrieve to override web2py DAL's standard retrieve,
            as that checks filenames for uuids, so doesn't work with
            pre-populated files in static
        """

        if not path:
            path = current.db.gis_marker.image.uploadfolder

        if "/" in filename:
            _path, filename = filename.split("/")
            image = open(os.path.join(path, _path, filename), "rb")
        else:
            image = open(os.path.join(path, filename), "rb")
        return (filename, image)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_projection_deduplicate(item):
        """
          This callback will be called when importing Projection records it will look
          to see if the record being imported is a duplicate.

          @param item: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

        """

        if item.tablename == "gis_projection" and \
            "epsg" in item.data:
            # Match by epsg
            table = item.table
            epsg = item.data.epsg
            query = (table.epsg == epsg)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_symbology_deduplicate(item):
        """
          This callback will be called when importing Symbology records it will look
          to see if the record being imported is a duplicate.

          @param item: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

        """

        if item.tablename == "gis_symbology" and \
            "name" in item.data:
            # Match by name (all-lowercase)
            table = item.table
            name = item.data.name
            query = (table.name.lower() == name.lower())
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3LayerEntityModel(S3Model):
    """
        Model for Layer SuperEntity
        - used to provide a common link table for:
            Layers <> Configs (applicable to Vectors & Rasters)
                for Enabled/Visible
            Layers <> Symbology (applicable to Vectors)
                for Marker/GPS Symbol
    """

    names = ["gis_layer_entity",
             "gis_layer_config",
             "gis_layer_symbology",
             "gis_layer_config_onaccept",
             ]

    def model(self):

        T = current.T
        db = current.db

        config_id = self.gis_config_id
        marker_id = self.gis_marker_id
        symbology_id = self.gis_symbology_id

        NONE = current.messages.NONE

        # Shortcuts
        add_component = self.add_component
        crud_strings = current.response.s3.crud_strings
        define_table = self.define_table

        # =====================================================================
        #  Layer Entity

        # @ToDo: shapefile, scan, xyz
        layer_types = Storage(gis_layer_feature = T("Feature Layer"),
                              gis_layer_arcrest = T("ArcGIS REST Layer"),
                              gis_layer_bing = T("Bing Layer"),
                              gis_layer_coordinate = T("Coordinate Layer"),
                              gis_layer_empty = T("No Base Layer"),
                              gis_layer_openstreetmap = T("OpenStreetMap Layer"),
                              gis_layer_geojson = T("GeoJSON Layer"),
                              gis_layer_georss = T("GeoRSS Layer"),
                              gis_layer_google = T("Google Layer"),
                              gis_layer_gpx = T("GPX Layer"),
                              gis_layer_js = T("JS Layer"),
                              gis_layer_kml = T("KML Layer"),
                              gis_layer_mgrs = T("MGRS Layer"),
                              gis_layer_openweathermap = T("OpenWeatherMap Layer"),
                              gis_layer_theme = T("Theme Layer"),
                              gis_layer_tms = T("TMS Layer"),
                              gis_layer_wfs = T("WFS Layer"),
                              gis_layer_wms = T("WMS Layer"),
                              gis_layer_xyz = T("XYZ Layer"),
                            )

        tablename = "gis_layer_entity"
        table = self.super_entity(tablename, "layer_id", layer_types,
                                  name_field()(),
                                  Field("description", label=T("Description")),
                                  #role_required(),       # Single Role
                                  ##roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                )

        crud_strings[tablename] = Storage(
                    title_create = T("Add Layer"),
                    title_display = T("Layer Details"),
                    title_list = T("Layers"),
                    title_update = T("Edit Layer"),
                    title_search = T("Search Layers"),
                    subtitle_create = T("Add New Layer"),
                    label_list_button = T("List Layers"),
                    label_create_button = T("Add Layer"),
                    label_delete_button = T("Delete Layer"),
                    msg_record_created = T("Layer added"),
                    msg_record_modified = T("Layer updated"),
                    msg_record_deleted = T("Layer deleted"),
                    msg_list_empty=T("No Layers currently defined"))

        layer_id = self.super_link("layer_id", "gis_layer_entity",
                                    label = T("Layer"),
                                    # SuperLinks don't support requires
                                    #requires = IS_ONE_OF(db,
                                    #                     "gis_layer_entity.layer_id",
                                    #                     "%(name)s",
                                    # This filter is applied in the symbology controller to restrict to just those layer types with Markers
                                    #                     filterby="instance_type",
                                    #                     filter_opts=("gis_layer_feature",
                                    #                                  "gis_layer_georss",
                                    #                                  "gis_layer_geojson",
                                    #                                  "gis_layer_kml")
                                    #                     ),
                                    represent = gis_layer_represent,
                                    readable=True, writable=True)

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_entity=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # Symbologies
        add_component("gis_symbology",
                      gis_layer_entity=Storage(
                                    link="gis_layer_symbology",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="symbology_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # =====================================================================
        #  Layer Config link table

        # Style is a JSON object with the following structure (only the 3 starred elements are currently parsed):
        #Style = [{
        #   low: float,   //*
        #   high: float,  //*
        #   fill: string, //*
        #   fill_opacity: float,
        #   stroke: stroke
        #   stroke_opacity: float
        #   stroke_width: float or int, // OpenLayers wants int, SLD wants float
        #   marker: {
        #       image: string,
        #       height: int,
        #       width: int
        #   }
        #   shape: string,
        #   label: {}
        #}]

        tablename = "gis_layer_config"
        table = define_table(tablename,
                             layer_id,
                             config_id(),
                             Field("enabled", "boolean", default=True,
                                   label=T("Available in Viewer?")),
                             Field("visible", "boolean", default=True,
                                   label=T("On by default?")),
                             Field("base", "boolean", default=False,
                                   label=T("Default Base layer?")),
                             Field("style", "text",
                                   # Only used by Theme Layers currently
                                   readable=False,
                                   writable=False,
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("Style"),
                                                                   T("This is normally edited using the Widget in the Style Tab in the Layer Properties on the Map."))),
                                   label=T("Style")),
                             *s3_meta_fields())
        # Default to the Layer -> Config view
        # sinne there are many diff layers
        # - override for single Config -> Layer
        crud_strings[tablename] = Storage(
                    title_create = T("Add Profile Configuration for this Layer"),
                    title_display = T("Profile Configuration"),
                    title_list = T("Profile Configurations"),
                    title_update = T("Edit Profile Configuration"),
                    subtitle_create = T("Add New Profile Configuration"),
                    label_list_button = T("List Profiles configured for this Layer"),
                    label_create_button = T("Add Profile Configuration"),
                    label_delete_button = T("Remove Profile Configuration for Layer"),
                    msg_record_created = T("Profile Configured"),
                    msg_record_modified = T("Profile Configuration updated"),
                    msg_record_deleted = T("Profile Configuration removed"),
                    msg_list_empty = T("No Profiles currently have Configurations for this Layer"))

        self.configure(tablename,
                        onvalidation=self.layer_config_onvalidation,
                        onaccept=self.layer_config_onaccept)

        # =====================================================================
        #  Layer Symbology link table

        tablename = "gis_layer_symbology"
        table = define_table(tablename,
                             layer_id,
                             symbology_id(),
                             marker_id(),
                             Field("gps_marker", label = T("GPS Marker"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("GPS Marker"),
                                                                   T("Defines the icon used for display of features on handheld GPS."))),
                                   # This is the list of GPS Markers for Garmin devices
                                   requires = IS_NULL_OR(IS_IN_SET(current.gis.gps_symbols(),
                                                                   zero=T("Use default")))),
                             *s3_meta_fields())

        # Default to the Layer -> Symbology view
        # since there are many diff layers
        # - override for single Symbology -> Layer
        crud_strings[tablename] = Storage(
                    title_create = T("Add Symbology for Layer"),
                    title_display = T("Symbology"),
                    title_list = T("Symbologies"),
                    title_update = T("Edit Symbology"),
                    subtitle_create = T("Add New Symbology for Layer"),
                    label_list_button = T("List Symbologies for Layer"),
                    label_create_button = T("Add Symbology for Layer"),
                    label_delete_button = T("Remove Symbology from Layer"),
                    msg_record_created = T("Symbology added"),
                    msg_record_modified = T("Symbology updated"),
                    msg_record_deleted = T("Symbology removed from Layer"),
                    msg_list_empty = T("No Symbologies currently defined for this Layer"))

        # ---------------------------------------------------------------------
        return Storage(
                gis_layer_types = layer_types,
                gis_layer_config_onaccept = self.layer_config_onaccept
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def layer_config_onvalidation(form):
        """
            Ensure that Style JSON can be loaded by json.loads()
        """

        vars = form.vars
        if "style" in vars and vars.style:
            vars.style = vars.style.replace("'", "\"")

    # -------------------------------------------------------------------------
    @staticmethod
    def layer_config_onaccept(form):
        """
            If this is the default base layer then remove this flag from all
            others in this config.
        """

        vars = form.vars
        base = vars.base
        if base == "False":
            base = False
        enabled = vars.enabled
        if enabled == "False":
            enabled = False

        if base and enabled:
            db = current.db
            s3db = current.s3db
            ctable = s3db.gis_config
            ltable = db.gis_layer_config
            query = (ltable.id == vars.id) & \
                    (ltable.config_id == ctable.id)
            config = db(query).select(ctable.id,
                                      limitby=(0, 1)).first()
            if config:
                # Set all others in this config as not the default Base Layer
                query  = (ltable.config_id == config.id) & \
                         (ltable.base == True) & \
                         (ltable.id != vars.id)
                db(query).update(base = False)

# =============================================================================
class S3FeatureLayerModel(S3Model):
    """
        Model for Feature Layers
        - used to select a set of Features for either Display on a Map
          or Export as XML: S3XML.gis_encode()
          (for transformation to GeoJSON/KML/GPX)
    """

    names = ["gis_layer_feature"]

    def model(self):

        T = current.T
        db = current.db

        add_component = self.add_component
        crud_strings = current.response.s3.crud_strings

        # =====================================================================
        # Feature Layers

        tablename = "gis_layer_feature"
        table = self.define_table(tablename,
                                  self.super_link("layer_id", "gis_layer_entity"),
                                  name_field()(),
                                  Field("description", label=T("Description")),
                                  # Kept for backwards-compatibility
                                  Field("module",
                                        readable=False,
                                        writable=False),
                                  Field("resource",
                                        readable=False,
                                        writable=False),
                                  Field("trackable", "boolean",
                                        label = T("Trackable"),
                                        default = False,
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Trackable"),
                                                                        T("Whether the resource should be tracked using S3Track rather than just using the Base Location")))),
                                  # REST Query added to Map JS to call back to server
                                  Field("controller",
                                        requires = IS_NOT_EMPTY(),
                                        label = T("Controller"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s /" % (T("Controller"),
                                                                          T("Part of the URL to call to access the Features")))),
                                  Field("function",
                                        requires = IS_NOT_EMPTY(),
                                        label = T("Function"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s /" % (T("Function"),
                                                                          T("Part of the URL to call to access the Features")))),
                                  Field("filter",
                                        label = T("REST Filter"),
                                        comment = DIV(_class="stickytip",
                                                      _title="%s|%s" % (T("REST Filter"),
                                                                        "%s: <a href='http://eden.sahanafoundation.org/wiki/S3XRC/RESTfulAPI/URLFormat#BasicQueryFormat' target='_blank'>Trac</a>" % \
                                                                          T("Uses the REST Query Format defined in")))),
                                  # SQL Query to determine icon for feed export (e.g. type=1)
                                  # @ToDo: Have both be REST-style with this being used for both & optional additional params available for main map (e.g. obsolete=False&time_between...)
                                  Field("filter_field",
                                        label = T("Filter Field")),
                                  Field("filter_value",
                                        label = T("Filter Value"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s /" % (T("Filter Value"),
                                                                          T("If you want several values, then separate with")))),
                                  Field("popup_label",        # @ToDo: Replace with s3.crud_strings[tablename]?
                                        label = T("Popup Label"),
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Popup Label"),
                                                                      T("Used in onHover Tooltip & Cluster Popups to differentiate between types.")))),
                                  Field("popup_fields",
                                        default = "name",
                                        label = T("Popup Fields"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s" % (T("Popup Fields"),
                                                                        T("Used to build onHover Tooltip & 1st field also used in Cluster Popups to differentiate between records.")))),
                                  gis_layer_folder()(),
                                  Field("polygons", "boolean", default=False,
                                        label=T("Display Polygons?")),
                                  gis_opacity()(),
                                  # @ToDo: Expose the Graphic options
                                  gis_refresh()(),
                                  cluster_distance()(),
                                  cluster_threshold()(),
                                  s3_role_required(),    # Single Role
                                  #s3_roles_permitted(), # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3_meta_fields())

        # CRUD Strings
        ADD_FEATURE_LAYER = T("Add Feature Layer")
        crud_strings[tablename] = Storage(
            title_create = ADD_FEATURE_LAYER,
            title_display = T("Feature Layer Details"),
            title_list = T("Feature Layers"),
            title_update = T("Edit Feature Layer"),
            title_search = T("Search Feature Layers"),
            subtitle_create = T("Add New Feature Layer"),
            label_list_button = T("List Feature Layers"),
            label_create_button = ADD_FEATURE_LAYER,
            label_delete_button = T("Delete Feature Layer"),
            msg_record_created = T("Feature Layer added"),
            msg_record_modified = T("Feature Layer updated"),
            msg_record_deleted = T("Feature Layer deleted"),
            msg_list_empty = T("No Feature Layers currently defined"))

        self.configure(tablename,
                        onaccept=gis_layer_onaccept,
                        super_entity="gis_layer_entity",
                        deduplicate=self.gis_layer_feature_deduplicate,
                        list_fields=["id",
                                     "name",
                                     "description",
                                     "module",
                                     "resource",
                                     "filter",
                                     "filter_field",
                                     "filter_value",
                                     "popup_label",
                                     "popup_fields",
                                     "dir",
                                     ])

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_feature=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # Symbologies
        add_component("gis_symbology",
                      gis_layer_feature=Storage(
                                    link="gis_layer_symbology",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="symbology_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        return Storage(
            )


    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_feature_deduplicate(item):
        """
          This callback will be called when importing Symbology records it will look
          to see if the record being imported is a duplicate.

          @param item: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

        """

        if item.tablename == "gis_layer_feature":
            # Match if controller, function & filter are identical
            table = item.table
            data = item.data
            controller = data.controller
            function = data.function
            filter = data.filter
            query = (table.controller.lower() == controller.lower()) & \
                    (table.function.lower() == function.lower()) & \
                    (table.filter == filter)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3MapModel(S3Model):
    """ Models for Maps """

    names = ["gis_cache",
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
             "gis_layer_tms",
             "gis_layer_wfs",
             "gis_layer_wms",
             "gis_layer_xyz",
             #"gis_style"
             ]

    def model(self):

        T = current.T
        db = current.db
        request = current.request

        #location_id = self.gis_location_id
        marker_id = self.gis_marker_id
        projection_id = self.gis_projection_id

        # Shortcuts
        add_component = self.add_component
        configure = self.configure
        define_table = self.define_table

        layer_id = self.super_link("layer_id", "gis_layer_entity")

        # ---------------------------------------------------------------------
        # GIS Feature Queries
        #
        # Store results of Feature Queries in a temporary table to allow
        # BBOX queries, Clustering, Refresh, Client-side Filtering, etc

        tablename = "gis_feature_query"
        table = define_table(tablename,
                             Field("name", length=128, notnull=True),
                             Field("lat", "double", requires=IS_LAT()),
                             Field("lon", "double", requires=IS_LON()),
                             Field("popup_url"),
                             Field("popup_label"),
                             # Optional Marker
                             Field("marker_url"),
                             Field("marker_height", "integer"),
                             Field("marker_width", "integer"),
                             # or Shape/Size/Colour
                             Field("shape",
                                   requires=IS_NULL_OR(IS_IN_SET(["circle", "square", "star", "x", "cross", "triangle"]))),
                             Field("size", "integer"),
                             Field("colour", requires=IS_NULL_OR(IS_HTML_COLOUR())),
                             gis_opacity()(),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # GPS Waypoints
        #tablename = "gis_waypoint"
        #table = define_table(tablename,
        #                     Field("name", length=128, notnull=True,
        #                           label = T("Name")),
        #                     Field("description", length=128,
        #                           label = T("Description")),
        #                     Field("category", length=128,
        #                           label = T("Category")),
        #                     location_id(),
        #                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # GPS Tracks (stored as 1 record per point)
        #tablename = "gis_trackpoint"
        #table = define_table(tablename,
        #                     location_id(),
        #                     #track_id(),        # link to the uploaded file?
        #                     *s3_meta_fields())

        # ---------------------------------------------------------------------
        # ArcGIS REST
        #

        tablename = "gis_layer_arcrest"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("url", label=T("Location"),
                                   requires=IS_NOT_EMPTY(),
                                   comment=DIV(_class="stickytip",
                                               _title="%s|%s" % (T("Location"),
                                                                 "%s:%s" % (T("This should be an export service URL"),
                                                                            A("http://sampleserver1.arcgisonline.com/ArcGIS/SDK/REST/export.html",
                                                                              _href="http://sampleserver1.arcgisonline.com/ArcGIS/SDK/REST/export.html",
                                                                              _target="_blank"))))
                                   ),
                             Field("layers", "list:integer",
                                   default=0,
                                   label=T("Layers")),
                             Field("base", "boolean", default=False,
                                    label=T("Base Layer?")),
                             Field("transparent", "boolean", default=True,
                                   label=T("Transparent?")),
                             gis_layer_folder()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_arcrest=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # Bing
        #

        bing_layer_types = ["aerial", "road", "hybrid"]

        tablename = "gis_layer_bing"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("type", length=16, label=T("Type"),
                                   requires=IS_IN_SET(bing_layer_types)),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_bing=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # Coordinate
        #

        tablename = "gis_layer_coordinate"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             gis_layer_folder()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_coordinate=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # Empty
        #

        tablename = "gis_layer_empty"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             gis_layer_folder()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_coordinate=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # GeoJSON
        #

        tablename = "gis_layer_geojson"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("url", label=T("Location"), requires=IS_NOT_EMPTY()),
                             projection_id(default=2,
                                           requires = IS_ONE_OF(db, "gis_projection.id",
                                                                "%(name)s")),
                             gis_layer_folder()(),
                             gis_opacity()(),
                             gis_refresh()(),
                             cluster_distance()(),
                             cluster_threshold()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_geojson=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # Symbologies
        add_component("gis_symbology",
                      gis_layer_geojson=Storage(
                                    link="gis_layer_symbology",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="symbology_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # GeoRSS
        #

        tablename = "gis_layer_georss"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("url", label=T("Location"), requires = IS_NOT_EMPTY()),
                             Field("data", label=T("Data"),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s|%s" % (T("Data"),
                                                                    T("Optional. The name of an element whose contents should be put into Popups."),
                                                                    T("If it is a URL leading to HTML, then this will downloaded.")))),
                             Field("image", label=T("Image"),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Image"),
                                                                 T("Optional. The name of an element whose contents should be a URL of an Image file put into Popups.")))),
                             gis_layer_folder()(),
                             gis_opacity()(),
                             gis_refresh()(),
                             cluster_distance()(),
                             cluster_threshold()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  deduplicate = self.gis_layer_georss_deduplicate,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_georss=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # Symbologies
        add_component("gis_symbology",
                      gis_layer_georss=Storage(
                                    link="gis_layer_symbology",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="symbology_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # Google
        #

        google_layer_types = ["satellite", "maps", "hybrid", "terrain",
                              "mapmaker", "mapmakerhybrid",
                              "earth", "streetview"]

        tablename = "gis_layer_google"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("type", length=16, label=T("Type"),
                                   requires=IS_IN_SET(google_layer_types)),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_google=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # GPX
        #

        tablename = "gis_layer_gpx"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("track", "upload", autodelete = True,
                                   label = T("GPS Track File"),
                                   requires = IS_UPLOAD_FILENAME(extension="gpx"),
                                   # upload folder needs to be visible to the download() function as well as the upload
                                   uploadfolder = os.path.join(request.folder,
                                                               "uploads",
                                                               "tracks"),
                                   comment = DIV(_class="tooltip",
                                                 _title="%s|%s" % (T("GPS Track"),
                                                                   T("A file in GPX format taken from a GPS."),
                                                                    #T("Timestamps can be correlated with the timestamps on the photos to locate them on the map.")
                                                                  ))),
                              Field("waypoints", "boolean", default=True,
                                   label=T("Display Waypoints?")),
                             Field("tracks", "boolean", default=True,
                                   label=T("Display Tracks?")),
                             Field("routes", "boolean", default=False,
                                   label=T("Display Routes?")),
                             gis_layer_folder()(),
                             gis_opacity()(),
                             cluster_distance()(),
                             cluster_threshold()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_gpx=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # KML
        #

        tablename = "gis_layer_kml"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("url", label=T("Location"),
                                   requires=IS_NOT_EMPTY(),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Location"),
                                                                 T("The URL to access the service.")))),
                             Field("title", label=T("Title"), default="name",
                                   comment=T("The attribute within the KML which is used for the title of popups.")),
                             Field("body", label=T("Body"), default="description",
                                   comment=T("The attribute(s) within the KML which are used for the body of popups. (Use a space between attributes)")),
                             gis_layer_folder()(),
                             gis_opacity()(),
                             gis_refresh()(),
                             cluster_distance()(),
                             cluster_threshold()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  deduplicate = self.gis_layer_kml_deduplicate,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_kml=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # Symbologies
        add_component("gis_symbology",
                      gis_layer_kml=Storage(
                                    link="gis_layer_symbology",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="symbology_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # JS
        # - raw JavaScript code for advanced users
        # @ToDo: Move to a Plugin (more flexible)

        tablename = "gis_layer_js"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("code", "text", label=T("Code"),
                                   default="var myNewLayer = new OpenLayers.Layer.XYZ();\nmap.addLayer(myNewLayer);"),
                             gis_layer_folder()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        # add_component("gis_config",
                      # gis_layer_js=Storage(
                                    # link="gis_layer_config",
                                    # pkey="layer_id",
                                    # joinby="layer_id",
                                    # key="config_id",
                                    # actuate="hide",
                                    # autocomplete="name",
                                    # autodelete=False))

        # ---------------------------------------------------------------------
        # MGRS
        #

        tablename = "gis_layer_mgrs"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("url", label=T("Location"),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Location"),
                                                                 T("The URL to access the service.")))),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        # add_component("gis_config",
                      # gis_layer_mgrs=Storage(
                                    # link="gis_layer_config",
                                    # pkey="layer_id",
                                    # joinby="layer_id",
                                    # key="config_id",
                                    # actuate="hide",
                                    # autocomplete="name",
                                    # autodelete=False))

        # ---------------------------------------------------------------------
        # OpenStreetMap
        #
        # @ToDo: Provide a catalogue of standard layers which are fully-defined
        #        in static & can just have name over-ridden, as well as
        #        fully-custom layers.

        tablename = "gis_layer_openstreetmap"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("url1", label=T("Location"), requires=IS_NOT_EMPTY(),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Location"),
                                                                 T("The URL to access the service.")))),
                             Field("url2", label=T("Secondary Server (Optional)")),
                             Field("url3", label=T("Tertiary Server (Optional)")),
                             Field("base", "boolean", default=True,
                                   label=T("Base Layer?")),
                             Field("attribution", label=T("Attribution")),
                             Field("zoom_levels", "integer",
                                   requires = IS_INT_IN_RANGE(1, 30),
                                   label=T("Zoom Levels"),
                                   default=19),
                             gis_layer_folder()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_openstreetmap=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # OpenWeatherMap
        #

        openweathermap_layer_types = ["station", "city"]

        tablename = "gis_layer_openweathermap"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("type", length=16, label=T("Type"),
                                   requires=IS_IN_SET(openweathermap_layer_types)),
                             gis_layer_folder()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_openweathermap=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # TMS
        #

        tablename = "gis_layer_tms"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("url", label=T("Location"), requires=IS_NOT_EMPTY(),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Location"),
                                                                 T("The URL to access the service.")))),
                             Field("url2", label=T("Secondary Server (Optional)")),
                             Field("url3", label=T("Tertiary Server (Optional)")),
                             Field("layername", label=T("Layer Name"),
                                   requires=IS_NOT_EMPTY()),
                             Field("img_format", label=T("Format")),
                             Field("attribution", label=T("Attribution")),
                             Field("zoom_levels", "integer",
                                   requires = IS_INT_IN_RANGE(1, 30),
                                    label=T("Zoom Levels"),
                                   default=19),
                             gis_layer_folder()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_tms=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # WFS
        #

        tablename = "gis_layer_wfs"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("url", label=T("Location"), requires = IS_NOT_EMPTY(),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Location"),
                                                                 T("Mandatory. The URL to access the service.")))),
                             Field("featureType", label=T("Feature Type"),
                                   requires = IS_NOT_EMPTY(),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Feature Type"),
                                                                  T("Mandatory. In GeoServer, this is the Layer Name. Within the WFS getCapabilities, this is the FeatureType Name part after the colon(:).")))),
                             Field("featureNS", label=T("Feature Namespace"),
                                   requires=IS_NULL_OR(IS_URL()),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Feature Namespace"),
                                                                 T("Optional. In GeoServer, this is the Workspace Namespace URI (not the name!). Within the WFS getCapabilities, this is the FeatureType Name part before the colon(:).")))),
                             Field("title", label=T("Title"), default="name",
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Title"),
                                                                 T("The attribute which is used for the title of popups.")))),
                             Field("username", label=T("Username"),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Username"),
                                                                 T("Optional username for HTTP Basic Authentication.")))),
                             Field("password", label=T("Password"),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Password"),
                                                                 T("Optional password for HTTP Basic Authentication.")))),
                             Field("style_field", label=T("Style Field"),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Style Field"),
                                                                 T("Optional. If you wish to style the features based on values of an attribute, select the attribute to use here.")))),
                             Field("style_values", label=T("Style Values"), default="{}",
                                   comment=DIV(_class="stickytip",
                                               _title="%s|%s" % (T("Style Values"),
                                                                  T("Format the list of attribute values & the RGB value to use for these as a JSON object, e.g.: {Red: '#FF0000', Green: '#00FF00', Yellow: '#FFFF00'}")))),
                             Field("geometryName", label=T("Geometry Name"), default = "the_geom",
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Geometry Name"),
                                                                 T("Optional. The name of the geometry column. In PostGIS this defaults to 'the_geom'.")))),
                             Field("wfs_schema", label=T("Schema"),
                                   requires=IS_NULL_OR(IS_URL()),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Schema"),
                                                                 T("Optional. The name of the schema. In Geoserver this has the form http://host_name/geoserver/wfs/DescribeFeatureType?version=1.1.0&;typename=workspace_name:layer_name.")))),
                             projection_id(default=2), # 4326
                             Field("version", label=T("Version"), default="1.1.0",
                                   requires=IS_IN_SET(["1.0.0", "1.1.0"], zero=None)),
                             gis_layer_folder()(),
                             #gis_refresh()(),
                             gis_opacity()(),
                             cluster_distance()(),
                             cluster_threshold()(),
                             #Field("editable", "boolean", default=False, label=T("Editable?")),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_wfs=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # WMS
        #

        wms_img_formats = ["image/jpeg", "image/jpeg;mode=24bit", "image/png",
                           "image/gif", "image/bmp", "image/tiff",
                           "image/svg+xml"]

        tablename = "gis_layer_wms"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("url", label=T("Location"), requires = IS_NOT_EMPTY(),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Location"),
                                                                 T("The URL to access the service.")))),
                             Field("version", length=32,
                                   label=T("Version"), default="1.1.1",
                                   requires=IS_IN_SET(["1.1.1", "1.3.0"], zero=None)),
                             Field("base", "boolean", default=False,
                                    label=T("Base Layer?")),
                             Field("transparent", "boolean", default=True,
                                   label=T("Transparent?")),
                             gis_layer_folder()(),
                             gis_opacity()(),
                             Field("map", length=32, label=T("Map"),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Map"),
                                                                 T("Optional selection of a MapServer map.")))),
                             Field("layers", label=T("Layers"),
                                   requires=IS_NOT_EMPTY()),
                             Field("username", label=T("Username"),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Username"),
                                                                 T("Optional username for HTTP Basic Authentication.")))),
                             Field("password", label=T("Password"),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Password"),
                                                                 T("Optional password for HTTP Basic Authentication.")))),
                             Field("img_format", length=32, label=T("Format"),
                                    requires=IS_NULL_OR(IS_IN_SET(wms_img_formats)),
                                   default="image/png"),
                             Field("style", length=32, label=T("Style"),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Style"),
                                                                 T("Optional selection of an alternate style.")))),
                             Field("bgcolor", length=32, label=T("Background Color"),
                                   requires=IS_NULL_OR(IS_HTML_COLOUR()),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Background Color"),
                                                                 T("Optional selection of a background color.")))),
                             Field("tiled", "boolean", label=T("Tiled"), default=False,
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s|%s" % (T("Tiled"),
                                                                     T("Tells GeoServer to do MetaTiling which reduces the number of duplicate labels."),
                                                                   T("Note that when using geowebcache, this can be set in the GWC config.")))),
                              Field("buffer", "integer", label=T("Buffer"), default=0,
                                   requires=IS_INT_IN_RANGE(0, 10),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Buffer"),
                                                                 T("The number of tiles around the visible map to download. Zero means that the 1st page loads faster, higher numbers mean subsequent panning is faster.")))),
                             Field("queryable", "boolean", default=True, label=T("Queryable?")),
                             Field("legend_url", label=T("Legend URL"),
                                   comment=DIV(_class="tooltip",
                                                _title="%s|%s" % (T("Legend URL"),
                                                                 T("Address of an image to use for this Layer in the Legend. This allows use of a controlled static image rather than querying the server automatically for what it provides (which won't work through GeoWebCache anyway).")))),
                             #Field("legend_format", label=T("Legend Format"), requires = IS_NULL_OR(IS_IN_SET(gis_layer_wms_img_formats))),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_wms=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # XYZ
        # - e.g. used by OSM community for JOSM/Potlatch
        #
        # @ToDo: Support Overlays with Opacity
        #

        tablename = "gis_layer_xyz"
        table = define_table(tablename,
                             layer_id,
                             name_field()(),
                             Field("description", label=T("Description")),
                             Field("url", label=T("Location"), requires=IS_NOT_EMPTY(),
                                   comment=DIV(_class="tooltip",
                                               _title="%s|%s" % (T("Location"),
                                                                 T("The URL to access the service.")))),
                             Field("url2", label=T("Secondary Server (Optional)")),
                             Field("url3", label=T("Tertiary Server (Optional)")),
                             Field("img_format", label=T("Format")),
                             Field("attribution", label=T("Attribution")),
                             Field("zoom_levels", "integer",
                                   requires = IS_INT_IN_RANGE(1, 30),
                                    label=T("Zoom Levels"),
                                   default=19),
                             gis_layer_folder()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  onaccept=gis_layer_onaccept,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_xyz=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # ---------------------------------------------------------------------
        # GIS Cache
        # ---------------------------------------------------------------------
        # Store downloaded GeoRSS feeds in the DB
        # - to allow refresh timer, BBOX queries, unified approach to Markers & Popups
        tablename = "gis_cache"
        table = define_table(tablename,
                             Field("title"),
                             Field("description"),
                             Field("link"),      # Used by GeoRSS
                             Field("data"),
                             Field("image"),
                             Field("lat", "double"),
                             Field("lon", "double"),
                             Field("marker"),    # Used by KML
                             Field("source", requires=IS_NULL_OR(IS_URL())),
                             *s3_meta_fields())

        # Store downloaded KML feeds on the filesystem
        # @ToDo: Migrate to DB instead (using above gis_cache)
        tablename = "gis_cache2"
        table = define_table(tablename,
                             Field("name", length=128, notnull=True, unique=True),
                             Field("file", "upload", autodelete = True,
                                   custom_retrieve = self.gis_cache2_retrieve,
                                   # upload folder needs to be visible to the download() function as well as the upload
                                   uploadfolder = os.path.join(request.folder,
                                                               "uploads",
                                                               "gis_cache")),
                             *s3_meta_fields())

        # ---------------------------------------------------------------------
        # Below tables are not yet implemented

        # ---------------------------------------------------------------------
        # GIS Styles: SLD
        #
        # We store XML which can be configured using a GUI client
        #
        # We also store a pointer to the resource on a GeoServer co-app:
        # http://docs.geoserver.org/stable/en/user/restconfig/rest-config-api.html#styles

        #tablename = "gis_style"
        #table = define_table(tablename,
        #                     Field("name", notnull=True, unique=True)
        #                     *s3_meta_fields())
        #db.gis_style.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "gis_style.name")]

        # ---------------------------------------------------------------------
        return Storage(
            )


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
    def gis_layer_georss_deduplicate(item):
        """
          This callback will be called when importing Symbology records it will look
          to see if the record being imported is a duplicate.

          @param item: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update
        """

        if item.tablename == "gis_layer_georss":
            # Match if url is identical
            table = item.table
            data = item.data
            url = data.url
            query = (table.url == url)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_kml_deduplicate(item):
        """
          This callback will be called when importing Symbology records it will look
          to see if the record being imported is a duplicate.

          @param item: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update
        """

        if item.tablename == "gis_layer_kml":
            # Match if url is identical
            table = item.table
            data = item.data
            url = data.url
            query = (table.url == url)
            duplicate = current.db(query).select(table.id,
                                                 limitby=(0, 1)).first()
            if duplicate:
                item.id = duplicate.id
                item.method = item.METHOD.UPDATE
        return

# =============================================================================
class S3GISThemeModel(S3Model):
    """
        Thematic Mapping model
    """

    names = ["gis_layer_theme",
             "gis_theme_data",
             "gis_layer_theme_id",
             ]

    def model(self):

        T = current.T
        db = current.db

        #UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # Shortcuts
        add_component = self.add_component
        configure = self.configure
        define_table = self.define_table
        layer_id = self.super_link("layer_id", "gis_layer_entity")

        # =====================================================================
        # Theme Layer
        #

        gis_theme_type_opts = {
            # This should be stored
            #"population":T("Population"),
            }

        tablename = "gis_layer_theme"
        table = define_table(tablename,
                             layer_id,
                             name_field()(unique = True),
                             Field("description", label=T("Description")),
                             #Field("type", label = T("Type"),
                             #      requires=IS_NULL_OR(IS_IN_SET(gis_theme_type_opts))
                             #      represent = lambda opt: gis_theme_type_opts.get(opt,
                             #                                                      UNKNOWN_OPT),
                             #      ),
                             Field("date", "datetime", label = T("Date")),
                             gis_layer_folder()(),
                             # Avoid clustering
                             cluster_distance()(default = 1),
                             cluster_threshold()(),
                             s3_role_required(),       # Single Role
                             #s3_roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                             *s3_meta_fields())

        configure(tablename,
                  super_entity="gis_layer_entity")

        # Components
        # Configs
        add_component("gis_config",
                      gis_layer_theme=Storage(
                                    link="gis_layer_config",
                                    pkey="layer_id",
                                    joinby="layer_id",
                                    key="config_id",
                                    actuate="hide",
                                    autocomplete="name",
                                    autodelete=False))

        # Theme Data
        add_component("gis_theme_data", gis_layer_theme="layer_theme_id")

        layer_theme_id = S3ReusableField("layer_theme_id", table,
                                         label = "Theme Layer",
                                         requires = IS_ONE_OF(db,
                                                              "gis_layer_theme.id",
                                                              "%(name)s"),
                                         represent = self.theme_represent,
                                         ondelete = "CASCADE")

        # =====================================================================
        # GIS Theme Data
        #
        # @ToDo: Replace this with gis_location_tag?
        #        - layer just selects a tag to filter on?
        #

        tablename = "gis_theme_data"
        table = define_table(tablename,
                             layer_theme_id(),
                             self.gis_location_id(
                                widget=S3LocationAutocompleteWidget(),
                                requires = IS_LOCATION(level=["L1", "L2", "L3", "L4"]),
                                ),
                             Field("value", label = T("Value")),
                             *s3_meta_fields())

        ADD_THEME = T("Add Data to Theme Layer")
        current.response.s3.crud_strings[tablename] = Storage(
            title_create = ADD_THEME,
            title_display = T("Theme Data"),
            title_list = T("Theme Data"),
            title_update = T("Edit Theme Data"),
            title_search = T("Search Theme Data"),
            title_upload = T("Import Data for Theme Layer"),
            subtitle_create = T("Add New Data to Theme Layer"),
            label_list_button = T("List Data in Theme Layer"),
            label_create_button = ADD_THEME,
            label_delete_button = T("Delete Data from Theme layer"),
            msg_record_created = T("Data added to Theme Layer"),
            msg_record_modified = T("Theme Data updated"),
            msg_record_deleted = T("Theme Data deleted"),
            msg_list_empty = T("No Data currently defined for this Theme Layer")
        )

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (s3db.*)
        #
        return Storage(
                    gis_layer_theme_id = layer_theme_id,
                )


    # ---------------------------------------------------------------------
    @staticmethod
    def theme_represent(id):
        """
        """

        if not id:
            return current.messages.NONE
        db = current.db
        table = db.gis_layer_theme
        query = (table.id == id)
        theme = db(query).select(table.name,
                                 limitby=(0, 1)).first()
        try:
            return theme.name
        except:
            return current.messages.UNKNOWN_OPT

# =============================================================================
class S3POIFeedModel(S3Model):
    """ Data Model for POI feeds """

    names = ["gis_poi_feed"]

    def model(self):

        # =====================================================================
        # Table to store last update time for a POI feed
        #
        tablename = "gis_poi_feed"
        table = self.define_table(tablename,
                                  self.gis_location_id(),
                                  Field("tablename"),
                                  Field("last_update", "datetime"),
                                  *s3_meta_fields())

        # ---------------------------------------------------------------------
        return Storage()

# =============================================================================
def name_field():
    T = current.T
    return S3ReusableField("name", length=64, notnull=True,
                           #unique=True,
                           label=T("Name"))

# =============================================================================
def gis_layer_folder():
    T = current.T
    return S3ReusableField("dir", length=32,
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Folder"),
                                                           T("If you enter a foldername then the layer will appear in this folder in the Map's layer switcher."))),
                           label = T("Folder"))

# =============================================================================
def gis_opacity():
    T = current.T
    return S3ReusableField("opacity", "double", default=1.0,
                           requires = IS_FLOAT_IN_RANGE(0, 1),
                           widget = S3SliderWidget(minval=0, maxval=1, steprange=0.01, value=1),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Opacity"),
                                                           T("Left-side is fully transparent (0), right-side is opaque (1.0)."))),
                           label = T("Opacity"))

# =============================================================================
def gis_refresh():
    T = current.T
    return S3ReusableField("refresh", "integer", default=900,        # 15 minutes
                           requires = IS_INT_IN_RANGE(10, 86400),    # 10 seconds - 24 hours
                           label = T("Refresh Rate (seconds)"))

# =============================================================================
def cluster_distance():
    T = current.T
    return S3ReusableField("cluster_distance", "integer", notnull=True,
                           label = T("Cluster Distance"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Cluster Distance"),
                                                           T("The number of pixels apart that features need to be before they are clustered."))),
                           requires = IS_INT_IN_RANGE(1, 30),
                           default = 20)

# =============================================================================
def cluster_threshold():
    T = current.T
    return S3ReusableField("cluster_threshold", "integer", notnull=True,
                           label = T("Cluster Threshold"),
                           comment = DIV(_class="tooltip",
                                         _title="%s|%s" % (T("Cluster Threshold"),
                                                           T("The minimum number of features to form a cluster."))),
                           requires = IS_INT_IN_RANGE(1, 10),
                           default = 2)

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
    return

# =============================================================================
def gis_location_filter(r):
    """
        Filter resources to those for a specified location
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
            filter = (S3FieldSelector(selector) == code)
            resource.add_filter(filter)
        elif resource.name == "project":
            selector = "project.countries_id"
            if row.level != "L0":
                id = current.gis.get_parent_country(row)
            else:
                id = lfilter
            filter = (S3FieldSelector(selector).contains(id))
            resource.add_filter(filter)
        else:
            # Normal case: resource with location_id
            selector = "%s.location_id$%s" % (resource.name, row.level)
            filter = (S3FieldSelector(selector) == row.name)
            resource.add_filter(filter)

# =============================================================================
def gis_location_represent(id, row=None, show_link=True, simpletext=False):
    """ FK representation """

    if row:
        db = current.db
        table = db.gis_location
    elif not id:
        return current.messages.NONE
    else:
        db = current.db
        table = db.gis_location
        row = db(table.id == id).select(table.id,
                                        table.name,
                                        table.level,
                                        table.parent,
                                        table.addr_street,
                                        table.inherited,
                                        table.lat,
                                        table.lon,
                                        limitby=(0, 1)).first()
    if not row:
        return current.messages.UNKNOWN_OPT

    # -------------------------------------------------------------------------
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

        format = current.deployment_settings.get_L10n_lat_lon_format()
        formatted = format.replace("%d", "%d" % degrees) \
                          .replace("%m", "%d" % minutes) \
                          .replace("%s", "%lf" % seconds) \
                          .replace("%f", "%lf" % coord)
        return formatted

    # -------------------------------------------------------------------------
    def lat_lon_represent(row):
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
            text = "%s %s, %s %s" % (lat_lon_format(lat),
                                     lat_suffix,
                                     lat_lon_format(lon),
                                     lon_suffix)
            return text

    # -------------------------------------------------------------------------
    def parent_represent(row):
        parent = db(table.id == row.parent).select(table.name,
                                                   cache=cache,
                                                   limitby=(0, 1)).first()
        if parent:
            return parent.name
        else:
            return ""

    request = current.request
    if (request.raw_args and ".plain" in request.raw_args) or \
       (row.lat == None and row.lon == None or \
        row.parent == None):
        # Map popups don't support iframes (& meaningless anyway), and if there
        # is no lat, lon or parent, there's no way to place this on a map.
        show_link = False

    if show_link and simpletext:
        # We aren't going to use the represent, so skip making it.
        represent_text = current.T("Show on Map")
    elif row.level == "L0":
        represent_text = "%s (%s)" % (row.name, current.messages.COUNTRY)
    else:
        s3db = current.s3db
        cache = s3db.cache
        if row.level in ["L1", "L2", "L3", "L4", "L5"]:
            level_name = None
            # Find the L0 Ancestor to lookup the hierarchy
            gis = current.gis
            L0 = gis.get_parent_country(row)
            if L0:
                htable = s3db.gis_hierarchy
                query = (htable.location_id == L0)
                config = db(query).select(htable.L1,
                                          htable.L2,
                                          htable.L3,
                                          htable.L4,
                                          htable.L5,
                                          cache=cache,
                                          limitby=(0, 1)).first()
                if config:
                    level_name = config[row.level]
            if level_name is None:
                # Fallback to system default
                level_name = gis.get_all_current_levels(row.level)
            parent_info = parent_represent(row)
            if parent_info:
                extra = "(%s), %s" % (level_name, parent_info)
            else:
                extra = level_name
            represent_text = "%s %s" % (row.name, extra)
        else:
            # Specific location:
            # Don't duplicate the Resource Name
            # Street address or lat/lon as base
            represent_text = ""
            if row.addr_street:
                # Get the 1st line of the street address.
                represent_text = row.addr_street.splitlines()[0]
            if (not represent_text) and \
               (row.inherited == False) and \
               (row.lat != None) and \
               (row.lon != None):
                represent_text = lat_lon_represent(row)
            if row.parent:
                if represent_text:
                    parent_repr = parent_represent(row)
                    if parent_repr:
                        represent_text = "%s, %s" % \
                            (represent_text, parent_repr)
                else:
                    represent_text = parent_represent(row)
            if not represent_text:
                represent_text = row.name or row.id

    if show_link:
        # ToDo: Convert to popup? (HTML again!)
        represent = A(represent_text,
                      _style="cursor:pointer;cursor:hand",
                      _onclick="s3_showMap(%i);return false" % row.id)
    else:
        represent = represent_text

    return represent


# =============================================================================
def gis_location_lx_represent(record):
    """
        Represent a location, given either its id or full Row, as a simple string

        @param record: database record
        @return: string
    """

    if not record:
        return current.messages.NONE

    if isinstance(record, Row):
        location = record
    else:
        db = current.db
        s3db = current.s3db
        cache = s3db.cache
        table = s3db.gis_location
        location = db(table.id == record).select(table.id,
                                                 table.name,
                                                 cache=cache,
                                                 limitby=(0, 1)).first()

    parents = Storage()
    parents = current.gis.get_parent_per_level(parents,
                                               location.id,
                                               ids=False,
                                               names=True)

    location_list = []
    if location.name:
        location_list.append(location.name)
    if parents:
        fields = ["L%s" % (i) for i in xrange(0, 5)]
        for field in reversed(fields):
            if field in parents and parents[field]:
                location_list.append(parents[field])

    return ", ".join(location_list)

# =============================================================================
def gis_layer_represent(id, link=True):
    """ Represent a Layer  """

    db = current.db
    s3db = current.s3db
    represent = current.messages.NONE

    ltable = s3db.gis_layer_entity

    if not id:
        return represent

    if isinstance(id, Row) and "instance_type" in id:
        # Do not repeat the lookup if already done by IS_ONE_OF
        layer = id
        id = None
    else:
        layer = db(ltable._id == id).select(ltable.name,
                                            ltable.layer_id,
                                            ltable.instance_type,
                                            limitby=(0, 1)).first()
        if not layer:
            return represent

    instance_type = layer.instance_type
    try:
        table = s3db[instance_type]
    except:
        return represent

    instance_type_nice = ltable.instance_type.represent(instance_type)

    if layer:
        represent = "%s (%s)" % (layer.name, instance_type_nice)
    else:
        # Since name is notnull for all types so far, this won't be reached.
        represent = "[layer %d] (%s)" % (id, instance_type_nice)

    if link and layer:
        query = (table.layer_id == layer.layer_id)
        id = db(query).select(table.id,
                              limitby=(0, 1)).first().id
        c, f = instance_type.split("_", 1)
        represent = A(represent,
                      _href = URL(c=c, f=f,
                                  args = [id],
                                  extension = "" # removes the .aaData extension in paginated views!
                                ))

    return represent

# =============================================================================
def gis_rheader(r, tabs=[]):
    """ GIS page headers """

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
                (T("Import from OpenStreetMap"), "import_poi"),
                (T("Local Names"), "name"),
                (T("Key Value pairs"), "tag"),
                ]
        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(TABLE(
                            TR(
                                TH("%s: " % table.name.label),
                                record.name,
                                ),
                            TR(
                                TH("%s: " % T("Level")),
                                record.level,
                                ),
                        ), rheader_tabs)

    elif resourcename == "config":
        # Tabs
        if not tabs:
            tabs = [(T("Profile Details"), None),
                    (T("Layers"), "layer_entity"),
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
                    context = s3db.pr_pentity_represent(pe_id, show_label=False)

            region_location_id = record.region_location_id
            if region_location_id:
                location_represent = gis_location_represent(region_location_id)
                if context:
                    T("%(pe)s in %(location)s") % \
                        dict(pe=context,
                             location=location_represent)
                else:
                    context = location_represent

        rheader = DIV(TABLE(
                            TR(
                                TH("%s: " % table.name.label),
                                record.name,
                                ),
                            TR(
                                TH("%s: " % T("Context")),
                                context,
                                ),
                        ), rheader_tabs)

    elif resourcename == "symbology":
        # Tabs
        if not tabs:
            tabs = [(T("Symbology Details"), None),
                    (T("Layers"), "layer_entity"),
                    (T("Markers"), "marker"),
                   ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(TABLE(
                            TR(TH("%s: " % table.name.label),
                                record.name),
                            ),
                      rheader_tabs)

    elif resourcename == "marker":
        # Tabs
        if not tabs:
            tabs = [(T("Basic Details"), None),
                    (T("Layers"), "layer_entity"),
                   ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        rheader = DIV(TABLE(
                            TR(TH("%s: " % table.name.label),
                                record.name),
                            ),
                      rheader_tabs)

    elif resourcename == "layer_feature" or \
         resourcename == "layer_georss" or \
         resourcename == "layer_geojson" or \
         resourcename == "layer_kml":
        # Tabs
        if not tabs:
            tabs = [(T("Layer Details"), None),
                    (T("Profiles"), "config"),
                    (T("Markers"), "symbology"),
                   ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        if record.description:
            description = TR(TH("%s: " % table.description.label),
                             record.description)
        else:
            description = ""

        rheader = DIV(TABLE(
                            TR(TH("%s: " % table.name.label),
                               record.name,
                            ),
                            description,
                            ),
                      rheader_tabs)

    elif resourcename == "layer_entity":
        # Tabs
        if not tabs:
            tabs = [(T("Layer Details"), None), # @ToDo: Make this the layer instance not entity
                    (T("Profiles"), "config"),
                    (T("Markers"), "symbology"),
                   ]

        rheader_tabs = s3_rheader_tabs(r, tabs)

        if record.description:
            description = TR(TH("%s: " % table.description.label),
                             record.description)
        else:
            description = ""

        rheader = DIV(TABLE(
                            TR(TH("%s: " % table.name.label),
                               record.name,
                            ),
                            description,
                            ),
                      rheader_tabs)

    elif resourcename == "layer_openstreetmap" or \
         resourcename == "layer_bing" or \
         resourcename == "layer_empty" or \
         resourcename == "layer_google" or \
         resourcename == "layer_openweathermap" or \
         resourcename == "layer_tms" or \
         resourcename == "layer_wms" or \
         resourcename == "layer_wfs" or \
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

        rheader = DIV(TABLE(
                            TR(TH("%s: " % table.name.label),
                               record.name,
                            ),
                            description,
                            ),
                      rheader_tabs)

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

        rheader = DIV(TABLE(
                            TR(TH("%s: " % table.name.label),
                               record.name,
                            ),
                            description,
                            ),
                      rheader_tabs)
    else:
        rheader = None

    return rheader

# END =========================================================================
