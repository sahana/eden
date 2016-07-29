# -*- coding: utf-8 -*-

""" Dashboards

    @copyright: 2016 (c) Sahana Software Foundation
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

    @status: experimental, work in progress
"""

__all__ = ("S3Dashboard",
           "S3DashboardConfig",
           "S3DashboardWidget",
           )

import json

from gluon import *

from s3utils import s3_get_extension
from s3widgets import ICON

DEFAULT = lambda: None
DEFAULT_FORMAT = "html"

# =============================================================================
class S3DashboardContext(object):
    """ Context data for a dashboard """

    def __init__(self, r=None):
        """
            Constructor

            @param r: the request object (defaults to current.request)

        """

        # @todo: add request owner info (to select the active config)
        # @todo: extract the URL method (like default/dashboard/[method])

        # Context variables
        self.shared = {}

        # Global filters
        # @todo: implement
        self.filters = {}

        # Parse request info
        self._parse()

    # -------------------------------------------------------------------------
    def error(self, status, message, _next=None):
        """
            Action upon error

            @param status: HTTP status code
            @param message: the error message
            @param _next: destination URL for redirection upon error
                          (defaults to the index page of the module)
        """

        if self.representation == "html":

            current.session.error = message

            if _next is None:
                _next = URL(f="index")
            redirect(_next)

        else:

            current.log.error(message)

            headers = {"Content-Type":"application/json"}
            body = current.xml.json_message(success=False,
                                            statuscode=status,
                                            message=message,
                                            )

            raise HTTP(status, body=body, web2py_error=message, **headers)

    # -------------------------------------------------------------------------
    # Getters and setters for shared context variables
    #
    # Widgets and callbacks can share data in the context, e.g. when they
    # use common object instances, or need to coordinate identifiers, like:
    #
    #   - set the value for a variable:
    #       >>> context["key"] = value
    #
    #   - get the value of a variable:
    #       >>> value = context["key"]
    #       >>> value = context.get("key", "some_default_value")
    #
    #   - check for a variable:
    #       >>> if key in context:
    #
    #   - remove a variable:
    #       >>> del context["key"]
    #
    def get(self, key, default=None):

        return self.shared.get(key, default)

    def __getitem__(self, key):

        return self.shared[key]

    def __setitem__(self, key, value):

        self.shared[key] = value

    def __delitem__(self, key):

        del self.shared[key]

    def __contains__(self, key):

        return key in self.shared

    # -------------------------------------------------------------------------
    def __getattr__(self, key):
        """
            Called upon context.<key> - looks up the value for the <key>
            attribute. Falls back to current.request if the attribute is
            not defined in this context.

            @param key: the key to lookup
        """

        if key in self.__dict__:
            return self.__dict__[key]

        sentinel = object()
        value = getattr(current.request, key, sentinel)
        if value is sentinel:
            raise AttributeError
        return value

    # -------------------------------------------------------------------------
    def _parse(self, r=None):
        """
            Parse the request info

            @param r: the web2py Request, falls back to current.request
        """

        request = current.request if r is None else r

        args = request.args
        get_vars = request.get_vars

        command = None
        if len(args) > 0:
            command = args[0]
            if "." in command:
                command = command.split(".", 1)[0]
        if command:
            self.command = command

        # Dashboard controller can explicitly mark requests as bulk
        # even with a single agent ID (e.g. if the dashboard happens
        # to only have one widget) - either by appending a comma to
        # the agent ID, or by specifying ?bulk=1
        bulk = get_vars.get("bulk")
        bulk = True if bulk and bulk.lower() in ("1", "true") else False

        agent_id = request.get_vars.get("agent")
        if agent_id:
            if type(agent_id) is list:
                agent_id = ",".join(agent_id)
            if "," in agent_id:
                bulk = True
                agent_id = set([s.strip() for s in agent_id.split(",")])
                agent_id.discard("")
                agent_id = list(agent_id)
            elif bulk:
                agent_id = [agent_id]
            self.agent = agent_id

        self.bulk = bulk

        self.http = current.request.env.request_method or "GET"
        self.representation = s3_get_extension(request) or DEFAULT_FORMAT

