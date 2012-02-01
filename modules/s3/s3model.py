# -*- coding: utf-8 -*-

"""
    S3 Data Model Extensions

    @see: U{B{I{S3XRC}} <http://eden.sahanafoundation.org/wiki/S3XRC>}

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @author: Dominic König <dominic[at]aidiq.com>

    @copyright: 2009-2011 (c) Sahana Software Foundation
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

__all__ = ["S3Model", "S3ModelExtensions", "S3RecordLinker"]

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
                     ondelete = "RESTRICT")

    # -------------------------------------------------------------------------
    def update_super(self, table, record):
        """
            Updates the super-entity links of an instance record

            @param table: the instance table
            @param record: the instance record
        """

        # Get tablename and record
        tablename = table._tablename
        id = record.get("id", None)
        _record = current.db(table.id == id).select(table.ALL,
                                                    limitby=(0, 1)).first()
        if not _record:
            return True

        # Get all super-entities of this table
        supertable = self.get_config(tablename, "super_entity")
        if not supertable:
            return True
        elif not isinstance(supertable, (list, tuple)):
            supertable = [supertable]

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
                data = dict([(f, _record[shared[f]])
                             for f in shared
                             if shared[f] in _record and f in s.fields and f != key])
            else:
                data = dict([(f, _record[f])
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
                row = None
            _tablename = s._tablename
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
                    onaccept(dict(vars=_record).update(data))
            else:
                onaccept = self.get_config(_tablename, "create_onaccept",
                           self.get_config(_tablename, "onaccept", None))
                k = s.insert(**data)
                if k:
                    current.db(table.id == id).update(**{key:k})
                    super_keys.update({key:k})
                data.update({key:k})
                if onaccept:
                    onaccept(dict(vars=_record).update(data))
        record.update(super_keys)
        return True

    # -------------------------------------------------------------------------
    def delete_super(self, table, record):
        """
            Removes the super-entity links of an instance record

            @param table: the instance table
            @param record: the instance record
        """

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
                if "deleted" in s.fields:
                    current.db(s.uuid == uid).update(deleted=True)

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
            instancetable = db[entry.instance_type]
            query = instancetable.uuid == entry.uuid
            record = db(query).select(instancetable.id,
                                      limitby=(0, 1)).first()
            if record:
                return (prefix, name, record.id)
        return (None, None, None)

# =============================================================================

class S3RecordLinker(object):
    """
        Hyperlinks between resources

        @status: to be deprecated
    """

    # -------------------------------------------------------------------------
    def __init__(self):
        """ Constructor """

        manager = current.manager
        self.tablename = manager.rlink_tablename


        self.table = current.db.get(self.tablename, None)
        if not self.table:
            self.table = current.db.define_table(self.tablename,
                                              Field("link_class", length=128),
                                              Field("origin_table"),
                                              Field("origin_id", "list:integer"),
                                              Field("target_table"),
                                              Field("target_id", "integer"),
                                              )

    # -------------------------------------------------------------------------
    def link(self, from_table, from_id, to_table, to_id, link_class=None):
        """
            Create a hyperlink between resources

            @param from_table: the originating table
            @param from_id: ID or list of IDs of the originating record(s)
            @param to_table: the target table
            @param to_id: ID or list of IDs of the target record(s)
            @param link_class: link class name

            @returns: a list of record IDs of the created links
        """

        o_tn = from_table._tablename
        t_tn = to_table._tablename
        links = []
        if not from_id:
            return links
        elif not isinstance(from_id, (list, tuple)):
            o_id = [str(from_id)]
        else:
            o_id = map(str, from_id)
        if not to_id:
            return links
        elif not isinstance(to_id, (list, tuple)):
            t_id = [str(to_id)]
        else:
            t_id = map(str, to_id)
        table = self.table
        query = ((table.origin_table == o_tn) &
                 (table.target_table == t_tn) &
                 (table.link_class == link_class) &
                 (table.target_id.belongs(t_id)))
        rows = current.db(query).select()
        rows = dict([(str(r.target_id), r) for r in rows])
        success = True
        for target_id in t_id:
            if target_id in rows:
                row = rows[target_id]
                ids = map(str, row.origin_id)
                add = [i for i in o_id if i not in ids]
                ids += add
                row.update_record(origin_id=ids)
                links.append(row.id)
            else:
                row = table.insert(origin_table=o_tn,
                                   target_table=t_tn,
                                   link_class=link_class,
                                   target_id=target_id,
                                   origin_id=o_id)
                links.append(row)
        return links

    # -------------------------------------------------------------------------
    def unlink(self, from_table, from_id, to_table, to_id, link_class=None):
        """
            Remove a hyperlink between resources

            @param from_table: the originating table
            @param from_id: ID or list of IDs of the originating record(s)
            @param to_table: the target table
            @param to_id: ID or list of IDs of the target record(s)
            @param link_class: link class name

            @note: None for from_id or to_id means *any* record
        """

        o_tn = from_table._tablename
        t_tn = to_table._tablename

        table = self.table
        query = ((table.origin_table == o_tn) &
                 (table.target_table == t_tn) &
                 (table.link_class == link_class))
        q = None
        if from_id is not None:
            if not isinstance(from_id, (list, tuple)):
                o_id = [str(from_id)]
            else:
                o_id = map(str, from_id)
            for origin_id in o_id:
                iq = table.origin_id.contains(origin_id)
                if q is None:
                    q = iq
                else:
                    q = q | iq
        else:
            o_id = None
        if q is not None:
            query = query & (q)
        q = None
        if to_id is not None:
            if not isinstance(to_id, (list, tuple)):
                q = table.target_id == str(to_id)
            else:
                t_id = map(str, to_id)
                q = table.target_id.belongs(t_id)
        if q is not None:
            query = query & (q)
        rows = current.db(query).select()
        for row in rows:
            if o_id:
                ids = [i for i in row.origin_id if str(i) not in o_id]
            else:
                ids = []
            if ids:
                row.update_record(origin_id=ids)
            else:
                row.delete_record()
        return

    # -------------------------------------------------------------------------
    def get_origin_query(self, from_table, to_table, to_id,
                         link_class=None,
                         union=False):
        """
            Get a query for the origin table to retrieve records that are
            linked to a set of target table records.

            @param from_table: the origin table
            @param to_table: the target table
            @param to_id: target record ID or list of target record IDs
            @param link_class: link class name
            @param union: retrieve a union (True) or an intersection (False, default)
                            of all sets of links (in case of multiple target records)

            @note: None for to_id means *any* record
        """

        o_tn = from_table._tablename
        t_tn = to_table._tablename

        table = self.table
        if not to_id:
            query = (table.target_id != None)
        elif not isinstance(to_id, (list, tuple)):
            query = (table.target_id == to_id)
        else:
            query = (table.target_id.belongs(to_id))
        query = (table.origin_table == o_tn) & \
                (table.target_table == t_tn) & \
                (table.link_class == link_class) & query
        ids = []
        rows = current.db(query).select(table.origin_id)
        for row in rows:
            if union:
                add = [i for i in row.origin_id if i not in ids]
                ids += add
            elif not ids:
                ids = row.origin_id
            else:
                ids = [i for i in ids if i in row.origin_id]
        if ids and len(ids) == 1:
            mq = (from_table.id == ids[0])
        elif ids:
            mq = (from_table.id.belongs(ids))
        else:
            mq = (from_table.id == None)
        return mq

    # -------------------------------------------------------------------------
    def get_target_query(self, from_table, from_id, to_table,
                         link_class=None,
                         union=False):
        """
            Get a query for the target table to retrieve records that are
            linked to a set of origin table records.

            @param from_table: the origin table
            @param from_id: origin record ID or list of origin record IDs
            @param to_table: the target table
            @param link_class: link class name
            @param union: retrieve a union (True) or an intersection (False, default)
                            of all sets of links (in case of multiple origin records)

            @note: None for from_id means *any* record
        """

        o_tn = from_table._tablename
        t_tn = to_table._tablename
        table = self.table
        if not from_id:
            query = (table.origin_id != None)
        elif not isinstance(from_id, (list, tuple)):
            query = (table.origin_id.contains(from_id))
        else:
            q = None
            for origin_id in from_id:
                iq = table.origin_id.contains(origin_id)
                if q and union:
                    q = q | iq
                elif q and not union:
                    q = q & iq
                else:
                    q = iq
            if q:
                query = (q)
        query = (table.origin_table == o_tn) & \
                (table.target_table == t_tn) & \
                (table.link_class == link_class) & query
        rows = current.db(query).select(table.target_id, distinct=True)
        ids = [row.target_id for row in rows]
        if ids and len(ids) == 1:
            mq = (to_table.id == ids[0])
        elif ids:
            mq = (to_table.id.belongs(ids))
        else:
            mq = (to_table.id == None)
        return mq

# END =========================================================================
