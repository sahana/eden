# -*- coding: utf-8 -*-
#
# Org Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3db/org.py
#
import unittest

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import *
from gluon.storage import Storage

from lxml import etree

# =============================================================================
class RootOrgUpdateTests(unittest.TestCase):
    """ Test update of the root_organisation field in org_organisation """

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

    # -------------------------------------------------------------------------
    def testRootOrgOnaccept(self):
        """ Test the root organisation is set onaccept """

        db = current.db
        s3db = current.s3db
        otable = s3db.org_organisation

        # Insert new record
        organisation = Storage(name = "RootOrgOnacceptTest")
        record_id = otable.insert(**organisation)
        self.assertNotEqual(record_id, None)

        # Execute update_super and onaccept
        organisation["id"] = record_id
        s3db.update_super(otable, organisation)
        s3db.onaccept(otable, organisation, method="create")

        # Reload the record
        row = db(otable.id == record_id).select(otable.id,
                                                otable.root_organisation,
                                                limitby=(0, 1)).first()

        self.assertNotEqual(row, None)
        self.assertEqual(row.root_organisation, row.id)

    # -------------------------------------------------------------------------
    def testRootOrgUpdate(self):
        """ Test the root organisation is updated when adding a branch link """

        db = current.db
        s3db = current.s3db
        otable = s3db.org_organisation
        ltable = s3db.org_organisation_branch

        # Insert organisation records
        org1 = Storage(name = "RootOrgUpdateTest1")
        org1_id = otable.insert(**org1)
        self.assertNotEqual(org1_id, None)
        org1["id"] = org1_id
        s3db.update_super(otable, org1)
        s3db.onaccept(otable, org1, method="create")

        org2 = Storage(name = "RootOrgUpdateTest2")
        org2_id = otable.insert(**org2)
        self.assertNotEqual(org2_id, None)
        org2["id"] = org2_id
        s3db.update_super(otable, org2)
        s3db.onaccept(otable, org2, method="create")

        org3 = Storage(name = "RootOrgUpdateTest3")
        org3_id = otable.insert(**org3)
        self.assertNotEqual(org3_id, None)
        org3["id"] = org3_id
        s3db.update_super(otable, org3)
        s3db.onaccept(otable, org3, method="create")

        # Make org3 a branch of org2
        link = Storage(organisation_id = org2_id,
                       branch_id = org3_id)
        link_id = ltable.insert(**link)
        self.assertNotEqual(link_id, None)
        link["id"] = link_id
        s3db.onaccept(ltable, link, method="create")

        # Check root_organisations
        check = (org2_id, org3_id)
        rows = db(otable.id.belongs(check)).select(otable.id,
                                                   otable.root_organisation)
        self.assertNotEqual(rows, None)
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row.root_organisation, org2_id)

        # Make org2 a branch of org1
        link = Storage(organisation_id = org1_id,
                       branch_id = org2_id)
        link_id = ltable.insert(**link)
        self.assertNotEqual(link_id, None)
        link["id"] = link_id
        s3db.onaccept(ltable, link, method="create")

        # Check root_organisations
        check = (org1_id, org2_id, org3_id)
        rows = db(otable.id.belongs(check)).select(otable.id,
                                                   otable.root_organisation)
        self.assertNotEqual(rows, None)
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row.root_organisation, org1_id)

