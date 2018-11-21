# -*- coding: utf-8 -*-

""" S3 Organizer (Calendar-based CRUD)

    @copyright: 2018 (c) Sahana Software Foundation
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

from gluon import current, DIV

from s3rest import S3Method
from s3utils import s3_str

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
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def get_json_data(self, r, **attr):
        """
            Extract the resource data and return them as JSON (Ajax method)

            @param r: the S3Request instance
            @param attr: controller attributes

            @returns: JSON string containing an array of items, format:
                      [{"id": the record ID,
                        "title": the record title,
                        "start": start date as ISO8601 string,
                        "end": end date as ISO8601 string (if resource has end dates),
                        TODO:
                        "editable": item date/duration can be changed (true|false),
                        "deletable": item can be deleted (true|false),
                        "description": dict of item values to render a description,
                        },
                       ...
                       ]
        """

        resource = self.resource
        id_col = str(resource._id)

        config = self.parse_config(resource)

        # Determine fields to load
        fields = [resource._id.name]

        start_rfield = config["start"]
        fields.append(start_rfield.selector)

        end_rfield = config["end"]
        if end_rfield:
            fields.append(end_rfield.selector)

        represent = config["represent"]
        if hasattr(represent, "selector"):
            title_field = represent.colname
            fields.append(represent.selector)
        else:
            title_field = None

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

        # TODO
        # Determine which records can be updated (permission)
        # Determine which records can be deleted (permission)

        # Get the column names
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
                    "title": s3_str(title),
                    "start": start_date,
                    #"editable": True,   # TODO
                    #"deletable": True,  # TODO
                    }

            if end_rfield:
                end_date = self.isoformat(raw[end_rfield.colname])
                item["end"] = end_date

            # TODO implement description
            #       - have a "description" config option
            #       - should be a list of field selectors
            #       - add the description selectors to the resource.select
            #       - extract the represented data here and add as dict
            #item["description"] = ""

            items.append(item)

        return json.dumps(items)

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

        widget_id = "organizer"

        # Filter Defaults
        hide_filter = self.hide_filter
        filter_widgets = get_config("filter_widgets", None)

        show_filter_form = False
        if filter_widgets and not hide_filter:
            show_filter_form = True
            # Apply filter defaults (before rendering the data!)
            from s3filter import S3FilterForm
            default_filters = S3FilterForm.apply_filter_defaults(r, resource)
        else:
            default_filters = None

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

        # Configure resources for organizer
        config = self.parse_config(resource)

        # TODO allow adding other resources
        resource_config = {"ajax_url": r.url(representation="json"),
                           }
        start_rfield = config.get("start")
        if start_rfield:
            resource_config["start"] = start_rfield.selector
        end_rfield = config.get("end")
        if end_rfield:
            resource_config["end"] = end_rfield.selector

        resource_configs = [resource_config,
                            ]

        # Instantiate Organizer Widget
        widget = S3OrganizerWidget(resource_configs)
        output["organizer"] = widget.html(widget_id=widget_id)

        # View
        current.response.view = self._view(r, "organize.html")

        return output

    # -------------------------------------------------------------------------
    @classmethod
    def parse_config(cls, resource):
        """
            Parse the resource configuration and add any fallbacks

            @param resource: the S3Resource

            @returns: the resource organizer configuration, format:
                      {"start": S3ResourceField,
                       "end": S3ResourceField or None,
                       "represent": callable to produce item titles,
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

        # If represent is a field selector, resolve it
        represent = config.get("represent")
        if type(represent) is str:
            represent = resource.resolve_selector(prefix(represent))

        return {"start": start_rfield,
                "end": end_rfield,
                "use_time": use_time,
                "represent": represent,
                }

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
    def html(self, widget_id=None):
        """
            Render the organizer container and instantiate the UI widget

            @param widget_id: the container's DOM ID
        """

        if not widget_id:
            widget_id = "organizer"

        # Parse resource configuration
        resources = self.resources
        if not isinstance(resources, (list, tuple)):
            resources = [resources]
        resource_configs = []
        use_time = False
        for resource_config in resources:
            resource_use_time = resource_config.get("use_time")
            if resource_use_time:
                use_time = True
            resource_configs.append({
                "ajaxURL": resource_config.get("ajax_url"),
                "start": resource_config.get("start"),
                "end": resource_config.get("end"),
                "useTime": resource_use_time,
                })

        # Inject script and widget instantiation
        script_opts = {"resources": resource_configs,
                       "useTime": use_time,
                       }
        self.inject_script(widget_id, script_opts)

        # Generate and return the HTML for the widget container
        return DIV(_id = widget_id,
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
        else:
            s3.stylesheets.append("fullcalendar/fullcalendar.min.css")

        # Select scripts
        if s3.debug:
            inject = ["moment.js",
                      "fullcalendar/fullcalendar.js",
                      "S3/s3.ui.organizer.js",
                      ]
        else:
            inject = ["moment.min.js",
                      "fullcalendar/fullcalendar.min.js",
                      "S3/s3.ui.organizer.min.js",
                      ]

        # Choose locale
        language = current.session.s3.language
        i18n_path = os.path.join(request.folder,
                                 "static", "scripts", "fullcalendar", "locale",
                                 )
        i18n_file = "%s.js" % language
        script = "fullcalendar/locale/%s" % i18n_file
        if script not in scripts and \
           os.path.exists(os.path.join(i18n_path, i18n_file)):
            options["locale"] = language
            inject.insert(-1, "fullcalendar/locale/%s" % i18n_file)

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