# =============================================================================
class S3DashboardConfig(object):
    """
        Dashboard Configuration

        - can load and store configurations (@todo)
        - can determine the active configuration (@todo)
        - can parse default configuration
        - builds the configuration GUI and handles its requests (@todo)
    """

    DEFAULT_LAYOUT = "boxes"

    def __init__(self,
                 layout,
                 widgets=None,
                 default=None,
                 configurable=False,
                 ):
        """
            Constructor

            @param layout: the layout, or the config dict
            @param widgets: the available widgets as dict {name: widget}
            @param default: the default configuration (=list of widget configs)
            @param configurable: whether this dashboard is user-configurable
        """

        if isinstance(layout, dict):
            config = layout
            title = config.get("title", current.T("Dashboard"))
            layout = config.get("layout")
            widgets = config.get("widgets", widgets)
            default = config.get("default", default)
            configurable = config.get("configurable", configurable)

        # Configuration ID
        # - None means the hardcoded default
        self.config_id = None

        # Page Title
        self.title = title

        # Layout
        if layout is None:
            layout = self.DEFAULT_LAYOUT
        self.layout = layout

        # Available Widgets
        if not widgets:
            widgets = {}
        self.available_widgets = widgets

        # Active Widgets
        if not default:
            default = []
        self.active_widgets = default

        # Is this dashboard user-configurable?
        self.configurable = configurable
        self.loaded = True if not configurable else False

    # -------------------------------------------------------------------------
    def load(self, context):
        """
            Load the current active configuration for the context

            @param context: the current S3DashboardContext
        """

        if not self.configurable:
            return

        table = current.s3db.s3_dashboard
        query = (table.controller == context.controller) & \
                (table.function == context.function) & \
                (table.active == True) & \
                (table.deleted != True)
        row = current.db(query).select(table.id,
                                       table.layout,
                                       table.title,
                                       table.widgets,
                                       limitby = (0, 1),
                                       ).first()

        if row:
            if row.title:
                self.title = row.title

            self.layout = row.layout

            widgets = row.widgets
            if type(widgets) is list:
                self.active_widgets = widgets

            self.config_id = row.id

# =============================================================================
class S3DashboardChannel(object):
    """
        A dashboard channel
        (=a section of the dashboard where widgets can be added)
    """

    def __init__(self):
        """
            Constructor
        """

        self.widgets = {}

    # -------------------------------------------------------------------------
    def add_widget(self, widget, position=None):
        """
            Add XML for a widget to this channel

            @param widget: the widget XML (e.g. DIV instance)
            @param position: the position of the widget in the channel,
                             if there are multiple widgets in the channel
        """

        widgets = self.widgets
        if position not in widgets:
            widgets[position] = [widget]
        else:
            widgets[position].append(widget)

    # -------------------------------------------------------------------------
    def __iter__(self):
        """
            Iterate over the widgets in this channel, in order of their
            positions; used in layouts to build the channel contents.

            @note: Widgets without explicit position (=None), or multiple
                   widgets at the same position, will be returned in the
                   order in which they have been added to the channel.
        """

        widgets = self.widgets
        positions = sorted(p for p in widgets if p is not None)

        if None in widgets:
            positions.append(None)

        for position in positions:
            widget_list = widgets[position]
            for widget in widget_list:
                yield(widget)

    # -------------------------------------------------------------------------
    def __len__(self):
        """
            Number of widgets in this channel, useful for sizing of
            container elements in layouts:

                - number_of_widgets = len(channel)
        """

        total = sum(len(widgets) for widgets in self.widgets.values())
        return total

# =============================================================================
class S3DashboardLayout(object):
    """
        Base class for dashboard layouts, can be subclassed
        to implement custom layouts
    """

    # Tuple of available channels
    # - leave at None in subclasses that dynamically generate channels
    CHANNELS = None

    # The default channel
    DEFAULT_CHANNEL = None

    # -------------------------------------------------------------------------
    # Methods to be implemented in subclasses
    # -------------------------------------------------------------------------
    def build(self, context):
        """
            Build the layout with the contents added by agents
            - to be implemented in subclasses

            @param context: the current S3DashboardContext

            @return: the dashboard contents, usually a TAG instance,
                     alternatively a dict for the view (for custom
                     views)

            @note: can override current.response.view to use a
                   specific view template (default is dashboard.html)
        """

        return ""

    # -------------------------------------------------------------------------
    def add_widget(self, widget, channel=DEFAULT, position=None):
        """
            Add contents to layout,
            - can be overwritten in subclasses (e.g. to dynamically
              create channels)

            @param contents: the contents to insert
            @param channel: the channel where to insert the contents,
                            using the default channel if None
            @param position: the position within the channel (numeric),
                             append to channel if None
        """

        # Fall back to default channel
        if channel is DEFAULT:
            channel = self.DEFAULT_CHANNEL

        # Get the channel
        # - subclasses may want to dynamically generate channels here
        channel_ = self.channels.get(channel)

        # Add widget to channel
        if channel_ is not None:
            channel_.add_widget(widget, position=position)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    def build_channel(self, key, **attr):
        """
            Build a single channel, usually called by build()

            @param key: the channel key
            @param attr: HTML attributes for the channel

            @return: the XML for the channel, usually a DIV instance
        """

        widgets = default = XML("&nbsp;")

        channel = self.channels.get(key)
        if channel is not None:
            widgets = [w for w in channel]
            if not widgets:
                widgets = default

        return DIV(widgets, **attr)

    # -------------------------------------------------------------------------
    # Base class methods
    # -------------------------------------------------------------------------
    def __init__(self, config):
        """
            Constructor

            @param config: the active S3DashboardConfig
        """

        self.config = config

        # Set up channels
        CHANNELS = self.CHANNELS
        if CHANNELS:
            self.channels = dict((name, S3DashboardChannel()) for name in CHANNELS)
        else:
            self.channels = {}

