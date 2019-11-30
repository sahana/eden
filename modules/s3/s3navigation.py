# -*- coding: utf-8 -*-

""" S3 Navigation Module

    @copyright: 2011-2019 (c) Sahana Software Foundation
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

    @todo: - refine check_selected (e.g. must be False if link=False)
           - implement collapse-flag (render only components in a TAG[""])
           - implement convenience methods for breadcrumbs (+renderer))
           - add site-map generator and renderer (easy)
           - rewrite action buttons/links as S3NavigationItems
           - ...and any todo's in the code
"""

__all__ = ("S3NavigationItem",
           "S3ScriptItem",
           "S3ResourceHeader",
           "s3_rheader_tabs",
           "s3_rheader_resource",
           )

from gluon import *
from gluon.storage import Storage

from s3compat import basestring, xrange
from .s3utils import s3_str

# =============================================================================
class S3NavigationItem(object):
    """
        Base class and API for navigation items.

        Navigation items are GUI elements to navigate the application,
        typically represented as hyperlinks. Besides form elements,
        navigation items are most common type of GUI controls.

        This base class can be used to implement both nagivation items
        and navigation item containers (e.g. menus), each as subclasses.

        Subclasses should implement the layout() method to render the item as
        HTML (ideally using the web2py helpers). There is no default layout,
        items will not be rendered at all unless the subclass implements a
        layout method or the particular instance receives a renderer as
        parameter.

        Additionally, subclasses should implement the check_*() methods:

            Method:             Checks whether:

            check_active        this item belongs to the requested page
            check_enabled       this item is enabled
            check_permission    the user is permitted to access this item
            check_selected      the item has been selected to request the page

        check_active is the first check run, and the only method that
        actually deactivates the item completely, whereas the other
        methods just set flags for the renderer. All of these methods
        must return True or False for the respective condition.

        There are default check_*() methods in this base class which support
        a menu-alike behavior of the item - which may though not fit for all
        navigation elements.

        For more details, see the S3Navigation wiki page:
        http://eden.sahanafoundation.org/wiki/S3/S3Navigation
    """

    # -------------------------------------------------------------------------
    # Construction
    #
    def __init__(self,
                 label=None,
                 c=None,
                 f=None,
                 args=None,
                 vars=None,
                 extension=None,
                 a=None,
                 r=None,
                 m=None,
                 p=None,
                 t=None,
                 url=None,
                 tags=None,
                 parent=None,
                 translate=True,
                 layout=None,
                 check=None,
                 restrict=None,
                 link=True,
                 mandatory=False,
                 ltr=False,
                 **attributes):
        """
            Constructor

            @param label: the label

            @param c: the controller
            @param f: the function
            @param args: the arguments list
            @param vars: the variables Storage
            @param extension: the request extension
            @param a: the application (defaults to current.request.application)
            @param r: the request to default to

            @param m: the URL method (will be appended to args)
            @param p: the method to check authorization for
                      (will not be appended to args)
            @param t: the table concerned by this request
                      (overrides c_f for auth)

            @param url: a URL to use instead of building one manually
                        - e.g. for external websites or mailto: links

            @param tags: list of tags for this item
            @param parent: the parent item

            @param translate: translate the label
            @param layout: the layout
            @param check: a condition or list of conditions to automatically
                          enable/disable this item
            @param restrict: restrict to roles (role UID or list of role UIDs)
            @param link: item has its own URL
            @param mandatory: item is always active
            @param ltr: item is always rendered LTR

            @param attributes: attributes to use in layout
        """

        # Label
        if isinstance(label, basestring) and translate:
            self.label = current.T(label)
        else:
            self.label = label

        # Register tags
        if tags:
            if type(tags) is not list:
                tags = [tags]
            self.tags = tags
        else:
            self.tags = []

        # Request parameters
        if r is not None:
            self.r = r
            if a is None:
                a = r.application
            if c is None:
                c = r.controller
            if f is None:
                f = r.function
            if args is None:
                args = r.args
            if vars is None:
                vars = r.vars
        else:
            self.r = current.request

        # Application, controller, function, args, vars, extension
        self.application = a

        if isinstance(c, (list, tuple)) and len(c):
            self.controller = c[0]
            self.match_controller = c
        else:
            self.controller = c
            self.match_controller = [c]

        if isinstance(f, (list, tuple)) and len(f):
            self.function = f[0]
            self.match_function = f
        else:
            self.function = f
            self.match_function = [f]

        if args is None:
            args = []
        elif isinstance(args, str):
            args = args.split("/")
        self.args = args
        if vars:
            self.vars = vars
        else:
            self.vars = Storage()
        self.extension = extension

        # Table and method
        self.tablename = t
        self.method = m
        if m is not None:
            if not len(args):
                self.args = [m]
            elif args[-1] != m:
                self.args.append(m)
        if p is not None:
            self.p = p
        else:
            self.p = m

        self.override_url = url

        # Layout attributes and options
        attr = Storage()
        opts = Storage()
        for k, v in attributes.items():
            if k[0] == "_":
                attr[k] = v
            else:
                opts[k] = v
        self.attr = attr
        self.opts = opts

        # Initialize parent and components
        self.parent = parent
        self.components = []

        # Flags
        self.enabled = True             # Item is enabled/disabled
        self.selected = None            # Item is in the current selected-path
        self.visible = None             # Item is visible
        self.link = link                # Item shall be linked
        self.mandatory = mandatory      # Item is always active
        self.ltr = ltr                  # Item is always rendered LTR
        self.authorized = None          # True|False after authorization

        # Role restriction
        self.restrict = restrict
        if restrict is not None:
            if not isinstance(restrict, (list, tuple)):
                self.restrict = [restrict]

        # Hook in custom-checks
        self.check = check

        # Set the renderer (override with set_layout())
        renderer = None
        if layout is not None:
            # Custom layout for this particular instance
            renderer = layout
        elif hasattr(self.__class__, "OVERRIDE"):
            # Theme layout
            renderer = self.get_layout(self.OVERRIDE)
        if renderer is None and hasattr(self.__class__, "layout"):
            # Default layout
            renderer = self.layout
        self.renderer = renderer

    # -------------------------------------------------------------------------
    @staticmethod
    def get_layout(name):
        """
            Check whether the current theme has a custom layout for this
            class, and if so, store it in current.layouts

            @param: the name of the custom layout
            @return: the layout or None if not present
        """

        if hasattr(current, "layouts"):
            layouts = current.layouts
        else:
            layouts = {}
        if layouts is False:
            return None
        if name in layouts:
            return layouts[name]

        # Try to find custom layout in theme
        application = current.request.application
        theme = current.deployment_settings.get_theme_layouts().replace("/", ".")
        package = "applications.%s.modules.templates.%s.layouts" % \
                  (application, theme)
        try:
            override = getattr(__import__(package, fromlist=[name]), name)
        except ImportError:
            # No layouts in theme - no point to try again
            current.layouts = False
            return None
        except AttributeError:
            override = None

        if override and \
           hasattr(override, "layout") and \
           type(override.layout) == type(lambda:None):
            layout = override.layout
        else:
            layout = None

        layouts[name] = layout
        current.layouts = layouts

        return layout

    # -------------------------------------------------------------------------
    def clone(self):
        """ Clone this item and its components """

        item = self.__class__()
        item.label = self.label
        item.tags = self.tags

        item.r = self.r

        item.application = self.application
        item.controller = self.controller
        item.function = self.function

        item.match_controller = [c for c in self.match_controller]
        item.match_function = [f for f in self.match_function]

        item.args = [a for a in self.args]
        item.vars = Storage(**self.vars)

        item.extension = self.extension
        item.tablename = self.tablename
        item.method = self.method
        item.p = self.p

        item.override_url = self.override_url

        item.attr = Storage(**self.attr)
        item.opts = Storage(**self.opts)

        item.parent = self.parent
        item.components = [i.clone() for i in self.components]

        item.enabled = self.enabled
        item.selected = self.selected
        item.visible = self.visible
        item.link = self.link
        item.mandatory = self.mandatory
        if self.restrict is not None:
            item.restrict = [r for r in self.restrict]
        else:
            item.restrict = None

        item.check = self.check
        item.renderer = self.renderer

        return item

    # -------------------------------------------------------------------------
    # Check methods
    #
    def check_active(self, request=None):
        """
            Check whether this item belongs to the requested page (request).

            If this check returns False, then the item will be deactivated
            entirely, i.e. no further checks will be run and the renderer
            will never be called.

            @param request: the request object (defaults to current.request)
        """

        # Deactivate the item if its target controller is deactivated
        c = self.get("controller")
        if c:
            return current.deployment_settings.has_module(c)

        # Fall back to current.request
        if request is None:
            request = current.request

        parent = self.parent
        if parent is not None:
            # For component items, the parent's status applies
            return parent.check_active(request)

        elif self.mandatory:
            # mandatory flag overrides request match
            return True

        elif self.match(request):
            # item is active if it matches the request
            return True

        return False

    # -------------------------------------------------------------------------
    def check_enabled(self):
        """
            Check whether this item is enabled.

            This check does not directly disable the item, but rather
            sets the enabled-flag in the item which can then be used
            by the renderer.

            This function is called as the very last action immediately
            before rendering the item. If it returns True, then the
            enabled-flag of the item remains unchanged, otherwise
            it gets set to False (False-override).
        """

        # to be implemented in subclass, default True
        return True

    # -------------------------------------------------------------------------
    def check_permission(self):
        """
            Check whether the user is permitted to access this item.

            This check does not directly disable the item, but rather
            sets the authorized-flag in the item which can then be used
            by the renderer.
        """

        authorized = False

        restrict = self.restrict
        if restrict:
            authorized = current.auth.s3_has_roles(restrict)
        else:
            authorized = True

        if self.accessible_url() == False:
            authorized = False
        return authorized

    # -------------------------------------------------------------------------
    def check_selected(self, request=None):
        """
            Check whether this item is in the selected path (i.e. whether it
            is or contains the item used to trigger the request).

            This check doesn't change the processing of the item, but
            rather sets the selected-flag which can then be used by the
            renderer

            If this is a top-level item, then this check sets the
            selected-flags for the whole selected path down to the leaf
            item that has triggered the request.

            Note that this doesn't currently reset selected-flags, so this
            check can be performed only once per subtree and request. If
            it would be really neccessary to perform this check more than
            once, then it should be easy to implement a reset_flags method.

            @param request: the request object, defaults to current.request
        """

        if self.selected is not None:
            # Already selected
            return self.selected
        if request is None:
            request = current.request
        if self.parent is None:
            # If this is the root item, then set the selected path
            branch = self.branch(request)
            if branch is not None:
                branch.select()
            if not self.selected:
                self.selected = False
        else:
            # Otherwise: check the root item
            root = self.get_root()
            if root.selected is None:
                root.check_selected(request)

        return True if self.selected else False

    # -------------------------------------------------------------------------
    def check_hook(self):
        """
            Run hooked-in checks
        """

        cond = True
        check = self.check
        if check is not None:
            if not isinstance(check, (list, tuple)):
                check = [check]
            for condition in check:
                if callable(condition) and not condition(self):
                    cond = False
                elif not condition:
                    cond = False
        return cond

    # -------------------------------------------------------------------------
    # Tag methods, allows to enable/disable/alter items by tag
    #
    def __contains__(self, tag):
        """ Check whether a tag is present in any item of the subtree """

        components = self.components
        for i in components:
            if tag in i.tags or tag in i:
                return 1
        return 0

    # -------------------------------------------------------------------------
    def findall(self, tag):
        """
            Find all items within the tree with the specified tag

            @param tag: the tag
        """

        items = []
        if tag in self.tags:
            items.append(self)
        components = self.components
        for c in components:
            _items = c.findall(tag)
            items.extend(_items)
        return items

    # -------------------------------------------------------------------------
    def enable(self, tag=None):
        """
            Enable items

            @param tag: enable all items in the subtree with this tag
                        (no tag enables only this item)
        """

        if tag is not None:
            items = self.findall(tag)
            for item in items:
                item.enable()
        else:
            self.enabled = True
        return

    # -------------------------------------------------------------------------
    def disable(self, tag=None):
        """
            Disable items

            @param tag: disable all items in the subtree with this tag
                        (no tag disables only this item)
        """

        if tag is not None:
            items = self.findall(tag)
            for item in items:
                item.disable()
        else:
            self.enabled = False
        return

    # -------------------------------------------------------------------------
    def select(self, tag=None):
        """
            Select an item. If given a tag, this selects the first matching
            descendant (depth-first search), otherwise selects this item.

            Propagates the selection up the path to the root item (including
            the root item)

            @param tag: a string
        """

        selected = None
        if tag is None:
            parent = self.parent
            if parent:
                parent.select()
            else:
                self.deselect_all()
            selected = True
        else:
            for item in self.components:
                if not selected:
                    selected = item.select(tag=tag)
                else:
                    item.deselect_all()
            if not selected and tag in self.tags:
                selected = True
        self.selected = selected
        return selected

    # -------------------------------------------------------------------------
    def deselect_all(self):
        """ De-select this item and all its descendants """

        self.selected = None
        for item in self.components:
            item.deselect_all()
        return

    # -------------------------------------------------------------------------
    def set_layout(self, layout, recursive=False, tag=None):
        """
            Alter the renderer for a tagged subset of items in the subtree.

            @param layout: the layout (renderer)
            @param recursive: set this layout recursively for the subtree
            @param tag: set this layout only for items with this tag
        """

        if layout is not None:
            if tag is None or tag in self.tags:
                self.renderer = layout
            if recursive:
                for c in self.components:
                    if tag is None or tag in c.tags:
                        c.set_layout(layout, recursive=recursive, tag=tag)
        return

    # -------------------------------------------------------------------------
    # Activation methods
    #
    # -------------------------------------------------------------------------
    def get(self, name, default=None):
        """
            Get a Python-attribute of this item instance, falls back
            to the same attribute in the parent item if not set in
            this instance, used to inherit attributes to components

            @param name: the attribute name
        """

        if name in self.__dict__:
            value = self.__dict__[name]
        else:
            value = None
        if value is not None:
            return value
        if name[:2] == "__":
            raise AttributeError
        parent = self.parent
        if parent is not None:
            return parent.get(name)
        return default

    # -------------------------------------------------------------------------
    def match(self, request=None):
        """
            Match this item against request (uses GET vars)

            @param request: the request object (defaults to current.request)

            @return: the match level (integer):
                        0=no match
                        1=controller
                        2=controller+function
                        3=controller+function+args
                        4=controller+function+args+vars

            @note: currently ignores numerical arguments in the request,
                   which is though subject to change (in order to support
                   numerical arguments in the item)
        """

        level = 0
        args = self.args
        link_vars = self.vars

        if self.application is not None and \
           self.application != request.application:
            # Foreign application links never match
            return 0

        if self.opts.selectable is False:
            return 0

        # Check hook and enabled
        check = self.check_hook()
        if check:
            enabled = self.check_enabled()
            if not enabled:
                check = False
        if not check:
            # Hook failed or disabled: doesn't match in any case
            return 0

        if request is None:
            request = current.request

        c = self.get("controller")
        mc = self.get("match_controller")

        # Top-level items with no controller setting
        # (=application level items) match any controller, but not more
        if not c and self.parent is None:
            return 1


        rvars = request.get_vars
        controller = request.controller
        function = request.function

        # Handle "viewing" (foreign controller in a tab)
        # NOTE: this tries to match the item against the resource name
        # in "viewing", so if the target controller/function of the item
        # are different from prefix/name in the resource name, then this
        # may require additional match_controller/match_function to be
        # set for this item! (beware ambiguity then, though)
        if "viewing" in rvars:
            try:
                tn = rvars["viewing"].split(".", 1)[0]
                controller, function = tn.split("_", 1)
            except (AttributeError, ValueError):
                pass

        # Controller
        if controller == c or controller in mc:
            level = 1

        # Function
        if level == 1:
            f = self.get("function")
            mf = self.get("match_function")
            if function == f or function in mf:
                level = 2
            elif f == "index" or "index" in mf:
                # "weak" match: homepage link matches any function
                return 1
            elif f is not None:
                return 0

        # Args and vars
        # Match levels (=order of preference):
        #   0 = args mismatch
        #   1 = last arg mismatch (numeric instead of method)
        #   2 = no args in item and vars mismatch
        #   3 = no args and no vars in item
        #   4 = no args in item but vars match
        #   5 = args match but vars mismatch
        #   6 = args match and no vars in item
        #   7 = args match and vars match
        if level == 2:
            extra = 1
            for k, v in link_vars.items():
                if k not in rvars or k in rvars and rvars[k] != s3_str(v):
                    extra = 0
                    break
                else:
                    extra = 2
            rargs = request.args
            if rargs:
                if args:
                    largs = [a for a in request.args if not a.isdigit()]
                    if len(args) == len(largs) and \
                       all([args[i] == largs[i] for i in xrange(len(args))]):
                        level = 5
                    else:
                        if len(rargs) >= len(args) > 0 and \
                           rargs[len(args)-1].isdigit() and \
                           not str(args[-1]).isdigit():
                            level = 1
                        else:
                            return 0
                else:
                    level = 3
            elif args:
                return 0
            else:
                level = 5
            level += extra

        return level

    # -------------------------------------------------------------------------
    def branch(self, request=None):
        """
            Get the matching branch item for request

            @param request: the request object (defaults to current.request)
        """

        if request is None:
            request = current.request

        leaf, level = self.__branch(request)
        if level:
            return leaf
        else:
            return None

    # -------------------------------------------------------------------------
    def __branch(self, request):
        """
            Find the best match for request within the subtree, recursive
            helper method for branch().

            @param request: the request object
        """

        items = self.get_all(enabled=True)
        l = self.match(request)
        if not items:
            return self, l
        else:
            match, maxlevel = None, l - 1
            for i in items:
                item, level = i.__branch(request)
                if item is not None and level > maxlevel:
                    match = item
                    maxlevel = level
            if match is not None:
                return match, maxlevel
            else:
                return self, l

    # -------------------------------------------------------------------------
    # Representation methods
    #
    # -------------------------------------------------------------------------
    def __repr__(self):
        """ String representation of this item """

        components = [str(c) for c in self.components]
        if self.enabled:
            label = str(self.label)
        else:
            label = "%s (disabled)" % self.label
        label = "%s:%s" % (self.__class__.__name__, label)
        if components:
            return "<%s {%s}>" % (label, ",".join(components))
        else:
            return "<%s>" % label

    # -------------------------------------------------------------------------
    def url(self, extension=None, **kwargs):
        """
            Return the target URL for this item, doesn't check permissions

            @param extension: override the format extension
            @param kwargs: override URL query vars
        """

        if not self.link:
            return None

        if self.override_url:
            return self.override_url

        args = self.args
        if self.vars:
            link_vars = Storage(self.vars)
            link_vars.update(kwargs)
        else:
            link_vars = Storage(kwargs)
        if extension is None:
            extension = self.extension
        a = self.get("application")
        if a is None:
            a = current.request.application
        c = self.get("controller")
        if c is None:
            c = "default"
        f = self.get("function")
        if f is None:
            f = "index"
        f, args = self.__format(f, args, extension)
        return URL(a=a, c=c, f=f, args=args, vars=link_vars)

    # -------------------------------------------------------------------------
    def accessible_url(self, extension=None, **kwargs):
        """
            Return the target URL for this item if accessible by the
            current user, otherwise False

            @param extension: override the format extension
            @param kwargs: override URL query vars
        """

        aURL = current.auth.permission.accessible_url

        if not self.link:
            return None

        args = self.args
        if self.vars:
            link_vars = Storage(self.vars)
            link_vars.update(kwargs)
        else:
            link_vars = Storage(kwargs)
        if extension is None:
            extension = self.extension
        a = self.get("application")
        if a is None:
            a = current.request.application
        c = self.get("controller")
        if c is None:
            c = "default"
        f = self.get("function")
        if f is None:
            f = "index"
        f, args = self.__format(f, args, extension)
        return aURL(c=c, f=f, p=self.p, a=a, t=self.tablename,
                    args=args, vars=link_vars)

    # -------------------------------------------------------------------------
    @staticmethod
    def __format(f, args, ext):
        """
            Append the format extension to the last argument

            @param f: the function
            @param args: argument list
            @param ext: the format extension

            @return: tuple (f, args)
        """

        if not ext or ext == "html":
            return f, args
        items = [f]
        if args:
            items += args
        items = [i.rsplit(".", 1)[0] for i in items]
        items.append("%s.%s" % (items.pop(), ext))
        return (items[0], items[1:])

    # -------------------------------------------------------------------------
    def render(self, request=None):
        """
            Perform the checks and render this item.

            @param request: the request object (defaults to current.request)
        """

        renderer = self.renderer
        output = None

        if request is None:
            request = current.request

        if self.check_active(request):

            # Run the class' check_permission method
            self.authorized = self.check_permission()

            # Run check_selected
            self.selected = self.check_selected()

            # Check custom conditions (hook), these methods
            # can alter any prior flags, which can then only be
            # overridden by the class' check_enabled method
            cond = self.check_hook()

            if cond:
                # Run the class' check_enabled method:
                # if this returns False, then this overrides any prior status
                enabled = self.check_enabled()
                if not enabled:
                    self.enabled = False

                # Render the item
                if renderer is not None:
                    output = renderer(self)

        return output

    # -------------------------------------------------------------------------
    def render_components(self):
        """
            Render the components of this item and return the results as list
        """

        items = []
        for c in self.components:
            i = c.render()
            if i is not None:
                if type(i) is list:
                    items.extend(i)
                else:
                    items.append(i)
        return items

    # -------------------------------------------------------------------------
    def xml(self):
        """
            Invokes the renderer and serializes the output for the web2py
            template parser, returns a string to be written to the response
            body, uses the xml() method of the renderer output, if present.
        """

        output = self.render()
        if output is None:
            return ""
        elif hasattr(output, "xml"):
            return output.xml()
        else:
            return str(output)

    # -------------------------------------------------------------------------
    # Tree construction methods
    #
    def set_parent(self, p=None, i=None):
        """
            Set a parent for this item, base method for tree construction

            @param p: the parent
            @param i: the list index where to insert the item
        """

        if p is None:
            p = self.parent
        if p is None:
            return
        parent = self.parent
        if parent is not None and parent !=p:
            while self in parent.components:
                parent.components.remove(self)
        if i is not None:
            p.component.insert(i, self)
        else:
            p.components.append(self)
        self.parent = p
        return

    # -------------------------------------------------------------------------
    def append(self, item=None):
        """
            Append a component

            @param item: the component
        """

        if item is not None:
            if type(item) is list:
                for i in item:
                    self.append(i)
            else:
                item.set_parent(self)
        return self

    # -------------------------------------------------------------------------
    def insert(self, i, item=None):
        """
            Insert a component item at position i

            @param i: the index position
            @param item: the component item
        """

        if item is not None:
            item.set_parent(self, i=i)
        return self

    # -------------------------------------------------------------------------
    def extend(self, items):
        """
            Extend this item with a list of components

            @param items: list of component items
        """

        if items:
            for item in items:
                self.append(item)
        return self

    # -------------------------------------------------------------------------
    def __call__(self, *components):
        """
            Convenience shortcut for extend

            @param components: list of components
        """

        self.extend(components)
        return self

    # -------------------------------------------------------------------------
    def __add__(self, items):
        """
            Append component items to this item

            @param items: the items to append
        """

        if isinstance(items, (list, tuple)):
            self.extend(items)
        else:
            self.append(items)
        return self

    # -------------------------------------------------------------------------
    # Tree introspection and manipulation methods
    #
    def __getitem__(self, i):
        """
            Get the component item at position i

            @param i: the index of the component item
        """

        return self.components.__getitem__(i)

    # -------------------------------------------------------------------------
    def __setitem__(self, i, item):
        """
            Overwrite the component item at position i with item

            @param i: the index within the component list
            @param item: the item
        """

        self.components.__setitem__(i, item)

    # -------------------------------------------------------------------------
    def pop(self, i=-1):
        """
            Return the component at index i and remove it from the list

            @param i: the component index
        """

        return self.components.pop(i)

    # -------------------------------------------------------------------------
    def get_root(self):
        """
            Get the top level item of this navigation tree
        """

        parent = self.parent
        if parent:
            return parent.get_root()
        else:
            return self

    # -------------------------------------------------------------------------
    def path(self, sub=None):
        """
            Get the full path to this item (=a list of items from the root
            item down to this item).
        """

        path = [self]
        if sub:
            path.extend(sub)
        if self.parent:
            return self.parent.path(sub=path)
        else:
            return path

    # -------------------------------------------------------------------------
    def get_all(self, **flags):
        """
            Get all components with these flags

            @param flags: dictionary of flags
        """

        items = []
        for item in self.components:
            if not flags or \
               all([getattr(item, f) == flags[f] for f in flags]):
                items.append(item)
        return items

    # -------------------------------------------------------------------------
    def get_first(self, **flags):
        """
            Get the first component item with these flags

            @param flags: dictionary of flags
        """

        for item in self.components:
            if not flags or \
               all([getattr(item, f) == flags[f] for f in flags]):
                return item
        return None

    # -------------------------------------------------------------------------
    def get_last(self, **flags):
        """
            Get the first component item with these flags

            @param flags: dictionary of flags
        """

        components = list(self.components)
        components.reverse()
        for item in components:
            if not flags or \
               all([getattr(item, f) == flags[f] for f in flags]):
                return item
        return None

    # -------------------------------------------------------------------------
    # List methods
    #
    def __len__(self):
        """ The total number of components of this item """

        return len(self.components)

    # -------------------------------------------------------------------------
    def __bool__(self):
        """
            To be used instead of __len__ to determine the boolean value
            if this item, should always return True for instances
        """

        return self is not None

    def __nonzero__(self):
        """ Python-2.7 backwards-compatibility """

        return self is not None

    # -------------------------------------------------------------------------
    def index(self, item):
        """
            Get the index of a component item within the component list

            @param item: the item
        """

        return self.components.index(item)

    # -------------------------------------------------------------------------
    def pos(self):
        """
            Get the position of this item within the parent's component
            list, reverse method for index()
        """

        if self.parent:
            return self.parent.index(self)
        else:
            return None

    # -------------------------------------------------------------------------
    def is_first(self, **flags):
        """
            Check whether this is the first item within the parent's
            components list with these flags

            @param flags: dictionary of flags
        """

        if not flags:
            return len(self.preceding()) == 0
        if not all([getattr(self, f) == flags[f] for f in flags]):
            return False
        preceding = self.preceding()
        if preceding:
            for item in preceding:
                if all([getattr(item, f) == flags[f] for f in flags]):
                    return False
        return True

    # -------------------------------------------------------------------------
    def is_last(self, **flags):
        """
            Check whether this is the last item within the parent's
            components list with these flags

            @param flags: dictionary of flags
        """

        if not flags:
            return len(self.following()) == 0
        if not all([getattr(self, f) == flags[f] for f in flags]):
            return False
        following = self.following()
        if following:
            for item in following:
                if all([getattr(item, f) == flags[f] for f in flags]):
                    return False
        return True

    # -------------------------------------------------------------------------
    def preceding(self):
        """ Get the preceding siblings within the parent's component list """

        parent = self.parent
        if parent:
            pos = self.pos()
            if pos is not None:
                return parent.components[:pos]
        return []

    # -------------------------------------------------------------------------
    def following(self):
        """ Get the following siblings within the parent's component list """

        parent = self.parent
        if parent:
            items = parent.components
            pos = self.pos()
            if pos is not None:
                pos = pos + 1
                if pos < len(items):
                    return items[pos:]
        return []

    # -------------------------------------------------------------------------
    def get_prev(self, **flags):
        """
            Get the previous item in the parent's component list with these
            flags

            @param flags: dictionary of flags
        """

        preceding = self.preceding()
        preceding.reverse()
        for item in preceding:
            if not flags or \
               all([getattr(item, f) == flags[f] for f in flags]):
                return item
        return None

    # -------------------------------------------------------------------------
    def get_next(self, **flags):
        """
            Get the next item in the parent's component list with these flags

            @param flags: dictionary of flags
        """

        following = self.following()
        for item in following:
            if not flags or \
               all([getattr(item, f) == flags[f] for f in flags]):
                return item
        return None