# =============================================================================
class OrgDeduplicationTests(unittest.TestCase):
    """ Tests for de-duplication of org_organisation import items """

    TEST_ORGANISATIONS = {
        "DEDUPORGA": {"name": "DeDupOrgA", "parent": None},
        "DEDUPORGB": {"name": "DeDupOrgB", "parent": None},
        "DEDUPORGC": {"name": "DeDupOrgC", "parent": None},
        "DEDUPBRANCHA1": {"name": "DeDupBranch1", "parent": "DEDUPORGA"},
        "DEDUPBRANCHA2": {"name": "DeDupBranch2", "parent": "DEDUPORGA"},
        "DEDUPBRANCHB2": {"name": "DeDupBranch2", "parent": "DEDUPORGB"},
        # Duplicate branch under same parent:
        "DEDUPBRANCHB3": {"name": "DeDupBranch3", "parent": "DEDUPORGB"},
        "DEDUPBRANCHB3DUP": {"name": "DeDupBranch3", "parent": "DEDUPORGB"},
        "DEDUPBRANCHC3": {"name": "DeDupBranch3", "parent": "DEDUPORGC"},
        "DEDUPBRANCHC4": {"name": "DeDupBranch4", "parent": "DEDUPORGC"},
        # Branch with same name as a root organisation:
        "DEDUPSUBBRANCHB3A": {"name": "DeDupOrgA", "parent": "DEDUPBRANCHB3"},
    }

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db

        otable = s3db.org_organisation

        records = {}

        for uuid, data in cls.TEST_ORGANISATIONS.items():
            record_id = otable.insert(uuid = uuid,
                                      name = data["name"],
                                      )
            if not record_id:
                raise RuntimeError("Could not create test record")
            records[uuid] = record_id

        btable = s3db.org_organisation_branch

        for uuid, data in cls.TEST_ORGANISATIONS.items():
            parent = data["parent"]
            if parent:
                record_id = records[uuid]
                parent_id = records[parent]
                link_id = btable.insert(organisation_id = parent_id,
                                        branch_id = record_id,
                                        )
                if not link_id:
                    raise RuntimeError("Could not create test record")

        current.db.commit()

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        db = current.db
        s3db = current.s3db

        # Delete all links
        otable = s3db.org_organisation
        query = otable.uuid.belongs(cls.TEST_ORGANISATIONS.keys())
        rows = db(query).select(otable.id,
                                otable.uuid,
                                )
        records = dict((row.uuid, row.id) for row in rows)

        btable = s3db.org_organisation_branch
        for uuid, data in cls.TEST_ORGANISATIONS.items():
            parent = data["parent"]
            if parent:
                record_id = records[uuid]
                parent_id = records[parent]
                query = (btable.organisation_id == parent_id) & \
                        (btable.branch_id == record_id)
                db(query).delete()

        # Delete the orgs
        query = otable.id.belongs(records.values())
        db(query).delete()

        db.commit()

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False
        current.db.rollback()

    # -------------------------------------------------------------------------
    def testNoNameMatch(self):
        """ Verify import items without name match create new records """

        db = current.db
        s3db = current.s3db

        assertEqual = self.assertEqual

        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        # Verify test organisations do not exist
        query = ((otable.name == "DeDupOrgD") |
                 (otable.name == "DeDupBranch5")) & \
                (otable.deleted != True)
        rows = db(query).select(otable.id)
        assertEqual(len(rows), 0)

        # Import new organisations with no name match in the DB
        xmlstr = """
<s3xml>
    <resource name="org_organisation" tuid="DEDUPORGD">
        <data field="name">DeDupOrgD</data>
    </resource>
    <resource name="org_organisation" tuid="DEDUPBRANCHD5">
        <data field="name">DeDupBranch5</data>
        <resource name="org_organisation_branch" alias="parent">
            <reference field="organisation_id" resource="org_organisation" tuid="DEDUPORGD"/>
        </resource>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = s3db.resource("org_organisation")
        resource.import_xml(xmltree, ignore_errors=True)

        # Verify DEDUPORGD has been created
        query = (otable.name == "DeDupOrgD") & \
                (otable.deleted != True)
        rows = db(query).select(otable.id)
        assertEqual(len(rows), 1)

        organisation_id = rows.first().id

        # Verify DEDUPORGD has no parent
        query = (btable.branch_id == organisation_id) & \
                (btable.deleted != True)
        rows = db(query).select(btable.id)
        assertEqual(len(rows), 0)

        # Verify DEDUPBRANCHD5 has been created
        query = (otable.name == "DeDupBranch5") & \
                (otable.deleted != True)
        rows = db(query).select(otable.id)
        assertEqual(len(rows), 1)

        branch_id = rows.first().id

        # Verify DEDUPBRANCHD5 has DEDUPORGD as parent
        query = (btable.organisation_id == organisation_id) & \
                (btable.branch_id == branch_id) & \
                (btable.deleted != True)
        rows = db(query).select(btable.id)
        assertEqual(len(rows), 1)

    # -------------------------------------------------------------------------
    def testSingleNameMatchWithoutParentItem(self):
        """
            Test update detection for single name match with no
            parent specified in import source (should always update the match)
        """

        db = current.db
        s3db = current.s3db

        assertEqual = self.assertEqual

        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        # Verify test organisations are in pristine state
        query = ((otable.name == "DeDupOrgB") |
                 (otable.name == "DeDupBranch1")) & \
                (otable.deleted != True)
        rows = db(query).select(otable.id, otable.comments)
        assertEqual(len(rows), 2)

        for row in rows:
            assertEqual(row.comments, None)

        # Import organisations with single name matches in the DB
        xmlstr = """