# =============================================================================
class S3DashboardBoxesLayout(S3DashboardLayout):
    """
        Simple 5-boxes layout for dashboards

        +--------------------+
        |         N          |
        +----+----------+----+
        | W  |    C     |  E |
        +----+----------+----+
        |         S          |
        +--------------------+
    """

    # Tuple of available channels
    CHANNELS = ("N", "W", "C", "E", "S")

    # The default channel
    DEFAULT_CHANNEL = "C"

    # -------------------------------------------------------------------------
    def build(self, context):
        """
            Build the layout with the contents added by agents

            @param context: the current S3DashboardContext

            @return: the dashboard contents (TAG)
        """

        T = current.T

        channel = self.build_channel

        contents = TAG[""](
                    DIV(channel("N",
                                _class="small-12 columns db-box db-box-n",
                                ),
                        _class="row",
                        ),
                    DIV(channel("W",
                                _class="small-3 columns db-box db-box-w",
                                ),
                        channel("C",
                                _class="small-6 columns db-box db-box-c",
                                ),
                        channel("E",
                                _class="small-3 columns db-box db-box-e",
                                ),
                        _class="row",
                        ),
                    DIV(channel("S",
                                _class="small-12 columns db-box db-box-s",
                                ),
                        _class="row",
                        ),
                    )

        return contents


# =============================================================================
class S3DashboardColumnsLayout(S3DashboardLayout):
    # @todo
    pass

# =============================================================================
class S3DashboardGridLayout(S3DashboardLayout):
    # @todo
    pass