# =============================================================================
def s3_rheader_resource(r):
    """
        Identify the tablename and record ID for the rheader

        @param r: the current S3Request

    """

    get_vars = r.get_vars

    if "viewing" in get_vars:
        try:
            tablename, record_id = get_vars.viewing.rsplit(".", 1)
        except AttributeError:
            tablename = r.tablename
            record = r.record
        else:
            db = current.db
            record = db[tablename][record_id]
    else:
        tablename = r.tablename
        record = r.record

    return (tablename, record)

# =============================================================================
def s3_rheader_tabs(r, tabs=None):
    """
        Constructs a DIV of component links for a S3RESTRequest

        @param tabs: the tabs as list of tuples (title, component_name, vars),
                     where vars is optional
    """

    rheader_tabs = S3ComponentTabs(tabs)
    return rheader_tabs.render(r)

# =============================================================================
class S3ComponentTabs(object):
    """ Class representing a row of component tabs """

    def __init__(self, tabs=None):
        """
            Constructor

            @param tabs: the tabs configuration as list of names or tuples
                         (label, name)
        """

        if not tabs:
            self.tabs = []
        else:
            self.tabs = [S3ComponentTab(t) for t in tabs if t]

    # -------------------------------------------------------------------------
    def render(self, r):
        """
            Render the tabs row

            @param r: the S3Request
        """

        rheader_tabs = []

        if r.resource.get_config("dynamic_components"):
            self.dynamic_tabs(r.resource.tablename)

        tabs = [t for t in self.tabs if t.active(r)]

        mtab = False
        if r.component is None:
            # Check whether there is a tab for the current URL method
            for t in tabs:
                if t.component == r.method:
                    mtab = True
                    break

        record_id = r.id
        if not record_id and r.record:
            record_id = r.record[r.table._id]

        for i, tab in enumerate(tabs):

            # Determine the query variables for the tab URL
            vars_match = tab.vars_match(r)
            if vars_match:
                _vars = Storage(r.get_vars)
            else:
                _vars = Storage(tab.vars)
                if "viewing" in r.get_vars:
                    _vars.viewing = r.get_vars.viewing

            # Determine the controller function for the tab URL
            if tab.function is None:
                # Infer function from current request
                if "viewing" in _vars:
                    tablename, record_id = _vars.viewing.split(".", 1)
                    function = tablename.split("_", 1)[1]
                else:
                    function = r.function
            else:
                # Tab defines controller function
                function = tab.function

            # Is this the current tab?
            component = tab.component
            here = False
            if function == r.name or function == r.function:
                here = r.method == component or not mtab
            if component:
                if r.component and \
                   r.component.alias == component and \
                   vars_match:
                    here = True
                elif not r.component and r.method == component:
                    here = True
                else:
                    here = False
            else:
                if r.component or not vars_match:
                    here = False

            # HTML class for the tab position
            if here:
                _class = "tab_here"
            elif i == len(tabs) - 1:
                _class = "tab_last"
            else:
                _class = "tab_other"

            # Complete the tab URL with args, deal with "viewing"
            if component:
                args = [record_id, component] if record_id else [component]
                if tab.method:
                    args.append(tab.method)
                if "viewing" in _vars:
                    del _vars["viewing"]
                _href = URL(function, args=args, vars=_vars)
                _id = "rheader_tab_%s" % component
            else:
                args = []
                if function != r.name and not tab.native:
                    if "viewing" not in _vars and r.id:
                        _vars.update(viewing="%s.%s" % (r.tablename, r.id))
                    elif not tab.component and not tab.function:
                        if "viewing" in _vars:
                            del _vars["viewing"]
                        args = [record_id]
                else:
                    if "viewing" not in _vars and record_id:
                        args = [record_id]
                _href = URL(function, args=args, vars=_vars)
                _id = "rheader_tab_%s" % function

            # Render tab
            rheader_tabs.append(SPAN(A(tab.title,
                                       _href=_href,
                                       _id=_id,
                                       ),
                                     _class=_class,
                                     ))

        # Render tab row
        if rheader_tabs:
            rheader_tabs = DIV(rheader_tabs, _class="tabs")
        else:
            rheader_tabs = ""
        return rheader_tabs

    # -------------------------------------------------------------------------
    def dynamic_tabs(self, master):
        """
            Add dynamic tabs

            @param master: the name of the master table
        """

        T = current.T
        s3db = current.s3db

        tabs = self.tabs
        if not tabs:
            return

        ftable = s3db.s3_field
        query = (ftable.component_key == True) & \
                (ftable.component_tab == True) & \
                (ftable.master == master) & \
                (ftable.deleted == False)
        rows = current.db(query).select(ftable.component_alias,
                                        ftable.settings,
                                        )
        for row in rows:
            alias = row.component_alias
            if not alias:
                continue

            static_tab = False
            for tab in tabs:
                if tab.component == alias:
                    static_tab = True
                    break

            if not static_tab:

                label = None
                position = None

                settings = row.settings
                if settings:

                    label = settings.get("tab_label")

                    position = settings.get("tab_position")
                    if position is not None:
                        try:
                            position = int(position)
                        except ValueError:
                            position = None
                    if position < 1 or position >= len(tabs):
                        position = None

                if not label:
                    # Generate default label from component alias
                    label = T(" ".join(s.capitalize()
                                       for s in alias.split("_")
                                       ))
                tab = S3ComponentTab((label, alias))
                if not position:
                    tabs.append(tab)
                else:
                    tabs.insert(position, tab)

