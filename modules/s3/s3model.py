# -*- coding: utf-8 -*-

""" S3 Data Model Extensions

    @copyright: 2009-2014 (c) Sahana Software Foundation
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

__all__ = ("S3Model",)

from gluon import *
try:
    from gluon.dal.objects import Table
except ImportError:
    # old web2py
    from gluon.dal import Table
# Here are dependencies listed for reference:
#from gluon import current
#from gluon.dal import Field
#from gluon.validators import IS_EMPTY_OR
from gluon.storage import Storage
from gluon.tools import callback

from s3navigation import S3ScriptItem
from s3resource import S3Resource
from s3validators import IS_ONE_OF

DEFAULT = lambda: None

DEBUG = False
if DEBUG:
    import sys
    print >> sys.stderr, "S3MODEL: DEBUG MODE"
    def _debug(m):
        print >> sys.stderr, m
else:
    _debug = lambda m: None

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
        self.classes = Storage()

        # Initialize current.model
        if not hasattr(current, "model"):
            current.model = Storage(config = Storage(),
                                    components = Storage(),
                                    methods = Storage(),
                                    cmethods = Storage(),
                                    hierarchies = Storage())

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
                            "org")

        if module is not None:
            if self.__loaded():
                return
            self.__lock()
            if module in mandatory_models or \
               current.deployment_settings.has_module(module):
                env = self.model()
            else:
                env = self.defaults()
            if isinstance(env, (Storage, dict)):
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
        found = None
        if hasattr(db, tablename):
            return ogetattr(db, tablename)
        elif ogetattr(db, "_lazy_tables") and \
             tablename in ogetattr(db, "_LAZY_TABLES"):
            return ogetattr(db, tablename)
        else:
            prefix, name = tablename.split("_", 1)
            if hasattr(models, prefix):
                module = models.__dict__[prefix]
                loaded = False
                generic = []
                for n in module.__all__:
                    model = module.__dict__[n]
                    if hasattr(model, "_s3model"):
                        if loaded:
                            continue
                        if hasattr(model, "names"):
                            if tablename in model.names:
                                model(prefix)
                                loaded = True
                            else:
                                continue
                        else:
                            generic.append(n)
                    else:
                        if n == tablename:
                            s3db.classes[tablename] = (prefix, n)
                            found = model
                            loaded = True
                if not loaded:
                    [module.__dict__[n](prefix) for n in generic]
        if found:
            return found
        if not db_only and tablename in s3:
            return s3[tablename]
        elif hasattr(db, tablename):
            return ogetattr(db, tablename)
        elif ogetattr(db, "_lazy_tables") and \
             tablename in ogetattr(db, "_LAZY_TABLES"):
            return ogetattr(db, tablename)
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
                [module.__dict__[n](prefix) for n in generic]
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

        models = current.models

        # Load models
        if models is not None:
            for name in models.__dict__:
                if type(models.__dict__[name]).__name__ == "module":
                    cls.load(name)

        # Define importer tables
        from s3import import S3Importer, S3ImportJob

        S3Importer.define_upload_table()
        S3ImportJob.define_job_table()
        S3ImportJob.define_item_table()

        # Don't do this again within the current request cycle
        s3.all_models_loaded = True
        return

    # -------------------------------------------------------------------------
    @classmethod
    def define_table(cls, tablename, *fields, **args):
        """
            Same as db.define_table except that it does not repeat
            a table definition if the table is already defined.
        """

        db = current.db
        if hasattr(db, tablename):
            table = ogetattr(db, tablename)
        else:
            table = db.define_table(tablename, *fields, **args)
        return table

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

        config = current.model.config

        tn = tablename._tablename if type(tablename) is Table else tablename
        if tn not in config:
            config[tn] = Storage()
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

        config = current.model.config

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

        config = current.model.config

        tn = tablename._tablename if type(tablename) is Table else tablename
        if tn in config:
            if not keys:
                del config[tn]
            else:
                [config[tn].pop(k, None) for k in keys]
        return

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
        if "vars" not in record:
            record = Storage(vars=record, errors=Storage())
        if onaccept:
            callback(onaccept, record, tablename=tablename)
        return

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
            record = Storage(vars=record, errors=Storage())
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

        components = current.model.components

        master = master._tablename if type(master) is Table else master

        hooks = components.get(master)
        if hooks is None:
            hooks = Storage()
        for tablename, ll in links.items():

            prefix, name = tablename.split("_", 1)
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
                    values = None
                    multiple = True
                    filterby = None
                    filterfor = None

                elif isinstance(link, dict):
                    alias = link.get("name", name)

                    joinby = link.get("joinby")
                    if not joinby:
                        continue

                    linktable = link.get("link")
                    linktable = linktable._tablename \
                                if type(linktable) is Table else linktable

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
                    values = link.get("values")
                    multiple = link.get("multiple", True)
                    filterby = link.get("filterby")
                    filterfor = link.get("filterfor")

                else:
                    continue

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
                                    multiple=multiple,
                                    filterby=filterby,
                                    filterfor=filterfor)
                hooks[alias] = component

        components[master] = hooks
        return

    # -------------------------------------------------------------------------
    @classmethod
    def get_component(cls, table, name):
        """
            Finds a component definition.

            @param table: the primary table or table name
            @param name: the component name (without prefix)
        """

        components = cls.get_components(table, names=name)
        if name in components:
            return components[name]
        else:
            return None

    # -------------------------------------------------------------------------
    @classmethod
    def get_components(cls, table, names=None):
        """
            Finds components of a table

            @param table: the table or table name
            @param names: a list of components names to limit the search to,
                          None or empty list for all available components
        """

        components = current.model.components

        load = cls.table
        get_hooks = cls.__get_hooks

        hooks = Storage()
        single = False
        if type(table) is Table:
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
        h = components.get(tablename, None)
        if h:
            get_hooks(hooks, h, names=names)
        if not single or single and not len(hooks):
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
                        get_hooks(hooks, h, names=names, supertable=s)

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

            if hook.filterby is not None:
                component.filterby = hook.filterby

            if hook.filterfor is not None:
                component.filterfor = hook.filterfor

            components[alias] = component
        return components

    # -------------------------------------------------------------------------
    @classmethod
    def has_components(cls, table):
        """
            Checks whether there are components defined for a table

            @param table: the table or table name
        """

        components = current.model.components

        load = cls.table
        get_hooks = cls.__get_hooks

        hooks = Storage()
        if type(table) is Table:
            tablename = table._tablename
        else:
            tablename = table
            table = load(tablename)
            if table is None:
                return False
        h = components.get(tablename, None)
        if h:
            get_hooks(hooks, h)
        if len(hooks):
            return True
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
                    get_hooks(hooks, h, supertable=s)
            if len(hooks):
                return True
        return False

    # -------------------------------------------------------------------------
    @classmethod
    def __get_hooks(cls, components, hooks, names=None, supertable=None):
        """
            DRY Helper method to filter component hooks
        """

        for alias in hooks:
            if alias in components:
                continue
            if names is not None and alias not in names:
                continue
            hook = hooks[alias]
            hook["supertable"] = supertable
            components[alias] = hook

    # -------------------------------------------------------------------------
    @classmethod
    def get_alias(cls, tablename, link):
        """
            Find a component alias from the link table alias.

            @param tablename: the name of the master table
            @param link: the alias of the link table
        """

        components = current.model.components

        table = cls.table(tablename)
        if not table:
            return None

        def get_alias(hooks, alias):
            for alias in hooks:
                hook = hooks[alias]
                if hook.linktable:
                    prefix, name = hook.linktable.split("_", 1)
                    if name == link:
                        return alias
            return None

        hooks = components.get(tablename, None)
        if hooks:
            alias = get_alias(hooks, link)
            if alias:
                return alias
        else:
            hooks = []

        supertables = cls.get_config(tablename, "super_entity")
        if supertables:
            if not isinstance(supertables, (list, tuple)):
                supertables = [supertables]
            for s in supertables:
                table = cls.table(s)
                if table is None:
                    continue
                hooks = components.get(table._tablename, [])
                if hooks:
                    alias = get_alias(hooks, link)
                    if alias:
                        return alias

        return None

    # -------------------------------------------------------------------------
    # Resource Methods
    # -------------------------------------------------------------------------
    @classmethod
    def set_method(cls, prefix, name,
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

        methods = current.model.methods
        cmethods = current.model.cmethods

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
        return

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

        methods = current.model.methods
        cmethods = current.model.cmethods

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
    def super_link(cls, name, supertable,
                   label=None,
                   comment=None,
                   represent=None,
                   orderby=None,
                   sort=True,
                   filterby=None,
                   filter_opts=None,
                   not_filterby=None,
                   not_filter_opts=None,
                   instance_types=None,
                   realms=None,
                   updateable=False,
                   groupby=None,
                   script=None,
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
            supertable = cls.table(supertable)
        if supertable is None:
            if name is not None:
                return Field(name, "integer",
                             readable=False,
                             writable=False)
            else:
                raise SyntaxError("Undefined super-entity")
        else:
            key = cls.super_key(supertable)
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
                                 filter_opts=filter_opts,
                                 instance_types=instance_types,
                                 realms=realms,
                                 updateable=updateable,
                                 not_filterby=not_filterby,
                                 not_filter_opts=not_filter_opts,)
            if empty:
                requires = IS_EMPTY_OR(requires)

        # Add the script into the comment
        if script:
            if comment:
                comment = TAG[""](comment,
                                  S3ScriptItem(script=script))
            else:
                comment = S3ScriptItem(script=script)

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
    @classmethod
    def update_super(cls, table, record):
        """
            Updates the super-entity links of an instance record

            @param table: the instance table
            @param record: the instance record
        """

        get_config = cls.get_config

        # Get all super-entities of this table
        tablename = table._tablename
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
            if type(s) is not Table:
                s = cls.table(s)
            if s is None:
                continue
            tn = s._tablename
            key = cls.super_key(s)
            shared = get_config(tablename, "%s_fields" % tn)
            if not shared:
                shared = dict((fn, fn)
                              for fn in s.fields
                              if fn != key and fn in table.fields)
            else:
                shared = dict((fn, shared[fn])
                              for fn in shared
                              if fn != key and \
                                 fn in s.fields and \
                                 shared[fn] in table.fields)
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

        super_keys = Storage()
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
        supertables = get_config(table._tablename, "super_entity")

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
            sresource.delete(cascade=True)

            if sresource.error:
                # Restore the super key
                # @todo: is this really necessary? => caller must roll back
                #        anyway in this case, which would automatically restore
                update_record(**{key: value})
                return False

        return True

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
                                 limitby=(0, 1)).first()
        if entry:
            instance_type = entry.instance_type
            prefix, name = instance_type.split("_", 1)
            instancetable = current.s3db[entry.instance_type]
            query = instancetable.uuid == entry.uuid
            record = db(query).select(instancetable.id,
                                      limitby=(0, 1)).first()
            if record:
                return (prefix, name, record.id)
        return (None, None, None)

# END =========================================================================