<s3xml>
    <resource name="org_organisation">
        <data field="name">DeDupOrgB</data>
        <data field="comments">updated</data>
    </resource>
    <resource name="org_organisation">
        <data field="name">DeDupBranch1</data>
        <data field="comments">updated</data>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = s3db.resource("org_organisation")
        resource.import_xml(xmltree, ignore_errors=True)

        # Verify DEDUPORGB has been updated
        query = (otable.name == "DeDupOrgB") & \
                (otable.deleted != True)
        rows = db(query).select(otable.id, otable.uuid, otable.comments)
        assertEqual(len(rows), 1)
        row = rows.first()
        assertEqual(row.uuid, "DEDUPORGB")
        assertEqual(row.comments, "updated")

        # Verify DEDUPBRANCHA1 has been updated
        query = (otable.name == "DeDupBranch1") & \
                (otable.deleted != True)
        rows = db(query).select(otable.id, otable.uuid, otable.comments)
        assertEqual(len(rows), 1)
        row = rows.first()
        assertEqual(row.uuid, "DEDUPBRANCHA1")
        assertEqual(row.comments, "updated")

    # -------------------------------------------------------------------------
    def testSingleNameMatchWithParentItemMatch(self):
        """
            Test update detection for single name match with parent
            specified in source (matching parent => should update branch)
        """

        db = current.db
        s3db = current.s3db

        assertEqual = self.assertEqual

        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        # Verify that there is only one DeDupBranch4
        query = (otable.name == "DeDupBranch4")
        rows = db(query).select(otable.id, otable.comments)
        assertEqual(len(rows), 1)
        assertEqual(rows.first().comments, None)
        branch_id = rows.first().id

        # Verify that the parent for DeDupBranch4 is DeDupOrgC
        query = (btable.branch_id == branch_id) & \
                (btable.deleted != True) & \
                (otable.id == btable.organisation_id)
        rows = db(query).select(otable.id, otable.uuid)
        assertEqual(len(rows), 1)
        assertEqual(rows.first().uuid, "DEDUPORGC")

        # Test with parent match
        xmlstr = """
<s3xml>
    <resource name="org_organisation" tuid="PARENT">
        <data field="name">DeDupOrgC</data>
    </resource>
    <resource name="org_organisation">
        <data field="name">DeDupBranch4</data>
        <data field="comments">updated</data>
        <resource name="org_organisation_branch" alias="parent">
            <reference field="organisation_id" resource="org_organisation" tuid="PARENT"/>
        </resource>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = s3db.resource("org_organisation")
        resource.import_xml(xmltree, ignore_errors=True)

        # Verify that there is still only one DeDupBranch4
        query = (otable.name == "DeDupBranch4")
        rows = db(query).select(otable.id, otable.comments)
        assertEqual(len(rows), 1)
        assertEqual(rows.first().comments, "updated")
        branch_id = rows.first().id

        # Verify that the parent for DeDupBranch4 is still DEDUPORGC
        query = (btable.branch_id == branch_id) & \
                (btable.deleted != True) & \
                (otable.id == btable.organisation_id)
        rows = db(query).select(otable.id, otable.uuid)
        assertEqual(len(rows), 1)
        assertEqual(rows.first().uuid, "DEDUPORGC")

    # -------------------------------------------------------------------------
    def testSingleNameMatchWithParentItemMismatch(self):
        """
            Test update detection for single name match with parent
            specified in source (different parent => should create new branch)
        """

        db = current.db
        s3db = current.s3db

        assertEqual = self.assertEqual

        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        # Verify that there is only one DeDupBranch4
        query = (otable.name == "DeDupBranch4")
        rows = db(query).select(otable.id, otable.comments)
        assertEqual(len(rows), 1)
        assertEqual(rows.first().comments, None)
        branch_id = rows.first().id # Original branch ID

        # Verify that the parent for DeDupBranch4 is DeDupOrgC
        query = (btable.branch_id == branch_id) & \
                (btable.deleted != True) & \
                (otable.id == btable.organisation_id)
        rows = db(query).select(otable.id, otable.uuid)
        assertEqual(len(rows), 1)
        assertEqual(rows.first().uuid, "DEDUPORGC")

        # Test with different parent
        xmlstr = """
