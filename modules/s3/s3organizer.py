# -*- coding: utf-8 -*-

""" S3 Organizer (Calendar-based CRUD)

    @copyright: 2018-2019 (c) Sahana Software Foundation
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

__all__ = ("S3Organizer",
           "S3OrganizerWidget",
           )

import datetime
try:
    import dateutil
    import dateutil.tz
except ImportError:
    import sys
    sys.stderr.write("ERROR: python-dateutil module needed for date handling\n")
    raise
import json
import os
import uuid

from gluon import current, DIV, INPUT
from gluon.storage import Storage

from s3datetime import s3_decode_iso_datetime
from s3rest import S3Method
from s3utils import s3_str
from s3validators import JSONERRORS
from s3widgets import S3DateWidget

# =============================================================================
class S3Organizer(S3Method):
    """ Calendar-based CRUD Method """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Page-render entry point for REST interface.

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        output = {}
        if r.http == "GET":
            if r.representation == "json":
                output = self.get_json_data(r, **attr)
            elif r.interactive:
                output = self.organizer(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        elif r.http == "POST":
            if r.representation == "json":
                output = self.update_json(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def organizer(self, r, **attr):
        """
            Render the organizer view (HTML method)

            @param r: the S3Request instance
            @param attr: controller attributes

            @returns: dict of values for the view
        """

        output = {}

        resource = self.resource
        get_config = resource.get_config

        # Parse resource configuration
        config = self.parse_config(resource)
        start = config["start"]
        end = config["end"]

        widget_id = "organizer"

        # Filter Defaults
        hide_filter = self.hide_filter
        filter_widgets = get_config("filter_widgets", None)

        show_filter_form = False
        default_filters = None

        if filter_widgets and not hide_filter:

            # Drop all filter widgets for start/end fields
            # (so they don't clash with the organizer's own filters)
            fw = []
            prefix_selector = self.prefix_selector
            for filter_widget in filter_widgets:
                if not filter_widget:
                    continue
                filter_field = filter_widget.field
                if isinstance(filter_field, basestring):
                    filter_field = prefix_selector(resource, filter_field)
                if start and start.selector == filter_field or \
                   end and end.selector == filter_field:
                    continue
                fw.append(filter_widget)
            filter_widgets = fw

            if filter_widgets:
                show_filter_form = True
                # Apply filter defaults (before rendering the data!)
                from s3filter import S3FilterForm
                default_filters = S3FilterForm.apply_filter_defaults(r, resource)

        # Filter Form
        if show_filter_form:

            get_vars = r.get_vars

            # Where to retrieve filtered data from
            filter_submit_url = attr.get("filter_submit_url")
            if not filter_submit_url:
                get_vars_ = self._remove_filters(get_vars)
                filter_submit_url = r.url(vars=get_vars_)

            # Where to retrieve updated filter options from:
            filter_ajax_url = attr.get("filter_ajax_url")
            if filter_ajax_url is None:
                filter_ajax_url = r.url(method = "filter",
                                        vars = {},
                                        representation = "options",
                                        )

            filter_clear = get_config("filter_clear",
                                      current.deployment_settings.get_ui_filter_clear())
            filter_formstyle = get_config("filter_formstyle", None)
            filter_submit = get_config("filter_submit", True)
            filter_form = S3FilterForm(filter_widgets,
                                       clear = filter_clear,
                                       formstyle = filter_formstyle,
                                       submit = filter_submit,
                                       ajax = True,
                                       url = filter_submit_url,
                                       ajaxurl = filter_ajax_url,
                                       _class = "filter-form",
                                       _id = "%s-filter-form" % widget_id
                                       )
            fresource = current.s3db.resource(resource.tablename) # Use a clean resource
            alias = resource.alias if r.component else None
            output["list_filter_form"] = filter_form.html(fresource,
                                                          get_vars,
                                                          target = widget_id,
                                                          alias = alias
                                                          )
        else:
            # Render as empty string to avoid the exception in the view
            output["list_filter_form"] = ""

        # Page Title
        crud_string = self.crud_string
        if r.representation != "iframe":
            if r.component:
                title = crud_string(r.tablename, "title_display")
            else:
                title = crud_string(self.tablename, "title_list")
            output["title"] = title

        # Configure Resource
        permitted = self._permitted
        resource_config = {"ajaxURL": r.url(representation="json"),
                           "useTime": config.get("use_time"),
                           "baseURL": r.url(method=""),
                           "labelCreate": s3_str(crud_string(self.tablename, "label_create")),
                           "insertable": resource.get_config("insertable", True) and \
                                         permitted("create"),
                           "editable": resource.get_config("editable", True) and \
                                       permitted("update"),
                           "startEditable": start.field and start.field.writable,
                           "durationEditable": end and end.field and end.field.writable,
                           "deletable": resource.get_config("deletable", True) and \
                                        permitted("delete"),
                           # Forced reload on update, e.g. if onaccept changes
                           # other data that are visible in the organizer
                           "reloadOnUpdate": config.get("reload_on_update", False),
                           }

        # Start and End Field
        resource_config["start"] = start.selector if start else None
        resource_config["end"] = end.selector if end else None

        # Description Labels
        labels = []
        for rfield in config["description"]:
            label = rfield.label
            if label is not None:
                label = s3_str(label)
            labels.append((rfield.colname, label))
        resource_config["columns"] = labels

        # Colors
        color = config.get("color")
        if color:
            resource_config["color"] = color.colname
            resource_config["colors"] = config.get("colors")

        # Generate form key
        formkey = uuid.uuid4().get_hex()

        # Store form key in session
        session = current.session
        keyname = "_formkey[%s]" % self.formname(r)
        session[keyname] = session.get(keyname, [])[-9:] + [formkey]

        # Instantiate Organizer Widget
        widget = S3OrganizerWidget([resource_config])
        output["organizer"] = widget.html(widget_id = widget_id,
                                          formkey = formkey,
                                          )

        # View
        current.response.view = self._view(r, "organize.html")

        return output

    # -------------------------------------------------------------------------
    def get_json_data(self, r, **attr):
        """
            Extract the resource data and return them as JSON (Ajax method)

            @param r: the S3Request instance
            @param attr: controller attributes

            TODO correct documentation!
            @returns: JSON string containing an array of items, format:
                      [{"id": the record ID,
                        "title": the record title,
                        "start": start date as ISO8601 string,
                        "end": end date as ISO8601 string (if resource has end dates),
                        "description": array of item values to render a description,
                        TODO:
                        "editable": item date/duration can be changed (true|false),
                        "deletable": item can be deleted (true|false),
                        },
                       ...
                       ]
        """

        db = current.db
        auth = current.auth

        resource = self.resource
        table = resource.table
        id_col = str(resource._id)

        config = self.parse_config(resource)

        # Determine fields to load
        fields = [resource._id.name]

        start_rfield = config["start"]
        fields.append(start_rfield)

        end_rfield = config["end"]
        if end_rfield:
            fields.append(end_rfield)

        represent = config["title"]
        if hasattr(represent, "selector"):
            title_field = represent.colname
            fields.append(represent)
        else:
            title_field = None

        description = config["description"]
        if description:
            fields.extend(description)
            columns = [rfield.colname for rfield in description]
        else:
            columns = None

        color = config["color"]
        if color:
            fields.append(color)

        # Add date filter
        start, end = self.parse_interval(r.get_vars.get("$interval"))
        if start and end:
            from s3query import FS
            start_fs = FS(start_rfield.selector)
            if not end_rfield:
                query = (start_fs >= start) & (start_fs < end)
            else:
                end_fs = FS(end_rfield.selector)
                query = (start_fs < end) & (end_fs >= start) | \
                        (start_fs >= start) & (start_fs < end) & (end_fs == None)
            resource.add_filter(query)
        else:
            r.error(400, "Invalid interval parameter")

        # Extract the records
        data = resource.select(fields,
                               limit = None,
                               raw_data = True,
                               represent = True,
                               )
        rows = data.rows

        # Bulk-represent the records
        record_ids = [row._row[id_col] for row in rows]
        if hasattr(represent, "bulk"):
            representations = represent.bulk(record_ids)
        else:
            representations = None

        # Determine which records can be updated/deleted
        query = table.id.belongs(record_ids)

        q = query & auth.s3_accessible_query("update", table)
        accessible_rows = db(q).select(table._id,
                                       limitby = (0, len(record_ids)),
                                       )
        editable = set(row[id_col] for row in accessible_rows)

        q = query & auth.s3_accessible_query("delete", table)
        accessible_rows = db(q).select(table._id,
                                       limitby = (0, len(record_ids)),
                                       )
        deletable = set(row[id_col] for row in accessible_rows)

        # Encode the items
        items = []
        for row in rows:

            raw = row._row
            record_id = raw[id_col]

            # Get the start date
            if start_rfield:
                start_date = self.isoformat(raw[start_rfield.colname])
            else:
                start_date = None
            if start_date is None:
                # Undated item => skip
                continue

            # Construct item title
            if title_field:
                title = row[title_field]
            elif representations:
                title = representations.get(record_id)
            elif callable(represent):
                title = represent(record_id)
            else:
                # Fallback: record ID
                title = row[id_col]

            # Build the item
            item = {"id": record_id,
                    "t": s3_str(title),
                    "s": start_date,
                    "pe": 1 if record_id in editable else 0,
                    "pd": 1 if record_id in deletable else 0,
                    }

            if end_rfield:
                end_date = self.isoformat(raw[end_rfield.colname])
                item["e"] = end_date

            if columns:
                data = []
                for colname in columns:
                    value = row[colname]
                    if value is not None:
                        value = s3_str(value)
                    data.append(value)
                item["d"] = data

            if color:
                item["c"] = raw[color.colname]

            items.append(item)

        return json.dumps({"c": columns, "r": items})

    # -------------------------------------------------------------------------
    def update_json(self, r, **attr):
        """
            Update or delete calendar items (Ajax method)

            @param r: the S3Request instance
            @param attr: controller attributes
        """

        # Read+parse body JSON
        s = r.body
        s.seek(0)
        try:
            options = json.load(s)
        except JSONERRORS:
            options = None
        if not isinstance(options, dict):
            r.error(400, "Invalid request options")

        # Verify formkey
        keyname = "_formkey[%s]" % self.formname(r)
        formkey = options.get("k")
        if not formkey or formkey not in current.session.get(keyname, []):
            r.error(403, current.ERROR.NOT_PERMITTED)

        resource = self.resource
        tablename = resource.tablename

        # Updates
        items = options.get("u")
        if items and type(items) is list:

            # Error if resource is not editable
            if not resource.get_config("editable", True):
                r.error(403, current.ERROR.NOT_PERMITTED)

            # Parse the organizer-config of the target resource
            config = self.parse_config(resource)
            start = config.get("start")
            if start:
                if not start.field or start.tname != tablename:
                    # Field must be in target resource
                    # TODO support fields in subtables
                    start = None
            end = config.get("end")
            if end:
                if not end.field or end.tname != tablename:
                    # Field must be in target resource
                    # TODO support fields in subtables
                    end = None

            # Resource details
            db = current.db
            table = resource.table
            prefix, name = resource.prefix, resource.name

            # Model methods
            s3db = current.s3db
            onaccept = s3db.onaccept
            update_super = s3db.update_super

            # Auth methods
            auth = current.auth
            audit = current.audit
            permitted = auth.s3_has_permission
            set_realm_entity = auth.set_realm_entity

            # Process the updates
            for item in items:

                # Get the record ID
                record_id = item.get("id")
                if not record_id:
                    continue

                # Check permission to update the record
                if not permitted("update", table, record_id=record_id):
                    r.unauthorised()

                # Collect and validate the update-data
                data = {}
                error = None
                if "s" in item:
                    if not start:
                        error = "Event start not editable"
                    else:
                        try:
                            dt = s3_decode_iso_datetime(item["s"])
                        except ValueError:
                            error = "Invalid start date"
                        if start.field:
                            dt, error = start.field.validate(dt)
                        data[start.fname] = dt
                if not error and "e" in item:
                    if not end:
                        error = "Event end not editable"
                    else:
                        try:
                            dt = s3_decode_iso_datetime(item["e"])
                        except ValueError:
                            error = "Invalid end date"
                        if end.field:
                            dt, error = end.field.validate(dt)
                        data[end.fname] = dt
                if error:
                    r.error(400, error)

                # Update the record, postprocess update
                if data:
                    success = db(table._id == record_id).update(**data)
                    if not success:
                        r.error(400, "Failed to update %s#%s" % (tablename, record_id))
                    else:
                        data[table._id.name] = record_id

                    # Audit update
                    audit("update", prefix, name,
                          record=record_id, representation="json")
                    # Update super entity links
                    update_super(table, data)
                    # Update realm
                    if resource.get_config("update_realm"):
                        set_realm_entity(table, record_id, force_update=True)
                    # Onaccept
                    onaccept(table, data, method="update")

        # Deletions
        items = options.get("d")
        if items and type(items) is list:

            # Error if resource is not deletable
            if not resource.get_config("deletable", True):
                r.error(403, current.ERROR.NOT_PERMITTED)

            # Collect record IDs
            delete_ids = []
            for item in items:
                record_id = item.get("id")
                if not record_id:
                    continue
                delete_ids.append(record_id)

            # Delete the records
            # (includes permission check, audit and ondelete-postprocess)
            if delete_ids:
                dresource = current.s3db.resource(tablename, id=delete_ids)
                deleted = dresource.delete(cascade=True)
                if deleted != len(delete_ids):
                    r.error(400, "Failed to delete %s items" % tablename)

        return current.xml.json_message()

    # -------------------------------------------------------------------------
    @classmethod
    def parse_config(cls, resource):
        """
            Parse the resource configuration and add any fallbacks

            @param resource: the S3Resource

            @returns: the resource organizer configuration, format:
                      {"start": S3ResourceField,
                       "end": S3ResourceField or None,
                       "use_time": whether this resource has timed events,
                       "title": selector or callable to produce item titles,
                       "description": list of selectors for the item description,
                       }
        """

        prefix = lambda selector: cls.prefix_selector(resource, selector)

        table = resource.table
        config = resource.get_config("organize")
        if not config:
            config = {}

        # Identify start field
        introspect = False
        start_rfield = end_rfield = None
        start = config.get("start")
        if not start:
            introspect = True
            for fn in ("date", "start_date"):
                if fn in table.fields:
                    start = fn
                    break
        if start:
            start_rfield = resource.resolve_selector(prefix(start))
        else:
            raise AttributeError("No start date found in %s" % table)

        # Identify end field
        end = config.get("end")
        if not end and introspect:
            for fn in ("end_date", "closed_on"):
                if fn in table.fields:
                    start = fn
                    break
        if end:
            end_rfield = resource.resolve_selector(prefix(end))
            if start_rfield.colname == end_rfield.colname:
                end_rfield = None

        # Should we use a timed calendar to organize?
        use_time = True
        if start_rfield.ftype == "date":
            use_time = False
        elif end_rfield:
            if end_rfield.ftype == "date":
                if introspect:
                    # Ignore end if introspected
                    end_rfield = None
                else:
                    use_time = False

        # Get represent-function to produce an item title
        represent = config.get("title")
        if represent is None:
            for fn in ("subject", "name", "type_id"):
                if fn in table.fields:
                    represent = fn
                    break

        # If represent is a field selector, resolve it
        if type(represent) is str:
            represent = resource.resolve_selector(prefix(represent))

        # Description
        setting = config.get("description")
        description = []
        if isinstance(setting, (tuple, list)):
            for item in setting:
                if type(item) is tuple and len(item) > 1:
                    label, selector = item[:2]
                else:
                    label, selector = None, item
                rfield = resource.resolve_selector(prefix(selector))
                if label is not None:
                    rfield.label = label
                description.append(rfield)

        # Colors
        color = config.get("color")
        if color:
            colors = config.get("colors")
            if callable(colors):
                colors = colors(resource, color)
            color = resource.resolve_selector(prefix(color))
        else:
            colors = None

        return {"start": start_rfield,
                "end": end_rfield,
                "use_time": use_time,
                "title": represent,
                "description": description,
                "color": color,
                "colors": colors,
                }

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_interval(intervalstr):
        """
            Parse an interval string of the format "<ISO8601>--<ISO8601>"
            into a pair of datetimes

            @param intervalstr: the interval string

            @returns: tuple of datetimes (start, end)
        """

        start = end = None

        if intervalstr:
            dates = intervalstr.split("--")
            if len(dates) != 2:
                return start, end

            try:
                start = s3_decode_iso_datetime(dates[0])
            except ValueError:
                pass
            try:
                end = s3_decode_iso_datetime(dates[1])
            except ValueError:
                pass

        return start, end

    # -------------------------------------------------------------------------
    @staticmethod
    def prefix_selector(resource, selector):
        """
            Helper method to prefix an unprefixed field selector

            @param resource: the target resource
            @param selector: the field selector

            @return: the prefixed selector
        """

        alias = resource.alias if resource.parent else None
        items = selector.split("$", 0)
        head = items[0]
        if "." in head:
            if alias not in (None, "~"):
                prefix, key = head.split(".", 1)
                if prefix == "~":
                    prefix = alias
                elif prefix != alias:
                    prefix = "%s.%s" % (alias, prefix)
                items[0] = "%s.%s" % (prefix, key)
                selector = "$".join(items)
        else:
            if alias is None:
                alias = "~"
            selector = "%s.%s" % (alias, selector)
        return selector

    # -------------------------------------------------------------------------
    @staticmethod
    def formname(r):

        if r.component:
            prefix = "%s/%s/%s" % (r.tablename, r.id, r.component.alias)
        else:
            prefix = r.tablename

        return "%s/organizer" % prefix

    # -------------------------------------------------------------------------
    @staticmethod
    def isoformat(dt):
        """
            Format a date/datetime as ISO8601 datetime string

            @param dt: the date/datetime instance

            @returns: the ISO-formatted datetime string,
                      or None if dt was None
        """

        if dt is None:
            formatted = None
        else:
            if isinstance(dt, datetime.datetime) and dt.tzinfo is None:
                dt = dt.replace(tzinfo = dateutil.tz.tzutc())
            formatted = dt.isoformat()
        return formatted

# =============================================================================
class S3OrganizerWidget(object):
    """ Helper to configure and render the organizer UI widget """

    def __init__(self, resources):
        """
            Constructor

            @param resources: a list of resource specs, format:
                              [{"ajax_url": URL to retrieve events
                                "start": start date field (selector)
                                "end": end date field (selector)
                                },
                                ...
                               ]
        """

        self.resources = resources

    # -------------------------------------------------------------------------
    def html(self, widget_id=None, formkey=None):
        """
            Render the organizer container and instantiate the UI widget

            @param widget_id: the container's DOM ID
        """

        T = current.T

        if not widget_id:
            widget_id = "organizer"

        # Parse resource configuration
        resources = self.resources
        if not isinstance(resources, (list, tuple)):
            resources = [resources]
        resource_configs = []
        use_time = False
        for resource_config in resources:
            resource_use_time = resource_config.get("useTime")
            if resource_use_time:
                use_time = True
            resource_configs.append(resource_config)

        # Inject script and widget instantiation
        script_opts = {"resources": resource_configs,
                       "useTime": use_time,
                       "labelEdit": s3_str(T("Edit")),
                       "labelDelete": s3_str(T("Delete")),
                       "deleteConfirmation": s3_str(T("Do you want to delete this entry?")),
                       }
        self.inject_script(widget_id, script_opts)

        # Add a datepicker to navigate to arbitrary dates
        picker = S3DateWidget()(Storage(name="date_select"),
                                None,
                                _type="hidden",
                                _id="%s-date-picker" % widget_id,
                                )

        # Generate and return the HTML for the widget container
        return DIV(INPUT(_name = "_formkey",
                         _type = "hidden",
                         _value = str(formkey) if formkey else "",
                         ),
                   picker,
                   _id = widget_id,
                   _class = "s3-organizer",
                   )

    # -------------------------------------------------------------------------
    def inject_script(self, widget_id, options):
        """
            Inject the necessary JavaScript

            @param widget_id: the container's DOM ID
            @param options: widget options (JSON-serializable dict)
        """

        s3 = current.response.s3
        scripts = s3.scripts

        request = current.request
        appname = request.application

        # Inject CSS
        # TODO move into themes?
        if s3.debug:
            s3.stylesheets.append("fullcalendar/fullcalendar.css")
            s3.stylesheets.append("qtip/jquery.qtip.css")
        else:
            s3.stylesheets.append("fullcalendar/fullcalendar.min.css")
            s3.stylesheets.append("qtip/jquery.qtip.min.css")

        # Select scripts
        if s3.debug:
            inject = ["moment.js",
                      "fullcalendar/fullcalendar.js",
                      "jquery.qtip.js",
                      "S3/s3.ui.organizer.js",
                      ]
        else:
            inject = ["moment.min.js",
                      "fullcalendar/fullcalendar.min.js",
                      "jquery.qtip.min.js",
                      "S3/s3.ui.organizer.min.js",
                      ]

        # Choose locale
        language = current.session.s3.language
        l10n_path = os.path.join(request.folder,
                                 "static", "scripts", "fullcalendar", "locale",
                                 )
        l10n_file = "%s.js" % language
        script = "fullcalendar/locale/%s" % l10n_file
        if script not in scripts and \
           os.path.exists(os.path.join(l10n_path, l10n_file)):
            options["locale"] = language
            inject.insert(-1, "fullcalendar/locale/%s" % l10n_file)

        # Inject scripts
        for path in inject:
            script = "/%s/static/scripts/%s" % (appname, path)
            if script not in scripts:
                scripts.append(script)

        # Script to attach the timeplot widget
        script = """$("#%(widget_id)s").organizer(%(options)s)""" % \
                    {"widget_id": widget_id,
                     "options": json.dumps(options),
                     }
        s3.jquery_ready.append(script)

# END =========================================================================
