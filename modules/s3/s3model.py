# -*- coding: utf-8 -*-

""" S3 Data Model Extensions

    @copyright: 2009-2021 (c) Sahana Software Foundation
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

__all__ = ("S3Model",
           #"S3DynamicModel",
           )

from collections import OrderedDict

from gluon import current, IS_EMPTY_OR, IS_FLOAT_IN_RANGE, IS_INT_IN_RANGE, \
                  IS_IN_SET, IS_NOT_EMPTY, SQLFORM, TAG
from gluon.storage import Storage
from gluon.tools import callback

from s3dal import Table, Field, original_tablename
from .s3navigation import S3ScriptItem
from .s3resource import S3Resource
from .s3validators import IS_ONE_OF, IS_JSONS3
from .s3widgets import s3_comments_widget, s3_richtext_widget

CUSTOM_PREFIX = "custom"
DYNAMIC_PREFIX = "s3dt"
DEFAULT = lambda: None

# Table options that are always JSON-serializable objects,
# and can thus be passed as-is from dynamic model "settings"
# to s3db.configure (& thence to mobile table.settings)
SERIALIZABLE_OPTS = ("autosync",
                     "autototals",
                     "card",
                     "grids",
                     "insertable",
                     "show_hidden",
                     "subheadings",
                     )

ogetattr = object.__getattribute__

# =============================================================================
class S3Model(object):
    """ Base class for S3 models """

    _s3model = True

    LOCK = "s3_model_lock"
    LOAD = "s3_model_load"
    DELETED = "deleted"

    def __init__(self, module=None):
        """ Constructor """

        self.cache = (current.cache.ram, 60)

        self.context = None
        self.classes = {}

        # Initialize current.model
        if not hasattr(current, "model"):
            current.model = {"config": {},
                             "components": {},
                             "methods": {},
                             "cmethods": {},
                             "hierarchies": {},
                             }

        response = current.response
        if "s3" not in response:
            response.s3 = Storage()
        self.prefix = module

        mandatory_models = ("auth",
                            "sync",
                            "s3",
                            "gis",
                            "pr",
                            "sit",
                            "org",
                            )

        if module is not None:
            if self.__loaded():
                return
            self.__lock()
            try:
                env = self.mandatory()
            except Exception:
                self.__unlock()
                raise
            else:
                if isinstance(env, dict):
                    response.s3.update(env)
            if module in mandatory_models or \
               current.deployment_settings.has_module(module):
                try:
                    env = self.model()
                except Exception:
                    self.__unlock()
                    raise
            else:
                try:
                    env = self.defaults()
                except Exception:
                    self.__unlock()
                    raise
            if isinstance(env, dict):
                response.s3.update(env)
            self.__loaded(True)
            self.__unlock()

    # -------------------------------------------------------------------------
    def __loaded(self, loaded=None):

        LOAD = self.LOAD
        name = self.__class__.__name__
        response = current.response
        if LOAD not in response:
            response[LOAD] = []
        if name in response[LOAD]:
            return True
        elif loaded:
            response[LOAD].append(name)
        return loaded

    # -------------------------------------------------------------------------
    def __lock(self):

        LOCK = self.LOCK
        name = self.__class__.__name__
        response = current.response
        if LOCK not in response:
            response[LOCK] = {}
        if name in response[LOCK]:
            raise RuntimeError("circular model reference deadlock in %s" % name)
        else:
            response[LOCK][name] = True
        return

    # -------------------------------------------------------------------------
    def __unlock(self):

        LOCK = self.LOCK
        name = self.__class__.__name__
        response = current.response
        if LOCK in response:
            if name in response[LOCK]:
                response[LOCK].pop(name, None)
            if not response[LOCK]:
                del response[LOCK]
        return

    # -------------------------------------------------------------------------
    def __getattr__(self, name):
        """ Model auto-loader """

        return self.table(name,
                          AttributeError("undefined table: %s" % name))

    # -------------------------------------------------------------------------
    def __getitem__(self, key):

        return self.__getattr__(str(key))

    # -------------------------------------------------------------------------
    def mandatory(self):
        """
            Mandatory objects defined by this model, regardless whether
            enabled or disabled
        """
        return None

    # -------------------------------------------------------------------------
    def model(self):
        """
            Defines all tables in this model, to be implemented by
            subclasses
        """
        return None

    # -------------------------------------------------------------------------
    def defaults(self):
        """
            Definitions of model globals (response.s3.*) if the model
            has been disabled in deployment settings, to be implemented
            by subclasses
        """
        return None

    # -------------------------------------------------------------------------
    @classmethod
    def table(cls, tablename, default=None, db_only=False):
        """
            Helper function to load a table definition by its name
        """

        s3 = current.response.s3
        if s3 is None:
            s3 = current.response.s3 = Storage()

        s3db = current.s3db
        models = current.models

        if not db_only:
            if tablename in s3:
                return s3[tablename]
            elif s3db is not None and tablename in s3db.classes:
                prefix, name = s3db.classes[tablename]
                return models.__dict__[prefix].__dict__[name]

        db = current.db

        # Table already defined?
        try:
            return getattr(db, tablename)
        except AttributeError:
            pass

        found = None

        prefix, name = tablename.split("_", 1)
        if prefix == DYNAMIC_PREFIX:
            # Load Dynamic Table
            try:
                found = S3DynamicModel(tablename).table
            except AttributeError:
                pass

        elif prefix == CUSTOM_PREFIX:
            # Load Custom Table from deployment_settings
            # should be a dict (or OrderedDict if want to manage dependency order):
            # settings.models = {tablename: function}
            # If wanting to have a REST controller for them, then also add an entry to the rest_controllers:
            # settings.base.rest_controllers = {("custom", resourcename): ("custom", resourcename)}

            # Better to raise, ideally explicit error
            #try:
            found = current.deployment_settings.models[tablename](db, tablename)
            #except KeyError:
            #pass

        elif hasattr(models, prefix):
            module = models.__dict__[prefix]

            names = module.__all__
            s3models = module.__dict__

            if not db_only and tablename in names:
                # A name defined at module level (e.g. a class)
                s3db.classes[tablename] = (prefix, tablename)
                found = s3models[tablename]
            else:
                # A name defined in an S3Model
                generic = []
                loaded = False
                for n in names:
                    model = s3models[n]
                    if hasattr(model, "_s3model"):
                        if hasattr(model, "names"):
                            if tablename in model.names:
                                model(prefix)
                                loaded = True
                                break
                        else:
                            generic.append(n)
                if not loaded:
                    for n in generic:
                        s3models[n](prefix)

        if found:
            return found

        if not db_only and tablename in s3:
            return s3[tablename]
        elif hasattr(db, tablename):
            return getattr(db, tablename)
        elif getattr(db, "_lazy_tables") and \
             tablename in getattr(db, "_LAZY_TABLES"):
            return getattr(db, tablename)
        elif isinstance(default, Exception):
            raise default
        else:
            return default

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, name, default=None):
        """
            Helper function to load a response.s3 variable from models
        """

        s3 = current.response.s3
        if s3 is None:
            s3 = current.response.s3 = Storage()

        if name in s3:
            return s3[name]
        elif "_" in name:
            prefix = name.split("_", 1)[0]
            models = current.models
            if hasattr(models, prefix):
                module = models.__dict__[prefix]
                loaded = False
                generic = []
                for n in module.__all__:
                    model = module.__dict__[n]
                    if type(model).__name__ == "type":
                        if loaded:
                            continue
                        if hasattr(model, "names"):
                            if name in model.names:
                                model(prefix)
                                loaded = True
                                generic = []
                            else:
                                continue
                        else:
                            generic.append(n)
                    elif n.startswith("%s_" % prefix):
                        s3[n] = model
                for n in generic:
                    module.__dict__[n](prefix)
        if name in s3:
            return s3[name]
        elif isinstance(default, Exception):
            raise default
        else:
            return default

    # -------------------------------------------------------------------------
    @classmethod
    def load(cls, name):
        """
            Helper function to load a model by its name (=prefix)
        """

        s3 = current.response.s3
        if s3 is None:
            s3 = current.response.s3 = Storage()
        models = current.models

        if models is not None and hasattr(models, name):
            module = models.__dict__[name]
            for n in module.__all__:
                model = module.__dict__[n]
                if type(model).__name__ == "type" and \
                   issubclass(model, S3Model):
                    model(name)
                elif n.startswith("%s_" % name):
                    s3[n] = model
        return

    # -------------------------------------------------------------------------
    @classmethod
    def load_all_models(cls):
        """
            Helper function to load all models
        """

        s3 = current.response.s3
        if s3.all_models_loaded:
            # Already loaded
            return
        s3.load_all_models = True

        models = current.models

        # Load models
        if models is not None:
            for name in models.__dict__:
                if type(models.__dict__[name]).__name__ == "module":
                    cls.load(name)

        # Define importer tables
        from .s3import import S3Importer, S3ImportJob
        S3Importer.define_upload_table()
        S3ImportJob.define_job_table()
        S3ImportJob.define_item_table()

        settings = current.deployment_settings

        # Define Scheduler tables
        # - already done during Scheduler().init() run during S3Task().init() in models/tasks.py
        #current.s3task.scheduler.define_tables(current.db,
        #                                       migrate = settings.get_base_migrate())

        # Define sessions table
        if settings.get_base_session_db():
            # Copied from https://github.com/web2py/web2py/blob/master/gluon/globals.py#L895
            # Not DRY, but no easy way to make it so
            current.db.define_table("web2py_session",
                                    Field("locked", "boolean",
                                          default = False,
                                          ),
                                    Field("client_ip", length=64),
                                    Field("created_datetime", "datetime",
                                          default = current.request.now,
                                          ),
                                    Field("modified_datetime", "datetime"),
                                    Field("unique_key", length=64),
                                    Field("session_data", "blob"),
                                    )

        # Load Custom Models
        if hasattr(settings, "models"):
            # A dict (or OrderedDict if want to manage dependency order) of {tablename: function}
            custom_models = settings.models
            db = current.db
            for tablename in custom_models:
                custom_models[tablename](db, tablename)

        # Don't do this again within the current request cycle
        s3.load_all_models = False
        s3.all_models_loaded = True

    # -------------------------------------------------------------------------
    @staticmethod
    def define_table(tablename, *fields, **args):
        """
            Same as db.define_table except that it does not repeat
            a table definition if the table is already defined.
        """

        db = current.db
        if hasattr(db, tablename):
            table = getattr(db, tablename)
        else:
            table = db.define_table(tablename, *fields, **args)
        return table

    # -------------------------------------------------------------------------
    @staticmethod
    def get_aliased(table, alias):
        """
            Helper method to get a Table instance with alias; prevents
            re-instantiation of an already existing alias for the same
            table (which can otherwise lead to name collisions in PyDAL).

            @param table: the original table
            @param alias: the alias

            @return: the aliased Table instance
        """

        db = current.db

        if hasattr(db, alias):
            aliased = getattr(db, alias)
            if original_tablename(aliased) == original_tablename(table):
                return aliased

        aliased = table.with_alias(alias)
        if aliased._id.table != aliased:
            # Older PyDAL not setting _id attribute correctly
            aliased._id = aliased[table._id.name]

        return aliased

    # -------------------------------------------------------------------------
    # Resource configuration
    # -------------------------------------------------------------------------
    @staticmethod
    def resource(tablename, *args, **kwargs):
        """
            Wrapper for the S3Resource constructor to realize
            the global s3db.resource() method
        """

        return S3Resource(tablename, *args, **kwargs)

    # -------------------------------------------------------------------------
    @classmethod
    def configure(cls, tablename, **attr):
        """
            Update the extra configuration of a table

            @param tablename: the name of the table
            @param attr: dict of attributes to update
        """

        config = current.model["config"]

        tn = tablename._tablename if type(tablename) is Table else tablename
        if tn not in config:
            config[tn] = {}
        config[tn].update(attr)
        return

    # -------------------------------------------------------------------------
    @classmethod
    def get_config(cls, tablename, key, default=None):
        """
            Reads a configuration attribute of a resource

            @param tablename: the name of the resource DB table
            @param key: the key (name) of the attribute
        """

        config = current.model["config"]

        tn = tablename._tablename if type(tablename) is Table else tablename
        if tn in config:
            return config[tn].get(key, default)
        else:
            return default

    # -------------------------------------------------------------------------
    @classmethod
    def clear_config(cls, tablename, *keys):
        """
            Removes configuration attributes of a resource

            @param table: the resource DB table
            @param keys: keys of attributes to remove (maybe multiple)
        """

        config = current.model["config"]

        tn = tablename._tablename if type(tablename) is Table else tablename
        if tn in config:
            if not keys:
                del config[tn]
            else:
                table_config = config[tn]
                for k in keys:
                    table_config.pop(k, None)

    # -------------------------------------------------------------------------
    @classmethod
    def add_custom_callback(cls, tablename, hook, cb, method=None):
        """
            Generic method to append a custom onvalidation|onaccept
            callback to the originally configured callback chain,
            for use in customise_* in templates

            @param tablename: the table name
            @param hook: the main hook ("onvalidation"|"onaccept")
            @param cb: the custom callback function
            @param method: the sub-hook ("create"|"update"|None)

            @example:
                # Add a create-onvalidation callback for the pr_person
                # table, while retaining any existing onvalidation:
                s3db.add_custom_callback("pr_person",
                                         "onvalidation",
                                         my_create_onvalidation,
                                         method = "create",
                                         )
        """

        def extend(this, new):
            if isinstance(this, (tuple, list)):
                this = list(this)
            elif this is not None:
                this = [this]
            else:
                this = []
            if new not in this:
                this.append(new)
            return this

        callbacks = {}
        for m in ("create", "update", None):
            key = "%s_%s" % (m, hook) if m else hook
            callbacks[m] = cls.get_config(tablename, key)

        if method is None:
            generic_cb = callbacks[None]
            if generic_cb:
                callbacks[None] = extend(generic_cb, cb)
            else:
                callbacks[None] = cb
            for m in ("create", "update"):
                current_cb = callbacks[m]
                if current_cb:
                    callbacks[m] = extend(current_cb, cb)
        else:
            current_cb = callbacks[method]
            if current_cb:
                callbacks[method] = extend(current_cb, cb)
            else:
                callbacks[method] = extend(callbacks[None], cb)

        settings = {}
        for m, setting in callbacks.items():
            if setting:
                key = "%s_%s" % (m, hook) if m else hook
                settings[key] = setting
        cls.configure(tablename, **settings)

    # -------------------------------------------------------------------------
    @classmethod
    def virtual_reference(cls, field):
        """
            Reverse-lookup of virtual references which are declared for
            the respective lookup-table as:

                configure(tablename,
                          referenced_by = [(tablename, fieldname), ...],
                          )

            & in the table with the fields(auth_user only current example) as:

                configure(tablename,
                          references = {fieldname: tablename,
                                        ...
                                        },
                          )

            @param field: the Field

            @returns: the name of the referenced table
        """

        if str(field.type) == "integer":

            config = current.model["config"]
            tablename, fieldname = str(field).split(".")

            # 1st try this table's references
            this_config = config.get(tablename)
            if this_config:
                references = this_config.get("references")
                if references is not None and fieldname in references:
                    return references[fieldname]

            # Then try other tables' referenced_by
            key = (tablename, fieldname)
            for tn in config:
                referenced_by = config[tn].get("referenced_by")
                if referenced_by is not None and key in referenced_by:
                    return tn

        return None

    # -------------------------------------------------------------------------
    @classmethod
    def onaccept(cls, table, record, method="create"):
        """
            Helper to run the onvalidation routine for a record

            @param table: the Table
            @param record: the FORM or the Row to validate
            @param method: the method
        """

        if hasattr(table, "_tablename"):
            tablename = table._tablename
        else:
            tablename = table

        onaccept = cls.get_config(tablename, "%s_onaccept" % method,
                   cls.get_config(tablename, "onaccept"))
        if onaccept:
            if "vars" not in record:
                record = Storage(vars = Storage(record),
                                 errors = Storage(),
                                 )
            callback(onaccept, record, tablename=tablename)

    # -------------------------------------------------------------------------
    @classmethod
    def onvalidation(cls, table, record, method="create"):
        """
            Helper to run the onvalidation routine for a record

            @param table: the Table
            @param record: the FORM or the Row to validate
            @param method: the method
        """

        if hasattr(table, "_tablename"):
            tablename = table._tablename
        else:
            tablename = table

        onvalidation = cls.get_config(tablename, "%s_onvalidation" % method,
                       cls.get_config(tablename, "onvalidation"))
        if "vars" not in record:
            record = Storage(vars=Storage(record), errors=Storage())
        if onvalidation:
            callback(onvalidation, record, tablename=tablename)
        return record.errors

    # -------------------------------------------------------------------------
    # Resource components
    #--------------------------------------------------------------------------
    @classmethod
    def add_components(cls, master, **links):
        """
            Configure component links for a master table.

            @param master: the name of the master table
            @param links: component link configurations
        """

        components = current.model["components"]
        load_all_models = current.response.s3.load_all_models

        master = master._tablename if type(master) is Table else master

        hooks = components.get(master)
        if hooks is None:
            hooks = {}
        for tablename, ll in links.items():

            name = tablename.split("_", 1)[1]
            if not isinstance(ll, (tuple, list)):
                ll = [ll]

            for link in ll:

                if isinstance(link, str):
                    alias = name

                    pkey = None
                    fkey = link
                    linktable = None
                    lkey = None
                    rkey = None
                    actuate = None
                    autodelete = False
                    autocomplete = None
                    defaults = None
                    multiple = True
                    filterby = None
                    # @ToDo: use these as fallback for RHeader Tabs on Web App
                    #        (see S3ComponentTab.__init__)
                    label = None
                    plural = None

                elif isinstance(link, dict):
                    alias = link.get("name", name)

                    joinby = link.get("joinby")
                    if not joinby:
                        continue

                    linktable = link.get("link")
                    linktable = linktable._tablename \
                                if type(linktable) is Table else linktable

                    if load_all_models:
                        # Warn for redeclaration of components (different table
                        # under the same alias) - this is wrong most of the time,
                        # even though it would produce valid+consistent results:
                        if alias in hooks and hooks[alias].tablename != tablename:
                            current.log.warning("Redeclaration of component (%s.%s)" %
                                              (master, alias))

                        # Ambiguous aliases can cause accidental deletions and
                        # other serious integrity problems, so we warn for ambiguous
                        # aliases (not raising exceptions just yet because there
                        # are a number of legacy cases),
                        # Currently only logging during load_all_models to not
                        # completely submerge other important log messages
                        if linktable and alias == linktable.split("_", 1)[1]:
                            # @todo: fix legacy cases (e.g. renaming the link tables)
                            # @todo: raise Exception once all legacy cases are fixed
                            current.log.warning("Ambiguous link/component alias (%s.%s)" %
                                                (master, alias))
                        if alias == master.split("_", 1)[1]:
                            # No legacy cases, so crash to prevent introduction of any
                            raise SyntaxError("Ambiguous master/component alias (%s.%s)" %
                                              (master, alias))

                    pkey = link.get("pkey")
                    if linktable is None:
                        lkey = None
                        rkey = None
                        fkey = joinby
                    else:
                        lkey = joinby
                        rkey = link.get("key")
                        if not rkey:
                            continue
                        fkey = link.get("fkey")

                    actuate = link.get("actuate")
                    autodelete = link.get("autodelete", False)
                    autocomplete = link.get("autocomplete")
                    defaults = link.get("defaults")
                    multiple = link.get("multiple", True)
                    filterby = link.get("filterby")
                    label = link.get("label")
                    plural = link.get("plural")

                else:
                    continue

                component = Storage(tablename = tablename,
                                    pkey = pkey,
                                    fkey = fkey,
                                    linktable = linktable,
                                    lkey = lkey,
                                    rkey = rkey,
                                    actuate = actuate,
                                    autodelete = autodelete,
                                    autocomplete = autocomplete,
                                    defaults = defaults,
                                    multiple = multiple,
                                    filterby = filterby,
                                    label = label,
                                    plural = plural,
                                    )
                hooks[alias] = component

        components[master] = hooks

    # -------------------------------------------------------------------------
    @classmethod
    def add_dynamic_components(cls, tablename, exclude=None):
        """
            Helper function to look up and declare dynamic components
            for a table; called by get_components if dynamic_components
            is configured for the table

            @param tablename: the table name
            @param exclude: names to exclude (static components)
        """

        mtable = cls.table(tablename)
        if mtable is None:
            return

        if cls.get_config(tablename, "dynamic_components_loaded"):
            # Already loaded
            return

        ttable = cls.table("s3_table")
        ftable = cls.table("s3_field")

        join = ttable.on(ttable.id == ftable.table_id)
        query = (ftable.master == tablename) & \
                (ftable.component_key == True) & \
                (ftable.deleted == False)
        rows = current.db(query).select(ftable.name,
                                        ftable.field_type,
                                        ftable.component_alias,
                                        ftable.settings,
                                        ttable.name,
                                        join = join,
                                        )

        # Don't do this again during the same request cycle
        cls.configure(tablename, dynamic_components_loaded=True)

        components = {}
        for row in rows:

            hook = {}

            ctable = row["s3_table"]
            ctablename = ctable.name
            default_alias = ctablename.split("_", 1)[-1]

            field = row["s3_field"]
            alias = field.component_alias

            if not alias:
                alias = default_alias
            if exclude and alias in exclude:
                continue

            if alias != default_alias:
                hook["name"] = alias

            hook["joinby"] = field.name

            settings = field.settings
            if settings:
                multiple = settings.get("component_multiple", DEFAULT)
                if multiple is not DEFAULT:
                    hook["multiple"] = multiple

            # Get the primary key
            field_type = field.field_type
            if field_type[:10] == "reference ":
                ktablename = field_type.split(" ", 1)[1]
                if "." in ktablename:
                    ktablename, pkey = ktablename.split(".", 1)[1]
                    if pkey and pkey != mtable._id.name:
                        hook["pkey"] = pkey

            components[ctablename] = hook

        if components:
            cls.add_components(tablename, **components)

    # -------------------------------------------------------------------------
    @classmethod
    def get_component(cls, table, alias):
        """
            Get a component description for a component alias

            @param table: the master table
            @param alias: the component alias

            @returns: the component description (Storage)
        """
        return cls.parse_hook(table, alias)

    # -------------------------------------------------------------------------
    @classmethod
    def get_components(cls, table, names=None):
        """
            Finds components of a table

            @param table: the table or table name
            @param names: a list of components names to limit the search to,
                          None for all available components

            @returns: the component descriptions (Storage {alias: description})
        """

        table, hooks = cls.get_hooks(table, names=names)

        # Build component-objects for each hook
        components = Storage()
        if table and hooks:
            for alias in hooks:
                component = cls.parse_hook(table, alias, hook=hooks[alias])
                if component:
                    components[alias] = component

        return components

    # -------------------------------------------------------------------------
    @classmethod
    def parse_hook(cls, table, alias, hook=None):
        """
            Parse a component configuration, loading all necessary table
            models and applying defaults

            @param table: the master table
            @param alias: the component alias
            @param hook: the component configuration (if already known)

            @returns: the component description (Storage {key: value})
        """

        load = cls.table

        if hook is None:
            table, hooks = cls.get_hooks(table, names=[alias])
            if hooks and alias in hooks:
                hook = hooks[alias]
            else:
                return None

        tn = hook.tablename
        lt = hook.linktable

        ctable = load(tn)
        if ctable is None:
            return None

        if lt:
            ltable = load(lt)
            if ltable is None:
                return None
        else:
            ltable = None

        prefix, name = tn.split("_", 1)
        component = Storage(defaults = hook.defaults,
                            multiple = hook.multiple,
                            tablename = tn,
                            table = ctable,
                            prefix = prefix,
                            name = name,
                            alias = alias,
                            label = hook.label,
                            plural = hook.plural,
                            )

        if hook.supertable is not None:
            joinby = hook.supertable._id.name
        else:
            joinby = hook.fkey

        if hook.pkey is None:
            if hook.supertable is not None:
                component.pkey = joinby
            else:
                component.pkey = table._id.name
        else:
            component.pkey = hook.pkey

        if ltable is not None:

            if hook.actuate:
                component.actuate = hook.actuate
            else:
                component.actuate = "link"
            component.linktable = ltable

            if hook.fkey is None:
                component.fkey = ctable._id.name
            else:
                component.fkey = hook.fkey

            component.lkey = hook.lkey
            component.rkey = hook.rkey
            component.autocomplete = hook.autocomplete
            component.autodelete = hook.autodelete

        else:
            component.linktable = None
            component.fkey = hook.fkey
            component.lkey = component.rkey = None
            component.actuate = None
            component.autocomplete = None
            component.autodelete = None

        if hook.filterby is not None:
            component.filterby = hook.filterby

        return component

    # -------------------------------------------------------------------------
    @classmethod
    def get_hooks(cls, table, names=None):
        """
            Find applicable component configurations (hooks) for a table

            @param table: the master table (or table name)
            @param names: component aliases to find (default: all configured
                          components for the master table)

            @returns: tuple (table, {alias: hook, ...})
        """

        components = current.model["components"]
        load = cls.table

        # Get tablename and table
        if type(table) is Table:
            tablename = original_tablename(table)
        else:
            tablename = table
            table = load(tablename)
            if table is None:
                # Primary table not defined
                return None, None

        # Single alias?
        if isinstance(names, str):
            names = set([names])
        elif names is not None:
            names = set(names)

        hooks = {}
        get_hooks = cls.__filter_hooks
        supertables = None

        # Get hooks for direct components
        direct_components = components.get(tablename)
        if direct_components:
            names = get_hooks(hooks, direct_components, names=names)

        if names is None or names:
            # Add hooks for super-components
            supertables = cls.get_config(tablename, "super_entity")
            if supertables:
                if not isinstance(supertables, (list, tuple)):
                    supertables = [supertables]
                for s in supertables:
                    if isinstance(s, str):
                        s = load(s)
                    if s is None:
                        continue
                    super_components = components.get(s._tablename)
                    if super_components:
                        names = get_hooks(hooks, super_components,
                                          names = names,
                                          supertable = s,
                                          )

        dynamic_components =  cls.get_config(tablename, "dynamic_components")
        if dynamic_components:

            if names is None or names:
                # Add hooks for dynamic components
                cls.add_dynamic_components(tablename, exclude=hooks)
                direct_components = components.get(tablename)
                if direct_components:
                    names = get_hooks(hooks, direct_components, names=names)

            if supertables and (names is None or names):
                # Add hooks for dynamic super-components
                for s in supertables:
                    if isinstance(s, str):
                        s = load(s)
                    if s is None:
                        continue
                    cls.add_dynamic_components(s._tablename, exclude=hooks)
                    super_components = components.get(s._tablename)
                    if super_components:
                        names = get_hooks(hooks, super_components,
                                          names = names,
                                          supertable = s,
                                          )

        return table, hooks

    # -------------------------------------------------------------------------
    @classmethod
    def __filter_hooks(cls, components, hooks, names=None, supertable=None):
        """
            DRY Helper method to filter component hooks

            @param components: components already found, dict {alias: component}
            @param hooks: component hooks to filter, dict {alias: hook}
            @param names: the names (=aliases) to include
            @param supertable: the super-table name to set for the component

            @returns: set of names that could not be found,
                      or None if names was None
        """

        for alias in hooks:
            if alias in components or \
               names is not None and alias not in names:
                continue
            hook = hooks[alias]
            hook["supertable"] = supertable
            components[alias] = hook

        return set(names) - set(hooks) if names is not None else None

    # -------------------------------------------------------------------------
    @classmethod
    def has_components(cls, table):
        """
            Checks whether there are components defined for a table

            @param table: the table or table name
        """

        components = current.model["components"]
        load = cls.table

        # Get tablename and table
        if type(table) is Table:
            tablename = table._tablename
        else:
            tablename = table
            table = load(tablename)
            if table is None:
                return False

        # Attach dynamic components
        if cls.get_config(tablename, "dynamic_components"):
            cls.add_dynamic_components(tablename)

        # Get table hooks
        hooks = {}
        filter_hooks = cls.__filter_hooks
        h = components.get(tablename, None)
        if h:
            filter_hooks(hooks, h)
        if len(hooks):
            return True

        # Check for super-components
        # FIXME: add dynamic components for super-table?
        supertables = cls.get_config(tablename, "super_entity")
        if supertables:
            if not isinstance(supertables, (list, tuple)):
                supertables = [supertables]
            for s in supertables:
                if isinstance(s, str):
                    s = load(s)
                if s is None:
                    continue
                h = components.get(s._tablename, None)
                if h:
                    filter_hooks(hooks, h, supertable=s)
            if len(hooks):
                return True

        # No components found
        return False

    # -------------------------------------------------------------------------
    @classmethod
    def get_alias(cls, tablename, link):
        """
            Find a component alias from the link table alias.

            @param tablename: the name of the master table
            @param link: the alias of the link table
        """

        components = current.model["components"]

        table = cls.table(tablename)
        if not table:
            return None

        def get_alias(hooks, link):

            if link[-6:] == "__link":
                alias = link.rsplit("__link", 1)[0]
                hook = hooks.get(alias)
                if hook:
                    return alias
            else:
                for alias in hooks:
                    hook = hooks[alias]
                    if hook.linktable:
                        name = hook.linktable.split("_", 1)[1]
                        if name == link:
                            return alias
            return None

        hooks = components.get(tablename)
        if hooks:
            alias = get_alias(hooks, link)
            if alias:
                return alias

        supertables = cls.get_config(tablename, "super_entity")
        if supertables:
            if not isinstance(supertables, (list, tuple)):
                supertables = [supertables]
            for s in supertables:
                table = cls.table(s)
                if table is None:
                    continue
                hooks = components.get(table._tablename)
                if hooks:
                    alias = get_alias(hooks, link)
                    if alias:
                        return alias
        return None

    # -------------------------------------------------------------------------
    @classmethod
    def hierarchy_link(cls, tablename):
        """
            Get the alias of the component that represents the parent
            node in a hierarchy (for link-table based hierarchies)

            @param tablename: the table name

            @returns: the alias of the hierarchy parent component
        """

        if not cls.table(tablename, db_only=True):
            return None

        hierarchy_link = cls.get_config(tablename, "hierarchy_link")
        if not hierarchy_link:

            hierarchy = cls.get_config(tablename, "hierarchy")
            if hierarchy and "." in hierarchy:
                alias = hierarchy.rsplit(".", 1)[0]
                if "__link" in alias:
                    hierarchy_link = alias.rsplit("__link", 1)[0]

        return hierarchy_link

    # -------------------------------------------------------------------------
    # Resource Methods
    # -------------------------------------------------------------------------
    @classmethod
    def set_method(cls, prefix, name,
                   component_name = None,
                   method = None,
                   action = None,
                   ):
        """
            Adds a custom method for a resource or component

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component
            @param method: name of the method
            @param action: function to invoke for this method
        """

        methods = current.model["methods"]
        cmethods = current.model["cmethods"]

        if not method:
            raise SyntaxError("No method specified")

        tablename = "%s_%s" % (prefix, name)

        if not component_name:
            if method not in methods:
                methods[method] = {}
            methods[method][tablename] = action
        else:
            if method not in cmethods:
                cmethods[method] = {}
            if component_name not in cmethods[method]:
                cmethods[method][component_name] = {}
            cmethods[method][component_name][tablename] = action

    # -------------------------------------------------------------------------
    @classmethod
    def get_method(cls, prefix, name,
                   component_name=None,
                   method=None):
        """
            Retrieves a custom method for a resource or component

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component
            @param method: name of the method
        """

        methods = current.model["methods"]
        cmethods = current.model["cmethods"]

        if not method:
            return None

        tablename = "%s_%s" % (prefix, name)

        if not component_name:
            if method in methods and tablename in methods[method]:
                return methods[method][tablename]
            else:
                return None
        else:
            if method in cmethods and \
               component_name in cmethods[method] and \
               tablename in cmethods[method][component_name]:
                return cmethods[method][component_name][tablename]
            else:
                return None

    # -------------------------------------------------------------------------
    # Super-Entity API
    # -------------------------------------------------------------------------
    @classmethod
    def super_entity(cls, tablename, key, types, *fields, **args):
        """
            Define a super-entity table

            @param tablename: the tablename
            @param key: name of the primary key
            @param types: a dictionary of instance types
            @param fields: any shared fields
            @param args: table arguments (e.g. migrate)
        """

        db = current.db
        if db._dbname == "postgres":
            sequence_name = "%s_%s_seq" % (tablename, key)
        else:
            sequence_name = None

        table = db.define_table(tablename,
                                Field(key, "id",
                                      readable=False,
                                      writable=False),
                                Field("deleted", "boolean",
                                      readable=False,
                                      writable=False,
                                      default=False),
                                Field("instance_type",
                                      represent = lambda opt: \
                                        types.get(opt, opt) or \
                                            current.messages["NONE"],
                                      readable=False,
                                      writable=False),
                                Field("uuid", length=128,
                                      readable=False,
                                      writable=False),
                                sequence_name=sequence_name,
                                *fields, **args)

        return table

    # -------------------------------------------------------------------------
    @classmethod
    def super_key(cls, supertable, default=None):
        """
            Get the name of the key for a super-entity

            @param supertable: the super-entity table
        """

        if supertable is None and default:
            return default
        if isinstance(supertable, str):
            supertable = cls.table(supertable)
        try:
            return supertable._id.name
        except AttributeError:
            pass
        raise SyntaxError("No id-type key found in %s" % supertable._tablename)

    # -------------------------------------------------------------------------
    @classmethod
    def super_link(cls,
                   name,
                   supertable,
                   label = None,
                   comment = None,
                   represent = None,
                   orderby = None,
                   sort = True,
                   filterby = None,
                   filter_opts = None,
                   not_filterby = None,
                   not_filter_opts = None,
                   instance_types = None,
                   realms = None,
                   updateable = False,
                   groupby = None,
                   script = None,
                   widget = None,
                   empty = True,
                   default = DEFAULT,
                   ondelete = "CASCADE",
                   readable = False,
                   writable = False,
                   ):
        """
            Get a foreign key field for a super-entity

            @param supertable: the super-entity table
            @param label: label for the field
            @param comment: comment for the field
            @param readable: set the field readable
            @param represent: set a representation function for the field
        """

        if isinstance(supertable, str):
            supertable = cls.table(supertable)

        if supertable is None:
            if name is not None:
                return Field(name,
                             "integer",
                             readable = False,
                             writable = False,
                             )
            else:
                raise SyntaxError("Undefined super-entity")

        try:
            key = supertable._id.name
        except AttributeError:
            raise SyntaxError("No id-type key found in %s" %
                              supertable._tablename)

        if name is not None and name != key:
            raise SyntaxError("Primary key %s not found in %s" %
                             (name, supertable._tablename))

        requires = IS_ONE_OF(current.db,
                             "%s.%s" % (supertable._tablename, key),
                             represent,
                             orderby = orderby,
                             sort = sort,
                             groupby = groupby,
                             filterby = filterby,
                             filter_opts = filter_opts,
                             instance_types = instance_types,
                             realms = realms,
                             updateable = updateable,
                             not_filterby = not_filterby,
                             not_filter_opts = not_filter_opts,
                             )
        if empty:
            requires = IS_EMPTY_OR(requires)

        # Add the script into the comment
        if script:
            if comment:
                comment = TAG[""](comment, S3ScriptItem(script=script))
            else:
                comment = S3ScriptItem(script=script)

        return Field(key,
                     supertable,
                     default = default,
                     requires = requires,
                     readable = readable,
                     writable = writable,
                     label = label,
                     comment = comment,
                     represent = represent,
                     widget = widget,
                     ondelete = ondelete,
                     )

    # -------------------------------------------------------------------------
    @classmethod
    def update_super(cls, table, record):
        """
            Updates the super-entity links of an instance record

            @param table: the instance table
            @param record: the instance record
        """

        get_config = cls.get_config

        # Get all super-entities of this table
        tablename = original_tablename(table)
        supertables = get_config(tablename, "super_entity")
        if not supertables:
            return False

        # Get the record
        record_id = record.get("id", None)
        if not record_id:
            return False

        # Find all super-tables, super-keys and shared fields
        if not isinstance(supertables, (list, tuple)):
            supertables = [supertables]
        updates = []
        fields = []
        has_deleted = "deleted" in table.fields
        has_uuid = "uuid" in table.fields

        for s in supertables:
            # Get the supertable and the corresponding superkey
            if type(s) is not Table:
                s = cls.table(s)
            if s is None:
                continue
            tn = s._tablename
            key = cls.super_key(s)
            protected = [key]

            # Fields in the supertable that shall not be treated as
            # shared fields (i.e. must not be overridden by instance
            # values)
            not_shared = get_config(tn, "no_shared_fields")
            if isinstance(not_shared, (tuple, list)):
                protected.extend(not_shared)

            # Shared fields
            shared = get_config(tablename, "%s_fields" % tn)
            if shared:
                # Instance table specifies a specific field mapping
                # {superfield: instfield} for this supertable
                shared = {fn: shared[fn] for fn in shared
                                         if fn not in protected and \
                                            fn in s.fields and \
                                            shared[fn] in table.fields}
            else:
                # All fields the supertable and instance table have
                # in common, except protected fields
                shared = {fn: fn for fn in s.fields
                                 if fn not in protected and \
                                    fn in table.fields}
            fields.extend(shared.values())
            fields.append(key)
            updates.append((tn, s, key, shared))

        # Get the record data
        db = current.db
        if has_deleted:
            fields.append("deleted")
        if has_uuid:
            fields.append("uuid")
        fields = [ogetattr(table, fn) for fn in list(set(fields))]
        _record = db(table.id == record_id).select(limitby=(0, 1),
                                                   *fields).first()
        if not _record:
            return False

        super_keys = {}
        for tn, s, key, shared in updates:
            data = Storage([(fn, _record[shared[fn]]) for fn in shared])
            data.instance_type = tablename
            if has_deleted:
                data.deleted = _record.get("deleted", False)
            if has_uuid:
                data.uuid = _record.get("uuid", None)

            # Do we already have a super-record?
            skey = ogetattr(_record, key)
            if skey:
                query = (s[key] == skey)
                row = db(query).select(s._id, limitby=(0, 1)).first()
            else:
                row = None

            if row:
                # Update the super-entity record
                db(s._id == skey).update(**data)
                super_keys[key] = skey
                data[key] = skey
                form = Storage(vars=data)
                onaccept = get_config(tn, "update_onaccept",
                           get_config(tn, "onaccept", None))
                if onaccept:
                    onaccept(form)
            else:
                # Insert a new super-entity record
                k = s.insert(**data)
                if k:
                    super_keys[key] = k
                    data[key] = k
                    onaccept = get_config(tn, "create_onaccept",
                               get_config(tn, "onaccept", None))
                    if onaccept:
                        form = Storage(vars=data)
                        onaccept(form)

        # Update the super_keys in the record
        if super_keys:
            # System update => don't update modified_by/on
            if "modified_on" in table.fields:
                super_keys["modified_by"] = table.modified_by
                super_keys["modified_on"] = table.modified_on
            db(table.id == record_id).update(**super_keys)

        record.update(super_keys)
        return True

    # -------------------------------------------------------------------------
    @classmethod
    def delete_super(cls, table, record):
        """
            Removes the super-entity links of an instance record

            @param table: the instance table
            @param record: the instance record

            @return: True if successful, otherwise False (caller must
                     roll back the transaction if False is returned!)
        """

        # Must have a record ID
        record_id = record.get(table._id.name, None)
        if not record_id:
            raise RuntimeError("Record ID required for delete_super")

        # Get all super-tables
        get_config = cls.get_config
        supertables = get_config(original_tablename(table), "super_entity")

        # None? Ok - done!
        if not supertables:
            return True
        if not isinstance(supertables, (list, tuple)):
            supertables = [supertables]

        # Get the keys for all super-tables
        keys = {}
        load = {}
        for sname in supertables:
            stable = cls.table(sname) if isinstance(sname, str) else sname
            if stable is None:
                continue
            key = stable._id.name
            if key in record:
                keys[stable._tablename] = (key, record[key])
            else:
                load[stable._tablename] = key

        # If necessary, load missing keys
        if load:
            row = current.db(table._id == record_id).select(
                    table._id, *load.values(), limitby=(0, 1)).first()
            for sname, key in load.items():
                keys[sname] = (key, row[key])

        # Delete super-records
        define_resource = current.s3db.resource
        update_record = record.update_record
        for sname in keys:
            key, value = keys[sname]
            if not value:
                # Skip if we don't have a super-key
                continue

            # Remove the super key
            update_record(**{key: None})

            # Delete the super record
            sresource = define_resource(sname, id=value)
            deleted = sresource.delete(cascade=True, log_errors=True)

            if not deleted or sresource.error:
                # Restore the super key
                # @todo: is this really necessary? => caller must roll back
                #        anyway in this case, which would automatically restore
                update_record(**{key: value})
                return False

        return True

    # -------------------------------------------------------------------------
    @classmethod
    def get_super_keys(cls, table):
        """
            Get the super-keys in an instance table

            @param table: the instance table
            @returns: list of field names
        """

        tablename = original_tablename(table)

        supertables = cls.get_config(tablename, "super_entity")
        if not supertables:
            return []
        if not isinstance(supertables, (list, tuple)):
            supertables = [supertables]

        keys = []
        append = keys.append
        for s in supertables:
            if type(s) is not Table:
                s = cls.table(s)
            if s is None:
                continue
            key = s._id.name
            if key in table.fields:
                append(key)

        return keys

    # -------------------------------------------------------------------------
    @classmethod
    def get_instance(cls, supertable, superid):
        """
            Get prefix, name and ID of an instance record

            @param supertable: the super-entity table
            @param superid: the super-entity record ID
            @return: a tuple (prefix, name, ID) of the instance
                      record (if it exists)
        """

        if not hasattr(supertable, "_tablename"):
            # tablename passed instead of Table
            supertable = cls.table(supertable)
        if supertable is None:
            return (None, None, None)
        db = current.db
        query = (supertable._id == superid)
        entry = db(query).select(supertable.instance_type,
                                 supertable.uuid,
                                 limitby = (0, 1)
                                 ).first()
        if entry:
            instance_type = entry.instance_type
            prefix, name = instance_type.split("_", 1)
            instancetable = current.s3db[entry.instance_type]
            query = (instancetable.uuid == entry.uuid)
            record = db(query).select(instancetable.id,
                                      limitby = (0, 1)
                                      ).first()
            if record:
                return (prefix, name, record.id)
        return (None, None, None)

# =============================================================================
class S3DynamicModel(object):
    """
        Class representing a dynamic table model
    """

    def __init__(self, tablename):
        """
            Constructor

            @param tablename: the table name
        """

        self.tablename = tablename
        table = self.define_table(tablename)
        if table:
            self.table = table
        else:
            raise AttributeError("Undefined dynamic model: %s" % tablename)

    # -------------------------------------------------------------------------
    def define_table(self, tablename):
        """
            Instantiate a dynamic Table

            @param tablename: the table name

            @return: a Table instance
        """

        # Is the table already defined?
        db = current.db
        redefine = tablename in db

        # Load the table model
        s3db = current.s3db
        ttable = s3db.s3_table
        ftable = s3db.s3_field
        query = (ttable.name == tablename) & \
                (ttable.deleted == False) & \
                (ftable.table_id == ttable.id)
        rows = db(query).select(ftable.name,
                                ftable.field_type,
                                ftable.label,
                                ftable.require_unique,
                                ftable.require_not_empty,
                                ftable.options,
                                ftable.default_value,
                                ftable.settings,
                                ftable.comments,
                                )
        if not rows:
            return None

        # Instantiate the fields
        fields = []
        for row in rows:
            field = self._field(tablename, row)
            if field:
                fields.append(field)

        # Automatically add standard meta-fields
        from .s3fields import s3_meta_fields
        fields.extend(s3_meta_fields())

        # Define the table
        if fields:
            # Enable migrate
            # => is globally disabled when settings.base.migrate
            #    is False, overriding the table parameter
            migrate_enabled = db._migrate_enabled
            db._migrate_enabled = True

            # Define the table
            db.define_table(tablename,
                            migrate = True,
                            redefine = redefine,
                            *fields)

            # Instantiate table
            # => otherwise lazy_tables may prevent it
            table = db[tablename]

            # Restore global migrate_enabled
            db._migrate_enabled = migrate_enabled

            # Configure the table
            self._configure(tablename)

            return table
        else:
            return None

    # -------------------------------------------------------------------------
    @staticmethod
    def _configure(tablename):
        """
            Configure the table (e.g. CRUD strings)
        """

        s3db = current.s3db

        # Load table configuration settings
        ttable = s3db.s3_table
        query = (ttable.name == tablename) & \
                (ttable.deleted == False)
        row = current.db(query).select(ttable.title,
                                       ttable.settings,
                                       limitby = (0, 1)
                                       ).first()
        if row:
            # Configure CRUD strings
            title = row.title
            if title:
                current.response.s3.crud_strings[tablename] = Storage(
                    title_list = current.T(title),
                    )

            # Table Configuration
            settings = row.settings
            if settings:

                config = {"orderby": "%s.created_on" % tablename,
                          }

                # CRUD Form
                crud_fields = settings.get("form")
                if crud_fields:
                    from .s3forms import S3SQLCustomForm
                    try:
                        crud_form = S3SQLCustomForm(**crud_fields)
                    except:
                        pass
                    else:
                        config["crud_form"] = crud_form

                # Mobile Form
                mobile_form = settings.get("mobile_form")
                if type(mobile_form) is list:
                    config["mobile_form"] = mobile_form

                # JSON-serializable config options can be configured
                # without pre-processing
                for key in SERIALIZABLE_OPTS:
                    setting = settings.get(key)
                    if setting:
                        config[key] = setting

                # Apply config
                if config:
                    s3db.configure(tablename, **config)

    # -------------------------------------------------------------------------
    @classmethod
    def _field(cls, tablename, row):
        """
            Convert a s3_field Row into a Field instance

            @param tablename: the table name
            @param row: the s3_field Row

            @return: a Field instance
        """

        field = None

        if row:

            # Type-specific field constructor
            fieldtype = row.field_type
            if row.options:
                construct = cls._options_field
            elif fieldtype == "date":
                construct = cls._date_field
            elif fieldtype == "datetime":
                construct = cls._datetime_field
            elif fieldtype[:9] == "reference":
                construct = cls._reference_field
            elif fieldtype == "boolean":
                construct = cls._boolean_field
            elif fieldtype in ("integer", "double"):
                construct = cls._numeric_field
            elif fieldtype == "json":
                construct = cls._json_field
            else:
                construct = cls._generic_field

            field = construct(tablename, row)
            if not field:
                return None

            requires = field.requires

            # Handle require_not_empty
            if fieldtype != "boolean":
                if row.require_not_empty:
                    if not requires:
                        requires = IS_NOT_EMPTY()
                elif requires:
                    requires = IS_EMPTY_OR(requires)

            field.requires = requires

            # Field label and comment
            T = current.T
            label = row.label
            if not label:
                fieldname = row.name
                label = " ".join(s.capitalize() for s in fieldname.split("_"))
            if label:
                field.label = T(label)
            comments = row.comments
            if comments:
                field.comment = T(comments)

            # Field settings
            settings = row.settings
            if settings:
                field.s3_settings = settings

        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _generic_field(tablename, row):
        """
            Generic field constructor

            @param tablename: the table name
            @param row: the s3_field Row

            @return: the Field instance
        """

        fieldname = row.name
        fieldtype = row.field_type

        multiple = fieldtype[:5] == "list:"

        if row.require_unique and not multiple:
            from .s3validators import IS_NOT_ONE_OF
            requires = IS_NOT_ONE_OF(current.db, "%s.%s" % (tablename,
                                                            fieldname,
                                                            ),
                                     )
        else:
            requires = None

        if fieldtype in ("string", "text"):
            default = row.default_value
            settings = row.settings or {}
            widget = settings.get("widget")
            if widget == "richtext":
                widget = s3_richtext_widget
            elif widget == "comments":
                widget = s3_comments_widget
            else:
                widget = None
        else:
            default = None
            widget = None

        field = Field(fieldname, fieldtype,
                      default = default,
                      requires = requires,
                      widget = widget,
                      )
        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _options_field(tablename, row):
        """
            Options-field constructor

            @param tablename: the table name
            @param row: the s3_field Row

            @return: the Field instance
        """

        fieldname = row.name
        fieldtype = row.field_type
        fieldopts = row.options

        settings = row.settings or {}

        # Always translate options unless translate_options is False
        translate = settings.get("translate_options", True)
        T = current.T

        from .s3utils import s3_str

        multiple = fieldtype[:5] == "list:"
        sort = False
        zero = ""

        if isinstance(fieldopts, dict):
            options = fieldopts
            if translate:
                options = {k: T(v) for k, v in options.items()}
            options_dict = options
            # Sort options unless sort_options is False (=default True)
            sort = settings.get("sort_options", True)

        elif isinstance(fieldopts, list):
            options = []
            for opt in fieldopts:
                if isinstance(opt, (tuple, list)) and len(opt) >= 2:
                    k, v = opt[:2]
                else:
                    k, v = opt, s3_str(opt)
                if translate:
                    v = T(v)
                options.append((k, v))
            options_dict = dict(options)
            # Retain list order unless sort_options is True (=default False)
            sort = settings.get("sort_options", False)

        else:
            options_dict = options = {}

        # Apply default value (if it is a valid option)
        default = row.default_value
        if default is not None:
            if multiple:
                if default and default[0] == "[":
                    # Attempt to JSON-parse the default value
                    import json
                    from .s3validators import JSONERRORS
                    try:
                        default = json.loads(default)
                    except JSONERRORS:
                        pass
                if not isinstance(default, list):
                    default = [default]
                zero = None
            elif s3_str(default) in (s3_str(k) for k in options_dict):
                # No zero-option if we have a default value and
                # the field must not be empty:
                zero = None if row.require_not_empty else ""
            else:
                default = None

        # Widget?
        widget = settings.get("widget")
        len_options = len(options)
        if multiple:
            if widget and widget == "groupedopts" or \
               not widget and len_options < 8:
                from .s3widgets import S3GroupedOptionsWidget
                widget = S3GroupedOptionsWidget(cols=4)
            else:
                from .s3widgets import S3MultiSelectWidget
                widget = S3MultiSelectWidget()
        elif widget and widget == "radio" or \
             not widget and len_options < 4:
            widget = lambda field, value: \
                         SQLFORM.widgets.radio.widget(field,
                                                      value,
                                                      cols = len_options,
                                                      )
        else:
            widget = None

        if multiple and row.require_not_empty and len_options:
            # Require at least one option selected, otherwise
            # IS_IN_SET will pass with no options selected:
            multiple = (1, len_options + 1)

        from .s3fields import S3Represent
        field = Field(fieldname, fieldtype,
                      default = default,
                      represent = S3Represent(options = options_dict,
                                              multiple = multiple,
                                              translate = translate,
                                              ),
                      requires = IS_IN_SET(options,
                                           multiple = multiple,
                                           sort = sort,
                                           zero = zero,
                                           ),
                      widget = widget,
                      )
        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _date_field(tablename, row):
        """
            Date field constructor

            @param tablename: the table name
            @param row: the s3_field Row

            @return: the Field instance
        """

        fieldname = row.name
        settings = row.settings or {}

        attr = {}
        for keyword in ("past", "future"):
            setting = settings.get(keyword, DEFAULT)
            if setting is not DEFAULT:
                attr[keyword] = setting
        attr["empty"] = False

        default = row.default_value
        if default:
            if default == "now":
                attr["default"] = default
            else:
                from .s3datetime import s3_decode_iso_datetime
                try:
                    dt = s3_decode_iso_datetime(default)
                except ValueError:
                    # Ignore
                    pass
                else:
                    attr["default"] = dt.date()

        from .s3fields import s3_date
        field = s3_date(fieldname, **attr)

        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _datetime_field(tablename, row):
        """
            DateTime field constructor

            @param tablename: the table name
            @param row: the s3_field Row

            @return: the Field instance
        """

        fieldname = row.name
        settings = row.settings or {}

        attr = {}
        for keyword in ("past", "future"):
            setting = settings.get(keyword, DEFAULT)
            if setting is not DEFAULT:
                attr[keyword] = setting
        attr["empty"] = False

        default = row.default_value
        if default:
            if default == "now":
                attr["default"] = default
            else:
                from .s3datetime import s3_decode_iso_datetime
                try:
                    dt = s3_decode_iso_datetime(default)
                except ValueError:
                    # Ignore
                    pass
                else:
                    attr["default"] = dt

        from .s3fields import s3_datetime
        field = s3_datetime(fieldname, **attr)

        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _reference_field(tablename, row):
        """
            Reference field constructor

            @param tablename: the table name
            @param row: the s3_field Row

            @return: the Field instance
        """

        fieldname = row.name
        fieldtype = row.field_type

        ktablename = fieldtype.split(" ", 1)[1].split(".", 1)[0]
        ktable = current.s3db.table(ktablename)
        if ktable:
            from .s3fields import S3Represent
            if "name" in ktable.fields:
                represent = S3Represent(lookup = ktablename,
                                        translate = True,
                                        )
            else:
                represent = None
            requires = IS_ONE_OF(current.db, str(ktable._id),
                                 represent,
                                 )
            field = Field(fieldname, fieldtype,
                          represent = represent,
                          requires = requires,
                          )
        else:
            field = None

        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _numeric_field(tablename, row):
        """
            Numeric field constructor

            @param tablename: the table name
            @param row: the s3_field Row

            @return: the Field instance
        """

        fieldname = row.name
        fieldtype = row.field_type

        settings = row.settings or {}
        minimum = settings.get("min")
        maximum = settings.get("max")

        if fieldtype == "integer":
            parse = int
            requires = IS_INT_IN_RANGE(minimum = minimum,
                                       maximum = maximum,
                                       )
        elif fieldtype == "double":
            parse = float
            requires = IS_FLOAT_IN_RANGE(minimum = minimum,
                                         maximum = maximum,
                                         )
        else:
            parse = None
            requires = None

        default = row.default_value
        if default and parse is not None:
            try:
                default = parse(default)
            except ValueError:
                default = None
        else:
            default = None

        field = Field(fieldname, fieldtype,
                      default = default,
                      requires = requires,
                      )
        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _boolean_field(tablename, row):
        """
            Boolean field constructor

            @param tablename: the table name
            @param row: the s3_field Row

            @return: the Field instance
        """

        fieldname = row.name
        fieldtype = row.field_type

        default = row.default_value
        if default:
            default = default.lower()
            if default == "true":
                default = True
            elif default == "none":
                default = None
            else:
                default = False
        else:
            default = False

        settings = row.settings or {}

        # NB no IS_EMPTY_OR for boolean-fields:
        # => NULL values in SQL are neither True nor False, so always
        #    require special handling; to prevent that, we remove the
        #    default IS_EMPTY_OR and always set a default
        # => DAL converts everything that isn't True to False anyway,
        #    so accepting an empty selection would create an
        #    implicit default with no visible feedback (poor UX)

        widget = settings.get("widget")
        if widget == "radio":
            # Render two radio-buttons Yes|No
            T = current.T
            requires = [IS_IN_SET(OrderedDict([(True, T("Yes")),
                                               (False, T("No")),
                                               ]),
                                  # better than "Value not allowed"
                                  error_message = T("Please select a value"),
                                  ),
                        # Form option comes in as str
                        # => convert to boolean
                        lambda v: (str(v) == "True", None),
                        ]
            widget = lambda field, value: \
                     SQLFORM.widgets.radio.widget(field, value, cols=2)
        else:
            # Remove default IS_EMPTY_OR
            requires = None

            # Default single checkbox widget
            widget = None

        from .s3utils import s3_yes_no_represent
        field = Field(fieldname, fieldtype,
                      default = default,
                      represent = s3_yes_no_represent,
                      requires = requires,
                      )

        if widget:
            field.widget = widget

        return field

    # -------------------------------------------------------------------------
    @staticmethod
    def _json_field(tablename, row):
        """
            Boolean field constructor

            @param tablename: the table name
            @param row: the s3_field Row

            @return: the Field instance
        """

        fieldname = row.name
        fieldtype = row.field_type

        default = row.default_value
        if default:
            value, error = IS_JSONS3()(default)
            default = None if error else value

        field = Field(fieldname, fieldtype,
                      default = default,
                      requires = IS_JSONS3(),
                      )

        return field

# END =========================================================================