# =============================================================================
class S3ComponentTab(object):
    """ Class representing a single Component Tab """

    def __init__(self, tab):
        """
            Constructor

            @param tab: the component tab configuration as tuple
                        (label, component_alias, {get_vars}), where the
                        get_vars dict is optional.
        """

        # @todo: use component hook label/plural as fallback for title
        #        (see S3Model.add_components)
        title, component = tab[:2]

        self.title = title

        if component and component.find("/") > 0:
            function, component = component.split("/", 1)
        else:
            function = None

        if function:
            self.function = function
        else:
            self.function = None

        if component:
            self.component = component
        else:
            self.component = None

        self.native = False
        self.method = None

        if len(tab) > 2:
            tab_vars = self.vars = Storage(tab[2])
            if "native" in tab_vars:
                self.native = True if tab_vars["native"] else False
                del tab_vars["native"]
            if len(tab) > 3:
                self.method = tab[3]
        else:
            self.vars = None

    # -------------------------------------------------------------------------
    def active(self, r):
        """
            Check whether the this tab is active

            @param r: the S3Request
        """

        s3db = current.s3db

        get_components = s3db.get_components
        get_method = s3db.get_method
        get_vars = r.get_vars
        tablename = None
        if "viewing" in get_vars:
            try:
                tablename = get_vars["viewing"].split(".", 1)[0]
            except AttributeError:
                pass

        resource = r.resource
        component = self.component
        function = self.function
        if component:
            clist = get_components(resource.table, names=[component])
            is_component = False
            if component in clist:
                is_component = True
            elif tablename:
                clist = get_components(tablename, names=[component])
                if component in clist:
                    is_component = True
            if is_component:
                return self.authorised(clist[component])
            handler = get_method(resource.prefix,
                                 resource.name,
                                 method=component)
            if handler is None and tablename:
                prefix, name = tablename.split("_", 1)
                handler = get_method(prefix, name,
                                     method=component)
            if handler is None:
                handler = r.get_handler(component)
            if handler is None:
                return component in ("create", "read", "update", "delete")

        elif function:
            return current.auth.permission.has_permission("read", f=function)

        return True

    # -------------------------------------------------------------------------
    def authorised(self, hook):
        """
            Check permissions for component tabs (in order to deactivate
            tabs the user is not permitted to access)

            @param hook: the component hook
        """

        READ = "read"
        has_permission = current.auth.s3_has_permission

        # Must have access to the link table (if any):
        if hook.linktable and not has_permission(READ, hook.linktable):
            return False

        # ...and to the component table itself:
        if has_permission(READ, hook.tablename):
            return True

        return False

    # -------------------------------------------------------------------------
    def vars_match(self, r):
        """
            Check whether the request GET vars match the GET vars in
            the URL of this tab

            @param r: the S3Request
        """

        if self.vars is None:
            return True
        get_vars = r.get_vars
        for k, v in self.vars.items():
            if v is None:
                continue
            if k not in get_vars or \
               k in get_vars and get_vars[k] != v:
                return False
        return True

