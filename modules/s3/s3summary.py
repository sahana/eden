# -*- coding: utf-8 -*-

""" Resource Summary Pages

    @copyright: 2013-2016 (c) Sahana Software Foundation
    @license: MIT

    @requires: U{B{I{gluon}} <http://web2py.com>}

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

from gluon import current, A, DIV, LI, UL

from s3filter import S3FilterForm
from s3gis import MAP
from s3rest import S3Method

# =============================================================================
class S3Summary(S3Method):
    """ Resource Summary Pages """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST interface

            @param r: the S3Request
            @param attr: controller attributes
        """

        if "w" in r.get_vars:
            # Ajax-request for a specific widget
            return self.ajax(r, **attr)
        else:
            # Full page request
            return self.summary(r, **attr)

    # -------------------------------------------------------------------------
    def summary(self, r, **attr):
        """
            Render the summary page

            @param r: the S3Request
            @param attr: controller attributes
        """

        output = {}
        response = current.response
        resource = self.resource
        get_config = resource.get_config

        # Get Summary Page Configuration
        config = self._get_config(resource)

        # Page title
        crud_string = self.crud_string
        title = crud_string(self.tablename, "title_list")
        output["title"] = title

        # Tabs
        tablist = UL()
        sections = []
        commons = []

        # Active tab
        if "t" in r.get_vars:
            active_tab = int(r.get_vars["t"])
        else:
            active_tab = 0
        active_map = None

        show_filter_form = False
        filter_widgets = get_config("filter_widgets")
        if filter_widgets and not self.hide_filter:
            # Apply filter defaults (before rendering the data!)
            show_filter_form = True
            S3FilterForm.apply_filter_defaults(r, resource)

        # Render sections
        tab_idx = 0
        widget_idx = 0
        targets = []
        pending = []

        # Dynamic filtering (e.g. plot-click in report widget)
        attr["filter_form"] = form_id = "summary-filter-form"

        for section in config:

            common = section.get("common")

            # Section container
            section_id = section["name"]
            s = DIV(_class="section-container", _id=section_id)

            if not common:
                # Label
                label = section["label"]
                translate = section.get("translate", True)
                if isinstance(label, basestring) and translate:
                    label = current.T(label)

                # Add tab
                tablist.append(LI(A(label, _href="#%s" % section_id)))

            if common or active_tab == tab_idx:
                visible = True
            else:
                visible = False

            # Widgets
            widgets = section.get("widgets", [])
            for widget in widgets:

                # Widget ID
                widget_id = "summary-%s" % widget_idx

                # Make sure widgets include the widget ID when
                # generating Ajax URLs:
                r.get_vars["w"] = r.vars["w"] = widget_id

                # Append to filter targets
                filterable = widget.get("filterable", True)
                if filterable:
                    targets.append(widget_id)
                    if not visible and widget.get("ajax_init"):
                        pending.append(widget_id)

                # Apply method
                method = widget.get("method")
                if callable(method):
                    content = method(r,
                                     widget_id=widget_id,
                                     visible=visible,
                                     **attr)
                else:
                    handler = r.get_widget_handler(method)
                    if handler is None:
                        # Fall back to CRUD
                        handler = resource.crud
                    if handler is not None:
                        if method == "datatable":
                            # Assume that we have a FilterForm, so disable Quick Search
                            dtargs = attr.get("dtargs", {})
                            dtargs["dt_searching"] = "false"
                            attr["dtargs"] = dtargs
                        content = handler(r,
                                          method=method,
                                          widget_id=widget_id,
                                          visible=visible,
                                          **attr)
                    else:
                        r.error(405, current.ERROR.BAD_METHOD)

                # Add content to section
                if isinstance(content, dict):
                    if r.http == "POST" and content.get("success"):
                        # Form successfully processed: behave like the
                        # primary method handler and redirect to next
                        next_url = content.get("next")
                        if next_url:
                            self.next = next_url
                            return content
                    for k, v in content.items():
                        if k not in ("tabs", "sections", "widget"):
                            output[k] = v
                    content = content.get("widget", "EMPTY")
                elif active_tab == tab_idx and isinstance(content, MAP):
                    active_map = content
                s.append(DIV(content,
                             _id="%s-container" % widget_id,
                             _class="widget-container"))
                widget_idx += 1

            if common:
                commons.append(s)
            else:
                sections.append(s)
                tab_idx += 1

        # Remove widget ID
        r.get_vars.pop("w", None)

        # Add tabs + sections to output
        if len(sections) > 1:
            output["tabs"] = tablist
            # Hide tabbed sections initially to avoid visible artifacts
            # in slow page loads (S3.search.summary_tabs will un-hide the active one):
            for s in sections:
                s.add_class("hide")
        else:
            # Hide tabs if there's only one section (but then don't hide
            # the section!)
            output["tabs"] = ""
        output["sections"] = sections

        # Add common sections to output
        output["common"] = commons

        # Filter targets
        target = " ".join(targets)

        # Filter form
        filter_ajax = True
        if show_filter_form:

            # Where to retrieve filtered data from:
            if active_tab != 0:
                submit_url_vars = {"t": active_tab}
            else:
                submit_url_vars = {}
            filter_submit_url = attr.get("filter_submit_url")
            if not filter_submit_url:
                _vars = self._remove_filters(r.get_vars)
                _vars.update(submit_url_vars)
                filter_submit_url = r.url(vars=_vars)

            # Where to retrieve updated filter options from:
            filter_ajax_url = attr.get("filter_ajax_url",
                                       r.url(method="filter",
                                             vars={},
                                             representation="options"))

            filter_clear = get_config("filter_clear",
                                      current.deployment_settings.get_ui_filter_clear())
            filter_formstyle = get_config("filter_formstyle")
            filter_submit = get_config("filter_submit", True)
            filter_form = S3FilterForm(filter_widgets,
                                       clear=filter_clear,
                                       formstyle=filter_formstyle,
                                       submit=filter_submit,
                                       ajax=filter_ajax,
                                       url=filter_submit_url,
                                       ajaxurl=filter_ajax_url,
                                       _class="filter-form",
                                       _id=form_id)
            fresource = current.s3db.resource(resource.tablename)

            alias = resource.alias if r.component else None
            output["filter_form"] = filter_form.html(fresource,
                                                     r.get_vars,
                                                     target=target,
                                                     alias=alias)
        else:
            # Render as empty string to avoid the exception in the view
            output["filter_form"] = ""

        # View
        response.view = self._view(r, "summary.html")

        if len(sections) > 1:
            # Provide a comma-separated list of initially hidden widgets
            # which are rendered empty and need a trigger to Ajax-load
            # their data layer (e.g. maps, reports):
            pending = ",".join(pending) if pending else "null"

            # Render the Sections as Tabs
            script = '''S3.search.summary_tabs("%s",%s,"%s")''' % \
                     (form_id, active_tab, pending)
            response.s3.jquery_ready.append(script)

        if active_map:
            # If there is a map on the active tab then we need to add
            # a callback to the Map JS Loader
            active_map.callback = '''S3.search.summary_maps("%s")''' % form_id

        return output

    # -------------------------------------------------------------------------
    def ajax(self, r, **attr):
        """
            Render a specific widget for pulling-in via AJAX

            @param r: the S3Request
            @param attr: controller attributes
        """

        # Get Summary Page Configuration
        config = self._get_config(self.resource)

        widget_id = r.get_vars.get("w")
        i = 0
        for section in config:
            widgets = section.get("widgets", [])
            for widget in widgets:
                if widget_id == "summary-%s" % i:
                    method = widget.get("method", None)
                    output = None
                    if callable(method):
                        output = method(r, widget_id=widget_id, **attr)
                    else:
                        handler = r.get_widget_handler(method)
                        if handler is not None:
                            output = handler(r,
                                             method=method,
                                             widget_id=widget_id,
                                             **attr)
                        else:
                            r.error(405, current.ERROR.BAD_METHOD)
                    return output
                i += 1

        # Not found?
        return None

    # -------------------------------------------------------------------------
    @staticmethod
    def _get_config(resource):
        """
            Get the summary page configuration

            @param resource: the target S3Resource
        """

        get_config = resource.get_config
        config = get_config("summary",
                            current.deployment_settings.get_ui_summary())
        if not config:
            config = [{"name": "table",
                       "label": "Table",
                       "widgets": [{"name": "datatable",
                                    "method": "datatable",
                                    }]
                       }]
        return config

# END =========================================================================