<s3xml>
    <resource name="org_organisation" tuid="PARENT">
        <data field="name">DeDupOrgA</data>
    </resource>
    <resource name="org_organisation">
        <data field="name">DeDupBranch4</data>
        <data field="comments">created</data>
        <resource name="org_organisation_branch" alias="parent">
            <reference field="organisation_id" resource="org_organisation" tuid="PARENT"/>
        </resource>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = s3db.resource("org_organisation")
        resource.import_xml(xmltree, ignore_errors=True)

        # Verify that there are now two DeDupBranch4
        query = (otable.name == "DeDupBranch4")
        rows = db(query).select(otable.id, otable.comments)
        assertEqual(len(rows), 2)
        for row in rows:
            if row.id == branch_id:
                # Original Branch has no comments
                assertEqual(row.comments, None)
            else:
                # New branch has comments
                assertEqual(row.comments, "created")
        branch_ids = [row.id for row in rows]

        # Verify the parents for the two DeDupBranch4
        query = (btable.branch_id.belongs(branch_ids)) & \
                (btable.deleted != True) & \
                (otable.id == btable.organisation_id)
        rows = db(query).select(otable.uuid, btable.branch_id)
        assertEqual(len(rows), 2)
        for row in rows:
            if row[btable.branch_id] == branch_id:
                # Original branch is still under DEDUPORGC
                assertEqual(row[otable.uuid], "DEDUPORGC")
            else:
                # New branch is under DEDUPORGA
                assertEqual(row[otable.uuid], "DEDUPORGA")

    # -------------------------------------------------------------------------
    def testMultipleNameMatchesWithParentItemMatch(self):
        """
            Test update detection for multiple name matches with parent
            specified in source (matching parent => should update branch)
        """

        db = current.db
        s3db = current.s3db

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        # Verify that there are two DeDupBranch2 (in pristine state)
        query = (otable.name == "DeDupBranch2")
        rows = db(query).select(otable.id, otable.comments)
        assertEqual(len(rows), 2)
        for row in rows:
            assertEqual(row.comments, None)
        branch_ids = [row.id for row in rows]

        # Verify the parents for DeDupBranch2
        query = (btable.branch_id.belongs(branch_ids)) & \
                (btable.deleted != True) & \
                (otable.id == btable.organisation_id)
        rows = db(query).select(otable.uuid)
        assertEqual(len(rows), 2)
        for row in rows:
            assertTrue(row.uuid in ("DEDUPORGA", "DEDUPORGB"))

        # Test with parent match
        xmlstr = """
<s3xml>
    <resource name="org_organisation" tuid="PARENT">
        <data field="name">DeDupOrgB</data>
    </resource>
    <resource name="org_organisation">
        <data field="name">DeDupBranch2</data>
        <data field="comments">updated</data>
        <resource name="org_organisation_branch" alias="parent">
            <reference field="organisation_id" resource="org_organisation" tuid="PARENT"/>
        </resource>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = s3db.resource("org_organisation")
        resource.import_xml(xmltree, ignore_errors=True)

        # Verify that there are still exactly two DeDupBranch2
        query = (otable.name == "DeDupBranch2")
        rows = db(query).select(otable.id, otable.uuid, otable.comments)
        assertEqual(len(rows), 2)
        for row in rows:
            if row.uuid == "DEDUPBRANCHA2":
                # DEDUPBRANCHA2 has not changed
                assertEqual(row.comments, None)
            elif row.uuid == "DEDUPBRANCHB2":
                # DEDUPBRANCHB2 has been updated
                assertEqual(row.comments, "updated")
            else:
                raise AssertionError("Unexpected branch UUID")
        branch_ids = [row.id for row in rows]

        # Verify the parents for DeDupBranch2
        query = (btable.branch_id.belongs(branch_ids)) & \
                (btable.deleted != True) & \
                (otable.id == btable.organisation_id)
        rows = db(query).select(otable.uuid)
        assertEqual(len(rows), 2)
        for row in rows:
            assertTrue(row.uuid in ("DEDUPORGA", "DEDUPORGB"))

    # -------------------------------------------------------------------------
    def testMultipleNameMatchesWithParentItemMismatch(self):
        """
            Test update detection for multiple name matches with parent
            specified in source (different parent => should create new branch)
        """

        db = current.db
        s3db = current.s3db

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        # Verify that there are two DeDupBranch2 (in pristine state)
        query = (otable.name == "DeDupBranch2")
        rows = db(query).select(otable.id, otable.comments)
        assertEqual(len(rows), 2)
        for row in rows:
            assertEqual(row.comments, None)
        branch_ids = [row.id for row in rows]

        # Verify the parents for DeDupBranch2
        query = (btable.branch_id.belongs(branch_ids)) & \
                (btable.deleted != True) & \
                (otable.id == btable.organisation_id)
        rows = db(query).select(otable.uuid)
        assertEqual(len(rows), 2)
        for row in rows:
            assertTrue(row.uuid in ("DEDUPORGA", "DEDUPORGB"))

        # Test with different parent
        xmlstr = """
