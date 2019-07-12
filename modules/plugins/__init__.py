# -*- coding: utf-8 -*-

import os
import sys

from gluon import current
from gluon.storage import Storage

from s3compat import reload

__all__ = ("PluginLoader",
           )

# Name of the plugin directory in modules
PLUGINS = "plugins"

# Module names to ignore when scanning for plugins
IGNORE = ("skeleton", "__init__")

# Name of the setup function in plugins
SETUP = "setup"

# Name of the variable that contains the version info in plugins
VERSION = "__version__"

# =============================================================================
class PluginLoader(object):
    """
        Simple plugin loader (experimental)

        Plugins are python modules or packages in the modules/plugins
        directory.

        Each plugin defines a setup() function which is called during
        the request cycle immediately before entering the controller.

        Plugins can be added by simply placing them in the plugins
        directory, without any code change required.

        The plugin directory will be scanned for new or updated plugins
        whenever a new session starts, or by calling explicitly:

            PluginLoader.detect(reset_all=True)

        NB the reloading of the plugins can only be enforced in the
           current interpreter thread - while other threads may still
           run the old version. Therefore, it is recommended to restart
           all threads (=reloading the server) after installing or updating
           a plugin.

        NB failing setup() methods will not be tried again until the next
           reload (new session, restart, or explicit call)

        session.s3.plugins contains a dict of all current plugins, like:

            {name: (version, status)}

        where:

            - name is the python module name of the plugin

            - version is the version string provided by the plugin (or
              "unknown" if not present)

            - status is:

                None = newly detected plugin, not set up yet
                True = plugin has been set up successfully
                False = plugin setup failed in the last attempt, deactivated
    """

    # -------------------------------------------------------------------------
    @classmethod
    def setup_all(cls, reload_all=False):
        """
            Setup all plugins

            @param reload_all: reload all plugins and reset the registry
        """

        if reload_all:
            cls.detect(reset_all=True)

        for name in list(cls._registry().keys()):
            cls.load(name)

    # -------------------------------------------------------------------------
    @classmethod
    def detect(cls, reset_all=False):
        """
            Detect new plugins and update the registry

            @param reset_all: reset all entries in the registry
        """

        default = (None, None)

        if reset_all:
            plugin = lambda name: default
        else:
            registry = cls._registry()
            plugin = lambda name: registry.get(name, default)

        plugins = dict((name, plugin(name)) for name in cls._scan())
        cls._registry(plugins)

    # -------------------------------------------------------------------------
    @classmethod
    def load(cls, name, force=False):
        """
            Run the setup method of a particular plugin

            @param name: the name of the plugin
            @param force: enforce the plugin to be reloaded and its
                          setup method to be re-run regardless of the
                          previous status
        """

        if name[0] == "_":
            return False

        log = current.log

        registry = cls._registry()
        if name not in registry:
            cls.detect()
        if name not in registry:
            raise NameError("plugin '%s' not found" % name)

        # Get version and status info from registry
        plugin_info = registry[name]
        if force or not isinstance(plugin_info, tuple):
            version, status = None, None
        else:
            version, status = plugin_info

        if status is None:
            new = True
            if not (cls._reload(name)):
                version, status = "unknown", False
            else:
                version, status = None, True
        else:
            new = False

        if status is False:
            # Skip plugins which have failed in previous attempts
            registry[name] = (version, status)
            return False

        status = True
        setup = None

        # Import manifest
        package = "%s.%s" % (PLUGINS, name)
        try:
            setup = getattr(__import__(package, fromlist=[SETUP]), SETUP)
        except (ImportError, AttributeError):
            # This may not be a plugin at all => remove from registry
            if new:
                log.debug("Plugin '%s' not found" % name)
            registry.pop(name, None)
            return False
        except SyntaxError:
            if new:
                log.error("Skipping invalid plugin '%s'" % name)
            if current.response.s3.debug:
                raise
            version, status = "invalid", False

        if version is None:
            # Update version info if plugin has been reloaded
            try:
                version = getattr(__import__(package, fromlist=[VERSION]), VERSION)
            except (ImportError, AttributeError):
                version = "unknown"

        if status and not callable(setup):
            # Is a module => find setup function
            try:
                setup = setup.setup
            except AttributeError:
                # No setup function found => treat as failed
                if new:
                    log.debug("No setup function found for plugin '%s'" % name)
                status = False

        if status:
            # Execute setup method
            if new:
                log.info("Setting up plugin '%s'" % name)
            try:
                setup()
            except Exception:
                log.error("Plugin '%s' setup failed" % name)
                if current.response.s3.debug:
                    raise
                status = False

        # Update the registry
        registry[name] = (version, status)

        return status

    # -------------------------------------------------------------------------
    @classmethod
    def _registry(cls, plugins=None):
        """
            Get (or replace) the current plugin registry

            @param plugins: the new registry
        """

        session_s3 = current.session.s3

        if plugins:
            registry = session_s3.plugins = plugins
        else:
            registry = session_s3.plugins
            if registry is None:
                # New session => run detect
                # - initialize registry first to prevent infinite recursion
                registry = session_s3.plugins = {}
                cls.detect()
        return registry

    # -------------------------------------------------------------------------
    @staticmethod
    def _scan():
        """
            Iterator scanning the plugin directory for available plugins

            @return: the names of the plugins
        """

        folder = current.request.folder
        path = os.path.join(folder, "modules", PLUGINS)

        names = os.listdir(path)
        for name in names:

            name_, extension = os.path.splitext(name)
            if name_ in IGNORE:
                continue

            path_ = os.path.join(path, name)
            if os.path.isdir(path_) or extension == ".py":
                yield(name_)

    # -------------------------------------------------------------------------
    @staticmethod
    def _reload(name):
        """
            Reload a plugin

            @param name: the plugin name

            @note: this works only within the current thread, other
                   threads may still be bound to the old version of
                   the plugin
        """

        if name in IGNORE:
            return

        success = True

        appname = current.request.application
        plugin_name = "applications.%s.modules.%s.%s" % (appname, PLUGINS, name)

        plugin = sys.modules.get(plugin_name)
        if plugin is not None:
            try:
                reload(plugin)
            except ImportError:
                current.log.error("Reloading plugin '%s' failed" % name)
                success = False

        return success

# =============================================================================
# Do a full scan when reloading the module (=when the thread starts)
PluginLoader.detect(reset_all=True)

# =============================================================================
