# -*- coding: utf-8 -*-

""" Sahana Eden GIS Model

    @author: Fran Boon <fran[at]aidiq.com>

    @copyright: 2009-2011 (c) Sahana Software Foundation
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
           "S3GISConfigModel",
           "S3MapModel",
           "gis_location_represent"
           ]

import os

from gluon import *
from gluon.dal import Row
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3LocationModel(S3Model):
    """ Locations Model """

    names = ["gis_location",
             "gis_location_name",
             "gis_location_id"]

    def model(self):

        T = current.T
        db = current.db
        gis = current.gis
        s3 = current.response.s3
        session = current.session

        messages = current.messages
        UNKNOWN_OPT = messages.UNKNOWN_OPT

        system_roles = session.s3.system_roles
        AUTHENTICATED = system_roles.AUTHENTICATED

        # ---------------------------------------------------------------------
        # Locations
        #
        #  A set of Coordinates &/or Address
        #
        gis_feature_type_opts = {
            1:T("Point"),
            2:T("LineString"),
            3:T("Polygon"),
            #4:T("MultiPolygon") This just counts as Polygon as far as we're concerned
            }
        gis_source_opts = {
            "gps":T("GPS"),
            "imagery":T("Imagery"),
            "geonames":"Geonames",
            "osm":"OpenStreetMap",
            "wikipedia":"Wikipedia",
            "yahoo":"Yahoo! GeoPlanet",
            }

        tablename = "gis_location"
        table = self.define_table(tablename,
                                  Field("name", length=128,
                                        # Placenames don't have to be unique.
                                        # Waypoints don't need to have a name at all.
                                        #requires = IS_NOT_EMPTY()
                                        label = T("Name")),
                                  #Field("name_short"),                           # Secondary name
                                  # @ToDo: Fixme by providing a way to add Names
                                  #Field("name_local", "list:reference gis_location_name",
                                  #      label = T("Local Names"),
                                  #      comment = DIV(_class="tooltip",
                                  #                    _title="%s|%s" % (T("Local Names"),
                                  #                                      T("Names can be added in multiple languages")))),
                                  # L0: ISO2
                                  # Others can be flexible as you need, e.g.
                                  # Christchurch: 'prupi', label=T("Property reference in the council system")
                                  Field("code", label = T("Code")),
                                  # L0: ISO3
                                  # Others can be flexible as you need, e.g.
                                  # Christchurch: 'gisratingid', label=T("Polygon reference of the rating unit")
                                  Field("code2",
                                        #label="ISO3",
                                        #label="P-Code",
                                        # Make these readable if you need them
                                        readable=False,
                                        writable=False),
                                  Field("level", length=2, label = T("Level"),
                                        represent = self.gis_level_represent),
                                  # @ToDo: If level is known, filter on higher than that?
                                  # If strict, filter on next higher level?
                                  Field("parent", "reference gis_location",       # This form of hierarchy may not work on all Databases
                                        label = T("Parent"),
                                        represent = self.gis_location_represent,
                                        widget=S3LocationAutocompleteWidget(level=gis.allowed_hierarchy_level_keys),
                                        ondelete = "RESTRICT"),
                                  Field("path", length=256,
                                        label = T("Path"),
                                        readable=False, writable=False),          # Materialised Path
                                  Field("members", "list:reference gis_location"),
                                  # Street Address (other address fields come from hierarchy)
                                  Field("addr_street", "text", label = T("Street Address")),
                                  Field("addr_postcode", length=128,
                                        label = T("Postcode")),
                                  Field("gis_feature_type", "integer",
                                        default=1, notnull=True,
                                        requires = IS_IN_SET(gis_feature_type_opts,
                                                             zero=None),
                                        represent = lambda opt: gis_feature_type_opts.get(opt,
                                                                                          UNKNOWN_OPT),
                                        label = T("Feature Type")),
                                  Field("lat", "double", label = T("Latitude"),       # Points or Centroid for Polygons
                                        requires = IS_NULL_OR(IS_LAT())),
                                  Field("lon", "double", label = T("Longitude"),      # Points or Centroid for Polygons
                                        requires = IS_NULL_OR(IS_LON())),
                                  Field("wkt", "text",                                # WKT is auto-calculated from lat/lon for Points
                                        requires = IS_LENGTH(2 ** 24),                # Full WKT validation is done in the onvalidation callback - all we do here is allow longer fields than the default (2 ** 16)
                                        represent = gis.abbreviate_wkt,
                                        label = "WKT (%s)" % T("Well-Known Text")),
                                  Field("url", label = "URL",
                                        requires = IS_NULL_OR(IS_URL())),
                                  Field("geonames_id", "integer", unique=True,    # Geonames ID (for cross-correlation. OSM cannot take data from Geonames as 'polluted' with unclear sources, so can't use them as UUIDs)
                                        requires = IS_EMPTY_OR([IS_INT_IN_RANGE(0, 999999999),
                                                                IS_NOT_ONE_OF(db, "%s.geonames_id" % tablename)]),
                                        label = "Geonames ID"),
                                  Field("osm_id", "integer", unique=True,         # OpenStreetMap ID (for cross-correlation. OSM IDs can change over time, so they also have UUID fields they can store our IDs in)
                                        requires = IS_EMPTY_OR([IS_INT_IN_RANGE(0, 999999999999),
                                                                IS_NOT_ONE_OF(db, "%s.osm_id" % tablename)]),
                                        label = "OpenStreetMap ID"),
                                  Field("lat_min", "double", writable=False,
                                        readable=False), # bounding-box
                                  Field("lat_max", "double", writable=False,
                                        readable=False), # bounding-box
                                  Field("lon_min", "double", writable=False,
                                        readable=False), # bounding-box
                                  Field("lon_max", "double", writable=False,
                                        readable=False), # bounding-box
                                  Field("elevation", "double", writable=False,
                                        readable=False),   # m in height above WGS84 ellipsoid (approximately sea-level). not displayed currently
                                  #Field("ce", "integer", writable=False, readable=False), # Circular 'Error' around Lat/Lon (in m). Needed for CoT.
                                  #Field("le", "integer", writable=False, readable=False), # Linear 'Error' for the Elevation (in m). Needed for CoT.
                                  Field("area", "double", writable=False, readable=False), # Area of the Polygon (in km2).
                                  Field("population", "integer", writable=False, readable=False), # Population of the Location
                                  Field("source", length=32,
                                        requires=IS_NULL_OR(IS_IN_SET(gis_source_opts))),
                                  s3.comments(),
                                  format=gis_location_represent,
                                  *s3.meta_fields())

        # Default the owning role to Authenticated. This can be used to allow the site
        # to control whether authenticated users get to create / update locations, or
        # just read them. Having an owner and using ACLs also allows us to take away
        # privileges from generic Authenticated users for particular locations (like
        # hierarchy or region locations) by changing the owner on those locations, e.g.
        # to MapAdmin.
        table.owned_by_role.default = AUTHENTICATED

        # Although the filter_opts here includes all allowed Ln keys, not just the
        # ones that are within the current hierarchy depth limit, this should not
        # let in any illegal parents, as the parent level was validated using the
        # current hierarchy limit.
        table.parent.requires = IS_NULL_OR(IS_ONE_OF(db, "gis_location.id",
                                                     gis_location_represent_row,
                                                     filterby="level",
                                                     filter_opts=gis.allowed_hierarchy_level_keys,
                                                     orderby="gis_location.name"))

        # We want these visible from forms which reference the Location
        table.lat.comment = DIV(_class="tooltip",
                                _id="gis_location_lat_tooltip",
                                _title="%s|%s|%s|%s|%s|%s" % (T("Latitude & Longitude"),
                                                              T("Latitude is North-South (Up-Down)."),
                                                              T("Longitude is West-East (sideways)."),
                                                              T("Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere."),
                                                              T("Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas."),
                                                              T("These need to be added in Decimal Degrees.")))
        table.lon.comment = A(T("Conversion Tool"),
                              _style="cursor:pointer;",
                              _title=T("You can use the Conversion Tool to convert from either GPS coordinates or Degrees/Minutes/Seconds."),
                              _id="gis_location_converter-btn")

        members = table.members
        # Can't be put in-line into table as db.gis_location not yet defined
        members.requires = IS_NULL_OR(IS_ONE_OF(db, "gis_location.id",
                                                gis_location_represent_row,
                                                multiple=True))
        # Location represent strings can be long, so show group members one per line
        # on read-only views.
        members.represent = lambda id: \
            id and s3_represent_multiref(db.gis_location, id,
                                         represent=lambda mbr_row: \
                                             gis_location_represent_row(mbr_row),
                                         separator=BR()) or NONE
        # FYI, this is how one would show plain text rather than links:
        #members.represent = lambda id: \
        #    id and s3_represent_multiref(db.gis_location, id,
        #                                 represent=lambda mbr_row: \
        #                                     gis_location_represent_row(mbr_row, showlink=False),
        #                                 separator=", ") or NONE

        # CRUD Strings
        ADD_LOCATION = messages.ADD_LOCATION
        LIST_LOCATIONS = T("List Locations")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_LOCATION,
            title_display = T("Location Details"),
            title_list = T("Locations"),
            title_update = T("Edit Location"),
            title_search = T("Search Locations"),
            subtitle_create = T("Add New Location"),
            subtitle_list = LIST_LOCATIONS,
            label_list_button = LIST_LOCATIONS,
            label_create_button = ADD_LOCATION,
            label_delete_button = T("Delete Location"),
            msg_record_created = T("Location added"),
            msg_record_modified = T("Location updated"),
            msg_record_deleted = T("Location deleted"),
            msg_list_empty = T("No Locations currently available"))

        # Reusable field to include in other table definitions
        location_id = S3ReusableField("location_id", db.gis_location,
                                      sortby = "name",
                                      label = T("Location"),
                                      represent = gis_location_represent,
                                      widget = S3LocationSelectorWidget(),
                                      requires = IS_NULL_OR(IS_LOCATION_SELECTOR()),
                                      # Alternate simple Autocomplete (e.g. used by pr_person_presence)
                                      #widget = S3LocationAutocompleteWidget(),
                                      ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Locations as component of Locations ('Parent')
        #self.add_component(table, joinby=dict(gis_location="parent"),
        #                   multiple=False)

        # ---------------------------------------------------------------------
        # Local Names
        tablename = "gis_location_name"
        table = self.define_table(tablename,
                                  location_id(),
                                  Field("language", label = T("Language"),
                                        requires = IS_IN_SET(s3.l10n_languages),
                                        represent = lambda opt: \
                                          s3.l10n_languages.get(opt,
                                                                UNKNOWN_OPT)),
                                  Field("name_l10n", label = T("Name")),
                                  *s3.meta_fields())

        # Names as component of Locations
        self.add_component(table, gis_location="location_id")

        self.configure("gis_location",
                       onvalidation=self.gis_location_onvalidation,
                       onaccept=self.gis_location_onaccept,
                       deduplicate=self.gis_location_duplicate,
                       list_fields = ["id",
                                      "name",
                                      "level",
                                      "parent",
                                      "gis_feature_type",
                                      "lat",
                                      "lon"
                                    ])

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                    gis_location_id = location_id
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_location_onaccept(form):
        """
            On Accept for GIS Locations (after DB I/O)
        """

        gis = current.gis

        # Update the Path
        gis.update_location_tree(form.vars.id, form.vars.parent)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_location_onvalidation(form):

        """
            On Validation for GIS Locations (before DB I/O)
        """

        T = current.T
        db = current.db
        s3db = current.s3db
        cache = s3db.cache
        gis = current.gis
        auth = current.auth
        request = current.request
        response = current.response
        session = current.session
        s3 = response.s3

        system_roles = session.s3.system_roles
        MAP_ADMIN = system_roles.MAP_ADMIN

        table = db.gis_location

        # If you need more info from the old location record, add it here.
        # Check if this has already been called and use the existing info.
        def get_location_info():
            if "id" in request:
                query = (table.id == request.id)
                return db(query).select(table.level,
                                        limitby=(0, 1)).first()
            else:
                return None

        record_error = T("Sorry, only users with the MapAdmin role are allowed to edit these locations")
        field_error = T("Please select another level")

        # Shortcuts
        level = "level" in form.vars and form.vars.level
        parent = "parent" in form.vars and form.vars.parent
        lat = "lat" in form.vars and form.vars.lat
        lon = "lon" in form.vars and form.vars.lon
        members = "members" in form.vars and form.vars.members
        id = "id" in request.vars and request.vars.id

        # For a new location, set the level to "GR" if members are present.
        # Existing locations cannot be converted to Groups or vice-versa.
        # Existing Groups cannot have all Members removed.
        # Note: We can't rely on checking form.vars.level to tell
        # if an existing location was a group, because it might not be available
        # in either form.vars or request.vars -- for an interactive form, that
        # field was set to not writable, so it's just plain text in the page.
        # Note also that many of the errors "available" here are not accessible
        # via the interactive form.
        if id:
            # Existing location
            # Is this a location group?
            # Use the breadcrumb set in prep if available to avoid a db read
            # and detect attempt to change level away from group.
            if "location_is_group" in s3:
                location_is_group = s3.location_is_group
            else:
                old_location = get_location_info()
                location_is_group = old_location.level == "GR"
            if location_is_group:
                if not s3.gis.edit_GR:
                    response.error = record_error
                    form.errors["members"] = record_error
                    return
                # Make sure no-one takes away all members.
                if "members" in form.vars and not form.vars.members:
                    error = T("A location group must have at least one member.")
                    response.error = error
                    form.errors["members"] = error
                    return
            else:
                # Don't allow changing non-group to group.
                error = T("Existing location cannot be converted into a group.")
                if members:
                    response.error = error
                    form.errors["members"] = error
                    return
                if level == "GR":
                    response.error = error
                    form.errors["level"] = error
                    return
        else:
            # New location -- if the location has members, and if permitted to
            # make a group, set "group" level. Don't allow also setting a parent.
            if members:
                if s3.gis.edit_GR:
                    if "parent" in form.vars and form.vars.parent:
                        error = T("Location group cannot have a parent.")
                        response.error = error
                        form.errors["parent"] = error
                        return
                    form.vars.level = "GR"
                else:
                    error = T("Sorry, only users with the MapAdmin role are allowed to create location groups.")
                    response.error = error
                    form.errors["members"] = error
                    return

        # 'MapAdmin' has permission to edit hierarchy locations, no matter what
        # 000_config or the ancestor country's gis_config has.
        if not auth.s3_has_role(MAP_ADMIN):
            if level and ((level == "L0") or (gis.is_level_key(level)) and \
               not gis.get_edit_level(level, parent)):
                response.error = record_error
                form.errors["level"] = T("This level is not open for editing.")
                return

        if parent:
            query = (table.id == parent)
            _parent = db(query).select(table.level,
                                       table.gis_feature_type,
                                       table.lat_min,
                                       table.lon_min,
                                       table.lat_max,
                                       table.lon_max,
                                       #table.level,
                                       limitby=(0, 1),
                                       cache=cache).first()

        # Don't allow a group as parent
        # (Check not needed here -- enforced in requires validator.)
        #if _parent and _parent.level == "GR":
        #    form.errors["parent"] = T("Location group cannot be a parent.")
        #    return

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
        if not "gis_feature_type" in form.vars or (form.vars.gis_feature_type == "1"):
            # Skip if no Lat/Lon provided
            if (lat != None) and (lon != None):
                if parent and _parent.gis_feature_type == 3:
                    # Check within Bounds of the Parent
                    # Rough (Bounding Box)
                    min_lat = _parent.lat_min
                    min_lon = _parent.lon_min
                    max_lat = _parent.lat_max
                    max_lon = _parent.lon_max
                    base_error = T("Sorry that location appears to be outside the area of the Parent.")
                    lat_error =  "%s: %s & %s" % (T("Latitude should be between"),
                                                  str(min_lat), str(max_lat))
                    lon_error = "%s: %s & %s" % (T("Longitude should be between"),
                                                 str(min_lon), str(max_lon))
                    if (lat > max_lat) or (lat < min_lat):
                        response.error = base_error
                        form.errors["lat"] = lat_error
                        return
                    elif (lon > max_lon) or (lon < min_lon):
                        response.error = base_error
                        form.errors["lon"] = lon_error
                        return

                    # @ToDo: Precise (GIS function)
                    # (if using PostGIS then don't do a separate BBOX check as this is done within the query)

                else:
                    # Check bounds for the Instance
                    config = gis.get_config()
                    min_lat = config.min_lat
                    min_lon = config.min_lon
                    max_lat = config.max_lat
                    max_lon = config.max_lon
                    base_error = T("Sorry that location appears to be outside the area supported by this deployment.")
                    lat_error =  "%s: %s & %s" % (T("Latitude should be between"),
                                                  str(min_lat), str(max_lat))
                    lon_error = "%s: %s & %s" % (T("Longitude should be between"),
                                                 str(min_lon), str(max_lon))
                    if (lat > max_lat) or (lat < min_lat):
                        response.error = base_error
                        form.errors["lat"] = lat_error
                        return
                    elif (lon > max_lon) or (lon < min_lon):
                        response.error = base_error
                        form.errors["lon"] = lon_error
                        return

        # ToDo: Check for probable duplicates
        # http://eden.sahanafoundation.org/ticket/481
        # name soundex
        # parent
        # radius
        # response.warning = T("This appears to be a duplicate of ") + xxx (with appropriate representation including hyperlink to view full details - launch de-duplication UI?)
        # form.errors["name"] = T("Duplicate?")
        # Set flag to say that this has been confirmed as not a duplicate

        # Add the bounds (& Centroid for Polygons)
        gis.wkt_centroid(form)

        return

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_location_duplicate(job):
        """
          This callback will be called when importing location records it will look
          to see if the record being imported is a duplicate.

          @param job: An S3ImportJob object which includes all the details
                      of the record being imported

          If the record is a duplicate then it will set the job method to update

          Rules for finding a duplicate:
           - If code is present in the import,
                Look for a record with the same code, ignoring case
           - If code2 is present instead,
                Look for a record with the same code2, ignoring case
           - Else, Look for a record with the same name, ignoring case
                and, if level exists in the import, the same level
                and, if parent exists in the import, the same parent
        """

        db = current.db

        # ignore this processing if we have an id
        if job.id:
            return
        if job.tablename == "gis_location":
            table = job.table
            name = "name" in job.data and job.data.name or None
            level = "level" in job.data and job.data.level or None
            parent = "parent" in job.data and job.data.parent or None
            code = "code" in job.data and job.data.code or None
            code2 = "code2" in job.data and job.data.code2 or None

            if not name:
                return

            # @ToDo: check the the lat and lon if they exist?
            #lat = "lat" in job.data and job.data.lat
            #lon = "lon" in job.data and job.data.lon

            if code:
                query = (table.code.lower().like('%%%s%%' % code.lower()))
            elif code2:
                query = (table.code2.lower().like('%%%s%%' % code2.lower()))
            else:
                # Name is primary
                query = (table.name.lower().like('%%%s%%' % name.lower()))
                if parent:
                    query = query & (table.parent == parent)
                if level:
                    query = query & (table.level == level)

            _duplicate = db(query).select(table.id,
                                          table.uuid,
                                          limitby=(0, 1)).first()
            if _duplicate:
                job.id = _duplicate.id
                job.data.id = _duplicate.id
                job.method = job.METHOD.UPDATE

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_level_represent(level):
        if not level:
            return current.messages.NONE
        elif level == "L0":
            T = current.T
            return T("Country")
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
class S3GISConfigModel(S3Model):
    """
        GIS Config Model
        - Site config
        - Personal config
        - @ToDo: OU config (Organisation &/or Team)
    """

    names = ["gis_config",
             "gis_config_id",
             "gis_marker",
             "gis_projection",
             "gis_symbology",
             "gis_feature_class",
             "gis_marker_id",
             "gis_projection_id",
             "gis_config_form_setup"
            ]

    def model(self):

        T = current.T
        db = current.db
        gis = current.gis
        auth = current.auth
        s3 = current.response.s3
        request = current.request
        settings = current.deployment_settings

        location_id = self.gis_location_id

        # =====================================================================
        # GIS Markers (Icons)
        tablename = "gis_marker"
        table = self.define_table(tablename,
                                  Field("name", length=64,
                                        notnull=True, unique=True,
                                        label = T("Name")),
                                  Field("image", "upload", autodelete=True,
                                        label = T("Image"),
                                        # upload folder needs to be visible to the download() function as well as the upload
                                        uploadfolder = os.path.join(request.folder,
                                                                    "static",
                                                                    "img",
                                                                    "markers"),
                                        represent = lambda filename: \
                                           (filename and [DIV(IMG(_src=URL(c="default", f="download",
                                                                           args=filename),
                                                                  _height=40))] or [""])[0]),
                                  Field("height", "integer", writable=False), # In Pixels, for display purposes
                                  Field("width", "integer", writable=False),  # We could get size client-side using Javascript's Image() class, although this is unreliable!
                                  *s3.meta_fields())

        # Reusable field to include in other table definitions
        ADD_MARKER = T("Add Marker")
        marker_id = S3ReusableField("marker_id", db.gis_marker, sortby="name",
                                    requires = IS_NULL_OR(IS_ONE_OF(db, "gis_marker.id", "%(name)s", zero=T("Use default"))),
                                    represent = lambda id: \
                                        (id and [DIV(IMG(_src=URL(c="default", f="download",
                                                                  args=db(db.gis_marker.id == id).select(db.gis_marker.image,limitby=(0, 1)).first().image),
                                                         _height=40))] or [""])[0],
                                    label = T("Marker"),
                                    comment = DIV(A(ADD_MARKER,
                                                    _class="colorbox",
                                                    _href=URL(c="gis", f="marker",
                                                              args="create",
                                                              vars=dict(format="popup")),
                                                    _target="top",
                                                    _title=ADD_MARKER),
                                              DIV(_class="tooltip",
                                                  _title="%s|%s|%s|%s" % (T("Marker"),
                                                                          T("Defines the icon used for display of features on interactive map & KML exports."),
                                                                          T("A Marker assigned to an individual Location is set if there is a need to override the Marker assigned to the Feature Class."),
                                                                          T("If neither are defined, then the Default Marker is used.")))),
                                    ondelete = "RESTRICT")

        # =====================================================================
        # GIS Projections
        tablename = "gis_projection"
        table = self.define_table(tablename,
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
                                  *s3.meta_fields())

        # Reusable field to include in other table definitions
        projection_id = S3ReusableField("projection_id", db.gis_projection,
                                        sortby="name",
                                        requires = IS_NULL_OR(IS_ONE_OF(db, "gis_projection.id", "%(name)s")),
                                        represent = lambda id: (id and [db(db.gis_projection.id == id).select(db.gis_projection.name,
                                                                                                              limitby=(0, 1)).first().name] or [NONE])[0],
                                        label = T("Projection"),
                                        comment = DIV(A(T("Add Projection"),
                                                        _class="colorbox",
                                                        _href=URL(c="gis", f="projection",
                                                                  args="create",
                                                                  vars=dict(format="popup")),
                                                        _target="top",
                                                        _title=T("Add Projection")),
                                                      DIV(_class="tooltip",
                                                          _title="%s|%s|%s|%s" % (T("Projection"),
                                                                                  T("The system supports 2 projections by default:"),
                                                                                  T("Spherical Mercator (900913) is needed to use OpenStreetMap/Google/Bing base layers."),
                                                                                  T("WGS84 (EPSG 4236) is required for many WMS servers.")))),
                                        ondelete = "RESTRICT")

        self.configure(tablename, deletable=False)

        # =====================================================================
        # GIS Symbology
        tablename = "gis_symbology"
        table = self.define_table(tablename,
                                  Field("name", length=32,
                                        notnull=True, unique=True),
                                  *s3.meta_fields())

        # Reusable field to include in other table definitions
        symbology_id = S3ReusableField("symbology_id", db.gis_symbology,
                                       sortby="name",
                                       requires = IS_NULL_OR(IS_ONE_OF(db, "gis_symbology.id", "%(name)s")),
                                       represent = lambda id: (id and [db(db.gis_symbology.id == id).select(db.gis_symbology.name,
                                                                                                            limitby=(0, 1)).first().name] or [NONE])[0],
                                       label = T("Symbology"),
                                       comment = "",
                                       ondelete = "RESTRICT")
        # =====================================================================
        # GIS Config
        #
        # id=1 = Site default settings
        # The defaults in the table are only initial fallback defaults, applied if
        # no value is included in the site config. After the site config exists, its
        # values will be used as defaults.

        # @ToDo: Include a field or fields for selected layers.

        tablename = "gis_config"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"), # pe_id for Personal configs
                                  # This name will be used in the 'Regions' menu.
                                  # This is the region name if this config represents
                                  # a region, the person's name for a personal config
                                  # or a name denoting "site config" for config # 1.
                                  Field("name"),

                                  # Region fields
                                  location_id("region_location_id",
                                              # @ToDo: The restriction to only hierarchy
                                              # levels and groups does not allow one major
                                              # case for regions, namely those represented
                                              # by a boundary or other physical area.
                                              # Physical regions are useful when the
                                              # region of interest does not align with
                                              # any administrative regions. For instance,
                                              # there is the use case described by Gavin,
                                              # where some obstacle (such as a river in
                                              # flood) cuts across an administrative
                                              # region, and we need to know what supplies,
                                              # medical facilities, etc., are actually
                                              # accessible.
                                              widget = S3LocationAutocompleteWidget(),
                                              requires = IS_NULL_OR(IS_LOCATION(level=gis.allowed_region_level_keys))),
                                  Field("show_in_menu", "boolean", default=False),
                                  # Default Location
                                  location_id("default_location_id",
                                              widget = S3LocationAutocompleteWidget(),
                                              requires = IS_NULL_OR(IS_LOCATION())),
                                  Field("map_height", "integer", notnull=True,
                                        requires = [IS_NOT_EMPTY(), IS_INT_IN_RANGE(160, 1024)],
                                        default = 600),
                                  Field("map_width", "integer", notnull=True,
                                        requires = [IS_NOT_EMPTY(), IS_INT_IN_RANGE(320, 1280)],
                                        default = 1000),
                                  Field("zoom", "integer",
                                        default = 7,
                                        requires = IS_INT_IN_RANGE(1, 20)),
                                  Field("lat", "double",
                                        requires = IS_LAT()),
                                  Field("lon", "double",
                                        requires = IS_LON()),
                                  projection_id(empty=False), # default: 900913 from deployment_settings.get_gis_default_projection()
                                  Field("wmsbrowser_url"),
                                  Field("wmsbrowser_name", default="Web Map Service"),
                                  # OpenStreetMap settings:
                                  # Register your app by logging in to www.openstreetmap.org & then selecting 'oauth settings'
                                  Field("osm_oauth_consumer_key"),
                                  Field("osm_oauth_consumer_secret"),
                                  symbology_id(empty=False),  # default: US from deployment_settings.get_gis_default_symbology()
                                  marker_id(empty=False),     # default: marker_red from deployment_settings.get_gis_default_marker()
                                  Field("geocoder", "boolean", default = True),

                                  # Overall Bounding Box for sanity-checking inputs
                                  Field("min_lat", "double", default=-90,
                                        requires = IS_LAT()),
                                  Field("max_lat", "double", default=90,
                                        requires = IS_LAT()),
                                  Field("min_lon", "double", default=-180,
                                        requires = IS_LON()),
                                  Field("max_lon", "double", default=180,
                                        requires = IS_LON()),

                                  # Fine-tune Map configuration
                                  Field("zoom_levels", "integer", notnull=True,
                                        requires = IS_INT_IN_RANGE(1, 30),
                                        default = 22),

                                  # Location hierarchy fields
                                  # @ToDo: These don't seem appropriate to Personal Configs
                                  # Move these somewhere else?
                                  Field("L0", default = "Country",
                                        writable = False),     # L0 should never change except in Translations
                                  Field("L1", default = "State / Province"),
                                  Field("L2", default = ""),   # Default: off
                                  Field("L3", default = "City / Town / Village"),
                                  Field("L4", default = ""),   # Default: off
                                  Field("L5", default = ""),   # Default: off
                                  Field("search_level", length=2, default="L0",
                                        requires=IS_IN_SET(["L0", "L1", "L2", "L3", "L4", "L5"])),
                                  Field("strict_hierarchy", "boolean", default=False),
                                  Field("location_parent_required", "boolean",
                                        default=False),
                                  Field("edit_L1", "boolean", default=True),
                                  Field("edit_L2", "boolean", default=True),
                                  Field("edit_L3", "boolean", default=True),
                                  Field("edit_L4", "boolean", default=True),
                                  Field("edit_L5", "boolean", default=True),

                                  *s3.meta_fields())

        # Reusable field - used by Events & Scenarios
        config_id = S3ReusableField("config_id", db.gis_config,
                                    #readable=False,
                                    represent = self.gis_config_represent,
                                    writable=False,
                                    label = T("Map Configuration"),
                                    ondelete = "RESTRICT")

        ADD_CONFIG = T("Add Map Configuration")
        LIST_CONFIGS = T("List Map Configurations")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_CONFIG,
            title_display = T("Map Configuration"),
            title_list = T("Map Configurations"),
            title_update = T("Edit Map Configuration"),
            title_search = T("Search Map Configurations"),
            subtitle_create = T("Add New Map Configuration"),
            subtitle_list = LIST_CONFIGS,
            label_list_button = LIST_CONFIGS,
            label_create_button = ADD_CONFIG,
            label_delete_button = T("Delete Map Configuration"),
            msg_record_created = T("Map Configuration added"),
            msg_record_modified = T("Map Configuration updated"),
            msg_record_deleted = T("Map Configuration deleted"),
            msg_list_empty = T("No Map Configurations currently defined")
        )

        # Configs as component of Persons (Personalised configurations)
        self.add_component(table,
                           pr_pentity=dict(joinby=self.super_key(db.pr_pentity),
                                           multiple=False))

        self.configure(tablename,
                       onvalidation=self.gis_config_onvalidation,
                       onaccept=self.gis_config_onaccept,
                       # @ToDo: Not currently allowing delete, but with some
                       # restrictions, we could.
                       #delete_onaccept=self.gis_config_ondelete,
                       update_ondelete=self.gis_config_ondelete,
                       list_fields = ["id",
                                      "name",
                                      "region_location_id",
                                      "default_location_id",
                                      "zoom",
                                      "lat",
                                      "lon"
                                    ])
        if settings.get_security_map() and not auth.s3_has_role("MapAdmin"):
            self.configure(tablename,
                           deletable=False)

        # ----------------------------------------------------------------------
        # GIS Feature Classes
        #
        #  These are used in exported feeds for Icons
        #
        tablename = "gis_feature_class"
        table = self.define_table(tablename,
                                  Field("name", length=64,
                                        notnull=True, unique=True,
                                        label = T("Name")),
                                  Field("description", label = T("Description")),
                                  symbology_id(), # Currently a server-side config option, whereas it would be more useful as a URL query option
                                  marker_id(),
                                  Field("gps_marker", label = T("GPS Marker"),
                                        # This is the list of GPS Markers for Garmin devices
                                        requires = IS_NULL_OR(IS_IN_SET(gis.gps_symbols,
                                                                        zero=T("Use default")))),
                                  Field("resource", label = T("Resource")),
                                  # e.g. L1 for Provinces, L2 for Districts, etc
                                  # e.g. office type 5 for Warehouses
                                  Field("filter_field",
                                        label = T("Filter Field")),
                                  Field("filter_value",
                                        label = T("Filter Value"),
                                        comment = DIV(_class="tooltip",
                                                      _title="%s|%s /" % (T("Filter Value"),
                                                                          T("If you want several values, then separate with")))),
                                  *s3.meta_fields())

        # Configured in zz_last.py when all tables are available
        #table.resource.requires = IS_NULL_OR(IS_IN_SET(db.tables))

        #ADD_FEATURE_CLASS = T("Add Feature Class")
        # Reusable field to include in other table definitions
        #feature_class_id = S3ReusableField("feature_class_id", db.gis_feature_class, sortby="name",
        #                                    requires = IS_NULL_OR(IS_ONE_OF(db, "gis_feature_class.id", "%(name)s")),
        #                                    represent = lambda id: (id and [db(db.gis_feature_class.id == id).select(db.gis_feature_class.name,
        #                                                                                                             limitby=(0, 1)).first().name] or [NONE])[0],
        #                                    label = T("Feature Class"),
        #                                    comment = DIV(A(ADD_FEATURE_CLASS,
        #                                                    _class="colorbox",
        #                                                    _href=URL(c="gis", f="feature_class", args="create", vars=dict(format="popup")),
        #                                                    _target="top",
        #                                                    _title=ADD_FEATURE_CLASS),
        #                                              DIV( _class="tooltip",
        #                                                   _title="%s|%s" % (T("Feature Class"),
        #                                                                     T("Defines the marker used for display & the attributes visible in the popup.")))),
        #                                    ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        #
        return Storage(
                gis_config_form_setup = self.gis_config_form_setup,
                gis_config_prep_helper = self.gis_config_prep_helper,
                gis_config_id = config_id,
                gis_marker_id = marker_id,
                gis_projection_id = projection_id,
                )

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_form_setup():
        """ Prepare the gis_config form """

        T = current.T
        db = current.db
        s3db = current.s3db
        gis = current.gis
        settings = current.deployment_settings

        table = s3db.gis_config

        # Defined here since Component (of Persons)
        # @ToDo: Need tooltips for projection, symbology, geocoder, zoom levels,
        # cluster distance, and cluster threshold.
        table.name.label = T("Name")
        table.name.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Name"),
                T("If this configuration represents a region for the Regions menu, give it a name to use in the menu. The name for a personal map configuration will be set to the user's name.")))
        table.region_location_id.label = T("Region Location")
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
        table.map_height.label = T("Map Height")
        table.map_height.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s" % (
                T("Map Height"),
                T("Default Height of the map window."),
                T("In Window layout the map maximises to fill the window, so no need to set a large value here.")))
        table.map_width.label = T("Map Width")
        table.map_width.comment = DIV(
            _class="tooltip",
            _title="%s|%s|%s" % (
                T("Map Width"),
                T("Default Width of the map window."),
                T("In Window layout the map maximises to fill the window, so no need to set a large value here.")))
        table.marker_id.label = T("Default Marker")
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
                T("In order to be able to edit OpenStreetMap data from within %(name_short)s, you need to register for an account on the OpenStreet server.") % dict(name_short=settings.get_system_name_short()),
                T("Go to %(url)s, sign up & then register your application. You can put any URL in & you only need to select the 'modify the map' permission.") % dict(url=A("http://www.openstreetmap.org",
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
        table.L0.label = T("Hierarchy Level 0 Name (i.e. Country)")
        table.L0.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Location Hierarchy Level 0 Name"),
                T("Term for the top-level administrative division (i.e. Country).")))
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
        table.search_level.label = T("Search Level")
        table.search_level.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Search Level"),
                T("The level at which Searches are filtered.")))
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
        table.show_in_menu.label = T("Show in Menu?")
        table.show_in_menu.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Show in Menu?"),
                T("Select to show this configuration in the menu.")))
        table.region_location_id.comment = DIV(
            _class="tooltip",
            _title="%s|%s" % (
                T("Region Location"),
                T("A location that specifies the geographic area for this region. This can be a location from the location hierarchy, or a 'group location', or a location that has a boundary for the area.")))
        edit_Ln_tip_1 = T("Set True to allow editing this level of the location hierarchy by users who are not MapAdmins.")
        edit_Ln_tip_2 = T("This is appropriate if this level is under construction. To prevent accidental modification after this level is complete, this can be set to False.")
        for n in range(1, gis.gis_config_table_max_level_num + 1):
            field = "edit_L%d" % n
            table[field].label = T("Edit Level %d Locations?") % n
            table[field].comment = DIV(
                _class="tooltip",
                _title="%s|%s|%s" % (
                    T("Is editing level L%d locations allowed?" % n),
                    edit_Ln_tip_1,
                    edit_Ln_tip_2))

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_represent(id):
        """ Represent a Configuration """
        T = current.T
        url = URL(c="gis", f="config", args=id)
        return A(T("Open"), _href=url, _class="action-btn")

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_onvalidation(form):
        """
            Check hierarchy and region values. Add name for personal & site configs.

            If strict, hierarchy names must not have gaps. If the config is intended
            for the region menu, it must have a region location and name to show in
            the menu.

            If this a region location is set, protect that location from accidental
            editing (e.g. if it is used as a default location for any resources in
            the region) but making it only editable by a MapAdmin.
        """

        db = current.db
        s3db = current.s3db
        gis = current.gis
        s3 = current.response.s3
        session = current.session

        system_roles = session.s3.system_roles
        MAP_ADMIN = system_roles.MAP_ADMIN

        gis.config_onvalidation(form.vars, form.errors)
        if form.errors:
            return

        try:
            # Infer a name for personal configs.
            if "pe_id" in form.request_vars:
                name = s3.pr_pentity_represent(form.request_vars.pe_id)
                name = "Personal: %s" % name
                form.vars.name = name
        except:
            # AJAX Save of Viewport from Map
            pass

        # If there's a region location, set its owned by role to MapAdmin.
        # That makes Authenticated no longer an owner, so they only get whatever
        # is permitted by uacl (currently that is set to READ).
        if "region_location_id" in form.vars and form.vars.region_location_id:
            table = s3db.gis_location
            query = (table.id == form.vars.region_location_id)
            db(query).update(owned_by_role = MAP_ADMIN)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_onaccept(form):
        """
            If this is a personal config, set it as the current config.
            If this is the cached config, update it.
        """

        db = current.db
        s3db = current.s3db
        gis = current.gis
        auth = current.auth
        session = current.session

        try:
            update = False
            if (form.request_vars.pe_id and form.vars.id):
                table = s3db.pr_person
                query = (table.uuid == auth.user.person_uuid)
                pentity = db(query).select(table.pe_id, limitby=(0, 1)).first()
                if pentity and pentity.pe_id == form.request_vars.pe_id:
                    update = True
            elif session.s3.gis_config_id and form.vars.id == session.s3.gis_config_id:
                update = True
            if update:
                gis.set_config(form.vars.id, force_update_cache=True)
        except:
            # AJAX Save of Viewport from Map
            pass

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_ondelete(form):
        """
            If the selected config was deleted, revert to the site config.
        """

        gis = current.gis
        session = current.session

        if form.record_id and session.s3.gis_config_id and \
           form.record_id == session.s3.gis_config_id:
            gis.set_config(1)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_config_prep_helper(r, id=None):
        """
            Helper for gis_config prep and others where gis_config is a component.

            Hide location hierarchy fields above max allowed. Table definitions may
            include more levels than a particular site wants to allow. Rather than
            changing the definitions, hide the extra levels.  Also hide the edit_Ln
            fields unless this is a region config for an L0 location.

            Defaults are set from the site config.

            @param r: the current S3Request
            @param id: the id of the gis_config record, if update
        """

        db = current.db
        s3db = current.s3db
        gis = current.gis
        s3 = current.response.s3

        table = s3db.gis_config

        if gis.gis_config_table_max_level_num > gis.max_allowed_level_num:
            for n in range(gis.max_allowed_level_num + 1,
                           gis.gis_config_table_max_level_num + 1):
                level = "L%d" % n
                table[level].readable = table[level].writable = False

        row = db(table.id == 1).select(limitby=(0, 1)).first()
        if row:
            exclude = ["id", "name", "region_location_id", "show_in_menu"]
            exclude.extend(s3.all_meta_field_names)
            for fieldname in table.fields:
                if fieldname in row and fieldname not in exclude:
                    table[fieldname].default = row[fieldname]

        # Hide edit_Ln fields if this isn't a country config.
        # @ToDo: There is nothing stopping someone from making extra configs that
        # have country locations as their region location. Need to select here
        # only those configs that belong to the hierarchy. If the L0 configs are
        # created during initial db creation, then we can tell which they are
        # either by recording the max id for an L0 config, or by taking the config
        # with lowest id if there are more than one per country. This same issue
        # applies to any other use of country configs that relies on getting the
        # official set (e.g. looking up hierarchy labels).
        if id:
            _location = s3db.gis_location
            query = (table.id == id) & (table.region_location_id == _location.id)
            location = db(query).select(_location.level, limitby=(0, 1)).first()
            if not location or location.level != "L0":
                for n in range(1, gis.gis_config_table_max_level_num + 1):
                    field = "edit_L%d" % n
                    table[field].readable = table[field].writable = False


# =============================================================================
class S3MapModel(S3Model):
    """ Models for Maps """

    names = ["gis_cache",
             "gis_cache2",
             "gis_feature_query",
             "gis_layer_bing",
             "gis_layer_coordinate",
             "gis_layer_feature",
             "gis_layer_geojson",
             "gis_layer_georss",
             "gis_layer_google",
             "gis_layer_gpx",
             "gis_layer_js",
             "gis_layer_kml",
             "gis_layer_mgrs",
             "gis_layer_openstreetmap",
             "gis_layer_tms",
             "gis_layer_wfs",
             "gis_layer_wms",
             #"gis_layer_xyz",
             #"gis_layer_yahoo",
             #"gis_wmc_layer",
             #"gis_wmc",
             #"gis_style"
            ]

    def model(self):

        T = current.T
        db = current.db
        request = current.request
        s3 = current.response.s3

        #location_id = self.gis_location_id
        marker_id = self.gis_marker_id
        projection_id = self.gis_projection_id

        name_field = s3.name_field
        role_required = s3.role_required
        #roles_permitted = s3.roles_permitted

        gis_layer_folder = self.gis_layer_folder()
        gis_opacity = self.gis_opacity()
        gis_refresh = self.gis_refresh()
        cluster_distance = self.cluster_distance()
        cluster_threshold = self.cluster_threshold()

        # =============================================================================
        # Feature Layers
        # Used to select a set of Features for either Display or Export
        #
        # This needs to be accessible from any resource controller which is used as a
        # feature layer
        #

        # Used by S3REST
        tablename = "gis_layer_feature"
        table = self.define_table(tablename,
                        Field("name", length=64, notnull=True, unique=True,
                              label = T("Name")),
                        Field("enabled", "boolean", default=True,
                              label=T("Available in Viewer?")),
                        Field("visible", "boolean", default=True,
                              label=T("On by default?")),
                        gis_layer_folder(),
                        Field("module",
                              label = T("Module")),
                        Field("resource",
                              label = T("Resource")),
                        # REST Query
                        Field("filter",
                              label = T("Filter"),
                              comment = DIV(_class="stickytip",
                                            _title="%s|%s" % (T("Filter"),
                                                              "%s: <a href='http://eden.sahanafoundation.org/wiki/S3XRC/RESTfulAPI/URLFormat#BasicQueryFormat' target='_blank'>Trac</a>" % T("Uses the REST Query Format defined in")))),
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
                        marker_id(),                # Optional Marker to over-ride the values from the Feature Classes
                        # Disabled until re-implemented:
                        #Field("polygons", "boolean", default=False,
                        #      label=T("Display Polygons?")),
                        gis_opacity(),
                        # @ToDo: Expose the Graphic options
                        gis_refresh(),
                        cluster_distance(),
                        cluster_threshold(),
                        role_required(),       # Single Role
                        #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                        s3.comments(),
                        *s3.meta_fields())

        # In Controller (to ensure all tables visible)
        #table.resource.requires = IS_IN_SET(db.tables)

        # ---------------------------------------------------------------------
        # GPS Feature Queries
        #
        # Store results of Feature Queries in a temporary table to allow
        # BBOX queries, Clustering, Refresh, Client-side Filtering, etc
        tablename = "gis_feature_query"
        table = self.define_table(tablename,
                                  Field("name", length=128, notnull=True),
                                  Field("lat", requires=IS_LAT()),
                                  Field("lon", requires=IS_LON()),
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
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # GPS Waypoints
        #tablename = "gis_waypoint"
        #table = self.define_table(tablename,
        #                          Field("name", length=128, notnull=True,
        #                                label = T("Name")),
        #                          Field("description", length=128,
        #                                label = T("Description")),
        #                          Field("category", length=128,
        #                                label = T("Category")),
        #                          location_id(),
        #                          *s3.meta_fields())

        # ---------------------------------------------------------------------
        # GPS Tracks (stored as 1 record per point)
        #tablename = "gis_trackpoint"
        #table = self.define_table(tablename,
        #                          location_id(),
        #                          #track_id(),        # link to the uploaded file?
        #                          *s3.meta_fields())

        # ---------------------------------------------------------------------
        # GIS Layers
        #
        #  Layers for display on the Map
        #

        # Make available to global scope (for Map Service Catalogue & ???)
        #s3.gis.layer_types = ["shapefile", "scan", "xyz", "yahoo"]
        s3.gis.layer_types = ["bing", "coordinate", "openstreetmap", "geojson", "georss", "google", "gpx", "js", "kml", "mgrs", "tms", "wfs", "wms"]
        gis_layer_wms_img_formats = ["image/jpeg", "image/png", "image/bmp", "image/tiff", "image/gif", "image/svg+xml"]

        # Base
        # Which is the default Base Layer? (for use in widgets which don't want all layers adding)
        # @ToDo: Constrain to a single record
        #table = self.define_table("gis_layer_base",
        #                          Field("tablename", label=T("Layer Type")),
        #                          Field("layer_id", label=T("Layer ID")),
        #                          *s3.meta_fields())

        # Bing
        # @ToDo: Constrain to a single record
        table = self.define_table("gis_layer_bing",
                                  name_field(),
                                  Field("description"),
                                  Field("enabled", "boolean", default=False),
                                  Field("apikey"),
                                  Field("aerial_enabled", "boolean", default=False),
                                  Field("aerial", default="Bing Satellite"),
                                  Field("road_enabled", "boolean", default=False),
                                  Field("road", default="Bing Roads"),
                                  Field("hybrid_enabled", "boolean", default=False),
                                  Field("hybrid", default="Bing Hybrid"),
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        self.configure("gis_layer_bing",
                       onvalidation=self.gis_bing_onvalidation)

        # ---------------------------------------------------------------------
        # Coordinate
        # @ToDo: Constrain to a single record
        table = self.define_table("gis_layer_coordinate",
                                  name_field(),
                                  Field("description", label=T("Description")),
                                  Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                                  Field("visible", "boolean", default=True,
                                        label=T("On by default? (only applicable to Overlays)")),
                                  gis_layer_folder(),
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # GeoJSON
        table = self.define_table("gis_layer_geojson",
                                  name_field(),
                                  Field("description", label=T("Description")),
                                  Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                                  Field("visible", "boolean", default=True,
                                        label=T("On by default? (only applicable to Overlays)")),
                                  gis_layer_folder(),
                                  Field("url", label=T("Location"), requires=IS_NOT_EMPTY()),
                                  projection_id(default=2,
                                                requires = IS_ONE_OF(db, "gis_projection.id",
                                                                     "%(name)s")),
                                  marker_id(),
                                  gis_opacity(),
                                  gis_refresh(),
                                  cluster_distance(),
                                  cluster_threshold(),
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # GeoRSS
        table = self.define_table("gis_layer_georss",
                                  name_field(),
                                  Field("description", label=T("Description")),
                                  Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                                  Field("visible", "boolean", default=True,
                                        label=T("On by default? (only applicable to Overlays)")),
                                  gis_layer_folder(),
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
                                  marker_id(),
                                  gis_opacity(),
                                  gis_refresh(),
                                  cluster_distance(),
                                  cluster_threshold(),
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Google
        # @ToDo: Constrain to a single record
        table = self.define_table("gis_layer_google",
                                  name_field(),
                                  Field("description"),
                                  Field("enabled", "boolean", default=False),
                                  Field("apikey"),
                                  Field("satellite_enabled", "boolean", default=False),
                                  Field("satellite", default="Google Satellite"),
                                  Field("maps_enabled", "boolean", default=False),
                                  Field("maps", default="Google Maps"),
                                  Field("hybrid_enabled", "boolean", default=False),
                                  Field("hybrid", default="Google Hybrid"),
                                  Field("mapmaker_enabled", "boolean", default=False),
                                  Field("mapmaker", default="Google MapMaker"),
                                  Field("mapmakerhybrid_enabled", "boolean", default=False),
                                  Field("mapmakerhybrid", default="Google MapMaker Hybrid"),
                                  Field("earth_enabled", "boolean", default=True),
                                  Field("streetview_enabled", "boolean", default=True),
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        self.configure("gis_layer_google",
                       onvalidation=self.gis_google_onvalidation)

        # ---------------------------------------------------------------------
        # GPX
        table = self.define_table("gis_layer_gpx",
                                  name_field(),
                                  Field("description", label=T("Description")),
                                  Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                                  Field("visible", "boolean", default=True,
                                        label=T("On by default? (only applicable to Overlays)")),
                                  gis_layer_folder(),
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
                                  marker_id(),
                                  gis_opacity(),
                                  cluster_distance(),
                                  cluster_threshold(),
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # KML
        table = self.define_table("gis_layer_kml",
                                  name_field(),
                                  Field("description", label=T("Description")),
                                  Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                                  Field("visible", "boolean", default=True,
                                        label=T("On by default? (only applicable to Overlays)")),
                                  gis_layer_folder(),
                                  Field("url", label=T("Location"),
                                        requires=IS_NOT_EMPTY(),
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Location"),
                                                                      T("The URL to access the service.")))),
                                  Field("title", label=T("Title"), default="name",
                                        comment=T("The attribute within the KML which is used for the title of popups.")),
                                  Field("body", label=T("Body"), default="description",
                                        comment=T("The attribute(s) within the KML which are used for the body of popups. (Use a space between attributes)")),
                                  gis_refresh(),
                                  gis_opacity(),
                                  cluster_distance(),
                                  cluster_threshold(),
                                  marker_id(),
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # JS
        # - raw JavaScript code for advanced users
        # @ToDo: Move to a Plugin (more flexible)
        table = self.define_table("gis_layer_js",
                                  name_field(),
                                  Field("description", label=T("Description")),
                                  Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                                  gis_layer_folder(),
                                  Field("code", "text", label=T("Code"),
                                        default="var myNewLayer = new OpenLayers.Layer.XYZ();\nmap.addLayer(myNewLayer);"),
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # MGRS
        table = self.define_table("gis_layer_mgrs",
                                  name_field(),
                                  Field("description", label=T("Description")),
                                  Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                                  Field("url", label=T("Location"),
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Location"),
                                                                      T("The URL to access the service.")))),
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # OpenStreetMap
        table = self.define_table("gis_layer_openstreetmap",
                                  name_field(),
                                  Field("description", label=T("Description")),
                                  Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                                  Field("visible", "boolean", default=True,
                                        label=T("On by default? (only applicable to Overlays)")),
                                  gis_layer_folder(),
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
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # TMS
        table = self.define_table("gis_layer_tms",
                                  name_field(),
                                  Field("description", label=T("Description")),
                                  Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                                  gis_layer_folder(),
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
                                  projection_id(default=1), # 900913
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # WFS
        table = self.define_table("gis_layer_wfs",
                                  name_field(),
                                  Field("description", label=T("Description")),
                                  Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                                  Field("visible", "boolean", default=True,
                                        label=T("On by default? (only applicable to Overlays)")),
                                  gis_layer_folder(),
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
                                  #gis_refresh(),
                                  gis_opacity(),
                                  cluster_distance(),
                                  cluster_threshold(),
                                  #Field("editable", "boolean", default=False, label=T("Editable?")),
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # WMS
        table = self.define_table("gis_layer_wms",
                                  name_field(),
                                  Field("description", label=T("Description")),
                                  Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
                                  Field("visible", "boolean", default=False,
                                        label=T("On by default? (only applicable to Overlays)")),
                                  gis_layer_folder(),
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
                                  gis_opacity(),
                                  Field("map", length=32, label=T("Map"),
                                        comment=DIV(_class="tooltip",
                                                    _title="%s|%s" % (T("Map"),
                                                                      T("Optional selection of a MapServer map.")))),
                                  Field("layers", label=T("Layers"),
                                        requires=IS_NOT_EMPTY()),
                                  Field("img_format", length=32, label=T("Format"),
                                        requires=IS_NULL_OR(IS_IN_SET(gis_layer_wms_img_formats)),
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
                                  #Field("queryable", "boolean", default=False, label=T("Queryable?")),
                                  #Field("legend_url", label=T("legend URL")),
                                  #Field("legend_format", label=T("Legend Format"), requires = IS_NULL_OR(IS_IN_SET(gis_layer_wms_img_formats))),
                                  role_required(),       # Single Role
                                  #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  *s3.meta_fields())

        #table.url.requires = [IS_URL, IS_NOT_EMPTY()]

        # ---------------------------------------------------------------------
        # XYZ
        #table = self.define_table("gis_layer_xyz",
        #                          name_field(),
        #                          Field("description", label=T("Description")),
        #                          Field("enabled", "boolean", default=True, label=T("Available in Viewer?")),
        #                          gis_layer_folder(),
        #                          Field("url", label=T("Location"), requires=IS_NOT_EMPTY(),
        #                                comment=DIV(_class="tooltip",
        #                                            _title="%s|%s" % (T("Location"),
        #                                                              T("The URL to access the service.")))),
        #                          Field("base", "boolean", default=True,
        #                                label=T("Base Layer?")),
        #                          Field("sphericalMercator", "boolean", default=False,
        #                                label=T("Spherical Mercator?")),
        #                          Field("transitionEffect",
        #                                requires=IS_NULL_OR(IS_IN_SET(["resize"])),
        #                                label=T("Transition Effect")),
        #                          Field("zoom_levels", "integer",
        #                                requires = IS_INT_IN_RANGE(1, 30),
        #                                label=T("Zoom Levels"),
        #                                default=19),
        #                          role_required(),       # Single Role
        #                          #roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
        #                          *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Yahoo
        # @ToDo: Constrain to a single record
        # table = self.define_table("gis_layer_yahoo",
                                  # name_field(),
                                  # Field("description"),
                                  # Field("enabled", "boolean", default=False),
                                  # Field("apikey"),
                                  # Field("satellite_enabled", "boolean", default=False),
                                  # Field("satellite", default="Yahoo Satellite"),
                                  # Field("maps_enabled", "boolean", default=False),
                                  # Field("maps", default="Yahoo Maps"),
                                  # Field("hybrid_enabled", "boolean", default=False),
                                  # Field("hybrid", default="Yahoo Hybrid"),
                                  # role_required(),       # Single Role
                                  ## roles_permitted(),    # Multiple Roles (needs implementing in modules/s3gis.py)
                                  # *s3.meta_fields())

        # self.configure("gis_layer_yahoo",
                        # onvalidation=self.gis_yahoo_onvalidation)

        # ---------------------------------------------------------------------
        # GIS Cache
        # ---------------------------------------------------------------------
        # Store downloaded GeoRSS feeds in the DB
        # - to allow refresh timer, BBOX queries, unified approach to Markers & Popups
        tablename = "gis_cache"
        table = self.define_table(tablename,
                                  Field("title"),
                                  Field("description"),
                                  Field("link"),      # Used by GeoRSS
                                  Field("data"),
                                  Field("image"),
                                  Field("lat"),
                                  Field("lon"),
                                  Field("marker"),    # Used by KML
                                  Field("source", requires=IS_NULL_OR(IS_URL())),
                                  *s3.meta_fields())

        # Store downloaded KML feeds on the filesystem
        # @ToDo: Migrate to DB instead (using above gis_cache)
        tablename = "gis_cache2"
        table = self.define_table(tablename,
                                  Field("name", length=128, notnull=True, unique=True),
                                  Field("file", "upload", autodelete = True,
                                        # upload folder needs to be visible to the download() function as well as the upload
                                        uploadfolder = os.path.join(request.folder,
                                                                    "uploads",
                                                                    "gis_cache")),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # GIS Web Map Contexts
        # (Saved Map definitions used by GeoExplorer)
        # GIS Config's Defaults should just be the version for id=1?

        # @ToDo Unify WMC Layers with the rest of the Layers system
        #tablename = "gis_wmc_layer"
        #table = self.define_table(tablename,
        #                          Field("source"),
        #                          Field("name"),
        #                          Field("title"),
        #                          Field("visibility", "boolean"),
        #                          Field("group_"),
        #                          Field("fixed", "boolean"),
        #                          gis_opacity(),
        #                          Field("type_"),
        #                          # Handle this as a special case for 'None' layer ('ol' source)
        #                          #"args":["None",{"visibility":false}]
        #                          Field("img_format"),
        #                          Field("styles"),
        #                          Field("transparent", "boolean"),
        #                          *s3.meta_fields())
        ## We don't need dropdowns as these aren't currently edited using Web2Py forms
        ## @ToDo Handle Added WMS servers (& KML/GeoRSS once GeoExplorer supports them!)
        ##table.source.requires = IS_IN_SET(["ol", "osm", "google", "local", "sahana"])
        ##table.name.requires = IS_IN_SET(["mapnik", "TERRAIN", "Pakistan:level3", "Pakistan:pak_flood_17Aug"])
        ## @ToDo Use this to split Internal/External Feeds
        ##table.group_.requires = IS_NULL_OR(IS_IN_SET(["background"]))
        ## @ToDo: Can we add KML/GeoRSS/GPX layers using this?
        ##table.type_.requires = IS_NULL_OR(IS_IN_SET(["OpenLayers.Layer"]))
        ##table.format.requires = IS_NULL_OR(IS_IN_SET(["image/png"]))

        # @ToDo add security
        #tablename = "gis_wmc"
        #table = self.define_table(tablename,
        #                          projection_id(),
        #                          Field("lat", "double",          # This is currently 'x' not 'lat'
        #                                label = T("Latitude")),
        #                          Field("lon", "double",          # This is currently 'y' not 'lon'
        #                                label = T("Longitude")),
        #                          Field("zoom", "integer", label = T("Zoom"),
        #                                requires = IS_INT_IN_RANGE(1, 20)),
        #                          Field("layer_id", "list:reference gis_wmc_layer",
        #                                requires=IS_ONE_OF(db, "gis_wmc_layer.id",
        #                                                   "%(title)s",
        #                                                   multiple=True)),
        #                          # Metadata tbc
        #                          *s3.meta_fields())

        ##table.lat.requires = IS_LAT()
        ##table.lon.requires = IS_LON()

        # ---------------------------------------------------------------------
        # Below tables are not yet implemented

        # GIS Styles: SLD
        #tablename = "gis_style"
        #table = self.define_table(tablename,
        #                          Field("name", notnull=True, unique=True)
        #                          *s3.meta_fields())
        #db.gis_style.name.requires = [IS_NOT_EMPTY(), IS_NOT_ONE_OF(db, "gis_style.name")]

        # ---------------------------------------------------------------------
        return Storage(
                gis_opacity = self.gis_opacity,
                gis_refresh = self.gis_refresh,
                gis_cluster_distance = self.cluster_distance,
                gis_cluster_threshold = self.cluster_threshold
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_layer_folder():
        T = current.T
        return S3ReusableField("dir", length=32,
                               comment = DIV(_class="tooltip",
                                             _title="%s|%s" % (T("Folder"),
                                                               T("If you enter a foldername then the layer will appear in this folder in the Map's layer switcher."))),
                               label = T("Folder"))

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_opacity():
        T = current.T
        return S3ReusableField("opacity", "double", default=1.0,
                               requires = IS_FLOAT_IN_RANGE(0, 1),
                               widget = S3SliderWidget(minval=0, maxval=1, steprange=0.01, value=1),
                               comment = DIV(_class="tooltip",
                                             _title="%s|%s" % (T("Opacity"),
                                                               T("Left-side is fully transparent (0), right-side is opaque (1.0)."))),
                               label = T("Opacity"))

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_refresh():
        T = current.T
        return S3ReusableField("refresh", "integer", default=900,        # 15 minutes
                               requires = IS_INT_IN_RANGE(10, 86400),    # 10 seconds - 24 hours
                               label = T("Refresh Rate (seconds)"))

    # -------------------------------------------------------------------------
    @staticmethod
    def cluster_distance():
        T = current.T
        return S3ReusableField("cluster_distance", "integer", notnull=True,
                               label = T("Cluster Distance"),
                               comment = DIV(_class="tooltip",
                                             _title="%s|%s" % (T("Cluster Distance"),
                                                               T("The number of pixels apart that features need to be before they are clustered."))),
                               requires = IS_INT_IN_RANGE(1, 30),
                               default = 5)

    # -------------------------------------------------------------------------
    @staticmethod
    def cluster_threshold():
        T = current.T
        return S3ReusableField("cluster_threshold", "integer", notnull=True,
                               label = T("Cluster Threshold"),
                               comment = DIV(_class="tooltip",
                                             _title="%s|%s" % (T("Cluster Threshold"),
                                                               T("The minimum number of features to form a cluster."))),
                               requires = IS_INT_IN_RANGE(1, 10),
                               default = 2)

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_bing_onvalidation(form):
        """
            Warn the user about issues
        """

        T = current.T
        reponse = current.response

        if not form.vars.apikey:
            response.warning = T("Bing Layers cannot be displayed if there isn't a valid API Key")
        # Enable the overall LayerType if any of the layers are enabled
        if "aerial_enabled" in form.vars or \
           "road_enabled" in form.vars or \
           "hybrid_enabled" in form.vars:
            form.vars.enabled = True
        else:
            # Disable it
            form.vars.enabled = False

    # -------------------------------------------------------------------------
    @staticmethod
    def gis_google_onvalidation(form):
        """
            Warn the user about issues
        """

        T = current.T
        reponse = current.response

        if not form.vars.apikey:
            response.warning = T("Google Layers cannot be displayed if there isn't a valid API Key")
        # Enable the overall LayerType if any of the layers are enabled
        if "satellite_enabled" in form.vars or \
           "maps_enabled" in form.vars or \
           "hybrid_enabled" in form.vars or \
           "mapmaker_enabled" in form.vars or \
           "mapmakerhybrid_enabled" in form.vars or \
           "earth_enabled" in form.vars or \
           "streetview_enabled" in form.vars:
            form.vars.enabled = True
        else:
            # Disable it
            form.vars.enabled = False

    # -------------------------------------------------------------------------
    #@staticmethod
    # def gis_yahoo_onvalidation(form):
        # """
            # Warn the user about issues
        # """

        # T = current.T
        # reponse = current.response

        # if not form.vars.apikey:
            # response.warning = T("Yahoo Layers cannot be displayed if there isn't a valid API Key")
        ## Enable the overall LayerType if any of the layers are enabled
        # if "satellite_enabled" in form.vars or \
           # "maps_enabled" in form.vars or \
           # "hybrid_enabled" in form.vars:
            # form.vars.enabled = True
        # else:
            ## Disable it
            # form.vars.enabled = False