<s3xml>
    <resource name="org_organisation" tuid="PARENT">
        <data field="name">DeDupOrgC</data>
    </resource>
    <resource name="org_organisation">
        <data field="name">DeDupBranch2</data>
        <data field="comments">created</data>
        <resource name="org_organisation_branch" alias="parent">
            <reference field="organisation_id" resource="org_organisation" tuid="PARENT"/>
        </resource>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = s3db.resource("org_organisation")
        resource.import_xml(xmltree, ignore_errors=True)

        # Verify that there are now three DeDupBranch2
        query = (otable.name == "DeDupBranch2")
        rows = db(query).select(otable.id, otable.uuid, otable.comments)
        assertEqual(len(rows), 3)
        for row in rows:
            if row.uuid in ("DEDUPBRANCHA2", "DEDUPBRANCHB2"):
                # DEDUPBRANCHA2 and DEDUPBRANCHB2 have not changed
                assertEqual(row.comments, None)
            else:
                # New branch has comments
                assertEqual(row.comments, "created")
        branch_ids = [row.id for row in rows]

        # Verify the parents for DeDupBranch2
        query = (btable.branch_id.belongs(branch_ids)) & \
                (btable.deleted != True) & \
                (otable.id == btable.organisation_id)
        rows = db(query).select(otable.uuid)
        assertEqual(len(rows), 3)
        for row in rows:
            assertTrue(row.uuid in ("DEDUPORGA", "DEDUPORGB", "DEDUPORGC"))

    # -------------------------------------------------------------------------
    def testMultipleNameMatchesWithParentItemAmbiguous(self):
        """
            Test update detection for multiple name matches with parent
            specified by source (duplicate match under the same parent =>
            should reject the import item)
        """

        db = current.db
        s3db = current.s3db

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        # Verify that there are three DeDupBranch3 (in pristine state)
        query = (otable.name == "DeDupBranch3")
        rows = db(query).select(otable.id, otable.comments)
        assertEqual(len(rows), 3)
        for row in rows:
            assertEqual(row.comments, None)

        # Import with parent that contains duplicates
        xmlstr = """
<s3xml>
    <resource name="org_organisation" tuid="PARENT">
        <data field="name">DeDupOrgB</data>
    </resource>
    <resource name="org_organisation">
        <data field="name">DeDupBranch3</data>
        <data field="comments">updated</data>
        <resource name="org_organisation_branch" alias="parent">
            <reference field="organisation_id" resource="org_organisation" tuid="PARENT"/>
        </resource>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = s3db.resource("org_organisation")
        result = resource.import_xml(xmltree, ignore_errors=True)

        # Verify that we have an error reported for the import item
        result = json.loads(result)
        msg = result["message"]

        error_tree = resource.error_tree
        assertNotEqual(error_tree, None)

        elements = error_tree.xpath("resource[data[@field='name']/text()='DeDupBranch3']")
        assertEqual(len(elements), 1)

        attrib = elements[0].attrib
        assertTrue("error" in attrib)
        assertTrue(attrib["error"] in msg)

        # Verify that nothing has changed in the database
        query = (otable.name == "DeDupBranch3")
        rows = db(query).select(otable.id, otable.comments)
        assertEqual(len(rows), 3)
        for row in rows:
            assertEqual(row.comments, None)

    # -------------------------------------------------------------------------
    def testMultipleNameMatchesWithoutParentItemRootMatch(self):
        """
            Test update detection for multiple name matches without parent
            in source (single root org match => should update the root org)
        """

        db = current.db
        s3db = current.s3db

        assertEqual = self.assertEqual

        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        # Verify that there are two DeDupOrgA (in pristine state)
        query = (otable.name == "DeDupOrgA") & \
                (otable.deleted != True)
        rows = db(query).select(otable.id, otable.comments)
        assertEqual(len(rows), 2)
        for row in rows:
            assertEqual(row.comments, None)

        # Import organisation with multiple name matches in the DB
        xmlstr = """
