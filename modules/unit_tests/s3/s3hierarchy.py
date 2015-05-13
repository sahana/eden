# -*- coding: utf-8 -*-
#
# S3Hierarchy Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3hierarchy.py
#
import unittest

from lxml import etree

from s3dal import Field, Query
from s3.s3utils import *
from s3.s3rest import s3_request
from s3 import FS, S3Hierarchy, S3HierarchyFilter, s3_meta_fields

# =============================================================================
class S3HierarchyTests(unittest.TestCase):
    """ Tests for standard hierarchies """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db

        s3db.define_table("test_hierarchy",
                          Field("name"),
                          Field("category"),
                          Field("type"),
                          Field("parent", "reference test_hierarchy"),
                          *s3_meta_fields())

        s3db.define_table("test_hierarchy_reference",
                          Field("test_hierarchy_id", "reference test_hierarchy",
                                ondelete = "RESTRICT",
                                ),
                          Field("test_hierarchy_multi_id", "list:reference test_hierarchy"),
                          *s3_meta_fields())

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
        current.db.commit()

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        db = current.db
        db.test_hierarchy_reference.drop()
        db.test_hierarchy.drop(mode="cascade")
        current.db.commit()

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

        db = current.db

        if not hasattr(self, "rows"):
            table = db.test_hierarchy
            rows = db((table.id>0) & (table.deleted != True)).select()
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

    # -------------------------------------------------------------------------
    def testHierarchyConstruction(self):
        """ Test hierarchy construction """

        uids = self.uids

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        h = S3Hierarchy("test_hierarchy")
        roots = h.roots
        assertEqual(len(roots), 2)
        assertTrue(uids["HIERARCHY1"] in roots)
        assertTrue(uids["HIERARCHY2"] in roots)

        nodes = h.nodes
        assertEqual(len(nodes), len(uids))
        assertTrue(all(node_id in nodes for node_id in uids.values()))

    # -------------------------------------------------------------------------
    def testPreprocessCreateNode(self):
        """ Test preprocessing of a create-node request """

        r = s3_request("test", "hierarchy", http="POST")
        parent_node = self.rows["HIERARCHY1"]
        parent_id = parent_node.id

        h = S3Hierarchy("test_hierarchy")
        link = h.preprocess_create_node(r, parent_id)
        self.assertEqual(link, None)

        assertEqual = self.assertEqual

        post_vars = r.post_vars
        assertEqual(post_vars["parent"], parent_id)

        field = r.table.parent
        assertEqual(field.default, parent_id)
        assertEqual(field.update, parent_id)
        self.assertFalse(field.readable)
        self.assertFalse(field.writable)

    # -------------------------------------------------------------------------
    def testDeleteBranch(self):
        """ Test recursive deletion of a hierarchy branch """

        # Add additional nodes
        xmlstr = """
<s3xml>
    <resource name="test_hierarchy" uuid="HIERARCHY1-3">
        <data field="name">Type 1-3</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY1"/>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY1-3-1">
        <data field="name">Type 1-3-1</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY1-3"/>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY1-3-2">
        <data field="name">Type 1-3-2</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY1-3"/>
    </resource>
</s3xml>
"""
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = current.s3db.resource("test_hierarchy")
        resource.import_xml(xmltree)

        # Commit here, otherwise failing deletion will roll back the import, too
        db = current.db
        db.commit()

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse
        assertEqual = self.assertEqual

        table = db.test_hierarchy
        try:
            # Capture the uuids
            rows = db(table.uuid.like("HIERARCHY1-3%")).select()

            uids = {}
            for row in rows:
                assertFalse(row.deleted)
                uids[row.uuid] = row.id

            # Mark as dirty after import
            h = S3Hierarchy("test_hierarchy")
            h.dirty("test_hierarchy")

            # Verify that branch node has been added to the hierarchy
            branches = h.children(self.uids["HIERARCHY1"])
            assertTrue(uids["HIERARCHY1-3"] in branches)

            # Verify that children have been added, too
            children = h.children(uids["HIERARCHY1-3"])
            assertEqual(len(children), 2)

            # Delete the branch
            success = h.delete([uids["HIERARCHY1-3"]])
            assertEqual(success, 3)

            # Verify that branch has been deleted
            branches = h.children(self.uids["HIERARCHY1"])
            assertFalse(uids["HIERARCHY1-3"] in branches)

            # Child nodes must be gone as well
            nodes = h.nodes
            assertTrue(all(uids[uid] not in nodes for uid in uids))

            # Verify that the nodes are deleted from database too
            rows = db(table.uuid.like("HIERARCHY1-3%")).select()
            for row in rows:
                assertTrue(row.deleted)
                uids[row.uuid] = row.id
        finally:
            # Cleanup
            db(table.uuid.like("HIERARCHY1-3%")).delete()

    # -------------------------------------------------------------------------
    def testDeleteBranchFailure(self):
        """
            Test proper handling of deletion cascade failure due to
            db integrity constraints
        """

        # Add additional nodes
        xmlstr = """
<s3xml>
    <resource name="test_hierarchy" uuid="HIERARCHY1-4">
        <data field="name">Type 1-4</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY1"/>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY1-4-1">
        <data field="name">Type 1-4-1</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY1-4"/>
    </resource>
    <resource name="test_hierarchy" uuid="HIERARCHY1-4-2">
        <data field="name">Type 1-4-2</data>
        <reference field="parent" resource="test_hierarchy" uuid="HIERARCHY1-4"/>
    </resource>
    <resource name="test_hierarchy_reference" uuid="REF1">
        <reference field="test_hierarchy_id" uuid="HIERARCHY1-4-1"/>
    </resource>
</s3xml>
"""
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        db = current.db
        s3db = current.s3db
        resource = s3db.resource("test_hierarchy")
        resource.import_xml(xmltree)
        resource = s3db.resource("test_hierarchy_reference")
        resource.import_xml(xmltree)

        # Commit here, otherwise failing deletion will roll back the import, too
        db.commit()

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse
        assertEqual = self.assertEqual

        table = db.test_hierarchy
        try:
            # Capture the uuids
            rows = db(table.uuid.like("HIERARCHY1-4%")).select()

            uids = {}
            for row in rows:
                assertFalse(row.deleted)
                uids[row.uuid] = row.id

            # Mark as dirty after import
            h = S3Hierarchy("test_hierarchy")
            h.dirty("test_hierarchy")

            # Verify that branch node has been added to the hierarchy
            branches = h.children(self.uids["HIERARCHY1"])
            assertTrue(uids["HIERARCHY1-4"] in branches)

            # Verify that children have been added, too
            children = h.children(uids["HIERARCHY1-4"])
            assertEqual(len(children), 2)

            # Try delete the branch => should fail
            success = h.delete([uids["HIERARCHY1-4"]])
            assertEqual(success, None)

            # Verify that branch has not been deleted
            branches = h.children(self.uids["HIERARCHY1"])
            assertTrue(uids["HIERARCHY1-4"] in branches)

            # Child nodes must still be in the hierarchy
            nodes = h.nodes
            assertTrue(all(uids[uid] in nodes for uid in uids))

            # Verify that the nodes are not deleted from database either
            rows = db(table.uuid.like("HIERARCHY1-4%")).select()
            for row in rows:
                assertFalse(row.deleted)

            # Remove the blocker
            db(db.test_hierarchy_reference.uuid == "REF1").delete()

            # Try again to delete the branch => should succeed now
            success = h.delete([uids["HIERARCHY1-4"]])
            assertEqual(success, 3)

            # Verify that branch has been deleted
            branches = h.children(self.uids["HIERARCHY1"])
            assertFalse(uids["HIERARCHY1-4"] in branches)

            # Child nodes must be gone as well
            nodes = h.nodes
            assertTrue(all(uids[uid] not in nodes for uid in uids))

            # Verify that the nodes are deleted from database too
            rows = db(table.uuid.like("HIERARCHY1-4%")).select()
            for row in rows:
                assertTrue(row.deleted)
                uids[row.uuid] = row.id
        finally:
            # Cleanup
            db(table.uuid.like("HIERARCHY1-4%")).delete()

    # -------------------------------------------------------------------------
    def testCategory(self):
        """ Test node category lookup """

        uids = self.uids
        rows = self.rows

        assertEqual = self.assertEqual

        h = S3Hierarchy("test_hierarchy")
        for uid in uids:
            category = h.category(uids[uid])
            assertEqual(category, rows[uid].category)

    # -------------------------------------------------------------------------
    def testParent(self):
        """ Test parent lookup """

        ids = self.ids
        uids = self.uids
        rows = self.rows

        assertEqual = self.assertEqual

        h = S3Hierarchy("test_hierarchy")
        for uid in uids:
            parent, category = h.parent(uids[uid], classify=True)
            assertEqual(parent, rows[uid].parent)
            if parent:
                parent_uid = ids[parent]
                assertEqual(category, rows[parent_uid].category)

    # -------------------------------------------------------------------------
    def testChildren(self):
        """ Test child node lookup """

        uids = self.uids
        rows = self.rows

        assertEqual = self.assertEqual

        h = S3Hierarchy("test_hierarchy")
        for uid in uids:
            assertEqual(h.children(uids[uid]),
                        set(row.id for row in rows.values()
                                   if row.parent == uids[uid]))

    # -------------------------------------------------------------------------
    def testPath(self):
        """ Test node path lookup """

        uids = self.uids
        rows = self.rows

        assertEqual = self.assertEqual

        # Standard path from root
        node = uids["HIERARCHY2-1-2"]
        h = S3Hierarchy("test_hierarchy")
        path = h.path(node)
        assertEqual(path, [uids["HIERARCHY2"],
                           uids["HIERARCHY2-1"],
                           uids["HIERARCHY2-1-2"]
                           ])

        # Path from category root
        node = uids["HIERARCHY1-1-1"]
        path = h.path(node, category="Cat 1", classify=True)
        classified = lambda uid: (uids[uid], rows[uid].category)
        assertEqual(path, [classified("HIERARCHY1-1"),
                           classified("HIERARCHY1-1-1"),
                           ])

        # Path of root
        node = uids["HIERARCHY2"]
        path = h.path(node, category="Cat 1", classify=True)
        classified = lambda uid: (uids[uid], rows[uid].category)
        assertEqual(path, [classified("HIERARCHY2")])

    # -------------------------------------------------------------------------
    def testRoot(self):
        """ Test root node lookup """

        uids = self.uids
        rows = self.rows

        assertEqual = self.assertEqual

        # Top root
        node = uids["HIERARCHY1-1-1"]
        h = S3Hierarchy("test_hierarchy")
        root = h.root(node)
        assertEqual(root, uids["HIERARCHY1"])

        # Root by category
        node = uids["HIERARCHY2-1"]
        root = h.root(node, classify=True)
        assertEqual(root, (uids["HIERARCHY2"], rows["HIERARCHY2"].category))

        # Root of root
        node = uids["HIERARCHY1"]
        root = h.root(node)
        assertEqual(root, uids["HIERARCHY1"])

        # None
        root = h.root(None)
        assertEqual(root, None)

    # -------------------------------------------------------------------------
    def testDepth(self):
        """ Test determination of the maximum depth beneath a node """

        uids = self.uids
        rows = self.rows

        assertEqual = self.assertEqual

        h = S3Hierarchy("test_hierarchy")

        # Top root
        node = uids["HIERARCHY1"]
        assertEqual(h.depth(node), 2)

        # Sub-node
        node = uids["HIERARCHY2-1"]
        assertEqual(h.depth(node), 1)

        # Leaf
        node = uids["HIERARCHY1-1-1"]
        assertEqual(h.depth(node), 0)

        # None (processes all roots)
        assertEqual(h.depth(None), 2)

    # -------------------------------------------------------------------------
    def testSiblings(self):
        """ Test lookup of sibling nodes """

        uids = self.uids
        rows = self.rows

        assertEqual = self.assertEqual

        h = S3Hierarchy("test_hierarchy")
        for uid in uids:

            parent = rows[uid].parent
            siblings = set(row.id for row in rows.values()
                                  if row.parent == parent)

            assertEqual(h.siblings(uids[uid], inclusive=True), siblings)
            siblings.discard(uids[uid])
            assertEqual(h.siblings(uids[uid], inclusive=False), siblings)

    # -------------------------------------------------------------------------
    def testFindAll(self):
        """ Test lookup of descendant nodes """

        uids = self.uids

        h = S3Hierarchy("test_hierarchy")

        assertEqual = self.assertEqual

        root = uids["HIERARCHY1"]
        nodes = h.findall(root)
        expected = ["HIERARCHY1-1",
                    "HIERARCHY1-1-1",
                    "HIERARCHY1-1-2",
                    "HIERARCHY1-2",
                    "HIERARCHY1-2-1",
                    "HIERARCHY1-2-2",
                    ]
        assertEqual(nodes, set(uids[uid] for uid in expected))

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
        assertEqual(nodes, set(uids[uid] for uid in expected))

        root = uids["HIERARCHY2"]
        nodes = h.findall(root, category="Cat 1")
        expected = ["HIERARCHY2-1",
                    ]
        assertEqual(nodes, set(uids[uid] for uid in expected))

        root = uids["HIERARCHY1"]
        nodes = h.findall(root, category="Cat 4")
        assertEqual(nodes, set())

    # -------------------------------------------------------------------------
    def testExportNode(self):
        """ Test export of nodes """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        h = S3Hierarchy("test_hierarchy")
        data = dict((self.uids[uid], self.rows[uid]) for uid in self.uids)

        # Export the rows beneath node HIERARCHY1
        root = self.uids["HIERARCHY1"]
        output = h.export_node(root,
                               depth=2,
                               prefix="_export",
                               data=data,
                               hcol = "test_hierarchy.name",
                               columns=["test_hierarchy.category"],
                               )

        # Should give 7 rows
        assertEqual(len(output), 7)

        for row in output:
            next_level = True
            for i in xrange(2):
                hcol = "_export.%s" % i
                # All hierarchy columns must be present
                assertTrue(hcol in row)
                label = row[hcol]
                # The row should belong to this branch
                if label != "" and next_level:
                    assertEqual(label[:6], "Type 1")
                else:
                    # Levels below the last level must be empty
                    next_level = False
                    assertEqual(label, "")

            assertTrue("test_hierarchy.category" in row)
            assertFalse("test_hierarchy.name" in row)

    # -------------------------------------------------------------------------
    def testFilteringLeafOnly(self):
        """ Test filtering of the tree with leafonly=True """

        uids = self.uids

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        h = S3Hierarchy("test_hierarchy",
                        filter = FS("type") == "D",
                        leafonly = True)

        # Check nodes
        nodes = h.nodes
        expected = ["HIERARCHY2",
                    "HIERARCHY2-1",
                    "HIERARCHY2-1-2"]
        assertEqual(len(nodes), len(expected))
        assertTrue(all(uids[uid] in nodes for uid in expected))

        # Check consistency
        for node in nodes.values():
            assertTrue(all(child_id in nodes for child_id in node["s"]))
            parent_id = node["p"]
            if parent_id:
                assertTrue(parent_id in nodes)

    # -------------------------------------------------------------------------
    def testFilteringAnyNode(self):
        """ Test filtering of the tree with leafonly=False """

        uids = self.uids

        h = S3Hierarchy("test_hierarchy",
                        filter = FS("type") == "C",
                        leafonly = False)

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        # Check nodes
        nodes = h.nodes
        expected = ["HIERARCHY1",
                    "HIERARCHY1-1",
                    "HIERARCHY1-2",
                    "HIERARCHY1-2-2",
                    "HIERARCHY2",
                    "HIERARCHY2-1",
                    "HIERARCHY2-1-1"]
        assertEqual(len(nodes), len(expected))
        assertTrue(all(uids[uid] in nodes for uid in expected))

        # Check consistency
        for node in nodes.values():
            assertTrue(all(child_id in nodes for child_id in node["s"]))
            parent_id = node["p"]
            if parent_id:
                assertTrue(parent_id in nodes)