# =============================================================================
class S3Dashboard(object):
    """
        Class to build and manage dashboards

        def my_controller():

            config = {
                # The default layout for the dashboard
                "layout": "...",

                # Available widgets
                "widgets": {...},

                # Default Widget Configurations
                "default": [...],

                # Allow the user to configure this dashboard
                "configurable": True,
            }

            dashboard = S3Dashboard(config)
            return dashboard()
    """

    # -------------------------------------------------------------------------
    # Standard layouts
    # - custom layouts/overrides can be specifed in constructor
    #
    layouts = {"boxes": ("Boxes", S3DashboardBoxesLayout),
               "columns": ("Columns", S3DashboardColumnsLayout),
               "grid": ("Grid", S3DashboardGridLayout),
               }

    # -------------------------------------------------------------------------
    def __init__(self, config, layouts=None):
        """
            Initializes the dashboard

            @param config: the default configuration for this dashboard
            @param layouts: custom layouts to override/extend the available
                            layouts, as dict {name: (label, class)}
        """

        if not isinstance(config, S3DashboardConfig):
            config = S3DashboardConfig(config)
        self._config = config

        self.context = S3DashboardContext()

        available_layouts = dict(self.layouts)
        if layouts:
            available_layouts.update(layouts)
        self.available_layouts = available_layouts

        self._agents = None

    # -------------------------------------------------------------------------
    @property
    def config(self):
        """
            Lazy property to load the current configuration from the database

            @return: the S3DashboardConfig
        """

        config = self._config
        if not config.loaded:
            config.load(self.context)

        return config

    # -------------------------------------------------------------------------
    @property
    def agents(self):
        """
            Lazy property to instantiate the dashboard agents

            @return: a dict {agent_id: agent}
        """

        agents = self._agents
        if agents is None:

            # The dashboard configuration
            config = self.config

            # The current context
            context = self.context

            config_id = config.config_id
            available_widgets = config.available_widgets

            agents = self._agents = {}
            for index, widget_config in enumerate(config.active_widgets):

                # Get the widget type
                name = widget_config.get("widget")
                widget = available_widgets.get(name)
                if not widget:
                    continue

                # Identify the widget
                if config_id is None:
                    agent_id = "db-none-%s" % index
                else:
                    agent_id = widget_config.get("agent_id")
                if not agent_id:
                    continue

                # Instantiate the agent
                agent = widget.create_agent(agent_id,
                                            config = widget_config,
                                            context = context,
                                            )

                # Register the agent
                agents[agent_id] = agent

        return agents

    # -------------------------------------------------------------------------
    def __call__(self, **attr):
        """
            Dispatch requests - this method is called by the controller.

            @param attr: keyword arguments from the controller

            @keyword _id: the node ID for the dashboard (default: "dashboard")

            @return: the output for the view
        """

        # @todo: handle the side menu (if any)

        context = self.context

        agent_id = context.agent
        http = context.http
        command = context.command

        status, msg = None, None

        if not agent_id:
            # Global request
            if http == "GET":
                if command:
                    # Global command
                    output, error = self.do(command, context)
                    if error:
                        status, msg = error
                else:
                    # Build dashboard
                    if context.representation == "html":
                        output = self.build(**attr)
                    else:
                        status, msg = 415, current.ERROR.BAD_FORMAT
            elif http == "POST":
                if command:
                    # Global command
                    output, error = self.do(command, context)
                    if error:
                        status, msg = error
                else:
                    # POST requires command
                    status, msg = 405, current.ERROR.BAD_METHOD
            else:
                status, msg = 405, current.ERROR.BAD_METHOD

        elif context.bulk:
            # Multi-agent request (bulk status check)
            # @todo: implement
            status, msg = 501, current.ERROR.NOT_IMPLEMENTED

        else:
            # Single-agent request
            agent = self.agents.get(agent_id)
            if agent:
                # Call the agent
                output, error = agent(context)
                if error:
                    status, msg = error
            else:
                status, msg = 404, current.ERROR.BAD_RESOURCE

        if status:
            context.error(status, msg)
        else:
            return output

    # -------------------------------------------------------------------------
    def build(self, **attr):
        """
            Build the dashboard and all its contents

            @param attr: keyword arguments from the controller

            @return: the output dict for the view
        """

        config = self.config
        context = self.context

        dashboard_id = attr.get("_id", "dashboard")

        # Switch for config mode
        hide = " hide" if not config.configurable else ""
        switch = SPAN(ICON("settings",
                           _class = "db-config-on%s" % hide,
                           ),
                      ICON("done",
                           _class = "db-config-off hide"),
                      _class = "db-config",
                      data = {"mode": "off"},
                      )

        output = {"title": config.title,
                  "contents": "",
                  "dashboard_id": dashboard_id,
                  "switch": switch,
                  }

        # Script Options
        ajax_url = URL(args=[], vars={})

        script_options = {"ajaxURL": ajax_url,
                          }

        # Inject JavaScript
        # - before building the widgets, so that widgets can subclass
        self.inject_script(dashboard_id, options=script_options)

        # Instantiate the layout for the active config
        layout = self.get_active_layout(config)

        # Build the widgets
        for agent in self.agents.values():
            agent.add_widget(layout, context)

        # Set the view
        current.response.view = "dashboard.html"

        # Build the layout
        contents = layout.build(context)

        if isinstance(contents, dict):
            output.update(contents)
        else:
            output["contents"] = contents

        return output

    # -------------------------------------------------------------------------
    def do(self, command, context):
        """
            Execute a dashboard global command

            @param command: the command
            @param context: the current S3DashboardContext

            @todo: implement global commands
        """

        output = None
        error = (501, current.ERROR.NOT_IMPLEMENTED)

        return output, error

    # -------------------------------------------------------------------------
    def get_active_layout(self, config):
        """
            Get the active layout

            @param config: the active dashboard configuration
            @return: an instance of the active layout
        """

        layout = self.available_layouts.get(config.layout)

        if layout is None:
            layout = S3DashboardBoxesLayout
        elif type(layout) is tuple:
            # Can be a tuple to specify a label for the layout selector
            layout = layout[-1]

        return layout(config)

    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(dashboard_id, options=None):

        s3 = current.response.s3

        scripts = s3.scripts
        appname = current.request.application

        # Inject UI widget script
        if s3.debug:
            script = "/%s/static/scripts/S3/s3.ui.dashboard.js" % appname
            if script not in scripts:
                scripts.append(script)
        else:
            script = "/%s/static/scripts/S3/s3.ui.dashboard.min.js" % appname
            if script not in scripts:
                scripts.append(script)

        # Inject widget instantiation
        if not options:
            options = {}
        script = """$("#%(dashboard_id)s").dashboardController(%(options)s)""" % \
                    {"dashboard_id": dashboard_id,
                     "options": json.dumps(options),
                     }
        s3.jquery_ready.append(script)


