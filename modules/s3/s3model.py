# -*- coding: utf-8 -*-

""" S3 Data Model Extensions

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

__all__ = ["S3Model", "S3ModelExtensions"]

from gluon import *
from gluon.dal import Table
# Here are dependencies listed for reference:
#from gluon import current
#from gluon.dal import Field
#from gluon.validators import IS_EMPTY_OR
from gluon.storage import Storage

from s3validators import IS_ONE_OF
from s3resource import S3Resource

DEFAULT = lambda: None

DEBUG = False
if DEBUG:
    import sys
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

        # Initialize current.model
        if not hasattr(current, "model"):
            current.model = Storage(config = Storage(),
                                    components = Storage(),
                                    methods = Storage(),
                                    cmethods = Storage())

        response = current.response
        if "s3" not in response:
            response.s3 = Storage()
        self.prefix = module

        mandatory_models = ("auth",
                            "sync",
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
        """ Model auto-loader """

        if str(name) in self.__dict__:
            return self.__dict__[str(name)]
        else:
            db = current.db
            if name in db:
                return db[name]
            else:
                s3 = current.response.s3
                if name in s3:
                    return s3[name]
                else:
                    return self.table(name,
                                      AttributeError("undefined table: %s" % name))

    # -------------------------------------------------------------------------
    def __getitem__(self, key):

        return self.__getattr__(key)

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
        response = current.response
        if "s3" not in response:
            response.s3 = Storage()
        s3 = response.s3
        db = current.db

        if tablename in db:
            return db[tablename]
        elif tablename in s3 and not db_only:
            return s3[tablename]
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
                        s3[n] = model
                [module.__dict__[n](prefix) for n in generic]
        if tablename in db:
            return db[tablename]
        elif tablename in s3 and not db_only:
            return s3[tablename]
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
        response = current.response
        if "s3" not in response:
            response.s3 = Storage()
        s3 = response.s3

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

        response = current.response
        if "s3" not in response:
            response.s3 = Storage()
        s3 = response.s3
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

        return

    # -------------------------------------------------------------------------
    @classmethod
    def define_table(cls, tablename, *fields, **args):
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
    # Resource configuration
    # -------------------------------------------------------------------------
    @classmethod
    def resource(cls, prefix, name=None, **attr):

        return S3Resource(prefix, name=name, **attr)

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
    # Resource components
    #--------------------------------------------------------------------------
    @classmethod
    def add_component(cls, table, **links):
        """
            Defines a component.

            @param table: the component table or table name
            @param links: the component links
        """

        components = current.model.components

        if not links:
            return
        tablename = table._tablename if type(table) is Table else table
        prefix, name = tablename.split("_", 1)
        for primary in links:
            hooks = components.get(primary, Storage())
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
                    linktable = linktable._tablename \
                                if type(linktable) is Table else linktable
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
            components[primary] = hooks
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
            sequence_name = "%s_%s_Seq" % (tablename, key)
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
                                        types.get(opt, opt),
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
                   updateable=False,
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
                                 updateable=updateable,
                                 not_filterby=not_filterby,
                                 not_filter_opts=not_filter_opts,)
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
        supertable = get_config(tablename, "super_entity")
        if not supertable:
            return True
        elif not isinstance(supertable, (list, tuple)):
            supertable = [supertable]

        # Get the record
        id = record.get("id", None)
        db = current.db
        _record = db(table.id == id).select(table.ALL,
                                            limitby=(0, 1)).first()
        if not _record:
            return True

        super_keys = Storage()
        for s in supertable:
            if isinstance(s, str):
                s = cls.table(s)
            if s is None:
                continue
            # Get the key
            key = cls.super_key(s)
            skey = _record.get(key, None)
            # Get the shared field map
            shared = get_config(tablename, "%s_fields" % s._tablename)
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
                row = db(query).select(s[key], limitby=(0, 1)).first()
            else:
                row = Storage()
            _tablename = s._tablename
            form = Storage(vars=Storage(row))
            if row:
                onaccept = get_config(_tablename, "update_onaccept",
                           get_config(_tablename, "onaccept", None))
                db(s[key] == row[key]).update(**data)
                k = {key:row[key]}
                super_keys.update(k)
                if _record[key] != row[key]:
                    db(table.id == id).update(**k)
                data.update(k)
                if onaccept:
                    form.vars.update(data)
                    onaccept(form)
            else:
                onaccept = get_config(_tablename, "create_onaccept",
                           get_config(_tablename, "onaccept", None))
                k = s.insert(**data)
                if k:
                    db(table.id == id).update(**{key:k})
                    super_keys.update({key:k})
                data.update({key:k})
                if onaccept:
                    form.vars.update(data)
                    onaccept(form)
        record.update(super_keys)
        return True

    # -------------------------------------------------------------------------
    @classmethod
    def delete_super(cls, table, record):
        """
            Removes the super-entity links of an instance record

            @param table: the instance table
            @param record: the instance record
        """

        get_config = cls.get_config
        supertable = get_config(table._tablename, "super_entity")
        if not supertable:
            return True
        if not isinstance(supertable, (list, tuple)):
            supertable = [supertable]

        uid = record.get("uuid", None)
        if uid:
            define_resource = current.s3db.resource
            for s in supertable:
                if isinstance(s, str):
                    s = cls.table(s)
                if s is None:
                    continue
                tn = s._tablename
                resource = define_resource(tn, uid=uid)
                ondelete = get_config(tn, "ondelete")
                resource.delete(ondelete=ondelete, cascade=True)
        return True

    # -------------------------------------------------------------------------
    @classmethod
    def get_instance(cls, supertable, superid):
        """
            Get prefix, name and ID of an instance record

            @param supertable: the super-entity table
            @param superid: the super-entity record ID
            @returns: a tuple (prefix, name, ID) of the instance
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
