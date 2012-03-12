# -*- coding: utf-8 -*-

"""
    S3 Data Model Extensions

    @copyright: 2009-2012 (c) Sahana Software Foundation
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

__all__ = ["S3Model", "S3ModelExtensions", "S3MultiPath"]

import sys

from gluon.storage import Storage
from gluon import *

from s3validators import IS_ONE_OF

DEFAULT = lambda: None

DEBUG = False
if DEBUG:
    print >> sys.stderr, "S3MODEL: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

# =============================================================================
class S3Model(object):
    """ Base class for S3 models """

    LOCK = "s3_model_lock"
    LOAD = "s3_model_load"
    DELETED = "deleted"

    def __init__(self, module=None):
        """ Constructor """

        self.cache = (current.cache.ram, 60)

        response = current.response
        if "s3" not in response:
            response.s3 = Storage()
        self.prefix = module
        self.settings = current.deployment_settings

        mandatory_models = ("auth",
                            "sync",
                            "gis",
                            "pr",
                            "sit",
                            #"doc",
                            "org")

        if module is not None:
            if self.__loaded():
                return
            self.__lock()
            mandatory = module in mandatory_models
            if mandatory or self.settings.has_module(module):
                env = self.model()
            else:
                env = self.defaults()
            if isinstance(env, dict):
                response.s3.update(env)
            self.__loaded(True)
            self.__unlock()
        return

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
            response[LOCK] = []
        if name in response[LOCK]:
            raise RuntimeError("circular model reference deadlock in %s" % name)
        else:
            response[LOCK].append(name)
        return

    # -------------------------------------------------------------------------
    def __unlock(self):

        LOCK = self.LOCK
        name = self.__class__.__name__
        response = current.response
        if LOCK in response:
            if name in response[LOCK]:
                response[LOCK].remove(name)
            if not response[LOCK]:
                del response[LOCK]
        return

    # -------------------------------------------------------------------------
    def __getattr__(self, name):

        return self[name]

    # -------------------------------------------------------------------------
    def __getitem__(self, key):
        """ Model auto-loader """

        response = current.response
        db = current.db
        if str(key) in self.__dict__:
            return dict.__getitem__(self, str(key))
        elif key in db:
            return db[key]
        elif key in response.s3:
            return response.s3[key]
        else:
            return self.table(key,
                              AttributeError("undefined table: %s" % key))

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
    @staticmethod
    def table(tablename, default=None):
        """
            Helper function to load a table definition by its name
        """
        response = current.response
        if "s3" not in response:
            response.s3 = Storage()
        db = current.db
        settings = current.deployment_settings

        if tablename in db:
            return db[tablename]
        else:
            prefix, name = tablename.split("_", 1)
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
                            if tablename in model.names:
                                model(prefix)
                                loaded = True
                                generic = []
                            else:
                                continue
                        else:
                            generic.append(n)
                    elif n.startswith("%s_" % prefix):
                        response.s3[n] = model
                [module.__dict__[n](prefix) for n in generic]
        if tablename not in db:
            # Backward compatiblity
            manager = current.manager
            manager.model.load(tablename)
        if tablename in db:
            return db[tablename]
        elif tablename in response.s3:
            return response.s3[tablename]
        elif isinstance(default, Exception):
            raise default
        else:
            return default

    # -------------------------------------------------------------------------
    @staticmethod
    def get(name, default=None):
        """
            Helper function to load a response.s3 variable from models
        """
        response = current.response
        if "s3" not in response:
            response.s3 = Storage()

        if name in response.s3:
            return response.s3[name]
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
                        response.s3[n] = model
                [module.__dict__[n](prefix) for n in generic]
        if name in response.s3:
            return response.s3[name]
        elif isinstance(default, Exception):
            raise default
        else:
            return default

    # -------------------------------------------------------------------------
    @staticmethod
    def load(name):
        """
            Helper function to load a model by its name (=prefix)
        """

        response = current.response
        if "s3" not in response:
            response.s3 = Storage()
        models = current.models

        if models is not None and hasattr(models, name):
            module = models.__dict__[name]
            for n in module.__all__:
                model = module.__dict__[n]
                if type(model).__name__ == "type":
                    model(name)
                elif n.startswith("%s_" % name):
                    response.s3[n] = model
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def load_all_models():
        """
            Helper function to load all models
        """

        models = current.models

        # Backward compatibility: load conventional models first
        manager = current.manager
        manager.model.load_all_models()

        if models is not None:
            for name in models.__dict__:
                if type(models.__dict__[name]).__name__ == "module":
                    S3Model.load(name)
        return

    # -------------------------------------------------------------------------
    @staticmethod
    def define_table(tablename, *fields, **args):
        """
            Same as db.define_table except that it does not repeat
            a table definition if the table is already defined.
        """

        db = current.db
        if tablename in db:
            table = db[tablename]
        else:
            table = db.define_table(tablename, *fields, **args)
        return table

    # -------------------------------------------------------------------------
    @staticmethod
    def super_entity(tablename, key, types, *fields, **args):
        """
            Shortcut for current.manager.model.super_entity
        """

        db = current.db
        if tablename in db:
            table = db[tablename]
        else:
            manager = current.manager
            model = manager.model
            table = model.super_entity(tablename, key, types, *fields, **args)
        return table

    # -------------------------------------------------------------------------
    @staticmethod
    def super_link(name, tablename, **args):
        """
            Shortcut for current.manager.model.super_link
        """

        manager = current.manager
        model = manager.model
        return model.super_link(name, tablename, **args)

    # -------------------------------------------------------------------------
    @staticmethod
    def super_key(supertable, default=None):
        """
            Shortcut for current.manager.model.super_key
        """

        manager = current.manager
        model = manager.model
        return model.super_key(supertable, default=default)

    # -------------------------------------------------------------------------
    @staticmethod
    def configure(tablename, **args):
        """
            Shortcut for current.manager.model.configure
        """

        manager = current.manager
        model = manager.model
        return model.configure(tablename, **args)

    # -------------------------------------------------------------------------
    @staticmethod
    def add_component(tablename, **args):
        """
            Shortcut for current.manager.model.add_component
        """

        manager = current.manager
        model = manager.model
        return model.add_component(tablename, **args)

    # -------------------------------------------------------------------------
    @staticmethod
    def set_method(tablename, **args):
        """
            Shortcut for current.manager.model.set_method
        """

        module, resourcename = tablename.split("_", 1)

        manager = current.manager
        model = manager.model
        return model.set_method(module, resourcename, **args)

# =============================================================================

class S3ModelExtensions(object):
    """
        S3 Model extensions
    """

    # -------------------------------------------------------------------------
    def __init__(self):
        """ Constructor """

        self.components = {}
        self.config = Storage()
        self.globalvars = Storage()
        self.methods = {}
        self.cmethods = {}

        # A list of fields which should be skipped from PDF/XLS exports
        self.indices = ["id", "pe_id", "site_id", "sit_id", "item_entity_id"]

    # -------------------------------------------------------------------------
    # Conditional Model Loading
    # -------------------------------------------------------------------------
    def loader(self, loader, *tables):
        """
            Configure a model loader for multiple tables

            @param loader: the loader
            @param tables: list of tables (tablenames) which the loader defines
        """

        if not tables and hasattr(loader, "tables"):
            tables = loader.tables
        try:
            for table in tables:
                self.configure(str(table), load=loader)
        except:
            pass
        return

    # -------------------------------------------------------------------------
    def load(self, tablename):
        """
            Load the Model for a table

            @param tablename: the name of the table to load
        """

        db = current.db

        if tablename in db:
            return
        loader = self.get_config(tablename, "load")
        output = None
        if hasattr(loader, "define_tables"):
            # this is an instance of a class with a
            # define_tables method:
            output = loader.define_tables()
        elif callable(loader):
            # This is a callable:
            output = loader()
        # If the loader returns a dict, then update response.s3 with it
        if isinstance(output, dict):
            response = current.response
            response.s3.update(output)
        return output

    # -------------------------------------------------------------------------
    def load_all_models(self):
        """
            Load all models
        """

        config = self.config
        db = current.db

        tables = [tn for tn in config
                     if "load" in config[tn]]
        for tablename in tables:
            if tablename not in db:
                self.load(tablename)

        # Also load importer tables
        from s3import import S3Importer, S3ImportJob

        S3Importer.define_upload_table()
        S3ImportJob.define_job_table()
        S3ImportJob.define_item_table()

    # -------------------------------------------------------------------------
    # Resource components
    #--------------------------------------------------------------------------
    def add_component(self, table, **links):
        """
            Defines a component.

            @param table: the component table or table name
            @param links: the component links
        """

        db = current.db

        if not links:
            return
        if hasattr(table, "_tablename"):
            tablename = table._tablename
        else:
            tablename = table
        prefix, name = tablename.split("_", 1)
        for primary in links:
            hooks = self.components.get(primary, Storage())
            l = links[primary]
            if not isinstance(l, (list, tuple)):
                l = [l]
            for link in l:
                if link is None or isinstance(link, str):
                    alias = name
                    pkey = None
                    fkey = link
                    linktable = None
                    lkey = None
                    rkey = None
                    actuate = None
                    autodelete = False
                    autocomplete = None
                    values = None
                    multiple = True
                else:
                    alias = link.get("name", name)
                    joinby = link.get("joinby", None)
                    if joinby is None:
                        continue
                    linktable = link.get("link", None)
                    if hasattr(linktable, "_tablename"):
                        linktable = linktable._tablename
                    pkey = link.get("pkey", None)
                    if linktable is None:
                        lkey = None
                        rkey = None
                        fkey = joinby
                    else:
                        lkey = joinby
                        rkey = link.get("key", None)
                        if not rkey:
                            continue
                        fkey = link.get("fkey", None)
                    actuate = link.get("actuate", None)
                    autodelete = link.get("autodelete", False)
                    autocomplete = link.get("autocomplete", None)
                    values = link.get("values", None)
                    multiple = link.get("multiple", True)
                component = Storage(tablename=tablename,
                                    pkey=pkey,
                                    fkey=fkey,
                                    linktable=linktable,
                                    lkey=lkey,
                                    rkey=rkey,
                                    actuate=actuate,
                                    autodelete=autodelete,
                                    autocomplete=autocomplete,
                                    values=values,
                                    multiple=multiple)

                hooks[alias] = component
            self.components[primary] = hooks
        return

    # -------------------------------------------------------------------------
    def get_component(self, table, name):
        """
            Finds a component definition.

            @param table: the primary table or table name
            @param name: the component name (without prefix)
        """

        components = self.get_components(table, names=name)
        if name in components:
            return components[name]
        else:
            return None

    # -------------------------------------------------------------------------
    def get_components(self, table, names=None):
        """
            Finds components of a table

            @param table: the table or table name
            @param names: a list of components names to limit the search to,
                          None or empty list for all available components
        """

        db = current.db
        load = S3Model.table

        hooks = Storage()
        single = False
        if hasattr(table, "_tablename"):
            tablename = table._tablename
        else:
            tablename = table
            table = load(tablename)
            if table is None:
                # Primary table not defined
                return None
        if isinstance(names, str):
            single = True
            names = [names]
        h = self.components.get(tablename, None)
        if h:
            self.__get_hooks(hooks, h, names=names)
        if not single or single and not len(hooks):
            supertables = self.get_config(tablename, "super_entity")
            if supertables:
                if not isinstance(supertables, (list, tuple)):
                    supertables = [supertables]
                for s in supertables:
                    if isinstance(s, str):
                        s = load(s)
                    if s is None:
                        continue
                    h = self.components.get(s._tablename, None)
                    if h:
                        self.__get_hooks(hooks, h, names=names, supertable=s)

        components = Storage()
        for alias in hooks:

            hook = hooks[alias]
            tn = hook.tablename
            lt = hook.linktable

            ctable = load(tn)
            if ctable is None:
                continue

            if lt:
                ltable = load(lt)
                if ltable is None:
                    continue
            else:
                ltable = None

            prefix, name = tn.split("_", 1)
            component = Storage(values=hook.values,
                                multiple=hook.multiple,
                                tablename=tn,
                                table=ctable,
                                prefix=prefix,
                                name=name,
                                alias=alias)

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

            components[alias] = component
        return components

    # -------------------------------------------------------------------------
    def has_components(self, table):
        """
            Checks whether there are components defined for a table

            @param table: the table or table name
        """

        db = current.db
        load = S3Model.table

        hooks = Storage()
        if hasattr(table, "_tablename"):
            tablename = table._tablename
        else:
            tablename = table
            table = load(tablename)
            if table is None:
                # Primary table not defined
                return False
        h = self.components.get(tablename, None)
        if h:
            self.__get_hooks(hooks, h)
        if len(hooks):
            return True
        supertables = self.get_config(tablename, "super_entity")
        if supertables:
            if not isinstance(supertables, (list, tuple)):
                supertables = [supertables]
            for s in supertables:
                if isinstance(s, str):
                    s = S3Model.table(s)
                if s is None:
                    continue
                h = self.components.get(s._tablename, None)
                if h:
                    self.__get_hooks(hooks, h, supertable=s)
            if len(hooks):
                return True
        return False

    # -------------------------------------------------------------------------
    def __get_hooks(self, components, hooks, names=None, supertable=None):
        """
            DRY Helper method to filter component hooks
        """

        db = current.db

        for alias in hooks:
            if alias in components:
                continue
            if names is not None and alias not in names:
                continue
            hook = hooks[alias]
            hook["supertable"] = supertable
            components[alias] = hook

    # -------------------------------------------------------------------------
    # Resource Methods
    # -------------------------------------------------------------------------
    def set_method(self, prefix, name,
                   component_name=None,
                   method=None,
                   action=None):
        """
            Adds a custom method for a resource or component

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component
            @param method: name of the method
            @param action: function to invoke for this method
        """

        if not method:
            raise SyntaxError("No method specified")

        tablename = "%s_%s" % (prefix, name)

        if not component_name:
            if method not in self.methods:
                self.methods[method] = {}
            self.methods[method][tablename] = action
        else:
            if method not in self.cmethods:
                self.cmethods[method] = {}
            if component_name not in self.cmethods[method]:
                self.cmethods[method][component_name] = {}
            self.cmethods[method][component_name][tablename] = action

    # -------------------------------------------------------------------------
    def get_method(self, prefix, name, component_name=None, method=None):
        """
            Retrieves a custom method for a resource or component

            @param prefix: prefix of the resource name (=module name)
            @param name: name of the resource (=without prefix)
            @param component_name: name of the component
            @param method: name of the method
        """

        if not method:
            return None

        tablename = "%s_%s" % (prefix, name)

        if not component_name:
            if method in self.methods and tablename in self.methods[method]:
                return self.methods[method][tablename]
            else:
                return None
        else:
            if method in self.cmethods and \
               component_name in self.cmethods[method] and \
               tablename in self.cmethods[method][component_name]:
                return self.cmethods[method][component_name][tablename]
            else:
                return None

    # -------------------------------------------------------------------------
    # Resource configuration
    # -------------------------------------------------------------------------
    def configure(self, tablename, **attr):
        """
            Update the extra configuration of a table

            @param tablename: the name of the table
            @param attr: dict of attributes to update
        """

        try:
            cfg = self.config.get(tablename, Storage())
        except:
            if hasattr(tablename, "_tablename"):
                tablename = tablename._tablename
                cfg = self.config.get(tablename, Storage())
            else:
                return
        cfg.update(attr)
        self.config[tablename] = cfg

    # -------------------------------------------------------------------------
    def get_config(self, tablename, key, default=None):
        """
            Reads a configuration attribute of a resource

            @param tablename: the name of the resource DB table
            @param key: the key (name) of the attribute
        """

        if tablename in self.config:
            return self.config[tablename].get(key, default)
        else:
            return default

    # -------------------------------------------------------------------------
    def clear_config(self, tablename, *keys):
        """
            Removes configuration attributes of a resource

            @param table: the resource DB table
            @param keys: keys of attributes to remove (maybe multiple)
        """

        if not keys:
            if tablename in self.config:
                del self.config[tablename]
        else:
            if tablename in self.config:
                for k in keys:
                    if k in self.config[tablename]:
                        del self.config[tablename][k]

    # -------------------------------------------------------------------------
    # Super-Entity API
    # -------------------------------------------------------------------------
    def super_entity(self, tablename, key, types, *fields, **args):
        """
            Define a super-entity table

            @param tablename: the tablename
            @param key: name of the primary key
            @param types: a dictionary of instance types
            @param fields: any shared fields
            @param args: table arguments (e.g. migrate)
        """

        # postgres workaround
        if current.db._dbname == "postgres":
            sequence_name = "%s_%s_Seq" % (tablename, key)
        else:
            sequence_name = None

        table = current.db.define_table(tablename,
                                     Field(key, "id",
                                           readable=False,
                                           writable=False),
                                     Field("deleted", "boolean",
                                           readable=False,
                                           writable=False,
                                           default=False),
                                     Field("instance_type",
                                           readable=False,
                                           writable=False),
                                     Field("uuid", length=128,
                                           readable=False,
                                           writable=False),
                                     sequence_name=sequence_name,
                                     *fields, **args)

        table.instance_type.represent = lambda opt: types.get(opt, opt)

        return table

    # -------------------------------------------------------------------------
    @staticmethod
    def super_key(supertable, default=None):
        """
            Get the name of the key for a super-entity

            @param supertable: the super-entity table
        """

        if supertable is None and default:
            return default
        try:
            return supertable._id.name
        except AttributeError:
            pass
        raise SyntaxError("No id-type key found in %s" % supertable._tablename)

    # -------------------------------------------------------------------------
    def super_link(self, name, supertable,
                   label=None,
                   comment=None,
                   represent=None,
                   orderby=None,
                   sort=True,
                   filterby=None,
                   filter_opts=None,
                   groupby=None,
                   widget=None,
                   empty=True,
                   default=DEFAULT,
                   ondelete="CASCADE",
                   readable=False,
                   writable=False):
        """
            Get a foreign key field for a super-entity

            @param supertable: the super-entity table
            @param label: label for the field
            @param comment: comment for the field
            @param readable: set the field readable
            @param represent: set a representation function for the field
        """

        if isinstance(supertable, str):
            supertable = S3Model.table(supertable)
        if supertable is None:
            if name is not None:
                return Field(name, "integer",
                             readable=False,
                             writable=False)
            else:
                raise SyntaxError("Undefined super-entity")
        else:
            key = self.super_key(supertable)
            if name is not None and name != key:
                raise SyntaxError("Primary key %s not found in %s" % \
                                 (name, supertable._tablename))
            requires = IS_ONE_OF(current.db,
                                 "%s.%s" % (supertable._tablename, key),
                                 represent,
                                 orderby=orderby,
                                 sort=sort,
                                 groupby=groupby,
                                 filterby=filterby,
                                 filter_opts=filter_opts)
            if empty:
                requires = IS_EMPTY_OR(requires)

        return Field(key, supertable,
                     default = default,
                     requires = requires,
                     readable = readable,
                     writable = writable,
                     label = label,
                     comment = comment,
                     represent = represent,
                     widget = widget,
                     ondelete = ondelete)

    # -------------------------------------------------------------------------
    def update_super(self, table, record):
        """
            Updates the super-entity links of an instance record

            @param table: the instance table
            @param record: the instance record
        """

        # Get all super-entities of this table
        tablename = table._tablename
        supertable = self.get_config(tablename, "super_entity")
        if not supertable:
            return True
        elif not isinstance(supertable, (list, tuple)):
            supertable = [supertable]

        # Get the record
        id = record.get("id", None)
        _record = current.db(table.id == id).select(table.ALL,
                                                    limitby=(0, 1)).first()
        if not _record:
            return True

        super_keys = Storage()
        for s in supertable:
            if isinstance(s, str):
                s = S3Model.table(s)
            if s is None:
                continue
            # Get the key
            key = self.super_key(s)
            skey = _record.get(key, None)
            # Get the shared field map
            shared = self.get_config(tablename, "%s_fields" % s._tablename)
            if shared:
                data = Storage([(f, _record[shared[f]])
                                for f in shared
                                if shared[f] in _record and f in s.fields and f != key])
            else:
                data = Storage([(f, _record[f])
                               for f in s.fields if f in _record and f != key])
            # Add instance type and deletion status
            data.update(instance_type=tablename,
                        deleted=_record.get("deleted", False))
            # UID
            uid = _record.get("uuid", None)
            data.update(uuid=uid)
            # Update records
            if skey:
                query = s[key] == skey
                row = current.db(query).select(s[key], limitby=(0, 1)).first()
            else:
                row = Storage()
            _tablename = s._tablename
            form = Storage(vars=row)
            if row:
                onaccept = self.get_config(_tablename, "update_onaccept",
                           self.get_config(_tablename, "onaccept", None))
                current.db(s[key] == row[key]).update(**data)
                k = {key:row[key]}
                super_keys.update(k)
                if _record[key] != row[key]:
                    current.db(table.id == id).update(**k)
                data.update(k)
                if onaccept:
                    form.vars.update(data)
                    onaccept(form)
            else:
                onaccept = self.get_config(_tablename, "create_onaccept",
                           self.get_config(_tablename, "onaccept", None))
                k = s.insert(**data)
                if k:
                    current.db(table.id == id).update(**{key:k})
                    super_keys.update({key:k})
                data.update({key:k})
                if onaccept:
                    form.vars.update(data)
                    onaccept(form)
        record.update(super_keys)
        return True

    # -------------------------------------------------------------------------
    def delete_super(self, table, record):
        """
            Removes the super-entity links of an instance record

            @param table: the instance table
            @param record: the instance record
        """

        manager = current.manager

        supertable = self.get_config(table._tablename, "super_entity")
        if not supertable:
            return True
        if not isinstance(supertable, (list, tuple)):
            supertable = [supertable]

        uid = record.get("uuid", None)
        if uid:
            for s in supertable:
                if isinstance(s, str):
                    s = S3Model.table(s)
                if s is None:
                    continue
                tn = s._tablename
                prefix, name = tn.split("_", 1)
                resource = manager.define_resource(prefix, name, uid=uid)
                ondelete = self.get_config(tn, "ondelete")
                resource.delete(ondelete=ondelete, cascade=True)
        return True

    # -------------------------------------------------------------------------
    def get_instance(self, supertable, superid):
        """
            Get prefix, name and ID of an instance record

            @param supertable: the super-entity table
            @param superid: the super-entity record ID
            @returns: a tuple (prefix, name, ID) of the instance
                      record (if it exists)
        """

        db = current.db
        s3db = current.s3db

        if not hasattr(supertable, "_tablename"):
            # tablename passed instead of Table
            supertable = S3Model.table(supertable)
        if supertable is None:
            return (None, None, None)
        query = supertable._id == superid
        entry = db(query).select(supertable.instance_type,
                                 supertable.uuid,
                                 limitby=(0, 1)).first()
        if entry:
            instance_type = entry.instance_type
            prefix, name = instance_type.split("_", 1)
            instancetable = s3db[entry.instance_type]
            query = instancetable.uuid == entry.uuid
            record = db(query).select(instancetable.id,
                                      limitby=(0, 1)).first()
            if record:
                return (prefix, name, record.id)
        return (None, None, None)

# =============================================================================
class S3MultiPath:
    """
        Simplified path toolkit for managing multi-ancestor-hypergraphs
        in a relational database.

        MultiPaths allow single-query searches for all ancestors and
        descendants of a node, as well as single-query affiliation
        testing - whereas they require multiple writes on update (one
        per each descendant node), so they should only be used for
        hypergraphs which rarely change.

        Every node of the hypergraph contains a path attribute, with the
        following MultiPath-syntax:

        MultiPath: <SimplePath>,<SimplePath>,...
        SimplePath: [|<Node>|<Node>|...|]
        Node: ID of the ancestor node

        SimplePaths contain only ancestors, not the node itself.

        SimplePaths contain the ancestors in reverse order, i.e. the nearest
        ancestor first (this is important because removing a vertex from the
        path will cut off the tail, not the head)

        A path like A<-B<-C can be constructed like:

            path = S3MultiPath([["C", "B", "A"]])
            [|C|B|A|]

        Extending this path by a vertex E<-B will result in a multipath like:

            path.extend("B", "E")
            [|C|B|A|],[|C|B|E|]

        Cutting the vertex A<-B reduces the multipath to:

            path.cut("B", "A")
            [|C|B|E|]

        Note the reverse notation (nearest ancestor first)!

        MultiPaths will be normalized automatically, i.e.:

            path = S3MultiPath([["C", "B", "A", "D", "F", "B", "E", "G"]])
            [|C|B|A|D|F|],[|C|B|E|G|]
    """

    # -------------------------------------------------------------------------
    # Construction
    #
    def __init__(self, paths=None):
        """ Constructor """
        self.paths = []
        if isinstance(paths, S3MultiPath):
            self.paths = list(paths.paths)
        else:
            if paths is None:
                paths = []
            elif type(paths) is str:
                paths = self.__parse(paths)
            elif not isinstance(paths, (list, tuple)):
                paths = [paths]
            append = self.append
            for p in paths:
                append(p)

    # -------------------------------------------------------------------------
    def append(self, path):
        """
            Append a new ancestor path to this multi-path

            @param path: the ancestor path
        """
        Path = self.Path

        if isinstance(path, Path):
            path = path.nodes
        else:
            path = Path(path).nodes
        multipath = None

        # Normalize any recurrent paths
        paths = self.__normalize(path)

        append = self.paths.append
        for p in paths:
            p = Path(p)
            if not self & p:
                append(p)
                multipath = self
        return multipath

    # -------------------------------------------------------------------------
    def extend(self, head, ancestors=None, cut=None):
        """
            Extend this multi-path with a new vertex ancestors<-head

            @param head: the head node
            @param ancestors: the ancestor (multi-)path of the head node
        """

        # If ancestors is a multi-path, extend recursively with all paths
        if isinstance(ancestors, S3MultiPath):
            extend = self.extend
            for p in ancestors.paths:
                extend(head, p, cut=cut)
            return self

        # Split-extend all paths which contain the head node
        extensions = []
        Path = self.Path
        append = extensions.append
        for p in self.paths:
            if cut:
                pos = p.find(cut)
                if pos > 0:
                    p.nodes = p.nodes[:pos-1]
            i = p.find(head)
            if i > 0:
                path = Path(p.nodes[:i]).extend(head, ancestors)
                detour = None
                for tail in self.paths:
                    j = tail.find(path.last())
                    if j > 0:
                        # append original tail
                        detour = Path(path)
                        detour.extend(path.last(), tail[j:])
                        append(detour)
                if not detour:
                    append(path)
        self.paths.extend(extensions)

        # Finally, cleanup for duplicate and empty paths
        return self.clean()

    # -------------------------------------------------------------------------
    def cut(self, head, ancestor=None):
        """
            Cut off the vertex ancestor<-head in this multi-path

            @param head: the head node
            @param ancestor: the ancestor node to cut off
        """
        for p in self.paths:
            p.cut(head, ancestor)
        # Must cleanup for duplicates
        return self.clean()

    # -------------------------------------------------------------------------
    def clean(self):
        """
            Remove any duplicate and empty paths from this multi-path
        """
        mp = S3MultiPath(self)
        pop = mp.paths.pop
        self.paths = []
        append = self.paths.append
        while len(mp):
            item = pop(0)
            if len(item) and not mp & item and not self & item:
                append(item)
        return self

    # -------------------------------------------------------------------------
    # Serialization/Deserialization
    #
    def __parse(self, value):
        """ Parse a multi-path-string into nodes """
        return value.split(",")

    def __repr__(self):
        """ Serialize this multi-path as string """
        return ",".join([str(p) for p in self.paths])

    def as_list(self):
        """ Return this multi-path as list of node lists """
        return [p.as_list() for p in self.paths if len(p)]

    # -------------------------------------------------------------------------
    # Introspection
    #
    def __len__(self):
        """ The number of paths in this multi-path """
        return len(self.paths)

    # -------------------------------------------------------------------------
    def __and__(self, sequence):
        """
            Check whether sequence is the start sequence of any of
            the paths in this multi-path (for de-duplciation)

            @param sequence: sequence of node IDs (or path)
        """
        for p in self.paths:
            if p.startswith(sequence):
                return 1
        return 0

    # -------------------------------------------------------------------------
    def __contains__(self, sequence):
        """
            Check whether sequence is contained in any of the paths (can
            also be used to check whether this multi-path contains a path
            to a particular node)

            @param sequence: the sequence (or node ID)
        """
        for p in self.paths:
            if sequence in p:
                return 1
        return 0

    # -------------------------------------------------------------------------
    def nodes(self):
        """ Get all nodes from this path """
        nodes = []
        for p in self.paths:
            n = [i for i in p.nodes if i not in nodes]
            nodes.extend(n)
        return nodes

    # -------------------------------------------------------------------------
    @staticmethod
    def all_nodes(paths):
        """
            Get all nodes from all paths

            @param paths: list of multi-paths
        """
        nodes = []
        for p in paths:
            n = [i for i in p.nodes() if i not in nodes]
            nodes.extend(n)
        return nodes

    # -------------------------------------------------------------------------
    # Normalization
    #
    @staticmethod
    def __normalize(path):
        """
            Normalize a path into a sequence of non-recurrent paths

            @param path: the path as a list of node IDs
        """
        seq = map(str, path)
        l = zip(seq, seq[1:])
        if not l:
            return [path]
        seq = S3MultiPath.__resolve(seq)
        pop = seq.pop
        paths = []
        append = paths.append
        while len(seq):
            p = pop(0)
            s = paths + seq
            contained = False
            lp = len(p)
            for i in s:
                if i[:lp] == p:
                    contained = True
                    break
            if not contained:
                append(p)
        return paths

    # -------------------------------------------------------------------------
    @staticmethod
    def __resolve(seq):
        """
            Resolve a sequence of vertices (=pairs of node IDs) into a
            sequence of non-recurrent paths

            @param seq: the vertex sequence
        """
        resolve = S3MultiPath.__resolve
        if seq:
            head = seq[0]
            tail = seq[1:]
            tails = []
            index = tail.index
            append = tails.append
            while head in tail:
                pos = index(head)
                append(tail[:pos])
                tail = tail[pos+1:]
            append(tail)
            r = []
            append = r.append
            for tail in tails:
                nt = resolve(tail)
                for t in nt:
                    append([head]+t)
            return r
        else:
            return [seq]

    # -------------------------------------------------------------------------
    # Helper class for simple ancestor paths
    #
    class Path:

        # ---------------------------------------------------------------------
        # Construction methods
        #
        def __init__(self, nodes=None):
            """ Constructor """
            self.nodes = []
            if isinstance(nodes, S3MultiPath.Path):
                self.nodes = list(nodes.nodes)
            else:
                if nodes is None:
                    nodes = []
                elif type(nodes) is str:
                    nodes = self.__parse(nodes)
                elif not isinstance(nodes, (list, tuple)):
                    nodes = [nodes]
                append = self.append
                for n in nodes:
                    if not append(n):
                        break

        # ---------------------------------------------------------------------
        def append(self, node=None):
            """
                Append a node to this path

                @param node: the node
            """
            if node is None:
                return True
            n = str(node)
            if not n:
                return True
            if n not in self.nodes:
                self.nodes.append(n)
                return True
            return False

        # ---------------------------------------------------------------------
        def extend(self, head, ancestors=None):
            """
                Extend this path with a new vertex ancestors<-head, if this
                path ends at the head node

                @param head: the head node
                @param ancestors: the ancestor sequence
            """
            if ancestors is None:
                # If no head node is specified, use the first ancestor node
                path = S3MultiPath.Path(head)
                head = path.first()
                ancestors = path.nodes[1:]
            last = self.last()
            if last is None or last == str(head):
                append = self.append
                path = S3MultiPath.Path(ancestors)
                for i in path.nodes:
                    if not append(i):
                        break
                return self
            else:
                return None

        # ---------------------------------------------------------------------
        def cut(self, head, ancestor=None):
            """
                Cut off the ancestor<-head vertex from this path, retaining
                the head node

                @param head: the head node
                @param ancestor: the ancestor node

            """
            if ancestor is not None:
                sequence = [str(head), str(ancestor)]
                pos = self.find(sequence)
                if pos > 0:
                    self.nodes = self.nodes[:pos]
            else:
                # if ancestor is None and the path starts with head,
                # then remove the entire path
                if str(head) == self.first():
                    self.nodes = []
            return self

        # ---------------------------------------------------------------------
        # Serialize/Deserialize
        #
        def __repr__(self):
            """ Represent this path as a string """
            return "[|%s|]" % "|".join(self.nodes)

        def __parse(self, value):
            """ Parse a string into nodes """
            return value.strip().strip("[").strip("]").strip("|").split("|")

        def as_list(self):
            """ Return the list of nodes """
            return list(self.nodes)

        # ---------------------------------------------------------------------
        # Item access
        #
        def __getitem__(self, i):
            """ Get the node at position i """
            try:
                return self.nodes.__getitem__(i)
            except IndexError:
                return None

        # ---------------------------------------------------------------------
        def first(self):
            """ Get the first node in this path (the nearest ancestor) """
            return self[0]

        # ---------------------------------------------------------------------
        def last(self):
            """ Get the last node in this path (the most distant ancestor) """
            return self[-1]

        # ---------------------------------------------------------------------
        # Tests
        #
        def __contains__(self, sequence):
            """
                Check whether this path contains sequence

                @param sequence: sequence of node IDs
            """
            if self.find(sequence) != -1:
                return 1
            else:
                return 0

        # ---------------------------------------------------------------------
        def __len__(self):
            """
                Get the number of nodes in this path
            """
            return len(self.nodes)

        # ---------------------------------------------------------------------
        def find(self, sequence):
            """
                Find a sequence of node IDs in this path

                @param sequence: sequence of node IDs (or path)
                @returns: position of the sequence (index+1), 0 if the path
                          is empty, -1 if the sequence wasn't found
            """
            path = S3MultiPath.Path(sequence)
            sequence = path.nodes
            nodes = self.nodes
            if not sequence:
                return -1
            if not nodes:
                return 0
            head, tail = sequence[0], sequence[1:]
            pos = 0
            l = len(tail)
            index = nodes.index
            while head in nodes[pos:]:
                pos = index(head, pos) + 1
                if not tail or nodes[pos:pos+l] == tail:
                    return pos
            return -1

        # ---------------------------------------------------------------------
        def startswith(self, sequence):
            """
                Check whether this path starts with sequence

                @param sequence: sequence of node IDs (or path)
            """
            sequence = S3MultiPath.Path(sequence).nodes
            if self.nodes[0:len(sequence)] == sequence:
                return True
            else:
                return False

# END =========================================================================