# =============================================================================
class delegated(object):
    """
        Decorator for widget methods that shall be exposed in the web API.

        Delegated methods will be available as URL commands, so that
        client-side scripts can send Ajax requests directly to their
        agent:

        /my/dashboard/[command]?agent=[agent-id]

        Delegated methods will be executed in the context of the agent
        rather than of the widget (therefore "delegated"), so that they
        have access to the agent configuration.

        Pattern:

        @delegated
        def example(agent, context):

            # Accessing the agent config:
            config = agent.config

            # Accessing the widget context (=self):
            widget = agent.widget

            # Accessing other agents of the same widget:
            agents = widget.agents

            # do something with the context, return output
            return {"output": "something"}
    """

    def __init__(self, function):
        self.function = function

    def __call__(self, function):
        self.function = function
        return self

    def execute(self, agent, context):
        function = self.function
        if callable(function):
            output = function(agent, context)
        else:
            output = function
        return output

# =============================================================================
class S3DashboardAgent(object):
    """
        Object serving a dashboard widget

        - renders the widget according to the active configuration
        - dispatches Ajax requests to widget methods
        - manages the widget configuration
    """

    def __init__(self, agent_id, widget=None, config=None):
        """
            Initialize the agent

            @param agent_id: the agent ID (string), a unique XML
                             identifier for the widget configuration
            @param widget: the widget (S3DashboardWidget instance)
            @param config: the widget configuration (dict)
        """

        self.agent_id = agent_id
        self.widget = widget

        self.config = config

    # -------------------------------------------------------------------------
    def __call__(self, context):
        """
            Dispatch Ajax requests

            @param context: the current S3DashboardContext

            @return: tuple (output, error), where:
                     - "output" is the output of the command execution
                     - "error" is a tuple (http_status, message), or None
        """

        command = context.command
        representation = context.representation

        output = None
        error = None

        if command:
            if command in ("config", "authorize"):
                # Agent command
                # @todo: implement agent commands
                error = (501, current.ERROR.NOT_IMPLEMENTED)
            else:
                # Delegated command
                try:
                    output = self.do(command, context)
                except NotImplementedError:
                    error = (501, current.ERROR.NOT_IMPLEMENTED)
        else:
            if context.http == "GET":
                if representation in ("html", "iframe"):
                    # Return the widget XML
                    output = self.widget.widget(self.agent_id,
                                                self.config,
                                                context = context,
                                                )
                else:
                    error = (415, current.ERROR.BAD_FORMAT)
            else:
                error = (405, current.ERROR.BAD_METHOD)

        return output, error

    # -------------------------------------------------------------------------
    def do(self, command, context):
        """
            Execute a delegated widget method

            @param command: the name of the delegated widget method
            @param context: the S3DashboardContext
        """

        widget = self.widget

        msg = "%s does not expose a '%s' method"
        exception = lambda: NotImplementedError(msg % (widget.__class__.__name__,
                                                       command,
                                                       ))
        try:
            method = getattr(widget, command)
        except AttributeError:
            raise exception()
        if type(method) is not delegated:
            raise exception()

        return method.execute(self, context)

    # -------------------------------------------------------------------------
    def add_widget(self, layout, context):
        """
            Build the widget XML for the context, and add it to the layout
        """

        config = self.config
        prototype = self.widget

        # Produce the contents XML
        contents = prototype.widget(self.agent_id,
                                    config,
                                    context = context,
                                    )

        # Get the config bar
        configbar = prototype.configbar()

        # Construct the widget
        widget = DIV(configbar,
                     contents,
                     _class = "db-widget",
                     _id = self.agent_id,
                     )

        # Add script file
        prototype._load_script()

        # Determine channel and position from config
        channel = config.get("channel", DEFAULT)
        position = config.get("position", None)

        # Add the widget to the layout
        layout.add_widget(widget,
                          channel=channel,
                          position=position,
                          )

