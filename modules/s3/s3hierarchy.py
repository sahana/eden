# -*- coding: utf-8 -*-

""" S3 Hierarchy Toolkit

    @copyright: 2013 (c) Sahana Software Foundation
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

    @status: experimental
"""

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from s3utils import s3_unicode

DEFAULT = lambda: None

# =============================================================================
class S3Hierarchy(object):
    """ Class representing an object hierarchy """

    # -------------------------------------------------------------------------
    def __init__(self, tablename=None, hierarchy=None, represent=None):
        """
            Constructor

            @param tablename: the tablename
            @param hierarchy: the hierarchy setting for the table
                              (replaces the current setting)
            @param represent: a representation method for the node IDs
        """

        self.tablename = tablename
        if hierarchy:
            current.s3db.configure(tablename, hierarchy=hierarchy)
        self.represent = represent

        self.__roots = None
        self.__nodes = None
        self.__flags = None
        
    # -------------------------------------------------------------------------
    @property
    def roots(self):
        """ Set of root node IDs """

        nodes = self.nodes
        return self.__roots

    # -------------------------------------------------------------------------
    @property
    def nodes(self):
        """
            The nodes dict like:

                {<node_id>: {"p": <parent_id>,
                             "c": <category>,
                             "s": set(child nodes)
                }}
        """

        if self.__nodes is None:
            self.__connect()
        if self.__status("dirty"):
            self.read()
        return self.__nodes

    # -------------------------------------------------------------------------
    @property
    def flags(self):
        """ Dict of status flags """

        if self.__flags is None:
            nodes = self.nodes
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
    def __connect(self):
        """ Connect this instance to the hierarchy """

        tablename = self.tablename
        if tablename :
            hierarchies = current.model.hierarchies
            if tablename in hierarchies:
                hierarchy = hierarchies[tablename]
                self.__roots = hierarchy["roots"]
                self.__nodes = hierarchy["nodes"]
                self.__flags = hierarchy["flags"]
            else:
                self.__roots = set()
                self.__nodes = dict()
                self.__flags = dict()
                self.load()
                hierarchy = {"roots": self.__roots,
                             "nodes": self.__nodes,
                             "flags": self.__flags}
                hierarchies[tablename] = hierarchy
        else:
            self.__roots = set()
            self.__nodes = dict()
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
            nodes = self.__nodes
            nodes.clear()
            for node_id, item in data["nodes"].items():
                nodes[long(node_id)] = {"p": item["p"],
                                        "c": item["c"],
                                        "s": set(item["s"]) \
                                             if item["s"] else set()}
            roots = self.__roots
            roots.clear()
            roots.update(set(data["roots"]))
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

        nodes = self.nodes
        if not self.__status("dbupdate"):
            return
            
        # Serialize the nodes
        nodes_dict = dict()
        for node_id, node in nodes.items():
            nodes_dict[node_id] = {"p": node["p"],
                                   "c": node["c"],
                                   "s": list(node["s"]) \
                                        if node["s"] else []}

        # Generate record
        data = {"tablename": tablename,
                "dirty": False,
                "hierarchy": {"roots": list(self.__roots),
                              "nodes": nodes_dict
                             }
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
        
        hierarchies = current.model.hierarchies
        if tablename in hierarchies:
            hierarchy = hierarchies[tablename]
            flags = hierarchy["flags"]
        else:
            flags = {}
            hierarchies[tablename] = {"roots": set(),
                                      "nodes": dict(),
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
        
        config = s3db.get_config(tablename, "hierarchy")
        if not config:
            return
            
        if isinstance(config, tuple):
            parent, category = config[:2]
        else:
            parent, category = config, None
        if parent is None:
            pkey = table._id.name
            parent_field = None
            for field in table:
                ftype = str(field.type)
                if ftype[:9] == "reference":
                    key = ftype[10:].split(".")
                    if key[0] == tablename and \
                       (len(key) == 1 or key[1] == pkey):
                        parent = field.name
                        parent_field = field
                        break
        else:
            parent_field = table[parent]
        if not parent_field:
            raise AttributeError
            
        fields = [table._id, parent_field]
        if category is not None:
            fields.append(table[category])

        if "deleted" in table:
            query = (table.deleted != True)
        else:
            query = (table.id > 0)
        rows = current.db(query).select(*fields)

        self.__nodes.clear()
        self.__roots.clear()
        
        add = self.add
        for row in rows:
            n = row[table._id.name]
            p = row[parent]
            if category:
                c = row[category]
            else:
                c = None
            add(n, parent_id=p, category=c)

        # Update status: memory is clean, db needs update
        self.__status(dirty=False, dbupdate=True)
        return

    # -------------------------------------------------------------------------
    def add(self, node_id, parent_id=None, category=None):
        """
            Add a new node to the hierarchy

            @param node_id: the node ID
            @param parent_id: the parent node ID
            @param category: the category
        """

        nodes = self.__nodes
        roots = self.__roots

        if node_id in nodes:
            node = nodes[node_id]
            if category is not None:
                node["c"] = category
        elif node_id:
            node = {"s": set(), "c": category}
        else:
            raise SyntaxError

        if parent_id:
            if parent_id not in nodes:
                parent = self.add(parent_id, None, None)
            else:
                parent = nodes[parent_id]
            parent["s"].add(node_id)
            roots.discard(node_id)
        else:
            roots.add(node_id)
        node["p"] = parent_id

        nodes[node_id] = node
        return node

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
                result.add(sibling)
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
        
        if hasattr(node_id, "__iter__"):
            for n in node_id:
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

        nodes = self.nodes
        LABEL = "l"

        if node_ids is None:
            node_ids = nodes.keys()

        pending = set()
        for node_id in node_ids:
            node = nodes.get(node_id)
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
                from s3fields import S3Represent
                self.represent = renderer = S3Represent(lookup=tablename)
            else:
                renderer = s3_unicode
        if hasattr(renderer, "bulk"):
            labels = renderer.bulk(list(pending), list_type = False)
            for node_id, label in labels.items():
                if node_id in nodes:
                    nodes[node_id][LABEL] = label
        else:
            for node_id in pending:
                try:
                    label = renderer(node_id)
                except:
                    label = s3_unicode(node_id)
                nodes[node_id][LABEL] = label
        return

    # -------------------------------------------------------------------------
    def label(self, node_id, represent=None):
        """
            Get a label for a node

            @param node_id: the node ID
            @param represent: the node ID representation method
        """

        LABEL = "l"

        nodes = self.nodes
        node = nodes.get(node_id)
        if node:
            if LABEL in node:
                return node[LABEL]
            else:
                self._represent(node_ids=[node_id], renderer=represent)
            if LABEL in node:
                return node[LABEL]
        return None

    # -------------------------------------------------------------------------
    def html(self, widget_id, represent=None, hidden=True, _class=None):
        """
            Render this hierarchy as nested unsorted list

            @param widget_id: a unique ID for the HTML widget
            @param represent: the representation method for the node IDs
            @param hidden: render with style display:none
            @param _class: the HTML class for the outermost list

            @return: the list (UL)
        """

        self._represent(renderer=represent)

        html = self._html
        output = UL([html(node_id, widget_id, represent=represent)
                    for node_id in self.roots],
                    _id=widget_id,
                    _style="display:none" if hidden else None)
        if _class:
            output.add_class(_class)
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
        """

        node = self.nodes.get(node_id)
        if not node:
            return None

        label = self.label(node_id, represent=represent)
        if label is None:
            label = s3_unicode(node_id)

        item = LI(A(label, _href="#", _class="s3-hierarchy-node"),
                  _id="%s-%s" % (widget_id, node_id))

        html = self._html
        subnodes = node["s"]
        if subnodes:
            sublist = UL([html(n, widget_id, represent=represent)
                         for n in subnodes])
            item.append(sublist)
        return item

# END =========================================================================