<s3xml>
    <resource name="org_organisation">
        <data field="name">DeDupOrgA</data>
        <data field="comments">updated</data>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = s3db.resource("org_organisation")
        resource.import_xml(xmltree, ignore_errors=True)

        # Verify DEDUPORGA has been updated, but not DEDUPSUBBRANCHB3A
        query = (otable.name == "DeDupOrgA") & \
                (otable.deleted != True)
        rows = db(query).select(otable.id, otable.uuid, otable.comments)
        assertEqual(len(rows), 2)
        for row in rows:
            if row.uuid == "DEDUPORGA":
                assertEqual(row.comments, "updated")
            else:
                assertEqual(row.comments, None)

    # -------------------------------------------------------------------------
    def testMultipleNameMatchesWithoutParentItemAmbiguous(self):
        """
            Test update detection for multiple name matches if no parent
            item has been specified in source (ambiguous => should reject
            the item)
        """

        db = current.db
        s3db = current.s3db

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        # Verify that there are two DeDupOrgA (in pristine state)
        query = (otable.name == "DeDupBranch2") & \
                (otable.deleted != True)
        rows = db(query).select(otable.id, otable.comments)
        assertEqual(len(rows), 2)
        for row in rows:
            assertEqual(row.comments, None)

        # Import organisation with multiple name matches in the DB
        xmlstr = """
<s3xml>
    <resource name="org_organisation">
        <data field="name">DeDupBranch2</data>
        <data field="comments">updated</data>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = s3db.resource("org_organisation")
        result = resource.import_xml(xmltree, ignore_errors=True)

        # Verify that we have an error reported for the import item
        result = json.loads(result)
        msg = result["message"]

        error_tree = resource.error_tree
        assertNotEqual(error_tree, None)

        elements = error_tree.xpath("resource[data[@field='name']/text()='DeDupBranch2']")
        assertEqual(len(elements), 1)

        attrib = elements[0].attrib
        assertTrue("error" in attrib)
        assertTrue(attrib["error"] in msg)

        # Verify that nothing has changed in the database
        query = (otable.name == "DeDupBranch2") & \
                (otable.deleted != True)
        rows = db(query).select(otable.id, otable.comments)
        assertEqual(len(rows), 2)
        for row in rows:
            assertEqual(row.comments, None)

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
        RootOrgUpdateTests,
        OrgDeduplicationTests,
    )

# END ========================================================================
