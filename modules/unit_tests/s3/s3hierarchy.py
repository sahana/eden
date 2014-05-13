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
        resource = current.s3db.resource("test_hierarchy")
        resource.import_xml(xmltree)

        resource.configure(hierarchy=("parent", "category"))

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
