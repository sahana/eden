# -*- coding: utf-8 -*-

""" S3 Hierarchy Toolkit

    @copyright: 2013-2019 (c) Sahana Software Foundation
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
"""

__all__ = ("S3Hierarchy", "S3HierarchyCRUD")

import json

from gluon import DIV, FORM, LI, UL, current
from gluon.storage import Storage
from gluon.tools import callback

from s3compat import long, unicodeT, xrange
from .s3utils import s3_str
from .s3rest import S3Method
from .s3widgets import SEPARATORS

DEFAULT = lambda: None

LABEL = "l"

# =============================================================================
class S3HierarchyCRUD(S3Method):
    """ Method handler for hierarchical CRUD """

    # -------------------------------------------------------------------------
    def apply_method(self, r, **attr):
        """
            Entry point for REST interface

            @param r: the S3Request
            @param attr: controller attributes
        """

        if r.http == "GET":
            if r.representation == "html":
                output = self.tree(r, **attr)
            elif r.representation == "json" and "node" in r.get_vars:
                output = self.node_json(r, **attr)
            elif r.representation == "xls":
                output = self.export_xls(r, **attr)
            else:
                r.error(415, current.ERROR.BAD_FORMAT)
        else:
            r.error(405, current.ERROR.BAD_METHOD)

        return output

    # -------------------------------------------------------------------------
    def tree(self, r, **attr):
        """
            Page load

            @param r: the S3Request
            @param attr: controller attributes
        """

        output = {}

        resource = self.resource
        tablename = resource.tablename

        # Widget ID
        widget_id = "%s-hierarchy" % tablename

        # Render the tree
        try:
            tree = self.render_tree(widget_id, record=r.record)
        except SyntaxError:
            r.error(405, "No hierarchy configured for %s" % tablename)

        # Page title
        if r.record:
            title = self.crud_string(tablename, "title_display")
        else:
            title = self.crud_string(tablename, "title_list")
        output["title"] = title

        # Build the form
        form = FORM(DIV(tree,
                        _class="s3-hierarchy-tree",
                        ),
                    _id = widget_id,
                    )
        output["form"] = form

        # Widget options and scripts
        T = current.T
        crud_string = lambda name: self.crud_string(tablename, name)

        widget_opts = {
            "widgetID": widget_id,

            "openLabel": str(T("Open")),
            "openURL": r.url(method="read", id="[id]"),
            "ajaxURL": r.url(id=None, representation="json"),

            "editLabel": str(T("Edit")),
            "editTitle": str(crud_string("title_update")),

            "addLabel": str(T("Add")),
            "addTitle": str(crud_string("label_create")),

            "deleteLabel": str(T("Delete")),
            "deleteRoot": False if r.record else True
        }

        # Check permissions and add CRUD URLs
        resource_config = resource.get_config
        has_permission = current.auth.s3_has_permission
        if resource_config("editable", True) and \
           has_permission("update", tablename):
            widget_opts["editURL"] = r.url(method = "update",
                                           id = "[id]",
                                           representation = "popup",
                                           )

        if resource_config("deletable", True) and \
           has_permission("delete", tablename):
            widget_opts["deleteURL"] = r.url(method = "delete",
                                             id = "[id]",
                                             representation = "json",
                                             )

        if resource_config("insertable", True) and \
           has_permission("create", tablename):
            widget_opts["addURL"] = r.url(method = "create",
                                          representation = "popup",
                                          )

        # Theme options
        theme = current.deployment_settings.get_ui_hierarchy_theme()
        icons = theme.get("icons", False)
        if icons:
            # Only include non-default options
            widget_opts["icons"] = icons
        stripes = theme.get("stripes", True)
        if not stripes:
            # Only include non-default options
            widget_opts["stripes"] = stripes
        self.include_scripts(widget_id, widget_opts)

        # View
        current.response.view = self._view(r, "hierarchy.html")

        return output

    # -------------------------------------------------------------------------
    def node_json(self, r, **attr):
        """
            Return a single node as JSON (id, parent and label)

            @param r: the S3Request
            @param attr: controller attributes
        """

        resource = self.resource
        tablename = resource.tablename

        h = S3Hierarchy(tablename = tablename)
        if not h.config:
            r.error(405, "No hierarchy configured for %s" % tablename)

        data = {}
        node_id = r.get_vars["node"]
        if node_id:
            try:
                node_id = long(node_id)
            except ValueError:
                pass
            else:
                data["node"] = node_id
                label = h.label(node_id)
                data["label"] = label if label else None
                data["parent"] = h.parent(node_id)

                children = h.children(node_id)
                if children:
                    nodes = []
                    h._represent(node_ids=children)
                    for child_id in children:
                        label = h.label(child_id)
                        # @todo: include CRUD permissions?
                        nodes.append({"node": child_id,
                                      "label": label if label else None,
                                      })
                    data["children"] = nodes

        current.response.headers["Content-Type"] = "application/json"
        return json.dumps(data, separators = SEPARATORS)

    # -------------------------------------------------------------------------
    def render_tree(self, widget_id, record=None):
        """
            Render the tree

            @param widget_id: the widget ID
            @param record: the root record (if requested)
        """

        resource = self.resource
        tablename = resource.tablename

        h = S3Hierarchy(tablename = tablename)
        if not h.config:
            raise SyntaxError()

        root = None
        if record:
            try:
                root = record[h.pkey]
            except AttributeError as e:
                # Hierarchy misconfigured? Or has r.record been tampered with?
                msg = "S3Hierarchy: key %s not found in record" % h.pkey
                e.args = tuple([msg] + list(e.args[1:]))
                raise

        # @todo: apply all resource filters?
        return h.html("%s-tree" % widget_id, root=root)

    # -------------------------------------------------------------------------
    @staticmethod
    def include_scripts(widget_id, widget_opts):
        """ Include JS & CSS needed for hierarchical CRUD """

        s3 = current.response.s3
        scripts = s3.scripts
        theme = current.deployment_settings.get_ui_hierarchy_theme()

        # Include static scripts & stylesheets
        script_dir = "/%s/static/scripts" % current.request.application
        if s3.debug:
            script = "%s/jstree.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            script = "%s/S3/s3.ui.hierarchicalcrud.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            style = "%s/jstree.css" % theme.get("css", "plugins")
            if style not in s3.stylesheets:
                s3.stylesheets.append(style)
        else:
            script = "%s/S3/s3.jstree.min.js" % script_dir
            if script not in scripts:
                scripts.append(script)
            style = "%s/jstree.min.css" % theme.get("css", "plugins")
            if style not in s3.stylesheets:
                s3.stylesheets.append(style)

        # Apply the widget JS
        script = '''$('#%(widget_id)s').hierarchicalcrud(%(widget_opts)s)''' % \
                 {"widget_id": widget_id,
                  "widget_opts": json.dumps(widget_opts, separators=SEPARATORS),
                  }
        s3.jquery_ready.append(script)

        return

    # -------------------------------------------------------------------------
    def export_xls(self, r, **attr):
        """
            Export nodes in the hierarchy in XLS format, including
            ancestor references.

            This is controlled by the hierarchy_export setting, which is
            a dict like:
            {
                "field": "name",        - the field name for the ancestor reference
                "root": "Organisation"  - the label for the root level
                "branch": "Branch"      - the label for the branch levels
                "prefix": "Sub"         - the prefix for the branch label
            }

            With this configuration, the ancestor columns would appear like:

            Organisation, Branch, SubBranch, SubSubBranch, SubSubSubBranch,...

            All parts of the setting can be omitted, the defaults are as follows:
            - "field" defaults to "name"
            - "root" is automatically generated from the resource name
            - "branch" defaults to prefix+root
            - "prefix" defaults to "Sub"

            @status: experimental
        """

        resource = self.resource
        tablename = resource.tablename

        # Get the hierarchy
        h = S3Hierarchy(tablename=tablename)
        if not h.config:
            r.error(405, "No hierarchy configured for %s" % tablename)

        # Intepret the hierarchy_export setting for the resource
        setting = resource.get_config("hierarchy_export", {})
        field = setting.get("field")
        if not field:
            field = "name" if "name" in resource.fields else resource._id.name
        prefix = setting.get("prefix", "Sub")
        root = setting.get("root")
        if not root:
            root = "".join(s.capitalize() for s in resource.name.split("_"))
        branch = setting.get("branch")
        if not branch:
            branch = "%s%s" % (prefix, root)

        rfield = resource.resolve_selector(field)

        # Get the list fields
        list_fields = resource.list_fields("export_fields", id_column=False)
        rfields = resource.resolve_selectors(list_fields,
                                             extra_fields=False,
                                             )[0]

        # Selectors = the fields to extract
        selectors = [h.pkey.name, rfield.selector]

        # Columns = the keys for the XLS Codec to access the rows
        # Types = the data types of the columns (in same order!)
        columns = []
        types = []

        # Generate the headers and type list for XLS Codec
        headers = {}
        for rf in rfields:
            selectors.append(rf.selector)
            if rf.colname == rfield.colname:
                continue
            columns.append(rf.colname)
            headers[rf.colname] = rf.label
            if rf.ftype == "virtual":
                types.append("string")
            else:
                types.append(rf.ftype)

        # Get the root nodes
        if self.record_id:
            if r.component and h.pkey.name != resource._id.name:
                query = resource.table._id == self.record_id
                row = current.db(query).select(h.pkey, limitby=(0, 1)).first()
                if not row:
                    r.error(404, current.ERROR.BAD_RECORD)
                roots = {row[h.pkey]}
            else:
                roots = {self.record_id}
        else:
            roots = h.roots

        # Find all child nodes
        all_nodes = h.findall(roots, inclusive=True)

        # ...and extract their data from a clone of the resource
        from .s3query import FS
        query = FS(h.pkey.name).belongs(all_nodes)
        clone = current.s3db.resource(resource, filter=query)
        data = clone.select(selectors, represent=True, raw_data=True)

        # Convert into dict {hierarchy key: row}
        hkey = str(h.pkey)
        data_dict = dict((row._row[hkey], row) for row in data.rows)

        # Add hierarchy headers and types
        depth = max(h.depth(node_id) for node_id in roots)
        htypes = []
        hcolumns = []
        colprefix = "HIERARCHY"
        htype = "string" if rfield.ftype == "virtual" else rfield.ftype
        for level in xrange(depth+1):
            col = "%s.%s" % (colprefix, level)
            if level == 0:
                headers[col] = root
            elif level == 1:
                headers[col] = branch
            else:
                headers[col] = "%s%s" % ("".join([prefix] * (level -1)), branch)
            hcolumns.append(col)
            htypes.append(htype)


        # Generate the output for XLS Codec
        output = [headers, htypes + types]
        for node_id in roots:
            rows = h.export_node(node_id,
                                 prefix = colprefix,
                                 depth=depth,
                                 hcol=rfield.colname,
                                 columns = columns,
                                 data = data_dict,
                                 )
            output.extend(rows)

        # Encode in XLS format
        from .s3codec import S3Codec
        codec = S3Codec.get_codec("xls")
        result = codec.encode(output,
                              title = resource.name,
                              list_fields=hcolumns+columns)

        # Reponse headers and file name are set in codec
        return result

