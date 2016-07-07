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
           "S3DashboardWidget",
           )

from gluon import *

from s3utils import s3_get_extension

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
        # @todo: extract the agent-id (?agent=agent-id)

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
        if len(args) > 0:
            self.command = args[0]

        self.agent = request.get_vars.get("agent")

        self.http = current.request.env.request_method
        self.representation = s3_get_extension(request) or DEFAULT_FORMAT

# =============================================================================
class S3DashboardConfig(object):
    """
        Dashboard Configuration

        - can load and store configurations (@todo)
        - can determine the active configuration (@todo)
        - can parse default configuration
        - renders the configuration GUI and handles its requests (@todo)
    """

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

        DEFAULT_LAYOUT = "boxes"

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
            layout = DEFAULT_LAYOUT
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

# =============================================================================
class S3DashboardChannel(object):
    """
        A dashboard channel
        (=a section of the dashboard where widgets can be rendered)
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
                             (lowest value is rendered first)
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
            position (lowest position value is rendered first); used in
            layouts to render the channel contents

            NB widgets without explicit position (=None), or multiple
               widgets with the same position, will be returned in the
               order in which they have been added to this channel
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
            container elements in layouts

            number_of_widgets = len(channel)
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
    def add_widget(self, widget, channel=DEFAULT, position=None):
        """
            Add contents to layout
            - can be overridden in subclasses

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
    def render(self, context):
        """
            Render the contents, build the output dict for the view
            - to be implemented in subclasses

            @param context: the current S3DashboardContext

            @return: the output dict for the view
        """

        return ""

    # -------------------------------------------------------------------------
    def render_channel(self, key, **attr):
        """
            Render a single channel, usually called by render()
            - can be overridden in subclass

            @param key: the channel key
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
    def render(self, context):
        """
            Render the contents, build the output dict for the view
            - to be implemented in subclasses

            @param context: the current S3DashboardContext

            @return: the output dict for the view
        """

        T = current.T

        channel = self.render_channel

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
        Class to render and manage dashboards

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

        self.config = config
        self.context = S3DashboardContext()

        available_layouts = dict(self.layouts)
        if layouts:
            available_layouts.update(layouts)
        self.available_layouts = available_layouts

        self._agents = None

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

                # Instantiate the agent
                agent = widget._create_agent(agent_id,
                                             config = widget_config,
                                             context = context,
                                             )

                # Register the agent
                agents[agent_id] = agent

        return agents

    # -------------------------------------------------------------------------
    def __call__(self):
        """
            Dispatch requests - this method is called by the controller.

            @return: the output for the view
        """

        # @todo: dispatch commands to agents
        # @todo: handle the side menu (if any)

        context = self.context

        if context.http == "GET":
            if context.representation == "html":
                output = self.render()
            else:
                context.error(415, current.ERROR.BAD_FORMAT)
        else:
            context.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def render(self):
        """
            Method to produce the dashboard
        """

        config = self.config
        context = self.context

        output = {"title": config.title,
                  "contents": "",
                  }

        # Inject JavaScript (before the widgets inject theirs)
        # @todo

        # Instantiate the layout for the active config
        layout = self.get_active_layout(config)

        # Render the widgets
        for agent in self.agents.values():
            agent.render_widget(layout, context)

        # Render the contents with the layout
        contents = layout.render(context)

        if isinstance(contents, dict):
            output.update(contents)
        else:
            output["contents"] = contents

        # Inject CSS (after the widgets inserted theirs)
        # @todo

        # Set the view
        # @todo: allow per-template views (to support other themes)
        current.response.view = "dashboard.html"

        return output

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

        # @todo: expose widget.options and widget.defaults for delegated functions

        self.config = config

    # -------------------------------------------------------------------------
    def __call__(self, context):
        """
            Dispatch Ajax requests

            @todo: process config-commands internally
            @todo: execute other commands through do-method
        """
        pass

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
    def render_widget(self, layout, context):
        """
            Build the widget XML for the context, and add it to the layout
        """

        config = self.config
        prototype = self.widget

        # Produce the widget XML
        widget = prototype.widget(self.agent_id,
                                  config,
                                  context = context,
                                  )

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

            @return: a DIV instance
        """

        # Base class just renders some static XML
        contents = config.get("xml", "")
        return DIV(XML(contents),
                   _class = "db-generic",
                   _id = agent_id,
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

    # -------------------------------------------------------------------------
    def _create_agent(self, agent_id, config=None, context=None):
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

# END =========================================================================