# =============================================================================
class S3ScriptItem(S3NavigationItem):
    """
        Simple Navigation Item just for injecting scripts into HTML forms
    """

    # -------------------------------------------------------------------------
    def __init__(self,
                 script=None,
                 **attributes):
        """
            @param script: script to inject into jquery_ready when rendered
        """

        super(S3ScriptItem, self).__init__(attributes)
        self.script = script

    # -------------------------------------------------------------------------
    def xml(self):
        """
            Injects associated script into jquery_ready.
        """

        if self.script:
            current.response.s3.jquery_ready.append(self.script)
        return ""

    # -------------------------------------------------------------------------
    @staticmethod
    def inline(item):
        """
            Present to ensure that script injected even in inline forms
        """

        return ""

# =============================================================================
class S3ResourceHeader(object):
    """ Simple Generic Resource Header for tabbed component views """

    def __init__(self, fields=None, tabs=None, title=None):
        """
            Constructor

            @param fields: the fields to display, list of lists of
                           fieldnames, Field instances or callables
            @param tabs: the tabs
            @param title: the title fieldname, Field or callable

            Fields are specified in order rows->cols, i.e. if written
            like:

            [
                ["fieldA", "fieldF", "fieldX"],
                ["fieldB", None, "fieldY"]
            ]

            then that's exactly the screen order. Row or column spans are
            not supported - empty fields will be rendered as empty fields.
            If you need to construct more complex rheaders, you should
            implement a custom method.

            Fields can be specified by field names, Field instances or
            as callables. Where a field specifier is a callable, it will
            be invoked with the record as parameter and is respected to
            return the representation value.

            Where a field specifier is a tuple of two items, the first
            item is taken for the label (overriding the field label, if
            any), like in:


            [
                [(T("Name"), s3_fullname)],
                ...
            ]

            Where the second item is a callable, it maybe necessary to
            specify a label.

            If you don't want any fields, specify this explicitly as:

                rheader = S3ResourceHeader(fields=[])

            Where you don't specify any fields and the table contains a
            "name" field, the rheader defaults to: [["name"]].
        """

        self.fields = fields
        self.tabs = tabs
        self.title = title

    # -------------------------------------------------------------------------
    def __call__(self, r, tabs=None, table=None, record=None, as_div=True):
        """
            Return the HTML representation of this rheader

            @param r: the S3Request instance to render the header for
            @param tabs: the tabs (overrides the original tabs definition)
            @param table: override r.table
            @param record: override r.record
            @param as_div: True: will return the rheader_fields and the
                           rheader_tabs together as a DIV
                           False will return the rheader_fields and the
                           rheader_tabs as a tuple
                           (rheader_fields, rheader_tabs)
        """

        if table is None:
            table = r.table
        if record is None:
            record = r.record

        if tabs is None:
            tabs = self.tabs

        if self.fields is None and "name" in table.fields:
            fields = [["name"]]
        else:
            fields = self.fields

        if record:

            if tabs is not None:
                rheader_tabs = s3_rheader_tabs(r, tabs)
            else:
                rheader_tabs = ""

            trs = []
            for row in fields:
                tr = TR()
                for col in row:
                    if col is None:
                        continue
                    label, value, colspan = self.render_field(table, record, col)
                    if value is False:
                        continue
                    if label is not None:
                        tr.append(TH(("%s: " % label) if label else ""))
                    tr.append(TD(value, _colspan=colspan) if colspan else TD(value))
                trs.append(tr)

            title = self.title
            if title:
                title = self.render_field(table, record, title)[1]

            if title:
                content = DIV(H6(title, _class="rheader-title"),
                              TABLE(trs),
                              _class="rheader-content",
                              )
            else:
                content = TABLE(trs, _class="rheader-content")

            rheader = (content, rheader_tabs)
            if as_div:
                rheader = DIV(*rheader)

        else:
            rheader = None

        return rheader

    # -------------------------------------------------------------------------
    def render_field(self, table, record, col):
        """
            Render an rheader field

            @param table: the table
            @param record: the record
            @param col: the column spec (field name or tuple (label, fieldname))

            @returns: tuple (label, value)
        """

        field = None
        label = True
        value = ""
        colspan = None

        # Parse column spec:
        # fieldname|(label, fieldname)|(label,fieldname,colspan)
        # label can be either a T(), str, HTML, or:
        #       True        => automatic (use field label, default)
        #       None        => no label column
        #       "" or False => empty label
        if isinstance(col, (tuple, list)):
            if len(col) == 2:
                label, f = col
            elif len(col) > 2:
                label, f, colspan = col
            else:
                f = col[0]
        else:
            f = col

        # Get value
        # - value can be a fieldname, a Field instance or a callable to
        #   extract the value from the record
        if callable(f):
            try:
                value = f(record)
            except:
                pass
        else:
            if isinstance(f, str):
                fn = f
                if "." in fn:
                    fn = f.split(".", 1)[1]
                if fn not in record or fn not in table:
                    return None, False, None
                field = table[fn]
                value = record[fn]
                # Field.Method?
                if callable(value):
                    value = value()
            elif isinstance(f, Field) and f.name in record:
                field = f
                value = record[f.name]
        if hasattr(field, "represent") and field.represent is not None:
            value = field.represent(value)

        # Render label
        if label is True:
            label = field.label if field is not None else False

        # Render value
        if not isinstance(value, basestring) and \
           not isinstance(value, DIV):
            value = s3_str(value)

        return label, value, colspan

# END =========================================================================
