"""
    Data Models

    Copyright: 2009-2022 (c) Sahana Software Foundation

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

__all__ = ("DataModel",
           )

import sys

from gluon import current, IS_EMPTY_OR, TAG
from gluon.storage import Storage
from gluon.tools import callback

from s3dal import Table, Field, original_tablename

from ..tools import IS_ONE_OF
from ..ui import S3ScriptItem

from .dynamic import DynamicTableModel, DYNAMIC_PREFIX
from .fields import MetaFields

DEFAULT = lambda: None
MODULE_TYPE = type(sys)

# =============================================================================
class DataModel:
    """ Base class for data models """

    _edenmodel = True

    LOCK = "eden_model_lock"
    LOAD = "eden_model_load"
    DELETED = "deleted"

    def __init__(self, module=None):

        self.cache = (current.cache.ram, 60)

        self.classes = {}
        self._module_map = None

        self._customised = {}

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
                            "gis",
                            "org",
                            "pr",
                            "s3",
                            "sit",
                            "sync",
                            "usr",
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

        table = self.table(name, DEFAULT)
        if table is DEFAULT:
            raise AttributeError("undefined table: %s" % name)
        return table

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
    @property
    def module_map(self):
        """
            Map of modules by prefix, for faster access (lazy property)
        """

        mmap = self._module_map
        if mmap is None:

            mmap = self._module_map = {}

            # Package locations
            packages = ["s3db"]
            models = current.deployment_settings.get_base_models()
            if models:
                if isinstance(models, str):
                    models = [models]
                if isinstance(models, (tuple, list)):
                    for name in models:
                        if isinstance(name, str) and name not in packages:
                            packages.append(name)

            # Map all modules
            for package in packages:
                try:
                    p = __import__(package, fromlist=("DEFAULT",))
                except ImportError:
                    current.log.error("DataModel cannot import package %s" % package)
                    continue

                for k, v in p.__dict__.items():
                    if type(v) is MODULE_TYPE:
                        if k not in mmap:
                            mmap[k] = [v]
                        else:
                            mmap[k].append(v)
        return mmap

    # -------------------------------------------------------------------------
    @staticmethod
    def customised(tablename, update=None):
        """
            Check (or mark) that customisations for a table model have
            been run

            Args:
                tablename: the name of the table
                update: True to mark that customisations have been run

            Returns:
                True|False whether customisations have been run
        """

        tables = current.s3db._customised

        if update is not None:
            tables[tablename] = bool(update)

        return tables.get(tablename, False)

    # -------------------------------------------------------------------------
    @classmethod
    def table(cls, tablename, default=None, db_only=False):
        """
            Helper function to load a table or other named object from models

            Args:
                tablename: the table name (or name of the object)
                default: the default value to return if not found
                db_only: find only tables, not other objects
        """

        s3 = current.response.s3
        if s3 is None:
            s3 = current.response.s3 = Storage()

        s3db = current.s3db

        if not db_only:
            if tablename in s3:
                return s3[tablename]
            elif tablename in s3db.classes:
                return s3db.classes[tablename].__dict__[tablename]

        db = current.db

        # Table already defined?
        try:
            return getattr(db, tablename)
        except AttributeError:
            pass

        found = None

        prefix = tablename.split("_", 1)[0]
        if prefix == DYNAMIC_PREFIX:
            try:
                found = DynamicTableModel(tablename).table
            except AttributeError:
                pass
        else:
            modules = s3db.module_map.get(prefix, "")
            for module in modules:
                names = module.__all__
                s3models = module.__dict__
                if not db_only and tablename in names:
                    # A name defined at module level (e.g. a class)
                    s3db.classes[tablename] = module
                    found = s3models[tablename]
                else:
                    # A name defined in a DataModel
                    for n in names:
                        model = s3models[n]
                        if hasattr(model, "_edenmodel") and \
                           hasattr(model, "names") and \
                           tablename in model.names:
                            model(prefix)
                            break

        if found:
            return found

        if not db_only and tablename in s3:
            found = s3[tablename]
        elif hasattr(db, tablename):
            found = getattr(db, tablename)
        elif getattr(db, "_lazy_tables") and \
             tablename in getattr(db, "_LAZY_TABLES"):
            found = getattr(db, tablename)
        else:
            found = default

        return found

    # -------------------------------------------------------------------------
    @classmethod
    def has(cls, name):
        """
            Check whether name is available with s3db.table(); does just
            a name lookup, without loading any models

            Args:
                name: the name

            Returns:
                boolean
        """

        s3 = current.response.s3
        if s3 is None:
            s3 = current.response.s3 = Storage()

        s3db = current.s3db

        if name in s3 or name in s3db.classes:
            return True

        if hasattr(current.db, name):
            return True

        found = False
        prefix = name.split("_", 1)[0]
        if prefix == DYNAMIC_PREFIX:
            try:
                found = DynamicTableModel(name).table
            except AttributeError:
                pass
        else:
            modules = s3db.module_map.get(prefix, "")
            for module in modules:
                names = module.__all__
                if name in names:
                    found = True
                    break
                s3models = module.__dict__
                for n in names:
                    model = s3models[n]
                    if hasattr(model, "_edenmodel") and \
                       hasattr(model, "names") and \
                        name in model.names:
                        found = True
                        break

        return found

    # -------------------------------------------------------------------------
    @classmethod
    def load(cls, prefix):
        """
            Helper function to load all DataModels in a module

            Args:
                prefix: the module prefix
        """

        s3 = current.response.s3
        if s3 is None:
            s3 = current.response.s3 = Storage()

        modules = current.s3db.module_map.get(prefix)
        if not modules:
            return

        for module in modules:
            for n in module.__all__:
                model = module.__dict__[n]
                if type(model).__name__ == "type" and \
                   issubclass(model, DataModel):
                    model(prefix)
                elif n.startswith("%s_" % prefix):
                    s3[n] = model

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

        # Load models
        for prefix in current.s3db.module_map:
            cls.load(prefix)

        # Define Scheduler tables
        # - already done during Scheduler().init() run during S3Task().init() in models/tasks.py
        #settings = current.deployment_settings
        #current.s3task.scheduler.define_tables(current.db,
        #                                       migrate = settings.get_base_migrate())

        # Define sessions table
        if current.deployment_settings.get_base_session_db():
            # Copied from https://github.com/web2py/web2py/blob/master/gluon/globals.py#L895
            # Not DRY, but no easy way to make it so
            current.db.define_table("web2py_session",
                                    Field("locked", "boolean", default=False),
                                    Field("client_ip", length=64),
                                    Field("created_datetime", "datetime",
                                          default=current.request.now),
                                    Field("modified_datetime", "datetime"),
                                    Field("unique_key", length=64),
                                    Field("session_data", "blob"),
                                    )

        # Don't do this again within the current request cycle
        s3.load_all_models = False
        s3.all_models_loaded = True

    # -------------------------------------------------------------------------
    @staticmethod
    def define_table(tablename, *fields, meta=True, **args):
        """
            Defines a table like db.define_table, but does not repeat
            a table definition if the table is already defined

            Args:
                meta: add all standard meta-fields to the table
        """

        db = current.db
        if hasattr(db, tablename):
            table = getattr(db, tablename)
        else:
            if meta:
                fields = fields + MetaFields()
            table = db.define_table(tablename, *fields, **args)
        return table

    # -------------------------------------------------------------------------
    @staticmethod
    def get_aliased(table, alias):
        """
            Helper method to get a Table instance with alias; prevents
            re-instantiation of an already existing alias for the same
            table (which can otherwise lead to name collisions in PyDAL).

            Args:
                table: the original table
                alias: the alias

            Returns:
                the aliased Table instance
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
            Wrapper for the CRUDResource constructor to realize
            the global s3db.resource() method
        """

        from ..resource import CRUDResource
        return CRUDResource(tablename, *args, **kwargs)

    # -------------------------------------------------------------------------
    @classmethod
    def configure(cls, tablename, **attr):
        """
            Update the extra configuration of a table

            Args:
                tablename: the name of the table
                attr: dict of attributes to update
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

            Args:
                tablename: the name of the resource DB table
                key: the key (name) of the attribute
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

            Args:
                table: the resource DB table
                keys: keys of attributes to remove (maybe multiple)
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

            Args:
                tablename: the table name
                hook: the main hook ("onvalidation"|"onaccept")
                cb: the custom callback function
                method: the sub-hook ("create"|"update"|None)

            Example:
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

            and in the table with the fields(auth_user only current example) as:

                configure(tablename,
                          references = {fieldname: tablename,
                                        ...
                                        },
                          )

            Args:
                field: the Field

            Returns:
                the name of the referenced table
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

            Args:
                table: the Table
                record: the FORM or the Row to validate
                method: the method
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

            Args:
                table: the Table
                record: the FORM or the Row to validate
                method: the method
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

            Args:
                master: the name of the master table
                links: component link configurations
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

            Args:
                tablename: the table name
                exclude: names to exclude (static components)
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

            Args:
                table: the master table
                alias: the component alias

            Returns:
                the component description (Storage)
        """
        return cls.parse_hook(table, alias)

    # -------------------------------------------------------------------------
    @classmethod
    def get_components(cls, table, names=None):
        """
            Finds components of a table

            Args:
                table: the table or table name
                names: a list of components names to limit the search to,
                       None for all available components

            Returns:
                the component descriptions (Storage {alias: description})
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

            Args:
                table: the master table
                alias: the component alias
                hook: the component configuration (if already known)

            Returns:
                the component description (Storage {key: value})
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
        component = Storage(defaults=hook.defaults,
                            multiple=hook.multiple,
                            tablename=tn,
                            table=ctable,
                            prefix=prefix,
                            name=name,
                            alias=alias,
                            label=hook.label,
                            plural=hook.plural,
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

            Args:
                table: the master table (or table name)
                names: component aliases to find (default: all configured
                       components for the master table)

            Returns:
                tuple (table, {alias: hook, ...})
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

            Args:
                components: components already found, dict {alias: component}
                hooks: component hooks to filter, dict {alias: hook}
                names: the names (=aliases) to include
                supertable: the super-table name to set for the component

            Returns:
                set of names that could not be found, or None if names was None
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

            Args:
                table: the table or table name
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

            Args:
                tablename: the name of the master table
                link: the alias of the link table
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

            Args:
                tablename: the table name

            Returns:
                the alias of the hierarchy parent component
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
    def set_method(cls, tablename,
                   component = None,
                   method = None,
                   action = None,
                   ):
        """
            Configure a URL method for a table, or a component in the context
            of the table

            Args:
                str tablename: the name of the table
                str component: component alias
                str method: name of the method
                action: function to invoke for this method
        """

        methods = current.model["methods"]
        cmethods = current.model["cmethods"]

        if not method:
            raise SyntaxError("No method specified")

        if not component:
            if method not in methods:
                methods[method] = {}
            methods[method][tablename] = action
        else:
            if method not in cmethods:
                cmethods[method] = {}
            if component not in cmethods[method]:
                cmethods[method][component] = {}
            cmethods[method][component][tablename] = action

    # -------------------------------------------------------------------------
    @classmethod
    def get_method(cls, tablename, component=None, method=None):
        """
            Get the handler for a URL method for a table, or a component
            in the context of the table

            Args:
                tablename: the name of the table
                component: component alias
                method: name of the method

            Returns:
                the method handler
        """

        methods = current.model["methods"]
        cmethods = current.model["cmethods"]

        if not method:
            return None

        if not component:
            if method in methods and tablename in methods[method]:
                return methods[method][tablename]
            else:
                return None
        else:
            if method in cmethods and \
               component in cmethods[method] and \
               tablename in cmethods[method][component]:
                return cmethods[method][component][tablename]
            else:
                return None

    # -------------------------------------------------------------------------
    # Super-Entity API
    # -------------------------------------------------------------------------
    @classmethod
    def super_entity(cls, tablename, key, types, *fields, **args):
        """
            Define a super-entity table

            Args:
                tablename: the tablename
                key: name of the primary key
                types: a dictionary of instance types
                fields: any shared fields
                args: table arguments (e.g. migrate)
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

            Args:
                supertable: the super-entity table
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

            Args:
                supertable: the super-entity table
                label: label for the field
                comment: comment for the field
                readable: set the field readable
                represent: set a representation function for the field
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

            Args:
                table: the instance table
                record: the instance record
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
        ogetattr = object.__getattribute__
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

            Args:
                table: the instance table
                record: the instance record

            Returns:
                True if successful, otherwise False (caller must roll back
                the transaction if False is returned!)
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

            Args:
                table: the instance table

            Returns:
                list of field names
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

            Args:
                supertable: the super-entity table
                superid: the super-entity record ID

            Returns:
                a tuple (tablename, ID) of the instance record (if it exists)
        """

        if not hasattr(supertable, "_tablename"):
            # tablename passed instead of Table
            supertable = cls.table(supertable)
        if supertable is None:
            return None, None

        db = current.db
        query = (supertable._id == superid)
        entry = db(query).select(supertable.instance_type,
                                 supertable.uuid,
                                 limitby=(0, 1)).first()
        if entry:
            instance_type = entry.instance_type
            instancetable = current.s3db[entry.instance_type]
            query = (instancetable.uuid == entry.uuid)
            record = db(query).select(instancetable.id,
                                      limitby = (0, 1),
                                      ).first()
            if record:
                return instance_type, record.id

        return None, None

# END =========================================================================