# =============================================================================
class S3LinkedHierarchyTests(unittest.TestCase):
    """ Tests for linktable-based hierarchies """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db

        s3db.define_table("test_lhierarchy",
                          Field("name"),
                          Field("category"),
                          Field("type"),
                          *s3_meta_fields())

        s3db.define_table("test_lhierarchy_link",
                          Field("parent_id", "reference test_lhierarchy"),
                          Field("child_id", "reference test_lhierarchy"),
                          *s3_meta_fields())

        # Component for import
        s3db.add_components("test_lhierarchy",
                            test_lhierarchy = {"name": "parent",
                                               "link": "test_lhierarchy_link",
                                               "joinby": "child_id",
                                               "key": "parent_id",
                                               },
                            ),


        xmlstr = """
<s3xml>
    <resource name="test_lhierarchy" uuid="LHIERARCHY1">
        <data field="name">Type 1</data>
        <data field="category">Cat 0</data>
        <data field="type">A</data>
    </resource>
    <resource name="test_lhierarchy" uuid="LHIERARCHY1-1">
        <data field="name">Type 1-1</data>
        <data field="category">Cat 1</data>
        <data field="type">C</data>
        <resource name="test_lhierarchy_link">
            <reference field="parent_id"
                       resource="test_lhierarchy" uuid="LHIERARCHY1"/>
        </resource>
    </resource>
    <resource name="test_lhierarchy" uuid="LHIERARCHY1-1-1">
        <data field="name">Type 1-1-1</data>
        <data field="category">Cat 2</data>
        <data field="type">B</data>
        <resource name="test_lhierarchy_link">
            <reference field="parent_id"
                       resource="test_lhierarchy" uuid="LHIERARCHY1-1"/>
        </resource>
    </resource>
    <resource name="test_lhierarchy" uuid="LHIERARCHY1-1-2">
        <data field="name">Type 1-1-2</data>
        <data field="category">Cat 2</data>
        <data field="type">A</data>
        <resource name="test_lhierarchy_link">
            <reference field="parent_id"
                       resource="test_lhierarchy" uuid="LHIERARCHY1-1"/>
        </resource>
    </resource>
    <resource name="test_lhierarchy" uuid="LHIERARCHY1-2">
        <data field="name">Type 1-2</data>
        <data field="category">Cat 1</data>
        <data field="type">B</data>
        <resource name="test_lhierarchy_link">
            <reference field="parent_id"
                       resource="test_lhierarchy" uuid="LHIERARCHY1"/>
        </resource>
    </resource>
    <resource name="test_lhierarchy" uuid="LHIERARCHY1-2-1">
        <data field="name">Type 1-2-1</data>
        <data field="category">Cat 2</data>
        <data field="type">B</data>
        <resource name="test_lhierarchy_link">
            <reference field="parent_id"
                       resource="test_lhierarchy" uuid="LHIERARCHY1-2"/>
        </resource>
    </resource>
    <resource name="test_lhierarchy" uuid="LHIERARCHY1-2-2">
        <data field="name">Type 1-2-2</data>
        <data field="category">Cat 2</data>
        <data field="type">C</data>
        <resource name="test_lhierarchy_link">
            <reference field="parent_id"
                       resource="test_lhierarchy" uuid="LHIERARCHY1-2"/>
        </resource>
    </resource>
    <resource name="test_lhierarchy" uuid="LHIERARCHY2">
        <data field="name">Type 2</data>
        <data field="category">Cat 0</data>
        <data field="type">B</data>
    </resource>
    <resource name="test_lhierarchy" uuid="LHIERARCHY2-1">
        <data field="name">Type 2-1</data>
        <data field="category">Cat 1</data>
        <data field="type">A</data>
        <resource name="test_lhierarchy_link">
            <reference field="parent_id"
                       resource="test_lhierarchy" uuid="LHIERARCHY2"/>
        </resource>
    </resource>
    <resource name="test_lhierarchy" uuid="LHIERARCHY2-1-1">
        <data field="name">Type 2-1-1</data>
        <data field="category">Cat 2</data>
        <data field="type">C</data>
        <resource name="test_lhierarchy_link">
            <reference field="parent_id"
                       resource="test_lhierarchy" uuid="LHIERARCHY2-1"/>
        </resource>
    </resource>
    <resource name="test_lhierarchy" uuid="LHIERARCHY2-1-2">
        <data field="name">Type 2-1-2</data>
        <data field="category">Cat 2</data>
        <data field="type">D</data>
        <resource name="test_lhierarchy_link">
            <reference field="parent_id"
                       resource="test_lhierarchy" uuid="LHIERARCHY2-1"/>
        </resource>
    </resource>
</s3xml>
"""
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        current.auth.override = True
        resource = s3db.resource("test_lhierarchy")
        resource.import_xml(xmltree)

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        db = current.db
        db.test_lhierarchy_link.drop()
        db.test_lhierarchy.drop()

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

        db = current.db

        if not hasattr(self, "rows"):
            table = db.test_lhierarchy
            linktable = db.test_lhierarchy_link
            left = linktable.on(linktable.child_id == table.id)
            rows = db(db.test_lhierarchy.id>0).select(table.id,
                                                      table.uuid,
                                                      table.category,
                                                      linktable.child_id,
                                                      linktable.parent_id,
                                                      left=left)
            self.rows = {}
            self.links = {}
            self.uids = {}
            self.ids = {}
            for row in rows:
                record = row.test_lhierarchy
                uid = record.uuid
                self.rows[uid] = record
                self.links[uid] = row.test_lhierarchy_link
                self.uids[uid] = record.id
                self.ids[record.id] = uid

        current.s3db.configure("test_lhierarchy",
                               hierarchy=("child_id:test_lhierarchy_link.parent_id",
                                          "category"))

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False

    # -------------------------------------------------------------------------
    def testHierarchyConstruction(self):
        """ Test hierarchy construction """

        uids = self.uids

        h = S3Hierarchy("test_lhierarchy")

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        roots = h.roots
        assertEqual(len(roots), 2)
        assertTrue(uids["LHIERARCHY1"] in roots)
        assertTrue(uids["LHIERARCHY2"] in roots)

        nodes = h.nodes
        assertEqual(len(nodes), len(uids))
        assertTrue(all(node_id in nodes for node_id in uids.values()))

    # -------------------------------------------------------------------------
    def testPreprocessCreateNode(self):
        """ Test preprocessing of a create-node request """

        r = s3_request("test", "lhierarchy", http="POST")
        parent_node = self.rows["LHIERARCHY1"]

        h = S3Hierarchy("test_lhierarchy")
        link = h.preprocess_create_node(r, parent_node.id)

        self.assertNotEqual(link, None)
        assertEqual = self.assertEqual
        assertEqual(link["linktable"], "test_lhierarchy_link")
        assertEqual(link["lkey"], "child_id")
        assertEqual(link["rkey"], "parent_id")
        assertEqual(link["parent_id"], parent_node.id)

    # -------------------------------------------------------------------------
    def testPostprocessCreateNode(self):
        """ Test postprocessing of a create-node request """

        r = s3_request("test", "lhierarchy", http="POST")
        parent_node = self.rows["LHIERARCHY1"]

        h = S3Hierarchy("test_lhierarchy")
        link = h.preprocess_create_node(r, parent_node.id)

        row = None
        record_id = None
        db = current.db
        table = db.test_lhierarchy
        linktable = db.test_lhierarchy_link
        try:
            record = {"uuid": "LHIERARCHYNEW", "name": "NewNode"}
            record_id = table.insert(**record)
            record["id"] = record_id
            h.postprocess_create_node(link, record)
            query = (linktable.parent_id == parent_node.id) & \
                    (linktable.child_id == record_id)
            row = db(query).select(linktable.id, limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
        finally:
            if row:
                row.delete_record()
            if record_id:
                db(table.id == record_id).delete()

    # -------------------------------------------------------------------------
    def testCategory(self):
        """ Test node category lookup """

        uids = self.uids
        rows = self.rows

        assertEqual = self.assertEqual

        h = S3Hierarchy("test_lhierarchy")
        for uid in uids:
            category = h.category(uids[uid])
            assertEqual(category, rows[uid].category)

    # -------------------------------------------------------------------------
    def testParent(self):
        """ Test parent lookup """

        uids = self.uids
        rows = self.rows
        links = self.links

        assertEqual = self.assertEqual

        h = S3Hierarchy("test_lhierarchy")
        for uid in uids:
            parent, category = h.parent(uids[uid], classify=True)
            assertEqual(parent, links[uid].parent_id)
            if parent:
                parent_uid = self.ids[parent]
                assertEqual(category, rows[parent_uid].category)

    # -------------------------------------------------------------------------
    def testChildren(self):
        """ Test child node lookup """

        uids = self.uids
        links = self.links

        assertEqual = self.assertEqual

        h = S3Hierarchy("test_lhierarchy")
        for uid in uids:
            assertEqual(h.children(uids[uid]),
                        set(link.child_id for link in links.values()
                                          if link.parent_id == uids[uid]))

    # -------------------------------------------------------------------------
    def testPath(self):
        """ Test node path lookup """

        uids = self.uids
        rows = self.rows

        assertEqual = self.assertEqual

        # Standard path from root
        node = uids["LHIERARCHY2-1-2"]
        h = S3Hierarchy("test_lhierarchy")
        path = h.path(node)
        assertEqual(path, [uids["LHIERARCHY2"],
                           uids["LHIERARCHY2-1"],
                           uids["LHIERARCHY2-1-2"]
                           ])

        # Path from category root
        node = uids["LHIERARCHY1-1-1"]
        path = h.path(node, category="Cat 1", classify=True)
        classified = lambda uid: (uids[uid], rows[uid].category)
        assertEqual(path, [classified("LHIERARCHY1-1"),
                           classified("LHIERARCHY1-1-1"),
                           ])

        # Path of root
        node = uids["LHIERARCHY2"]
        path = h.path(node, category="Cat 1", classify=True)
        classified = lambda uid: (uids[uid], rows[uid].category)
        assertEqual(path, [classified("LHIERARCHY2")])

    # -------------------------------------------------------------------------
    def testRoot(self):
        """ Test root node lookup """

        uids = self.uids
        rows = self.rows

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        # Top root
        node = uids["LHIERARCHY1-1-1"]
        h = S3Hierarchy("test_lhierarchy")
        root = h.root(node)
        assertEqual(root, uids["LHIERARCHY1"])

        # Root by category
        node = uids["LHIERARCHY2-1"]
        root = h.root(node, classify=True)
        assertEqual(root, (uids["LHIERARCHY2"],
                           rows["LHIERARCHY2"].category))

        # Root of root
        node = uids["LHIERARCHY1"]
        root = h.root(node)
        assertEqual(root, uids["LHIERARCHY1"])

        # None
        root = h.root(None)
        assertEqual(root, None)

    # -------------------------------------------------------------------------
    def testSiblings(self):
        """ Test lookup of sibling nodes """

        uids = self.uids
        ids = self.ids
        links = self.links

        assertEqual = self.assertEqual

        h = S3Hierarchy("test_lhierarchy")
        for uid in uids:

            parent = links[uid].parent_id
            siblings = set(node for node, _uid in ids.items()
                                if links[_uid].parent_id == parent)

            assertEqual(h.siblings(uids[uid], inclusive=True), siblings)
            siblings.discard(uids[uid])
            assertEqual(h.siblings(uids[uid], inclusive=False), siblings)

    # -------------------------------------------------------------------------
    def testFindAll(self):
        """ Test lookup of descendant nodes """

        uids = self.uids

        assertEqual = self.assertEqual

        h = S3Hierarchy("test_lhierarchy")

        root = uids["LHIERARCHY1"]
        nodes = h.findall(root)
        expected = ["LHIERARCHY1-1",
                    "LHIERARCHY1-1-1",
                    "LHIERARCHY1-1-2",
                    "LHIERARCHY1-2",
                    "LHIERARCHY1-2-1",
                    "LHIERARCHY1-2-2",
                    ]
        assertEqual(nodes, set(uids[uid] for uid in expected))

        root = uids["LHIERARCHY1"]
        nodes = h.findall(root, inclusive=True)
        expected = ["LHIERARCHY1",
                    "LHIERARCHY1-1",
                    "LHIERARCHY1-1-1",
                    "LHIERARCHY1-1-2",
                    "LHIERARCHY1-2",
                    "LHIERARCHY1-2-1",
                    "LHIERARCHY1-2-2",
                    ]
        assertEqual(nodes, set(uids[uid] for uid in expected))

        root = uids["LHIERARCHY2"]
        nodes = h.findall(root, category="Cat 1")
        expected = ["LHIERARCHY2-1",
                    ]
        assertEqual(nodes, set(uids[uid] for uid in expected))

        root = uids["LHIERARCHY1"]
        nodes = h.findall(root, category="Cat 4")
        assertEqual(nodes, set())

    # -------------------------------------------------------------------------
    def testFilteringLeafOnly(self):
        """ Test filtering of the tree with leafonly=True """

        uids = self.uids

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        h = S3Hierarchy("test_lhierarchy",
                        filter = FS("type") == "D",
                        leafonly = True)

        # Check nodes
        nodes = h.nodes
        expected = ["LHIERARCHY2",
                    "LHIERARCHY2-1",
                    "LHIERARCHY2-1-2"]
        assertEqual(len(nodes), len(expected))
        assertTrue(all(uids[uid] in nodes for uid in expected))

        # Check consistency
        for node in nodes.values():
            assertTrue(all(child_id in nodes for child_id in node["s"]))
            parent_id = node["p"]
            if parent_id:
                assertTrue(parent_id in nodes)


    # -------------------------------------------------------------------------
    def testFilteringAnyNode(self):
        """ Test filtering of the tree with leafonly=False """

        uids = self.uids

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        h = S3Hierarchy("test_lhierarchy",
                        filter = FS("type") == "C",
                        leafonly = False)

        # Check nodes
        nodes = h.nodes
        expected = ["LHIERARCHY1",
                    "LHIERARCHY1-1",
                    "LHIERARCHY1-2",
                    "LHIERARCHY1-2-2",
                    "LHIERARCHY2",
                    "LHIERARCHY2-1",
                    "LHIERARCHY2-1-1"]
        assertEqual(len(nodes), len(expected))
        assertTrue(all(uids[uid] in nodes for uid in expected))

        # Check consistency
        for node in nodes.values():
            assertTrue(all(child_id in nodes for child_id in node["s"]))
            parent_id = node["p"]
            if parent_id:
                assertTrue(parent_id in nodes)

# =============================================================================
class S3TypeOfTests(unittest.TestCase):
    """ Tests for __typeof query operator """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db

        s3db.define_table("typeof_nonhierarchy",
                          Field("name"),
                          *s3_meta_fields())

        s3db.define_table("typeof_hierarchy",
                          Field("name"),
                          Field("parent", "reference typeof_hierarchy"),
                          Field("typeof_nonhierarchy_id", "reference typeof_nonhierarchy"),
                          Field("typeof_nonhierarchy_multi_id", "list:reference typeof_nonhierarchy"),
                          Field.Method("vsfield", lambda row: "test"),
                          Field.Method("vmfield", lambda row: ["test1", "test2", "test3"]),
                          *s3_meta_fields())

        s3db.define_table("typeof_hierarchy_reference",
                          Field("typeof_hierarchy_id", "reference typeof_hierarchy"),
                          Field("typeof_hierarchy_multi_id", "list:reference typeof_hierarchy"),
                          *s3_meta_fields())

        xmlstr = """
<s3xml>
    <resource name="typeof_nonhierarchy" uuid="NONHIERARCHY1">
        <data field="name">NonHierarchy1</data>
    </resource>
    <resource name="typeof_nonhierarchy" uuid="NONHIERARCHY2">
        <data field="name">NonHierarchy2</data>
    </resource>
    <resource name="typeof_hierarchy" uuid="HIERARCHY1">
        <data field="name">Type 1</data>
    </resource>
    <resource name="typeof_hierarchy" uuid="HIERARCHY1-1">
        <data field="name">Type 1-1</data>
        <reference field="parent" resource="typeof_hierarchy" uuid="HIERARCHY1"/>
        <reference field="typeof_nonhierarchy_id" resource="typeof_nonhierarchy" uuid="NONHIERARCHY1"/>
    </resource>
    <resource name="typeof_hierarchy" uuid="HIERARCHY1-1-1">
        <data field="name">Type 1-1-1</data>
        <reference field="parent" resource="typeof_hierarchy" uuid="HIERARCHY1-1"/>
    </resource>
    <resource name="typeof_hierarchy" uuid="HIERARCHY1-1-2">
        <data field="name">Type 1-1-2</data>
        <reference field="parent" resource="typeof_hierarchy" uuid="HIERARCHY1-1"/>
    </resource>
    <resource name="typeof_hierarchy" uuid="HIERARCHY1-2">
        <data field="name">Type 1-2</data>
        <reference field="parent" resource="typeof_hierarchy" uuid="HIERARCHY1"/>
    </resource>
    <resource name="typeof_hierarchy" uuid="HIERARCHY1-2-1">
        <data field="name">Type 1-2-1</data>
        <reference field="parent" resource="typeof_hierarchy" uuid="HIERARCHY1-2"/>
    </resource>
    <resource name="typeof_hierarchy" uuid="HIERARCHY1-2-2">
        <data field="name">Type 1-2-2</data>
        <reference field="parent" resource="typeof_hierarchy" uuid="HIERARCHY1-2"/>
    </resource>
    <resource name="typeof_hierarchy" uuid="HIERARCHY2">
        <data field="name">Type 2</data>
    </resource>
    <resource name="typeof_hierarchy" uuid="HIERARCHY2-1">
        <data field="name">Type 2-1</data>
        <reference field="typeof_nonhierarchy_multi_id" resource="typeof_nonhierarchy"
                   uuid="[&quot;NONHIERARCHY1&quot;,&quot;NONHIERARCHY2&quot;]"/>
        <reference field="parent" resource="typeof_hierarchy" uuid="HIERARCHY2"/>
    </resource>
    <resource name="typeof_hierarchy" uuid="HIERARCHY2-1-1">
        <data field="name">Type 2-1-1</data>
        <reference field="parent" resource="typeof_hierarchy" uuid="HIERARCHY2-1"/>
    </resource>
    <resource name="typeof_hierarchy" uuid="HIERARCHY2-1-2">
        <data field="name">Type 2-1-2</data>
        <reference field="parent" resource="typeof_hierarchy" uuid="HIERARCHY2-1"/>
    </resource>
</s3xml>
"""
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        current.auth.override = True
        resource = s3db.resource("typeof_hierarchy")
        resource.import_xml(xmltree)

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        db = current.db
        db.typeof_hierarchy.drop(mode="cascade")
        db.typeof_hierarchy_reference.drop()
        db.typeof_nonhierarchy.drop()

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

        db = current.db

        if not hasattr(self, "rows"):
            rows = db(db.typeof_hierarchy.id>0).select()
            self.rows = {}
            self.uids = {}
            self.ids = {}
            for row in rows:
                uid = row.uuid
                self.rows[uid] = row
                self.uids[uid] = row.id
                self.ids[row.id] = uid

        if not hasattr(self, "lookup_uids"):
            rows = db(db.typeof_nonhierarchy.id>0).select()
            self.lookup_uids = {}
            for row in rows:
                uid = row.uuid
                self.lookup_uids[uid] = row.id

        current.s3db.configure("typeof_hierarchy", hierarchy="parent")

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False

    # -------------------------------------------------------------------------
    def testTypeOfReferenceSingle(self):
        """
            Test resolution of __typeof queries, for field in referencing
            table, with single value
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with field in referencing table
        expr = FS("typeof_hierarchy_id").typeof(uids["HIERARCHY1"])
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
        expected_query = table.typeof_hierarchy_id.belongs(expected)

        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfReferenceMultiple(self):
        """
            Test resolution of __typeof queries, for field in referencing
            table, with multiple values
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with field in referencing table
        expr = FS("typeof_hierarchy_id").typeof((uids["HIERARCHY1-2"],
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
        expected_query = table.typeof_hierarchy_id.belongs(expected)

        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfReferenceNone(self):
        """
            Test resolution of __typeof queries, for field in referencing
            table, with None value
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with None
        expr = FS("typeof_hierarchy_id").typeof(None)
        query = expr.query(resource)

        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             ))
        expected_query = (table.typeof_hierarchy_id == None)
        self.assertEquivalent(query, expected_query)

        # Test with list
        expr = FS("typeof_hierarchy_id").typeof([None])
        query = expr.query(resource)

        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             ))
        expected_query = (table.typeof_hierarchy_id == None)
        self.assertEquivalent(query, expected_query)

        # Test with multiple values
        expr = FS("typeof_hierarchy_id").typeof([None, uids["HIERARCHY1-2"]])
        query = expr.query(resource)

        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY1-2-1",
                                             "HIERARCHY1-2-2",
                                             ))
        expected_query = (table.typeof_hierarchy_id.belongs(expected)) | \
                         (table.typeof_hierarchy_id == None)
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
        current.s3db.clear_config("typeof_hierarchy", "hierarchy")

        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with field in referencing table, single value
        expr = FS("typeof_hierarchy_id").typeof(uids["HIERARCHY1-2"])
        query = expr.query(resource)

        expected = uids["HIERARCHY1-2"]
        expected_query = resource.table.typeof_hierarchy_id == expected

        self.assertEquivalent(query, expected_query)

        # Test with field in referencing table, multiple values
        expr = FS("typeof_hierarchy_id").typeof((uids["HIERARCHY1-2"],
                                                 uids["HIERARCHY2-1"]
                                               ))
        query = expr.query(resource)

        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY2-1",
                                             ))
        expected_query = resource.table.typeof_hierarchy_id.belongs(expected)

        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfLookupTableSingle(self):
        """
            Test resolution of __typeof queries, for field in lookup table,
            with single value
        """

        db = current.db

        uids = self.uids
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with field in hierarchy table
        expr = FS("typeof_hierarchy_id$name").typeof("Type 1")
        query = expr.query(resource)

        table = db.typeof_hierarchy
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
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with field in hierarchy table
        expr = FS("typeof_hierarchy_id$name").typeof(("Type 1-2", "Type 2-1"))
        query = expr.query(resource)

        table = db.typeof_hierarchy
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
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with field in hierarchy table, with wildcard
        expr = FS("typeof_hierarchy_id$name").typeof("Type 1-*")
        query = expr.query(resource)

        table = db.typeof_hierarchy
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
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with field in hierarchy table, with wildcard
        expr = FS("typeof_hierarchy_id$name").typeof(("Type 1-1-*", "Type 2-1*"))
        query = expr.query(resource)

        table = db.typeof_hierarchy
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
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with field in hierarchy table, with wildcard, no match
        expr = FS("typeof_hierarchy_id$name").typeof("Type 1-3*")
        query = expr.query(resource)

        table = db.typeof_hierarchy
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
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with None
        expr = FS("typeof_hierarchy_id$name").typeof(None)
        query = expr.query(resource)
        table = db.typeof_hierarchy
        expected_query = table.id.belongs(set())
        self.assertEquivalent(query, expected_query)

        # Test with list
        expr = FS("typeof_hierarchy_id$name").typeof([None])
        query = expr.query(resource)
        #table = db.typeof_hierarchy
        expected_query = table.id.belongs(set())
        self.assertEquivalent(query, expected_query)

        # Test with multiple values
        expr = FS("typeof_hierarchy_id$name").typeof([None, "Type 1-1-2"])
        query = expr.query(resource)
        #table = db.typeof_hierarchy
        expected_query = (table.id == uids["HIERARCHY1-1-2"])
        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfLookupTableReference(self):
        """
            Test resolution of __typeof queries, for reference field
            in lookup table
        """

        db = current.db

        uids = self.uids
        lookup_uids = self.lookup_uids
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with single value
        lookup = lookup_uids["NONHIERARCHY1"]
        expr = FS("typeof_hierarchy_id$typeof_nonhierarchy_id").typeof(lookup)
        query = expr.query(resource)

        table = db.typeof_hierarchy
        expected = set(uids[uid] for uid in ("HIERARCHY1-1",
                                             "HIERARCHY1-1-1",
                                             "HIERARCHY1-1-2",
                                             ))
        expected_query = table.id.belongs(expected)

        # Test with multiple values
        lookup = (lookup_uids["NONHIERARCHY1"],
                  lookup_uids["NONHIERARCHY2"])
        expr = FS("typeof_hierarchy_id$typeof_nonhierarchy_id").typeof(lookup)
        query = expr.query(resource)

        table = db.typeof_hierarchy
        expected = set(uids[uid] for uid in ("HIERARCHY1-1",
                                             "HIERARCHY1-1-1",
                                             "HIERARCHY1-1-2",
                                             ))
        expected_query = table.id.belongs(expected)

        self.assertEquivalent(query, expected_query)

    # -------------------------------------------------------------------------
    def testTypeOfLookupTableListReference(self):
        """
            Test resolution of __typeof queries, for list:reference field
            in lookup table
        """

        db = current.db

        uids = self.uids
        lookup_uids = self.lookup_uids
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with single value
        lookup = lookup_uids["NONHIERARCHY1"]
        expr = FS("typeof_hierarchy_id$typeof_nonhierarchy_multi_id").typeof(lookup)
        query = expr.query(resource)

        table = db.typeof_hierarchy
        expected = set(uids[uid] for uid in ("HIERARCHY2-1",
                                             "HIERARCHY2-1-1",
                                             "HIERARCHY2-1-2",
                                             ))
        expected_query = table.id.belongs(expected)

        # Test with multiple values
        lookup = (lookup_uids["NONHIERARCHY1"],
                  lookup_uids["NONHIERARCHY2"])
        expr = FS("typeof_hierarchy_id$typeof_nonhierarchy_multi_id").typeof(lookup)
        query = expr.query(resource)

        table = db.typeof_hierarchy
        expected = set(uids[uid] for uid in ("HIERARCHY2-1",
                                             "HIERARCHY2-1-1",
                                             "HIERARCHY2-1-2",
                                             ))
        expected_query = table.id.belongs(expected)

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
        current.s3db.clear_config("typeof_hierarchy", "hierarchy")

        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with field in lookup table, single value
        expr = FS("typeof_hierarchy_id$name").typeof("Type 1-2")
        query = expr.query(resource)

        table = db.typeof_hierarchy
        expected_query = (table.name == "Type 1-2")

        self.assertEquivalent(query, expected_query)

        # Test with field in lookup table
        expr = FS("typeof_hierarchy_id$name").typeof(("Type 1-2", "Type 2-1"))
        query = expr.query(resource)

        table = db.typeof_hierarchy
        expected_query = table.name.belongs(("Type 1-2", "Type 2-1"))

        self.assertEquivalent(query, expected_query)

        # Test with field in lookup table, multiple values + wildcards
        expr = FS("typeof_hierarchy_id$name").typeof(("Type 1-*", "Type 2-1"))
        query = expr.query(resource)

        table = db.typeof_hierarchy
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
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with single value
        expr = FS("typeof_hierarchy_multi_id").typeof(uids["HIERARCHY1"])
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
                                         field = table.typeof_hierarchy_multi_id,
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
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with multiple values
        expr = FS("typeof_hierarchy_multi_id").typeof((uids["HIERARCHY1-2"],
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
                                         field = table.typeof_hierarchy_multi_id,
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
        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with None
        expr = FS("typeof_hierarchy_multi_id").typeof(None)
        query = expr.query(resource)
        table = resource.table
        expected_query = table.id.belongs(set())
        self.assertEquivalent(query, expected_query)

        # Test with list
        expr = FS("typeof_hierarchy_multi_id").typeof([None])
        query = expr.query(resource)
        #table = resource.table
        expected_query = table.id.belongs(set())
        self.assertEquivalent(query, expected_query)

        # Test with multiple values
        expr = FS("typeof_hierarchy_multi_id").typeof((None,
                                                       uids["HIERARCHY2-1"]))
        query = expr.query(resource)
        #table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY2-1",
                                             "HIERARCHY2-1-1",
                                             "HIERARCHY2-1-2",
                                             ))
        found = self.inspect_multi_query(query,
                                         field = table.typeof_hierarchy_multi_id,
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
        current.s3db.clear_config("typeof_hierarchy", "hierarchy")

        resource = current.s3db.resource("typeof_hierarchy_reference")

        # Test with single value
        expr = FS("typeof_hierarchy_multi_id").typeof(uids["HIERARCHY1"])
        query = expr.query(resource)

        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1",))
        found = self.inspect_multi_query(query,
                                         field = table.typeof_hierarchy_multi_id,
                                         conjunction = db._adapter.OR,
                                         op = db._adapter.CONTAINS)

        self.assertEqual(found, expected)

        # Test with multiple values
        expr = FS("typeof_hierarchy_multi_id").typeof((uids["HIERARCHY1-2"],
                                                       uids["HIERARCHY2-1"]))
        query = expr.query(resource)

        table = resource.table
        expected = set(uids[uid] for uid in ("HIERARCHY1-2",
                                             "HIERARCHY2-1",
                                             ))
        found = self.inspect_multi_query(query,
                                         field = table.typeof_hierarchy_multi_id,
                                         conjunction = db._adapter.OR,
                                         op = db._adapter.CONTAINS)

        self.assertEqual(found, expected)

    # -------------------------------------------------------------------------
    def testVirtualFieldSingle(self):
        """ Test fallbacks for __typeof with single value virtual field """

        resource = current.s3db.resource("typeof_hierarchy")
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

        resource = current.s3db.resource("typeof_hierarchy")
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
    def testHierarchyFilterTypeOf(self):
        """ Test S3HierarchyFilter recognition of typeof queries """

        uids = self.uids
        resource = current.s3db.resource("typeof_hierarchy_reference")

        filter_widget = S3HierarchyFilter("typeof_hierarchy_id")

        # Test with belongs on filter field
        ids = str(uids["HIERARCHY1-1"])
        get_vars = {"~.typeof_hierarchy_id__belongs": ids}
        variable = filter_widget.variable(resource, get_vars)
        expected = set(ids)
        values = filter_widget._values(get_vars, variable)
        self.assertEqual(values, [ids])

        # Test with typeof on filter field
        ids = str(uids["HIERARCHY1-1"])
        get_vars = {"~.typeof_hierarchy_id__typeof": ids}
        variable = filter_widget.variable(resource, get_vars)
        expected = set(str(uids[uid]) for uid in ("HIERARCHY1-1",
                                                  "HIERARCHY1-1-1",
                                                  "HIERARCHY1-1-2",
                                                  ))
        values = filter_widget._values(get_vars, variable)
        self.assertEqual(set(values), expected)

        # Test with typeof on filter field, multiple values incl. None
        ids = ",".join(str(_id) for _id in (uids["HIERARCHY1-1"],
                                            uids["HIERARCHY2-1"],
                                            None))
        get_vars = {"~.typeof_hierarchy_id__typeof": ids}
        variable = filter_widget.variable(resource, get_vars)
        expected = set(str(uids[uid]) for uid in ("HIERARCHY1-1",
                                                  "HIERARCHY1-1-1",
                                                  "HIERARCHY1-1-2",
                                                  "HIERARCHY2-1",
                                                  "HIERARCHY2-1-1",
                                                  "HIERARCHY2-1-2",
                                                  ))
        expected.add(None)
        values = filter_widget._values(get_vars, variable)
        self.assertEqual(set(values), expected)

        # Test with typeof on field in lookup table
        get_vars = {"~.typeof_hierarchy_id$name__typeof": "Type 1-1"}
        variable = filter_widget.variable(resource, get_vars)
        expected = set(str(uids[uid]) for uid in ("HIERARCHY1-1",
                                                  "HIERARCHY1-1-1",
                                                  "HIERARCHY1-1-2",
                                                  ))
        values = filter_widget._values(get_vars, variable)
        self.assertEqual(set(values), expected)

        # Test with typeof on field in lookup table, multiple values
        get_vars = {"~.typeof_hierarchy_id$name__typeof": "Type 1-1,Type 2-1"}
        variable = filter_widget.variable(resource, get_vars)
        expected = set(str(uids[uid]) for uid in ("HIERARCHY1-1",
                                                  "HIERARCHY1-1-1",
                                                  "HIERARCHY1-1-2",
                                                  "HIERARCHY2-1",
                                                  "HIERARCHY2-1-1",
                                                  "HIERARCHY2-1-2",
                                                  ))
        values = filter_widget._values(get_vars, variable)
        self.assertEqual(set(values), expected)

        # Test with typeof on field in lookup table, unresolvable
        get_vars = {"~.typeof_hierarchy_id$name__typeof": "Type 1-3"}
        variable = filter_widget.variable(resource, get_vars)
        expected = set()
        values = filter_widget._values(get_vars, variable)
        self.assertEqual(set(values), expected)

        # Test with typeof on field in lookup table, None
        get_vars = {"~.typeof_hierarchy_id$name__typeof": "None"}
        variable = filter_widget.variable(resource, get_vars)
        expected = set()
        values = filter_widget._values(get_vars, variable)
        self.assertEqual(set(values), expected)

        # Test preferrence of belongs in mixed queries
        ids = str(uids["HIERARCHY1-1"])
        get_vars = {"~.typeof_hierarchy_id__belongs": ids,
                    "~.typeof_hierarchy_id$name__typeof": "Type 1-1",
                    }
        variable = filter_widget.variable(resource, get_vars)
        expected = set(ids)
        values = filter_widget._values(get_vars, variable)
        self.assertEqual(values, [ids])

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
        S3LinkedHierarchyTests,
        S3TypeOfTests,
    )

# END ========================================================================