# =============================================================================
class S3DashboardWidget(object):
    """
        Base class for dashboard widgets
    """

    # -------------------------------------------------------------------------
    # Methods to be implemented by subclasses
    # -------------------------------------------------------------------------
    def widget(self, agent_id, config, context=None):
        """
            Construct the XML for this widget

            @param context: the S3DashboardContext
            @param config: the active widget configuration

            @return: an XmlComponent with the widget contents,
                     the outer DIV will be added by the agent
        """

        # Base class just renders some static XML
        contents = config.get("xml", "")

        # Inject the JavaScript components
        self.inject_script(agent_id)

        return XML(contents)

    # -------------------------------------------------------------------------
    def get_script_path(self, debug=False):
        """
            Get the path to the script file for this widget, can be
            implemented in subclasses to override the default.

            @param debug: whether running in debug mode or not

            @return: path relative to static/scripts,
                     None if no separate script file required
        """

        #if debug:
        #    return "S3/mywidget.js"
        #else:
        #    return "S3/mywidget.min.js"

        # No separate script file required for base class
        return None

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    @staticmethod
    def inject_script(agent_id,
                      widget_class="dashboardWidget",
                      options=None):
        """
            Helper method to inject the init script for a particular agent,
            usually called by widget() method.

            @param agent_id: the agent ID
            @param widget_class: the widget class to instantiate
            @param options: JSON-serializable dict of options to pass
                            to the widget instance
        """

        s3 = current.response.s3

        if not agent_id or not widget_class:
            return
        if not options:
            options = {}
        script = """$("#%(agent_id)s").%(widget_class)s(%(options)s)""" % \
                    {"agent_id": agent_id,
                     "widget_class": widget_class,
                     "options": json.dumps(options),
                     }
        s3.jquery_ready.append(script)

    # -------------------------------------------------------------------------
    @staticmethod
    def configbar():
        """
            Build the widget configuration task bar

            @return: the XML for the task bar
        """

        return DIV(SPAN(ICON("move"),
                        _class="db-configbar-left",
                        ),
                   SPAN(ICON("delete"),
                        ICON("settings"),
                        _class="db-configbar-right",
                        ),
                   _class = "db-configbar",
                   )

    # -------------------------------------------------------------------------
    # Base class methods
    # -------------------------------------------------------------------------
    def __init__(self,
                 label=None,
                 defaults=None,
                 on_create_agent=None,
                 **options
                 ):
        """
            Initialize the widget, called when configuring an available
            widget for the dashboard.

            @param label: a label for this widget type, used in the widget
                          selector in the configuration GUI; if left empty,
                          then the widget type will not appear in the selector
            @param defaults: the default configuration for this widget
            @param on_create_agent: callback, invoked when an agent is created
                                    for this widget:
                                        - on_create_agent(agent, context)
            @param **options: type-specific options
        """

        self.label = label

        # The default configuration for this widget
        if defaults is None:
            defaults = {}
        self.defaults = defaults

        # Widget-type specific options
        self.options = options

        # Hooks
        self.on_create_agent = on_create_agent

        self.agents = {}
        self.script_loaded = False

    # -------------------------------------------------------------------------
    def create_agent(self, agent_id, config=None, context=None):
        """
            Create an agent for this widget

            @param agent_id: the agent ID
            @param config: the agent configuration
        """

        # Add widget defaults to configuration
        agent_config = dict(self.defaults)
        if config:
            agent_config.update(config)

        # Create or update agent for agent_id
        agent = self.agents.get(agent_id)
        if agent:
            # Update the agent configuration
            agent.config = agent_config
        else:
            # Create a new agent
            agent = S3DashboardAgent(agent_id,
                                     widget=self,
                                     config=agent_config,
                                     )
            self.agents[agent_id] = agent

            # Callback
            on_create_agent = self.on_create_agent
            if on_create_agent:
                on_create_agent(agent, context)

        return agent

    # -------------------------------------------------------------------------
    def _load_script(self):
        """
            Add the script file to s3.scripts, called when an agent
            builds the widget
        """

        if self.script_loaded:
            return

        s3 = current.response.s3
        scripts = s3.scripts

        path = self.get_script_path(debug=s3.debug)
        if path:
            appname = current.request.application

            # Add script to s3.scripts
            script = "/%s/static/scripts/%s" % (appname, path)
            if script not in scripts:
                scripts.append(script)

        self.script_loaded = True

# END =========================================================================