# =============================================================================
def gis_location_represent_row(location, showlink=True, simpletext=False):
    """
        Represent a location given its row.

        This is used as the represent for IS_ONE_OF, and the "format" for
        the gis_location table, which web2py uses to construct
        (e.g.) selection lists for default validators' widgets.
    """

    if not location:
        return current.messages.NONE

    T = current.T
    db = current.db
    s3db = current.s3db
    cache = s3db.cache
    request = current.request
    gis = current.gis

    def lat_lon_represent(location):
        lat = location.lat
        lon = location.lon
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
            text = "%s %s, %s %s" % (lat, lat_suffix, lon, lon_suffix)
            return text

    def parent_represent(location):
        table = s3db.gis_location
        query = (table.id == location.parent)
        parent = db(query).select(table.name,
                                  cache=cache,
                                  limitby=(0, 1)).first()
        if parent:
            return parent.name
        else:
            return ""

    def level_with_parent(location, level_name):
        parent_info = parent_represent(location)
        if parent_info:
            return "%s, %s" % (level_name, parent_info)
        else:
            return level_name

    if request.raw_args == "read.plain" or \
       (location.lat == None and location.lon == None or \
        location.parent == None):
        # Map popups don't support iframes (& meaningless anyway), and if there
        # is no lat, lon or parent, there's no way to place this on a map.
        showlink = False

    if showlink and simpletext:
        # We aren't going to use the represent, so skip making it.
        represent_text = T("Show on Map")
    else:
        # The basic location representation is the name, but extra info is useful.
        if location.level:
            level_name = None
            if location.level == "L0":
                level_name = T("Country")
            else:
                # Find the L0 Ancestor
                L0 = None
                ancestors = gis.get_parents(location.id, location)
                if ancestors:
                    for ancestor in ancestors:
                        if ancestor.level == "L0":
                            L0 = ancestor.id
                if L0:
                    table = s3db.gis_config
                    query = (table.region_location_id == L0)
                    config = db(query).select(table.L1,
                                              table.L2,
                                              table.L3,
                                              table.L4,
                                              table.L5,
                                              cache=cache,
                                              limitby=(0, 1)).first()
                    if config:
                        level_name = config[location.level]
            if level_name is None:
                # Fallback to system default
                level_name = gis.get_all_current_levels(location.level)
            # Countries don't have Parents & shouldn't be represented with Lat/Lon
            # Non-hierarchy levels (e.g. groups) only show the level.
            extra = level_name
            if location.level in ["L1", "L2", "L3"]:
                # Show the Parent location for larger regions
                extra = level_with_parent(location, level_name)
            elif location.level[0] == "L" and int(location.level[1:]) > 0:
                # For small regions, add Lat/Lon
                extra = level_with_parent(location, level_name)
                lat_lon = lat_lon_represent(location)
                if lat_lon:
                    extra = "%s, %s" % (extra, lat_lon)

        else:
            # Specific location:
            # For extra info, try street address, lat/lon, and OSM id...
            extra = ""
            if location.addr_street:
                # Get the 1st line of the street address.
                extra = location.addr_street.splitlines()[0]
            # Note some of these can end up with nothing in extra, hence the tests.
            if (not extra) and (location.lat != None) and (location.lon != None):
                extra = lat_lon_represent(location)
            if (not extra) and location.parent:
                extra = parent_represent(location)
            # If we have no name, but we have an OSM ID then use that
            if (not extra) and location.osm_id:
                extra = ("OSM ID %s" % location.osm_id)
        extra = extra.strip().strip(", ")
        if extra:
            represent_text = "%s (%s)" % (location.name, extra)
        elif location.name:
            represent_text = location.name
        else:
            # fallback if we have nothing else to show
            represent_text = str(location.id)

    if showlink:
        # ToDo: Convert to popup? (HTML again!)
        represent = A(represent_text,
                      _style="cursor:pointer; cursor:hand",
                      _onclick="s3_viewMap(%i);return false" % location.id)
    else:
        represent = represent_text

    return represent

# -------------------------------------------------------------------------
def gis_location_represent(record, showlink=True, simpletext=False):
    """ Represent a location given wither its id or full Row """

    if not record:
        return current.messages.NONE
    if isinstance(record, Row):
        # Do not repeat the lookup if already done by IS_ONE_OF or RHeader
        location = record
    else:
        db = current.db
        s3db = current.s3db
        cache = s3db.cache
        table = s3db.gis_location
        location = db(table.id == record).select(table.id,
                                                 table.name,
                                                 table.level,
                                                 table.parent,
                                                 table.addr_street,
                                                 table.lat,
                                                 table.lon,
                                                 table.osm_id,
                                                 cache=cache,
                                                 limitby=(0, 1)).first()

    return gis_location_represent_row(location, showlink, simpletext)

# END =========================================================================
