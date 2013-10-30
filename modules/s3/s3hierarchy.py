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
"""

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *

DEFAULT = lambda: None

# =============================================================================
class S3Hierarchy(object):
    """ Class representing an object hierarchy """

    # -------------------------------------------------------------------------
    def __init__(self, tablename=None):
        """
            Constructor

            @param tablename: the name of the hierarchy table, for DB
                              persistance (None to disable)
        """

        self.tablename = tablename

        self.roots = set()
        self.nodes = dict()

    # -------------------------------------------------------------------------
    def add(self, node_id, parent_id=None, category=None):
        """
            Add (or update) a node to the hierarchy

            @param node_id: the new node ID
            @param parent_id: the parent node ID
            @param category: the node category

            @return: the node as dict
        """

        nodes = self.nodes
        
        # Every node is a dict:
        #
        # {
        #   "p": ID of the parent node
        #   "c": category
        #   "s": {set of sub-node IDs}
        #   "r": representation of this node
        # }
        #
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
            self.roots.discard(node_id)
        else:
            self.roots.add(node_id)
        node["p"] = parent_id
            
        nodes[node_id] = node
        
        return node
        
    # -------------------------------------------------------------------------
    @classmethod
    def read(cls, table, parent=None, category=None):
        """
            Read a hierarchy from a database table. The database table
            must implement a foreign key to itself (parent key), and
            can implement a field that encodes the category.

            @param table: the Table (or tablename)
            @param parent: name of the parent key field
            @param category: name of the category field

            @return: the S3Hierarchy instance
        """
        
        if not hasattr(table, "_tablename"):
            table = current.s3db[table]
            
        if parent is None:
            # Find the parent field
            parent_field = None
            for field in table:
                ftype = str(field.type)
                if ftype[:9] == "reference":
                    key = ftype[10:].split(".")
                    if key[0] == tablename and \
                       (len(key) == 1 or key[1] == table._id.name):
                        parent = field.name
                        parent_field = field
                        break
        else:
            parent_field = table[parent]
        if not parent_field:
            raise AttributeError

        fields = [table._id, parent_field]
        if category:
            fields.append(table[category])
       
        if "deleted" in table:
            query = (table.deleted != True)
        else:
            query = (table.id > 0)

        rows = current.db(query).select(*fields)

        hierarchy = cls()
        add = hierarchy.add
        
        for row in rows:
            n = row[table._id.name]
            p = row[parent]
            if category:
                c = row[category]
            else:
                c = None
            add(n, parent_id=p, category=c)
            
        return hierarchy

    # -------------------------------------------------------------------------
    def store(self):
        """ Store this hierarchy in the database """

        tablename = self.tablename
        if not tablename:
            return

        htable = current.s3db.s3_hierarchy

        db = current.db
        row = db(htable.tablename == tablename).select(htable.id,
                                                       limitby=(0, 1)).first()

        hierarchy = self.serialize()
        if row:
            row.update_record(hierarchy=hierarchy)
        else:
            htable.insert(tablename=tablename,
                          hierarchy=hierarchy)
        return

    # -------------------------------------------------------------------------
    def serialize(self, as_json=False):
        """
            Serialize this hierarchy

            @param as_json: convert into JSON string

            @return: a JSON-serializable dict (or the corresponding JSON
                     string, respectively)
        """

        nodes_dict = dict()
        for node_id, node in self.nodes.items():
            nodes_dict[node_id] = {"p": node["p"],
                                   "c": node["c"],
                                   "s": list(node["s"]) \
                                        if node["s"] else []}
        if as_json:
            return json.dumps(nodes_dict)
        else:
            return nodes_dict

    # -------------------------------------------------------------------------
    @classmethod
    def deserialize(cls, data, from_json=False):
        """
            Deserialize a nodes dict into a new S3Hierarchy instance

            @param data: the nodes dict as generated by serialize
            @param from_json: convert from JSON string

            @return: the S3Hierarchy instance
        """

        if from_json:
            nodes_dict = json.loads(data)
        else:
            nodes_dict = data

        hierarchy = cls()
        nodes = hierarchy.nodes
        for node_id, item in nodes_dict.items():
            nodes[long(node_id)] = {"p": item["p"],
                                    "c": item["c"],
                                    "s": set(item["s"]) \
                                         if item["s"] else set()}
        return hierarchy

    # -------------------------------------------------------------------------
    @classmethod
    def update_hierarchy(cls, tablename=None):
        """
            Update the stored hierarchy for a table, or all stored
            hierarchies which are marked "dirty"

            @param tablename: tablename to force update of the respective
                              stored hierarchy
        """

        if tablename is None:
            htable = current.s3db.s3_hierarchy
            rows = db(htable.dirty == True).select(htable.tablename)
            for _tablename in [row.tablename for row in rows]:
                cls.update_hierarchy(tablename=_tablename)
        else:
            s3db = current.s3db

            hconf = s3db.get_config(tablename, "hierarchy")
            if not hierarchy:
                return
            if hconf is True:
                pfield, cfield = None, None
            elif isinstance(hconf, tuple):
                pfield, cfield = hconf[:2]
            else:
                pfield, cfield = hconf, None
            hierarchy = cls.read(tablename, parent=pfield, category=cfield)
            hierarchy.store()
            
        return

    # -------------------------------------------------------------------------
    def category(self, node_id):
        """
            Get the category of a node

            @param node_id: the node ID

            @return: the node category
        """

        nodes = self.nodes

        node = nodes.get(node_id)
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

# END =========================================================================