# =============================================================================
class S3Hierarchy(object):
    """ Class representing an object hierarchy """

    # -------------------------------------------------------------------------
    def __init__(self,
                 tablename=None,
                 hierarchy=None,
                 represent=None,
                 filter=None,
                 leafonly=True,
                 ):
        """
            Constructor

            @param tablename: the tablename
            @param hierarchy: the hierarchy setting for the table
                              (replaces the current setting)
            @param represent: a representation method for the node IDs
            @param filter: additional filter query for the table to
                           select the relevant subset
            @param leafonly: filter strictly for leaf nodes
        """

        self.tablename = tablename
        if hierarchy:
            current.s3db.configure(tablename, hierarchy=hierarchy)
        self.represent = represent

        self.filter = filter
        self.leafonly = leafonly

        self.__theset = None
        self.__flags = None

        self.__nodes = None
        self.__roots = None

        self.__pkey = None
        self.__fkey = None
        self.__ckey = None

        self.__link = DEFAULT
        self.__lkey = DEFAULT
        self.__left = DEFAULT

    # -------------------------------------------------------------------------
    @property
    def theset(self):
        """
            The raw nodes dict like:

                {<node_id>: {"p": <parent_id>,
                             "c": <category>,
                             "s": set(child nodes)
                }}
        """

        if self.__theset is None:
            self.__connect()
        if self.__status("dirty"):
            self.read()
        return self.__theset

    # -------------------------------------------------------------------------
    @property
    def flags(self):
        """ Dict of status flags """

        if self.__flags is None:
            theset = self.theset
        return self.__flags

    # -------------------------------------------------------------------------
    @property
    def config(self):
        """ Hierarchy configuration of the target table """

        tablename = self.tablename
        if tablename:
            s3db = current.s3db
            if tablename in current.db or \
               s3db.table(tablename, db_only=True):
                return s3db.get_config(tablename, "hierarchy")
        return None

    # -------------------------------------------------------------------------
    @property
    def nodes(self):
        """ The nodes in the subset """

        theset = self.theset
        if self.__nodes is None:
            self.__subset()
        return self.__nodes

    # -------------------------------------------------------------------------
    @property
    def roots(self):
        """ The IDs of the root nodes in the subset """

        nodes = self.nodes
        return self.__roots

    # -------------------------------------------------------------------------
    @property
    def pkey(self):
        """ The parent key """

        if self.__pkey is None:
            self.__keys()
        return self.__pkey

    # -------------------------------------------------------------------------
    @property
    def fkey(self):
        """ The foreign key referencing the parent key """

        if self.__fkey is None:
            self.__keys()
        return self.__fkey

    # -------------------------------------------------------------------------
    @property
    def link(self):
        """
            The name of the link table containing the foreign key, or
            None if the foreign key is in the hierarchical table itself
        """

        if self.__link is DEFAULT:
            self.__keys()
        return self.__link

    # -------------------------------------------------------------------------
    @property
    def lkey(self):
        """ The key in the link table referencing the child """

        if self.__lkey is DEFAULT:
            self.__keys()
        return self.__lkey

    # -------------------------------------------------------------------------
    @property
    def left(self):
        """ The left join with the link table containing the foreign key """

        if self.__left is DEFAULT:
            self.__keys()
        return self.__left

    # -------------------------------------------------------------------------
    @property
    def ckey(self):
        """ The category field """

        if self.__ckey is None:
            self.__keys()
        return self.__ckey

    # -------------------------------------------------------------------------
    def __connect(self):
        """ Connect this instance to the hierarchy """

        tablename = self.tablename
        if tablename :
            hierarchies = current.model["hierarchies"]
            if tablename in hierarchies:
                hierarchy = hierarchies[tablename]
                self.__theset = hierarchy["nodes"]
                self.__flags = hierarchy["flags"]
            else:
                self.__theset = dict()
                self.__flags = dict()
                self.load()
                hierarchy = {"nodes": self.__theset,
                             "flags": self.__flags}
                hierarchies[tablename] = hierarchy
        else:
            self.__theset = dict()
            self.__flags = dict()
        return

    # -------------------------------------------------------------------------
    def __status(self, flag=None, default=None, **attr):
        """
            Check or update status flags

            @param flag: the name of the status flag to return
            @param default: the default value if the flag is not set
            @param attr: key-value pairs for flags to set

            @return: the value of the requested flag, or all flags
                     as dict if no flag was specified
        """

        flags = self.flags
        for k, v in attr.items():
            if v is not None:
                flags[k] = v
            else:
                flags.pop(k, None)
        if flag is not None:
            return flags.get(flag, default)
        return flags

    # -------------------------------------------------------------------------
    def load(self):
        """ Try loading the hierarchy from s3_hierarchy """

        if not self.config:
            return
        tablename = self.tablename

        if not self.__status("dbstatus", True):
            # Cancel attempt if DB is known to be dirty
            self.__status(dirty=True)
            return

        htable = current.s3db.s3_hierarchy
        query = (htable.tablename == tablename)
        row = current.db(query).select(htable.dirty,
                                       htable.hierarchy,
                                       limitby=(0, 1)).first()
        if row and not row.dirty:
            data = row.hierarchy
            theset = self.__theset
            theset.clear()
            for node_id, item in data["nodes"].items():
                theset[long(node_id)] = {"p": item["p"],
                                         "c": item["c"],
                                         "s": set(item["s"]) \
                                              if item["s"] else set()}
            self.__status(dirty=False,
                          dbupdate=None,
                          dbstatus=True)
            return
        else:
            self.__status(dirty=True,
                          dbupdate=None,
                          dbstatus=False if row else None)
        return

    # -------------------------------------------------------------------------
    def save(self):
        """ Save this hierarchy in s3_hierarchy """

        if not self.config:
            return
        tablename = self.tablename

        theset = self.theset
        if not self.__status("dbupdate"):
            return

        # Serialize the theset
        nodes_dict = {}
        for node_id, node in theset.items():
            nodes_dict[node_id] = {"p": node["p"],
                                   "c": node["c"],
                                   "s": list(node["s"]) \
                                        if node["s"] else []}

        # Generate record
        data = {"tablename": tablename,
                "dirty": False,
                "hierarchy": {"nodes": nodes_dict}
                }

        # Get current entry
        htable = current.s3db.s3_hierarchy
        query = (htable.tablename == tablename)
        row = current.db(query).select(htable.id,
                                       limitby=(0, 1)).first()

        if row:
            # Update record
            row.update_record(**data)
        else:
            # Create new record
            htable.insert(**data)

        # Update status
        self.__status(dirty=False, dbupdate=None, dbstatus=True)
        return

    # -------------------------------------------------------------------------
    @classmethod
    def dirty(cls, tablename):
        """
            Mark this hierarchy as dirty. To be called when the target
            table gets updated (can be called repeatedly).

            @param tablename: the tablename
        """

        s3db = current.s3db

        if not tablename:
            return
        config = s3db.get_config(tablename, "hierarchy")
        if not config:
            return

        hierarchies = current.model["hierarchies"]
        if tablename in hierarchies:
            hierarchy = hierarchies[tablename]
            flags = hierarchy["flags"]
        else:
            flags = {}
            hierarchies[tablename] = {"nodes": dict(),
                                      "flags": flags}
        flags["dirty"] = True

        dbstatus = flags.get("dbstatus", True)
        if dbstatus:
            htable = current.s3db.s3_hierarchy
            query = (htable.tablename == tablename)
            row = current.db(query).select(htable.id,
                                           htable.dirty,
                                           limitby=(0, 1)).first()
            if not row:
                htable.insert(tablename=tablename, dirty=True)
            elif not row.dirty:
                row.update_record(dirty=True)
            flags["dbstatus"] = False
        return

    # -------------------------------------------------------------------------
    def read(self):
        """ Rebuild this hierarchy from the target table """

        tablename = self.tablename
        if not tablename:
            return

        s3db = current.s3db
        table = s3db[tablename]

        pkey = self.pkey
        fkey = self.fkey
        ckey = self.ckey

        fields = [pkey, fkey]
        if ckey is not None:
            fields.append(table[ckey])

        if "deleted" in table:
            query = (table.deleted != True)
        else:
            query = (table.id > 0)
        rows = current.db(query).select(left = self.left, *fields)

        self.__theset.clear()

        add = self.add
        cfield = table[ckey]
        for row in rows:
            n = row[pkey]
            p = row[fkey]
            if ckey:
                c = row[cfield]
            else:
                c = None
            add(n, parent_id=p, category=c)

        # Update status: memory is clean, db needs update
        self.__status(dirty=False, dbupdate=True)

        # Remove subset
        self.__roots = None
        self.__nodes = None

        return

    # -------------------------------------------------------------------------
    def __keys(self):
        """ Introspect the key fields in the hierarchical table """

        tablename = self.tablename
        if not tablename:
            return

        s3db = current.s3db
        table = s3db[tablename]

        config = s3db.get_config(tablename, "hierarchy")
        if not config:
            return

        if isinstance(config, tuple):
            parent, self.__ckey = config[:2]
        else:
            parent, self.__ckey = config, None

        pkey = None
        fkey = None
        if parent is None:

            # Assume self-reference
            pkey = table._id

            for field in table:
                ftype = str(field.type)
                if ftype[:9] == "reference":
                    key = ftype[10:].split(".")
                    if key[0] == tablename and \
                       (len(key) == 1 or key[1] == pkey.name):
                        parent = field.name
                        fkey = field
                        break
        else:
            resource = s3db.resource(tablename)
            master = resource.tablename

            rfield = resource.resolve_selector(parent)
            ltname = rfield.tname

            if ltname == master:
                # Self-reference
                fkey = rfield.field
                self.__link = None
                self.__lkey = None
                self.__left = None
            else:
                # Link table

                # Use the parent selector to find the link resource
                alias = parent.split(".%s" % rfield.fname)[0]
                calias = s3db.get_alias(master, alias)
                if not calias:
                    # Fall back to link table name
                    alias = ltname.split("_", 1)[1]
                    calias = s3db.get_alias(master, alias)

                # Load the component and get the link parameters
                if calias:
                    component = resource.components.get(calias)
                    link = component.link
                    if link:
                        fkey = rfield.field
                        self.__link = ltname
                        self.__lkey = link.fkey
                        self.__left = rfield.left.get(ltname)

        if not fkey:
            # No parent field found
            raise AttributeError("parent link not found")

        if pkey is None:
            ftype = str(fkey.type)
            if ftype[:9] != "reference":
                # Invalid parent field (not a foreign key)
                raise SyntaxError("Invalid parent field: "
                                  "%s is not a foreign key" % fkey)
            key = ftype[10:].split(".")
            if key[0] == tablename:
                # Self-reference
                pkey = table._id
            else:
                # Super-entity?
                ktable = s3db[key[0]]
                skey = ktable._id.name
                if skey != "id" and "instance_type" in ktable:
                    try:
                        pkey = table[skey]
                    except AttributeError:
                        raise SyntaxError("%s is not an instance type of %s" %
                                          (tablename, ktable._tablename))

        self.__pkey = pkey
        self.__fkey = fkey
        return

    # -------------------------------------------------------------------------
    def preprocess_create_node(self, r, parent_id):
        """
            Pre-process a CRUD request to create a new node

            @param r: the request
            @param table: the hierarchical table
            @param parent_id: the parent ID
        """

        # Make sure the parent record exists
        table = current.s3db.table(self.tablename)
        query = (table[self.pkey.name] == parent_id)
        DELETED = current.xml.DELETED
        if DELETED in table.fields:
            query &= table[DELETED] != True
        parent = current.db(query).select(table._id).first()
        if not parent:
            raise KeyError("Parent record not found")

        link = self.link
        fkey = self.fkey
        if self.link is None:
            # Parent field in table
            fkey.default = fkey.update = parent_id
            fkey.comment = None
            if r.http == "POST":
                r.post_vars[fkey.name] = parent_id
            fkey.readable = fkey.writable = False
            link = None
        else:
            # Parent field in link table
            link = {"linktable": self.link,
                    "rkey": fkey.name,
                    "lkey": self.lkey,
                    "parent_id": parent_id,
                    }
        return link

    # -------------------------------------------------------------------------
    def postprocess_create_node(self, link, node):
        """
            Create a link table entry for a new node

            @param link: the link information (as returned from
                         preprocess_create_node)
            @param node: the new node
        """

        try:
            node_id = node[self.pkey.name]
        except (AttributeError, KeyError):
            return

        s3db = current.s3db
        tablename = link["linktable"]
        linktable = s3db.table(tablename)
        if not linktable:
            return

        lkey = link["lkey"]
        rkey = link["rkey"]
        data = {rkey: link["parent_id"],
                lkey: node_id,
                }

        # Create the link if it does not already exist
        query = ((linktable[lkey] == data[lkey]) &
                 (linktable[rkey] == data[rkey]))
        row = current.db(query).select(linktable._id, limitby=(0, 1)).first()
        if not row:
            onaccept = s3db.get_config(tablename, "create_onaccept")
            if onaccept is None:
                onaccept = s3db.get_config(tablename, "onaccept")
            link_id = linktable.insert(**data)
            data[linktable._id.name] = link_id
            s3db.update_super(linktable, data)
            if link_id and onaccept:
                callback(onaccept, Storage(vars=Storage(data)))
        return

    # -------------------------------------------------------------------------
    def delete(self, node_ids, cascade=False):
        """
            Recursive deletion of hierarchy branches

            @param node_ids: the parent node IDs of the branches to be deleted
            @param cascade: cascade call, do not commit (internal use)

            @return: number of deleted nodes, or None if cascade failed
        """

        if not self.config:
            return None

        tablename = self.tablename

        total = 0
        for node_id in node_ids:

            # Recursively delete child nodes
            children = self.children(node_id)
            if children:
                result = self.delete(children, cascade=True)
                if result is None:
                    if not cascade:
                        current.db.rollback()
                    return None
                else:
                    total += result

            # Delete node
            from .s3query import FS
            query = (FS(self.pkey.name) == node_id)
            resource = current.s3db.resource(tablename, filter=query)
            success = resource.delete(cascade=True)
            if success:
                self.remove(node_id)
                total += 1
            else:
                if not cascade:
                    current.db.rollback()
                return None

        if not cascade and total:
            self.dirty(tablename)

        return total

    # -------------------------------------------------------------------------
    def add(self, node_id, parent_id=None, category=None):
        """
            Add a new node to the hierarchy

            @param node_id: the node ID
            @param parent_id: the parent node ID
            @param category: the category
        """

        theset = self.__theset

        if node_id in theset:
            node = theset[node_id]
            if category is not None:
                node["c"] = category
        elif node_id:
            node = {"s": set(), "c": category}
        else:
            raise SyntaxError

        if parent_id:
            if parent_id not in theset:
                parent = self.add(parent_id, None, None)
            else:
                parent = theset[parent_id]
            parent["s"].add(node_id)
        node["p"] = parent_id

        theset[node_id] = node
        return node

    # -------------------------------------------------------------------------
    def remove(self, node_id):
        """
            Remove a node from the hierarchy

            @param node_id: the node ID
        """

        theset = self.__theset

        if node_id in theset:
            node = theset[node_id]
        else:
            return False

        parent_id = node["p"]
        if parent_id:
            parent = theset[parent_id]
            parent["s"].discard(node_id)
        del theset[node_id]
        return True

    # -------------------------------------------------------------------------
    def __subset(self):
        """ Generate the subset of accessible nodes which match the filter """

        theset = self.theset

        roots = set()
        subset = {}

        resource = current.s3db.resource(self.tablename,
                                         filter = self.filter)

        pkey = self.pkey
        rows = resource.select([pkey.name], as_rows = True)

        if rows:
            key = str(pkey)
            if self.leafonly:
                # Select matching leaf nodes
                ids = set()
                for row in rows:
                    node_id = row[key]
                    if node_id in theset and not theset[node_id]["s"]:
                        ids.add(node_id)
            else:
                # Select all matching nodes
                ids = set(row[key] for row in rows)

            # Resolve the paths
            while ids:
                node_id = ids.pop()
                if node_id in subset:
                    continue
                node = theset.get(node_id)
                if not node:
                    continue
                parent_id = node["p"]
                if parent_id and parent_id not in subset:
                    ids.add(parent_id)
                elif not parent_id:
                    roots.add(node_id)
                subset[node_id] = dict(node)

            # Update the descendants
            for node in subset.values():
                node["s"] = set(node_id for node_id in node["s"]
                                        if node_id in subset)

        self.__roots = roots
        self.__nodes = subset
        return

    # -------------------------------------------------------------------------
    def category(self, node_id):
        """
            Get the category of a node

            @param node_id: the node ID

            @return: the node category
        """

        node = self.nodes.get(node_id)
        if not node:
            return None
        else:
            return node["c"]

    # -------------------------------------------------------------------------
    def parent(self, node_id, classify=False):
        """
            Get the parent node of a node

            @param node_id: the node ID
            @param classify: return the root node as tuple (id, category)
                             instead of just id

            @return: the root node ID (or tuple (id, category), respectively)
        """

        nodes = self.nodes

        default = (None, None) if classify else None

        node = nodes.get(node_id)
        if not node:
            return default

        parent_id = node["p"]
        if not parent_id:
            return default

        parent_node = nodes.get(parent_id)
        if not parent_node:
            return default

        parent_category = parent_node["c"]
        return (parent_id, parent_category) if classify else parent_id

    # -------------------------------------------------------------------------
    def children(self, node_id, category=DEFAULT, classify=False):
        """
            Get child nodes of a node

            @param node_id: the node ID
            @param category: return only children of this category
            @param classify: return each node as tuple (id, category) instead
                             of just ids

            @return: the child nodes as Python set
        """

        nodes = self.nodes
        default = set()

        node = nodes.get(node_id)
        if not node:
            return default

        child_ids = node["s"]
        if not child_ids:
            return default

        children = set()
        for child_id in child_ids:
            child_node = nodes.get(child_id)
            if not child_node:
                continue
            child_category = child_node["c"]
            child = (child_id, child_category) if classify else child_id
            if category is DEFAULT or category == child_category:
                children.add(child)
        return children

    # -------------------------------------------------------------------------
    def path(self, node_id, category=DEFAULT, classify=False):
        """
            Return the ancestor path of a node

            @param node_id: the node ID
            @param category: start with this category rather than with root
            @param classify: return each node as tuple (id, category) instead
                             of just ids

            @return: the path as list, starting at the root node
        """

        nodes = self.nodes

        node = nodes.get(node_id)
        if not node:
            return []
        this = (node_id, node["c"]) if classify else node_id
        if category is not DEFAULT and node["c"] == category:
            return [this]
        parent_id = node["p"]
        if not parent_id:
            return [this]
        path = self.path(parent_id, category=category, classify=classify)
        path.append(this)
        return path

    # -------------------------------------------------------------------------
    def root(self, node_id, category=DEFAULT, classify=False):
        """
            Get the root node for a node. Returns the node if it is the
            root node itself.

            @param node_id: the node ID
            @param category: find the closest node of this category rather
                             than the absolute root
            @param classify: return the root node as tuple (id, category)
                             instead of just id

            @return: the root node ID (or tuple (id, category), respectively)
        """

        nodes = self.nodes
        default = (None, None) if classify else None

        node = nodes.get(node_id)
        if not node:
            return default
        this = (node_id, node["c"]) if classify else node_id
        if category is not DEFAULT and node["c"] == category:
            return this
        parent_id = node["p"]
        if not parent_id:
            return this if category is DEFAULT else default
        return self.root(parent_id, category=category, classify=classify)

    # -------------------------------------------------------------------------
    def depth(self, node_id, level=0):
        """
            Determine the depth of a hierarchy

            @param node_id: the start node (default to all root nodes)
        """

        nodes = self.nodes
        depth = self.depth

        node = nodes.get(node_id)
        if not node:
            roots = self.roots
            result = max(depth(root) for root in roots)
        else:
            children = node["s"]
            if children:
                result = max(depth(n, level=level+1) for n in children)
            else:
                result = level
        return result

    # -------------------------------------------------------------------------
    def siblings(self,
                 node_id,
                 category=DEFAULT,
                 classify=False,
                 inclusive=False):
        """
            Get the sibling nodes of a node. If the node is a root node,
            this method returns all root nodes.

            @param node_id: the node ID
            @param category: return only nodes of this category
            @param classify: return each node as tuple (id, category)
                             instead of just id
            @param inclusive: include the start node

            @param return: a set of node IDs
                           (or tuples (id, category), respectively)
        """

        result = set()
        nodes = self.nodes

        node = nodes.get(node_id)
        if not node:
            return result

        parent_id = node["p"]
        if not parent_id:
            siblings = [(k, nodes[k]) for k in self.roots]
        else:
            parent = nodes[parent_id]
            if parent["s"]:
                siblings = [(k, nodes[k]) for k in parent["s"]]
            else:
                siblings = []

        add = result.add
        for sibling_id, sibling_node in siblings:
            if not inclusive and sibling_id == node_id:
                continue
            if category is DEFAULT or category == sibling_node["c"]:
                sibling = (sibling_id, sibling_node["c"]) \
                          if classify else sibling_id
                add(sibling)
        return result

    # -------------------------------------------------------------------------
    def findall(self,
                node_id,
                category=DEFAULT,
                classify=False,
                inclusive=False):
        """
            Find descendant nodes of a node

            @param node_id: the node ID (can be an iterable of node IDs)
            @param category: find nodes of this category
            @param classify: return each node as tuple (id, category) instead
                             of just ids
            @param inclusive: include the start node(s) if they match

            @return: a set of node IDs (or tuples (id, category), respectively)
        """

        result = set()
        findall = self.findall
        if isinstance(node_id, (set, list, tuple)):
            for n in node_id:
                if n is None:
                    continue
                result |= findall(n,
                                  category=category,
                                  classify=classify,
                                  inclusive=inclusive)
            return result
        nodes = self.nodes
        node = nodes.get(node_id)
        if not node:
            return result
        if node["s"]:
            result |= findall(node["s"],
                              category=category,
                              classify=classify,
                              inclusive=True)
        if inclusive:
            this = (node_id, node["c"]) if classify else node_id
            if category is DEFAULT or category == node["c"]:
                result.add(this)
        return result

    # -------------------------------------------------------------------------
    def _represent(self, node_ids=None, renderer=None):
        """
            Represent nodes as labels, the labels are stored in the
            nodes as attribute "l".

            @param node_ids: the node IDs (None for all nodes)
            @param renderer: the representation method (falls back
                             to the "name" field in the target table
                             if present)
        """

        theset = self.theset

        if node_ids is None:
            node_ids = self.nodes.keys()

        pending = set()
        for node_id in node_ids:
            node = theset.get(node_id)
            if not node:
                continue
            if LABEL not in node:
                pending.add(node_id)

        if renderer is None:
            renderer = self.represent
        if renderer is None:
            tablename = self.tablename
            table = current.s3db.table(tablename) if tablename else None
            if table and "name" in table.fields:
                from .s3fields import S3Represent
                self.represent = renderer = S3Represent(lookup = tablename,
                                                        key = self.pkey.name)
            else:
                renderer = s3_str
        if hasattr(renderer, "bulk"):
            labels = renderer.bulk(list(pending), list_type = False)
            for node_id, label in labels.items():
                if node_id in theset:
                    theset[node_id][LABEL] = label
        else:
            for node_id in pending:
                try:
                    label = renderer(node_id)
                except:
                    label = s3_str(node_id)
                theset[node_id][LABEL] = label
        return

    # -------------------------------------------------------------------------
    def label(self, node_id, represent=None):
        """
            Get a label for a node

            @param node_id: the node ID
            @param represent: the node ID representation method
        """

        theset = self.theset
        node = theset.get(node_id)
        if node:
            if LABEL in node:
                label = node[LABEL]
            else:
                self._represent(node_ids=[node_id], renderer=represent)
            if LABEL in node:
                label = node[LABEL]
            if type(label) is unicodeT:
                label = s3_str(label)
            return label
        return None

    # -------------------------------------------------------------------------
    def repr_expand(self, node_ids, levels=None, represent=None):
        """
            Helper function to represent a set of nodes as lists
            of their respective ancestors starting by the root node

            @param node_ids: the node_ids (iterable)
            @param levels: the number of levels to include (counting from root)
            @param represent: a representation function for each ancestor

            @returns: a dict {node_id: ["Label", "Label", ...]}
                      => each label list is padded with "-" to reach the
                         requested number of levels (TODO make this configurable)
        """

        paths = {}
        all_parents = set()
        for node_id in node_ids:
            paths[node_id] = path = self.path(node_id)
            all_parents |= set(path)

        self._represent(all_parents, renderer=represent)

        theset = self.theset
        result = {}
        for node_id, path in paths.items():
            p = (path + [None] * levels)[:levels]
            l = [theset[parent][LABEL] if parent else "-" for parent in p]
            result[node_id] = l

        return result

    # -------------------------------------------------------------------------
    def _json(self, node_id, represent=None, depth=0, max_depth=None):
        """
            Represent a node as JSON-serializable array

            @param node_id: the node ID
            @param represent: the representation method
            @param depth: the current recursion depth
            @param max_depth: the maximum recursion depth

            @returns: the node as [label, category, subnodes],
                      with subnodes as:
                        - False: if there are no subnodes
                        - True: if there are subnodes beyond max_depth
                        - otherwise: {node_id: [label, category, subnodes], ...}
        """

        node = self.nodes.get(node_id)
        if not node:
            return None

        label = self.label(node_id, represent=represent)
        if label is None:
            label = node_id

        category = node["c"]
        subnode_ids = node["s"]
        if subnode_ids:
            if max_depth and depth == max_depth:
                subnodes = True
            else:
                subnodes = {}
                for subnode_id in subnode_ids:
                    item = self._json(subnode_id,
                                      represent = represent,
                                      depth = depth + 1,
                                      max_depth = max_depth,
                                      )
                    if item:
                        subnodes[subnode_id] = item
        else:
            subnodes = False

        return [s3_str(label), category, subnodes]

    # -------------------------------------------------------------------------
    def json(self, root=None, represent=None, max_depth=None):
        """
            Represent the hierarchy as JSON-serializable dict

            @param root: the root node ID (or array of root node IDs)
            @param represent: the representation method
            @param max_depth: maximum recursion depth

            @returns: the hierarchy as dict:
                         {node_id: [label, category, subnodes], ...}
        """

        self._represent(renderer=represent)

        roots = [root] if root else self.roots

        output = {}
        for node_id in roots:
            item = self._json(node_id,
                              represent = represent,
                              max_depth = max_depth,
                              )
            if item:
                output[node_id] = item

        return output

    # -------------------------------------------------------------------------
    def html(self,
             widget_id,
             root=None,
             represent=None,
             hidden=True,
             none=None,
             _class=None):
        """
            Render this hierarchy as nested unsorted list

            @param widget_id: a unique ID for the HTML widget
            @param root: node ID of the start node (defaults to all
                         available root nodes)
            @param represent: the representation method for the node IDs
            @param hidden: render with style display:none
            @param _class: the HTML class for the outermost list

            @return: the list (UL)
        """

        self._represent(renderer=represent)

        roots = [root] if root else self.roots

        html = self._html
        output = UL([html(node_id, widget_id, represent=represent)
                    for node_id in roots],
                    _id=widget_id,
                    _style="display:none" if hidden else None)
        if _class:
            output.add_class(_class)
        if none:
            if none is True:
                none = current.messages["NONE"]
            output.insert(0, LI(none,
                                _id="%s-None" % widget_id,
                                _rel = "none",
                                _class = "s3-hierarchy-node s3-hierarchy-none",
                                ))
        return output

    # -------------------------------------------------------------------------
    def _html(self, node_id, widget_id, represent=None):
        """
            Recursively render a node as list item (with subnodes
            as unsorted list inside the item)

            @param node_id: the node ID
            @param widget_id: the unique ID for the outermost list
            @param represent: the node ID representation method

            @return: the list item (LI)

            @todo: option to add CRUD permissions
        """

        node = self.nodes.get(node_id)
        if not node:
            return None

        label = self.label(node_id, represent=represent)
        if label is None:
            label = s3_str(node_id)

        subnodes = node["s"]
        item = LI(label,
                  _id = "%s-%s" % (widget_id, node_id),
                  _rel = "parent" if subnodes else "leaf",
                  _class = "s3-hierarchy-node",
                  )

        html = self._html
        if subnodes:
            sublist = UL([html(n, widget_id, represent=represent)
                         for n in subnodes])
            item.append(sublist)
        return item

    # -------------------------------------------------------------------------
    def export_node(self,
                    node_id,
                    prefix = "_hierarchy",
                    depth=None,
                    level=0,
                    path=None,
                    hcol=None,
                    columns = None,
                    data = None,
                    node_list=None):
        """
            Export the hierarchy beneath a node

            @param node_id: the root node
            @param prefix: prefix for the hierarchy column in the output
            @param depth: the maximum depth to export
            @param level: the current recursion level (internal)
            @param path: the path dict for this node (internal)
            @param hcol: the hierarchy column in the input data
            @param columns: the list of columns to export
            @param data: the input data dict {node_id: row}
            @param node_list: the output data list (will be appended to)

            @returns: the output data list

            @todo: pass the input data as list and retain the original
                   order when recursing into child nodes?
        """

        if node_list is None:
            node_list = []

        # Do not recurse deeper than depth levels below the root node
        if depth is not None and level > depth:
            return node_list

        # Get the current node
        node = self.nodes.get(node_id)
        if not node:
            return node_list

        # Get the node data
        if data:
            if node_id not in data:
                return node_list
            node_data = data.get(node_id)
        else:
            node_data = {}

        # Generate the path dict if it doesn't exist yet
        if path is None:
            if depth is None:
                depth = self.depth(node_id)
            path = dict(("%s.%s" % (prefix, l), "") for l in xrange(depth+1))

        # Set the hierarchy column
        label = node_data.get(hcol) if hcol else node_id
        path["%s.%s" % (prefix, level)] = label

        # Add remaining columns to the record dict
        record = dict(path)
        if columns:
            for column in columns:
                if columns == hcol:
                    continue
                record[column] = node_data.get(column)

        # Append the record to the node list
        node_list.append(record)

        # Recurse into child nodes
        children = node["s"]
        for child in children:
            self.export_node(child,
                             prefix = prefix,
                             depth=depth,
                             level=level+1,
                             path=dict(path),
                             hcol=hcol,
                             columns=columns,
                             data=data,
                             node_list=node_list,
                             )
        return node_list

# END =========================================================================
