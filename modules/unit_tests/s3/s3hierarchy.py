# -*- coding: utf-8 -*-
#
# Utils Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3hierarchy.py
#
import unittest
from gluon.dal import Query
from s3.s3utils import *
from s3 import FS, S3Hierarchy, s3_uid
from lxml import etree

# =============================================================================
class S3HierarchyTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db

        s3db.define_table("test_hierarchy",
                          Field("name"),
                          Field("category"),
                          Field("type"),
                          Field("parent", "reference test_hierarchy"),
                          Field.Method("vsfield", lambda row: "test"),
                          Field.Method("vmfield", lambda row: ["test1", "test2", "test3"]),
                          *s3_uid()
                          )

        s3db.define_table("test_hierarchy_reference",
                          Field("test_hierarchy_id", "reference test_hierarchy"),
                          Field("test_hierarchy_multi_id", "list:reference test_hierarchy"),
                          *s3_uid()
                          )
                          
        xmlstr = """
<s3xml>
    <resource name="test_hierarchy" uuid="HIERARCHY1">
        <data field="name">Type 1</data>
        <data field="category">Cat 0</data>
        <data field="type">A</data>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY1-1">
        <data field="name">Type 1-1</data>
        <data field="category">Cat 1</data>
        <data field="type">C</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY1"/>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY1-1-1">
        <data field="name">Type 1-1-1</data>
        <data field="category">Cat 2</data>
        <data field="type">B</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY1-1"/>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY1-1-2">
        <data field="name">Type 1-1-2</data>
        <data field="category">Cat 2</data>
        <data field="type">A</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY1-1"/>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY1-2">
        <data field="name">Type 1-2</data>
        <data field="category">Cat 1</data>
        <data field="type">B</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY1"/>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY1-2-1">
        <data field="name">Type 1-2-1</data>
        <data field="category">Cat 2</data>
        <data field="type">B</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY1-2"/>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY1-2-2">
        <data field="name">Type 1-2-2</data>
        <data field="category">Cat 2</data>
        <data field="type">C</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY1-2"/>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY2">
        <data field="name">Type 2</data>
        <data field="category">Cat 0</data>
        <data field="type">B</data>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY2-1">
        <data field="name">Type 2-1</data>
        <data field="category">Cat 1</data>
        <data field="type">A</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY2"/>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY2-1-1">
        <data field="name">Type 2-1-1</data>
        <data field="category">Cat 2</data>
        <data field="type">C</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY2-1"/>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY2-1-2">
        <data field="name">Type 2-1-2</data>
        <data field="category">Cat 2</data>
        <data field="type">D</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY2-1"/>
    </resource>
</s3xml>
"""
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        current.auth.override = True
        resource = s3db.resource("test_hierarchy")
        resource.import_xml(xmltree)

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        db = current.db
        db.test_hierarchy.drop()

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True
        
        db = current.db
        rows = db(db.test_hierarchy.id>0).select()
        self.rows = {}
        self.uids = {}
        self.ids = {}
        for row in rows:
            uid = row.uuid
            self.rows[uid] = row
            self.uids[uid] = row.id
            self.ids[row.id] = uid

        current.s3db.configure("test_hierarchy",
                               hierarchy=("parent", "category"))

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False
        self.rows = None

    # -------------------------------------------------------------------------
    def testHierarchyConstruction(self):
        """ Test hierarchy construction """

        uids = self.uids

        h = S3Hierarchy("test_hierarchy")
        roots = h.roots
        self.assertEqual(len(roots), 2)
        self.assertTrue(uids["HIERARCHY1"] in roots)
        self.assertTrue(uids["HIERARCHY2"] in roots)

        nodes = h.nodes
        self.assertEqual(len(nodes), len(uids))
        self.assertTrue(all(node_id in nodes for node_id in uids.values()))

    # -------------------------------------------------------------------------
    def testCategory(self):
        """ Test node category lookup """

        uids = self.uids
        rows = self.rows

        h = S3Hierarchy("test_hierarchy")
        for uid in uids:
            category = h.category(uids[uid])
            self.assertEqual(category, rows[uid].category)

    # -------------------------------------------------------------------------
    def testParent(self):
        """ Test parent lookup """

        uids = self.uids
        rows = self.rows
        
        h = S3Hierarchy("test_hierarchy")
        for uid in uids:
            parent, category = h.parent(uids[uid], classify=True)
            self.assertEqual(parent, rows[uid].parent)
            if parent:
                parent_uid = self.ids[parent]
                self.assertEqual(category, rows[parent_uid].category)

    # -------------------------------------------------------------------------
    def testChildren(self):
        """ Test child node lookup """

        uids = self.uids
        rows = self.rows

        h = S3Hierarchy("test_hierarchy")
        for uid in uids:
            self.assertEqual(h.children(uids[uid]),
                             set(row.id for row in rows.values()
                                        if row.parent == uids[uid]))

    # -------------------------------------------------------------------------
    def testPath(self):
        """ Test node path lookup """

        uids = self.uids
        rows = self.rows

        # Standard path from root
        node = uids["HIERARCHY2-1-2"]
        h = S3Hierarchy("test_hierarchy")
        path = h.path(node)
        self.assertEqual(path, [uids["HIERARCHY2"],
                                uids["HIERARCHY2-1"],
                                uids["HIERARCHY2-1-2"]
                                ])

        # Path from category root
        node = uids["HIERARCHY1-1-1"]
        path = h.path(node, category="Cat 1", classify=True)
        classified = lambda uid: (uids[uid], rows[uid].category)
        self.assertEqual(path, [classified("HIERARCHY1-1"),
                                classified("HIERARCHY1-1-1"),
                                ])

        # Path of root
        node = uids["HIERARCHY2"]
        path = h.path(node, category="Cat 1", classify=True)
        classified = lambda uid: (uids[uid], rows[uid].category)
        self.assertEqual(path, [classified("HIERARCHY2")])

    # -------------------------------------------------------------------------
    def testRoot(self):
        """ Test root node lookup """

        uids = self.uids
        rows = self.rows

        # Top root
        node = uids["HIERARCHY1-1-1"]
        h = S3Hierarchy("test_hierarchy")
        root = h.root(node)
        self.assertEqual(root, uids["HIERARCHY1"])

        # Root by category
        node = uids["HIERARCHY2-1"]
        root = h.root(node, classify=True)
        self.assertEqual(root, (uids["HIERARCHY2"], rows["HIERARCHY2"].category))

        # Root of root
        node = uids["HIERARCHY1"]
        root = h.root(node)
        self.assertEqual(root, uids["HIERARCHY1"])

        # None
        root = h.root(None)
        self.assertEqual(root, None)

    # -------------------------------------------------------------------------
    def testSiblings(self):
        """ Test lookup of sibling nodes """

        uids = self.uids
        rows = self.rows

        h = S3Hierarchy("test_hierarchy")
        for uid in uids:

            parent = rows[uid].parent
            siblings = set(row.id for row in rows.values()
                                  if row.parent == parent)

            self.assertEqual(h.siblings(uids[uid], inclusive=True), siblings)
            siblings.discard(uids[uid])
            self.assertEqual(h.siblings(uids[uid], inclusive=False), siblings)

    # -------------------------------------------------------------------------
    def testFindAll(self):
        """ Test lookup of descendant nodes """

        uids = self.uids

        h = S3Hierarchy("test_hierarchy")
        
        root = uids["HIERARCHY1"]
        nodes = h.findall(root)
        expected = ["HIERARCHY1-1",
                    "HIERARCHY1-1-1",
                    "HIERARCHY1-1-2",
                    "HIERARCHY1-2",
                    "HIERARCHY1-2-1",
                    "HIERARCHY1-2-2",
                    ]
        self.assertEqual(nodes, set(uids[uid] for uid in expected))

        root = uids["HIERARCHY1"]
        nodes = h.findall(root, inclusive=True)
        expected = ["HIERARCHY1",
                    "HIERARCHY1-1",
                    "HIERARCHY1-1-1",
                    "HIERARCHY1-1-2",
                    "HIERARCHY1-2",
                    "HIERARCHY1-2-1",
                    "HIERARCHY1-2-2",
                    ]
        self.assertEqual(nodes, set(uids[uid] for uid in expected))
        
        root = uids["HIERARCHY2"]
        nodes = h.findall(root, category="Cat 1")
        expected = ["HIERARCHY2-1",
                    ]
        self.assertEqual(nodes, set(uids[uid] for uid in expected))

        root = uids["HIERARCHY1"]
        nodes = h.findall(root, category="Cat 4")
        self.assertEqual(nodes, set())

    # -------------------------------------------------------------------------
    def testFilteringLeafOnly(self):
        """ Test filtering of the tree with leafonly=True """

        uids = self.uids

        h = S3Hierarchy("test_hierarchy",
                        filter = FS("type") == "D",
                        leafonly = True)

        # Check nodes
        nodes = h.nodes
        expected = ["HIERARCHY2",
                    "HIERARCHY2-1",
                    "HIERARCHY2-1-2"]
        self.assertEqual(len(nodes), len(expected))
        self.assertTrue(all(uids[uid] in nodes for uid in expected))

        # Check consistency
        for node in nodes.values():
            for child_id in node["s"]:
                self.assertTrue(child_id in nodes)
            parent_id = node["p"]
            if parent_id:
                self.assertTrue(parent_id in nodes)


    # -------------------------------------------------------------------------
    def testFilteringAnyNode(self):
        """ Test filtering of the tree with leafonly=False """

        uids = self.uids

        h = S3Hierarchy("test_hierarchy",
                        filter = FS("type") == "C",
                        leafonly = False)

        # Check nodes
        nodes = h.nodes
        expected = ["HIERARCHY1",
                    "HIERARCHY1-1",
                    "HIERARCHY1-2",
                    "HIERARCHY1-2-2",
                    "HIERARCHY2",
                    "HIERARCHY2-1",
                    "HIERARCHY2-1-1"]
        self.assertEqual(len(nodes), len(expected))
        self.assertTrue(all(uids[uid] in nodes for uid in expected))

        # Check consistency
        for node in nodes.values():
            for child_id in node["s"]:
                self.assertTrue(child_id in nodes)
            parent_id = node["p"]
            if parent_id:
                self.assertTrue(parent_id in nodes)

    # -------------------------------------------------------------------------
    def testTypeOfReferenceSingle(self):
        """
            Test resolution of __typeof queries, for field in referencing
            table, with single value
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with field in referencing table
        expr = FS("test_hierarchy_id").typeof(uids["HIERARCHY1"])
        query = expr.query(resource)

        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1",
                                             "HIERARCHY1-1",
                                             "HIERARCHY1-1-1",
                                             "HIERARCHY1-1-2",
                                             "HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             ))
        expected_query = table.test_hierarchy_id.belongs(expected)
        
        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfReferenceMultiple(self):
        """
            Test resolution of __typeof queries, for field in referencing
            table, with multiple values
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with field in referencing table
        expr = FS("test_hierarchy_id").typeof((uids["HIERARCHY1-2"],
                                               uids["HIERARCHY2-1"],
                                               ))
        query = expr.query(resource)

        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             "HIERARCHY2-1",
                                             "HIERARCHY2-1-1",
                                             "HIERARCHY2-1-2",
                                             ))
        expected_query = table.test_hierarchy_id.belongs(expected)
        
        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfReferenceNone(self):
        """
            Test resolution of __typeof queries, for field in referencing
            table, with None value
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with None
        expr = FS("test_hierarchy_id").typeof(None)
        query = expr.query(resource)

        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             ))
        expected_query = (table.test_hierarchy_id == None)
        self.assertEquivalent(query, expected_query)

        # Test with list
        expr = FS("test_hierarchy_id").typeof([None])
        query = expr.query(resource)

        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             ))
        expected_query = (table.test_hierarchy_id == None)
        self.assertEquivalent(query, expected_query)

        # Test with multiple values
        expr = FS("test_hierarchy_id").typeof([None, uids["HIERARCHY1-2"]])
        query = expr.query(resource)
        
        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             ))
        expected_query = (table.test_hierarchy_id.belongs(expected)) | \
                         (table.test_hierarchy_id == None)
        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfReferenceNoHierarchy(self):
        """
            Test resolution of __typeof queries, for field in referencing
            table, with no hierarchy configured
        """

        db = current.db
        uids = self.uids

        # Remove hierarchy setting
        current.s3db.clear_config("test_hierarchy", "hierarchy")

        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with field in referencing table, single value
        expr = FS("test_hierarchy_id").typeof(uids["HIERARCHY1-2"])
        query = expr.query(resource)

        expected = uids["HIERARCHY1-2"]
        expected_query = resource.table.test_hierarchy_id == expected

        self.assertEquivalent(query, expected_query)

        # Test with field in referencing table, multiple values
        expr = FS("test_hierarchy_id").typeof((uids["HIERARCHY1-2"],
                                               uids["HIERARCHY2-1"]
                                               ))
        query = expr.query(resource)

        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY2-1",
                                             ))
        expected_query = resource.table.test_hierarchy_id.belongs(expected)

        self.assertEquivalent(query, expected_query)
        
    # -------------------------------------------------------------------------
    def testTypeOfLookupTableSingle(self):
        """
            Test resolution of __typeof queries, for field in lookup table,
            with single value
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with field in hierarchy table
        expr = FS("test_hierarchy_id$name").typeof("Type 1")
        query = expr.query(resource)
        
        table = db.test_hierarchy
        expected = set(uids[uid] for uid in ("HIERARCHY1",
                                             "HIERARCHY1-1",
                                             "HIERARCHY1-1-1",
                                             "HIERARCHY1-1-2",
                                             "HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             ))
        expected_query = table.id.belongs(expected)
        
        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfLookupTableMultiple(self):
        """
            Test resolution of __typeof queries, for field in lookup table,
            with multiple values
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with field in hierarchy table
        expr = FS("test_hierarchy_id$name").typeof(("Type 1-2", "Type 2-1"))
        query = expr.query(resource)
        
        table = db.test_hierarchy
        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             "HIERARCHY2-1",
                                             "HIERARCHY2-1-1",
                                             "HIERARCHY2-1-2",
                                             ))
        expected_query = table.id.belongs(expected)
        
        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfLookupTableSingleWildcard(self):
        """
            Test resolution of __typeof queries, for field in lookup table,
            with single value with wildcards
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with field in hierarchy table, with wildcard
        expr = FS("test_hierarchy_id$name").typeof("Type 1-*")
        query = expr.query(resource)
        
        table = db.test_hierarchy
        expected = set(uids[uid] for uid in ("HIERARCHY1-1",
                                             "HIERARCHY1-1-1",
                                             "HIERARCHY1-1-2",
                                             "HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             ))
        expected_query = table.id.belongs(expected)
        
        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfLookupTableMultipleWildcard(self):
        """
            Test resolution of __typeof queries, for field in lookup table,
            with multiple values with wildcards
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with field in hierarchy table, with wildcard
        expr = FS("test_hierarchy_id$name").typeof(("Type 1-1-*", "Type 2-1*"))
        query = expr.query(resource)
        
        table = db.test_hierarchy
        expected = set(uids[uid] for uid in ("HIERARCHY1-1-1",
                                             "HIERARCHY1-1-2",
                                             "HIERARCHY2-1",
                                             "HIERARCHY2-1-1",
                                             "HIERARCHY2-1-2",
                                             ))
        expected_query = table.id.belongs(expected)
        
        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfLookupTableSingleUnresolvable(self):
        """
            Test resolution of __typeof queries, for field in lookup table,
            with unresolvable value
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with field in hierarchy table, with wildcard, no match
        expr = FS("test_hierarchy_id$name").typeof("Type 1-3*")
        query = expr.query(resource)
        
        table = db.test_hierarchy
        expected_query = table.id.belongs(set())
        
        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfLookupTableNone(self):
        """
            Test resolution of __typeof queries, for field in lookup table,
            with None value
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with None
        expr = FS("test_hierarchy_id$name").typeof(None)
        query = expr.query(resource)
        table = db.test_hierarchy
        expected_query = table.id.belongs(set())
        self.assertEquivalent(query, expected_query)

        # Test with list
        expr = FS("test_hierarchy_id$name").typeof([None])
        query = expr.query(resource)
        #table = db.test_hierarchy
        expected_query = table.id.belongs(set())
        self.assertEquivalent(query, expected_query)

        # Test with multiple values
        expr = FS("test_hierarchy_id$name").typeof([None, "Type 1-1-2"])
        query = expr.query(resource)
        #table = db.test_hierarchy
        expected_query = (table.id == uids["HIERARCHY1-1-2"])
        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfLookupTableNoHierarchy(self):
        """
            Test resolution of __typeof queries, for field in lookup
            table, with no hierarchy configured
        """

        db = current.db

        uids = self.uids
        
        # Remove hierarchy setting
        current.s3db.clear_config("test_hierarchy", "hierarchy")

        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with field in lookup table, single value
        expr = FS("test_hierarchy_id$name").typeof("Type 1-2")
        query = expr.query(resource)

        table = db.test_hierarchy
        expected_query = (table.name == "Type 1-2")

        self.assertEquivalent(query, expected_query)

        # Test with field in lookup table
        expr = FS("test_hierarchy_id$name").typeof(("Type 1-2", "Type 2-1"))
        query = expr.query(resource)

        table = db.test_hierarchy
        expected_query = table.name.belongs(("Type 1-2", "Type 2-1"))

        self.assertEquivalent(query, expected_query)

        # Test with field in lookup table, multiple values + wildcards
        expr = FS("test_hierarchy_id$name").typeof(("Type 1-*", "Type 2-1"))
        query = expr.query(resource)

        table = db.test_hierarchy
        expected_query = (table.name.like("Type 1-%")) | \
                         (table.name == "Type 2-1")

        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfListReferenceSingle(self):
        """
            Test resolution of __typeof queries, for list:reference,
            with single value
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with single value
        expr = FS("test_hierarchy_multi_id").typeof(uids["HIERARCHY1"])
        query = expr.query(resource)
        
        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1",
                                             "HIERARCHY1-1",
                                             "HIERARCHY1-1-1",
                                             "HIERARCHY1-1-2",
                                             "HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             ))
        found = self.inspect_multi_query(query,
                                         field = table.test_hierarchy_multi_id,
                                         conjunction = db._adapter.OR,
                                         op = db._adapter.CONTAINS)

        self.assertEqual(found, expected)
        
    # -------------------------------------------------------------------------
    def testTypeOfListReferenceMultiple(self):
        """
            Test resolution of __typeof queries, for list:reference,
            with multiple values
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with multiple values
        expr = FS("test_hierarchy_multi_id").typeof((uids["HIERARCHY1-2"],
                                                     uids["HIERARCHY2-1"]))
        query = expr.query(resource)

        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             "HIERARCHY2-1",
                                             "HIERARCHY2-1-1",
                                             "HIERARCHY2-1-2",
                                             ))
        found = self.inspect_multi_query(query,
                                         field = table.test_hierarchy_multi_id,
                                         conjunction = db._adapter.OR,
                                         op = db._adapter.CONTAINS)

        self.assertEqual(found, expected)

    # -------------------------------------------------------------------------
    def testTypeOfListReferenceNone(self):
        """
            Test resolution of __typeof queries, for list:reference,
            with None value
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with None
        expr = FS("test_hierarchy_multi_id").typeof(None)
        query = expr.query(resource)
        table = resource.table
        expected_query = table.id.belongs(set())
        self.assertEquivalent(query, expected_query)

        # Test with list
        expr = FS("test_hierarchy_multi_id").typeof([None])
        query = expr.query(resource)
        #table = resource.table
        expected_query = table.id.belongs(set())
        self.assertEquivalent(query, expected_query)

        # Test with multiple values
        expr = FS("test_hierarchy_multi_id").typeof((None,
                                                     uids["HIERARCHY2-1"]))
        query = expr.query(resource)
        #table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY2-1",
                                             "HIERARCHY2-1-1",
                                             "HIERARCHY2-1-2",
                                             ))
        found = self.inspect_multi_query(query,
                                         field = table.test_hierarchy_multi_id,
                                         conjunction = db._adapter.OR,
                                         op = db._adapter.CONTAINS)

        self.assertEqual(found, expected)

    # -------------------------------------------------------------------------
    def testTypeOfListReferenceNoHierarchy(self):
        """
            Test resolution of __typeof queries, for list:reference,
            with single value
        """

        db = current.db
        uids = self.uids
        
        # Remove hierarchy setting
        current.s3db.clear_config("test_hierarchy", "hierarchy")

        resource = current.s3db.resource("test_hierarchy_reference")

        # Test with single value
        expr = FS("test_hierarchy_multi_id").typeof(uids["HIERARCHY1"])
        query = expr.query(resource)

        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1",))
        found = self.inspect_multi_query(query,
                                         field = table.test_hierarchy_multi_id,
                                         conjunction = db._adapter.OR,
                                         op = db._adapter.CONTAINS)

        self.assertEqual(found, expected)

        # Test with multiple values
        expr = FS("test_hierarchy_multi_id").typeof((uids["HIERARCHY1-2"],
                                                     uids["HIERARCHY2-1"]))
        query = expr.query(resource)

        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY2-1",
                                             ))
        found = self.inspect_multi_query(query,
                                         field = table.test_hierarchy_multi_id,
                                         conjunction = db._adapter.OR,
                                         op = db._adapter.CONTAINS)

        self.assertEqual(found, expected)

    # -------------------------------------------------------------------------
    def testVirtualFieldSingle(self):
        """ Test fallbacks for __typeof with single value virtual field """

        resource = current.s3db.resource("test_hierarchy")
        row = self.rows["HIERARCHY1"]

        # vsfield returns "test"

        expr = FS("vsfield").typeof("test")
        result = expr(resource, row, virtual=True)
        self.assertTrue(result)

        expr = FS("vsfield").typeof("other")
        result = expr(resource, row, virtual=True)
        self.assertFalse(result)

        expr = FS("vsfield").typeof(["test", "test1", "test2"])
        result = expr(resource, row, virtual=True)
        self.assertTrue(result)

        expr = FS("vsfield").typeof(["other", "other1", "other2"])
        result = expr(resource, row, virtual=True)
        self.assertFalse(result)

    # -------------------------------------------------------------------------
    def testVirtualFieldMultiple(self):
        """ Test fallbacks for __typeof with multi-value virtual field """

        resource = current.s3db.resource("test_hierarchy")
        row = self.rows["HIERARCHY2"]

        # vmfield returns ["test1", "test2", "test3"]

        expr = FS("vmfield").typeof("test1")
        result = expr(resource, row, virtual=True)
        self.assertTrue(result)

        expr = FS("vmfield").typeof("other")
        result = expr(resource, row, virtual=True)
        self.assertFalse(result)

        expr = FS("vmfield").typeof(["test1", "other"])
        result = expr(resource, row, virtual=True)
        self.assertTrue(result)

        expr = FS("vmfield").typeof(["other1", "other2"])
        result = expr(resource, row, virtual=True)
        self.assertFalse(result)

    # -------------------------------------------------------------------------
    def inspect_multi_query(self, query, field=None, conjunction=None, op=None):
        """
            Inspect a list:reference multi-value containment query

            @param query: the query
            @param field: the list:reference field
            @param conjunction: the conjunction operator (AND or OR)
            @param op: the containment operator (usually CONTAINS)
        """

        found = set()

        first = query.first
        second = query.second

        assertEqual = self.assertEqual
        inspect_multi_query = self.inspect_multi_query

        if isinstance(first, Query) and isinstance(second, Query):

            assertEqual(query.op, conjunction)
            found |= inspect_multi_query(first,
                                         conjunction = conjunction,
                                         op = op)
            found |= inspect_multi_query(second,
                                         conjunction = conjunction,
                                         op = op)
        else:
            assertEqual(query.first, field)
            assertEqual(query.op, op)
            found.add(int(query.second))
            
        return found

    # -------------------------------------------------------------------------
    def equivalent(self, l, r):
        """
            Check whether two queries are equivalent
        """

        first = l.first
        second = l.second

        equivalent = self.equivalent

        if l.op != r.op:
            return False
        if isinstance(first, Query):
            if isinstance(second, Query):

                return equivalent(l.first, r.first) and \
                       equivalent(l.second, r.second) or \
                       equivalent(l.second, r.first) and \
                       equivalent(l.first, r.second)
            else:
                return equivalent(l.first, r.first)
        else:
            return l.first == r.first and l.second == r.second

    # -------------------------------------------------------------------------
    def assertEquivalent(self, query, expected_query):
        """
            Shortcut for query equivalence assertion
        """
        
        self.assertTrue(self.equivalent(query, expected_query),
                        msg = "%s != %s" % (query, expected_query))

# =============================================================================
def run_suite(*test_classes):
    """ Run the test suite """

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    if suite is not None:
        unittest.TextTestRunner(verbosity=2).run(suite)
    return

if __name__ == "__main__":

    run_suite(
        S3HierarchyTests,
    )

# END ========================================================================
