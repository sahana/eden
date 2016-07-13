# -*- coding: utf-8 -*-
#
# S3 XML Importer Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3import.py
#
import datetime
import json
import unittest

from gluon import *
from gluon.storage import Storage

from s3 import S3Duplicate, S3ImportItem, S3ImportJob, s3_meta_fields

from unit_tests import run_suite

# =============================================================================
class ListStringImportTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    def setUp(self):

        xmlstr = """
<s3xml>
    <resource name="gis_layer_feature" uuid="TestLayerFeature">
        <data field="name">TestLayerFeature</data>
        <data field="controller">gis</data>
        <data field="function">location</data>
        <data field="popup_fields" value="[&quot;test1&quot;, &quot;test2&quot;]"/>
    </resource>
</s3xml>"""

        from lxml import etree
        self.tree = etree.ElementTree(etree.fromstring(xmlstr))
        current.auth.override = True

    # -------------------------------------------------------------------------
    def testListStringImport(self):
        """ Test import with list:string """

        db = current.db
        s3db = current.s3db

        resource = s3db.resource("gis_layer_feature")

        # Import the elements
        resource.import_xml(self.tree)

        # Check the record
        table = resource.table
        query = (table.uuid == "TestLayerFeature")
        row = db(query).select(table.popup_fields,
                               limitby=(0, 1)).first()
        self.assertTrue(isinstance(row.popup_fields, list))
        self.assertEqual(row.popup_fields, ['test1', 'test2'])

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False
        current.db.rollback()

# =============================================================================
class DefaultApproverOverrideTests(unittest.TestCase):
    """ Test ability to override default approver in imports """

    # -------------------------------------------------------------------------
    def setUp(self):

        xmlstr = """
<s3xml>
    <resource name="org_organisation" uuid="DAOOrganisation1">
        <data field="name">DAOOrganisation1</data>
    </resource>
    <resource name="org_organisation" uuid="DAOOrganisation2" approved="false">
        <data field="name">DAOOrganisation2</data>
    </resource>
</s3xml>"""

        from lxml import etree
        self.tree = etree.ElementTree(etree.fromstring(xmlstr))

    # -------------------------------------------------------------------------
    def testDefaultApproverOverride(self):
        """ Test import with approve-attribute """

        db = current.db
        s3db = current.s3db

        current.auth.override = True

        resource = s3db.resource("org_organisation")

        # Check default approver
        self.assertEqual(resource.table.approved_by.default, 0)

        # Import the elements
        resource.import_xml(self.tree)

        table = resource.table

        # Without approved-flag should be set to default approver
        query = (table.uuid == "DAOOrganisation1")
        row = db(query).select(table.approved_by, limitby=(0, 1)).first()
        self.assertEqual(row.approved_by, 0)

        # With approved-flag false should be set to None
        query = (table.uuid == "DAOOrganisation2")
        row = db(query).select(table.approved_by, limitby=(0, 1)).first()
        self.assertEqual(row.approved_by, None)

        current.auth.override = False

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()

# =============================================================================
class ComponentDisambiguationTests(unittest.TestCase):
    """ Test component disambiguation using the alias-attribute """

    # -------------------------------------------------------------------------
    def setUp(self):

        xmlstr1 = """
<s3xml>
    <resource name="org_organisation">
        <data field="name">MasterOrg1</data>
        <resource name="org_organisation_branch" alias="branch">
            <reference field="branch_id" tuid="TUID_OF_THE_BRANCH_ORG"/>
        </resource>
    </resource>
    <resource name="org_organisation" tuid="TUID_OF_THE_BRANCH_ORG">
        <data field="name">BranchOrg1</data>
    </resource>
</s3xml>"""

        xmlstr2 = """
<s3xml>
    <resource name="org_organisation">
        <data field="name">BranchOrg2</data>
            <resource name="org_organisation_branch" alias="parent">
                <reference field="organisation_id" tuid="TUID_OF_THE_MASTER_ORG"/>
            </resource>
    </resource>
    <resource name="org_organisation" tuid="TUID_OF_THE_MASTER_ORG">
        <data field="name">MasterOrg2</data>
    </resource>
</s3xml>"""

        from lxml import etree
        self.branch_tree = etree.ElementTree(etree.fromstring(xmlstr1))
        self.parent_tree = etree.ElementTree(etree.fromstring(xmlstr2))

    # -------------------------------------------------------------------------
    def testOrganisationBranchImport(self):
        """ Test import of organisation branches using alias-attribute """

        db = current.db
        s3db = current.s3db

        current.auth.override = True
        resource = s3db.resource("org_organisation")
        msg = resource.import_xml(self.branch_tree)

        table = resource.table

        query = (table.name == "MasterOrg1")
        master = db(query).select(table._id, limitby=(0, 1)).first()
        self.assertNotEqual(master, None)

        query = (table.name == "BranchOrg1")
        branch = db(query).select(table._id, limitby=(0, 1)).first()
        self.assertNotEqual(branch, None)

        table = s3db.org_organisation_branch
        query = (table.organisation_id == master.id) & \
                (table.branch_id == branch.id)
        link = db(query).select(limitby=(0, 1)).first()
        self.assertNotEqual(link, None)

    # -------------------------------------------------------------------------
    def testParentImport(self):
        """ Test import of organisation parents using alias-attribute """

        db = current.db
        s3db = current.s3db

        current.auth.override = True
        resource = s3db.resource("org_organisation")
        msg = resource.import_xml(self.parent_tree)

        table = resource.table

        query = (table.name == "MasterOrg2")
        master = db(query).select(table._id, limitby=(0, 1)).first()
        self.assertNotEqual(master, None)

        query = (table.name == "BranchOrg2")
        branch = db(query).select(table._id, limitby=(0, 1)).first()
        self.assertNotEqual(branch, None)

        table = s3db.org_organisation_branch
        query = (table.organisation_id == master.id) & \
                (table.branch_id == branch.id)
        link = db(query).select(limitby=(0, 1)).first()
        self.assertNotEqual(link, None)

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()

# =============================================================================
class PostParseTests(unittest.TestCase):
    """ Test xml_post_parse hook """

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True
        self.pp = current.s3db.get_config("pr_person", "xml_post_parse")

    # -------------------------------------------------------------------------
    def testDynamicDefaults(self):
        """ Test setting dynamic defaults with xml_post_parse """

        xmlstr = """
<s3xml>
    <resource name="pr_person">
        <data field="first_name">Test</data>
        <data field="last_name">PostParseAdd1</data>
    </resource>
    <resource name="pr_person">
        <data field="first_name">Test</data>
        <data field="last_name">PostParseAdd2</data>
        <data field="gender" value="3"/>
    </resource>
</s3xml>"""

        from lxml import etree
        tree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = current.s3db.resource("pr_person")

        def xml_post_parse(elem, record):
            record["_gender"] = 2 # set female as dynamic default

        resource.configure(xml_post_parse=xml_post_parse)
        resource.import_xml(tree)

        db = current.db
        table = resource.table
        query = (table.first_name == "Test") & \
                (table.last_name == "PostParseAdd1")
        row = db(query).select(table.id, table.gender).first()
        self.assertNotEqual(row, None)
        self.assertEqual(row.gender, 2)

        query = (table.first_name == "Test") & \
                (table.last_name == "PostParseAdd2")
        row = db(query).select(table.id, table.gender).first()
        self.assertNotEqual(row, None)
        self.assertEqual(row.gender, 3)

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False
        current.s3db.configure("pr_person", xml_post_parse=self.pp)

# =============================================================================
class FailedReferenceTests(unittest.TestCase):
    """ Test handling of failed references """

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

    # -------------------------------------------------------------------------
    def testFailedReferenceExplicit(self):
        """ Test handling of failed explicit reference """

        xmlstr = """
<s3xml>
    <resource name="org_office">
        <data field="name">FRTestOffice1</data>
        <reference field="organisation_id">
            <resource name="org_organisation" uuid="TROX">
                <data field="name">FRTestOrgX</data>
            </resource>
        </reference>
        <reference field="location_id" resource="gis_location" tuid="FRLOCATION"/>
    </resource>
    <resource name="gis_location" tuid="FRLOCATION">
        <!-- Error -->
        <data field="lat">283746.285753</data>
        <data field="lon">172834.334556</data>
    </resource>
</s3xml>"""

        from lxml import etree
        tree = etree.ElementTree(etree.fromstring(xmlstr))

        s3db = current.s3db

        org = s3db.resource("org_organisation", uid="TROX")
        before = org.count()

        resource = current.s3db.resource("org_office")
        result = resource.import_xml(tree)

        msg = json.loads(result)
        self.assertEqual(msg["status"], "failed")

        error_resources = msg["tree"].keys()
        self.assertEqual(len(error_resources), 2)
        self.assertTrue("$_gis_location" in error_resources)
        self.assertTrue("$_org_office" in error_resources)
        self.assertTrue("@error" in msg["tree"]["$_org_office"][0]["$k_location_id"])

        # Check rollback
        org = s3db.resource("org_organisation", uid="TROX")
        self.assertEqual(before, org.count())
        org.delete()

    # -------------------------------------------------------------------------
    def testFailedReferenceInline(self):
        """ Test handling of failed inline reference """

        xmlstr = """
<s3xml>
    <resource name="org_office">
        <data field="name">FRTestOffice2</data>
        <reference field="organisation_id">
            <resource name="org_organisation" uuid="TROY">
                <data field="name">FRTestOrgY</data>
            </resource>
        </reference>
        <reference field="location_id" resource="gis_location">
            <resource name="gis_location">
                <!-- Error -->
                <data field="lat">283746.285753</data>
                <data field="lon">172834.334556</data>
            </resource>
        </reference>
    </resource>
</s3xml>"""

        from lxml import etree
        tree = etree.ElementTree(etree.fromstring(xmlstr))

        s3db = current.s3db

        org = s3db.resource("org_organisation", uid="TROY")
        before = org.count()

        resource = current.s3db.resource("org_office")
        result = resource.import_xml(tree)

        msg = json.loads(result)
        self.assertEqual(msg["status"], "failed")

        error_resources = msg["tree"].keys()
        self.assertEqual(len(error_resources), 2)
        self.assertTrue("$_gis_location" in error_resources)
        self.assertTrue("$_org_office" in error_resources)
        self.assertTrue("@error" in msg["tree"]["$_org_office"][0]["$k_location_id"])

        # Check rollback
        org = s3db.resource("org_organisation", uid="TROY")
        self.assertEqual(before, org.count())
        org.delete()

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

# =============================================================================
class DuplicateDetectionTests(unittest.TestCase):
    """ Test cases for S3Duplicate """

    @classmethod
    def setUpClass(cls):

        db = current.db

        # Define test table
        db.define_table("dedup_test",
                        Field("name"),
                        Field("secondary"),
                        *s3_meta_fields())

        # Create sample records
        samples = (
            {"uuid": "TEST0", "name": "Test0", "secondary": "SecondaryX"},
            {"uuid": "TEST1", "name": "test1", "secondary": "Secondary1"},
            {"uuid": "TEST2", "name": "Test2", "secondary": "seCondaryX"},
            {"uuid": "TEST3", "name": "Test3", "secondary": "Secondary3"},
            {"uuid": "TEST4", "name": "test4", "secondary": "Secondary4"},
        )
        table = db.dedup_test
        for data in samples:
            table.insert(**data)

        current.db.commit()

    @classmethod
    def tearDownClass(cls):

        db = current.db
        db.dedup_test.drop()
        db.commit()

    def setUp(self):

        # Create a dummy import job
        self.job = S3ImportJob(current.db.dedup_test)

        db = current.db
        table = db.dedup_test
        rows = db(table.id > 0).select(table.uuid, table.id)

        ids = {}
        uids = {}
        for row in rows:
            uids[row.id] = row.uuid
            ids[row.uuid] = row.id

        self.ids = ids
        self.uids = uids

    def tearDown(self):

        self.job = None
        self.ids = None
        self.uids = None

    # -------------------------------------------------------------------------
    def testMatch(self):
        """ Test match with primary/secondary field """

        assertEqual = self.assertEqual

        deduplicate = S3Duplicate(primary=("name",),
                                  secondary=("secondary",),
                                  )

        # Dummy item for testing
        item = S3ImportItem(self.job)
        item.table = current.db.dedup_test

        ids = self.ids

        # Test primary match
        item.id = None
        item.method = item.METHOD.CREATE
        item.data = Storage(name="Test0")

        deduplicate(item)
        assertEqual(item.id, ids["TEST0"])
        assertEqual(item.method, item.METHOD.UPDATE)

        # Test primary match + secondary match
        item.id = None
        item.method = item.METHOD.CREATE
        item.data = Storage(name="Test2", secondary="secondaryX")

        deduplicate(item)
        assertEqual(item.id, ids["TEST2"])
        assertEqual(item.method, item.METHOD.UPDATE)

        # Test primary match + secondary mismatch
        item.id = None
        item.method = item.METHOD.CREATE
        item.data = Storage(name="test4", secondary="secondaryX")

        deduplicate(item)
        assertEqual(item.id, None)
        assertEqual(item.method, item.METHOD.CREATE)

        # Test primary mismatch
        item.id = None
        item.method = item.METHOD.CREATE
        item.data = Storage(name="Test")

        deduplicate(item)
        assertEqual(item.id, None)
        assertEqual(item.method, item.METHOD.CREATE)

    # -------------------------------------------------------------------------
    def testDefaults(self):
        """ Test default behavior """

        assertEqual = self.assertEqual

        deduplicate = S3Duplicate()

        # Dummy item for testing
        item = S3ImportItem(self.job)
        item.table = current.db.dedup_test

        ids = self.ids

        # Test primary match
        item.id = None
        item.method = item.METHOD.CREATE
        item.data = Storage(name="Test0")

        deduplicate(item)
        assertEqual(item.id, ids["TEST0"])
        assertEqual(item.method, item.METHOD.UPDATE)

        # Test primary match + secondary mismatch
        item.id = None
        item.method = item.METHOD.CREATE
        item.data = Storage(name="test4", secondary="secondaryX")

        deduplicate(item)
        assertEqual(item.id, ids["TEST4"])
        assertEqual(item.method, item.METHOD.UPDATE)

        # Test primary mismatch
        item.id = None
        item.method = item.METHOD.CREATE
        item.data = Storage(name="Test")

        deduplicate(item)
        assertEqual(item.id, None)
        assertEqual(item.method, item.METHOD.CREATE)

    # -------------------------------------------------------------------------
    def testExceptions(self):
        """ Test S3Duplicate exceptions for nonexistent fields """

        assertRaises = self.assertRaises


        # Dummy item for testing
        item = S3ImportItem(self.job)
        item.table = current.db.dedup_test

        # Test invalid primary
        deduplicate = S3Duplicate(primary=("nonexistent",))
        item.id = None
        item.method = item.METHOD.CREATE
        item.data = Storage(name="Test0")

        with assertRaises(SyntaxError):
            deduplicate(item)

        # Test invalid secondary
        deduplicate = S3Duplicate(secondary=("nonexistent",))
        item.id = None
        item.method = item.METHOD.CREATE
        item.data = Storage(name="Test0")

        with assertRaises(SyntaxError):
            deduplicate(item)

        # Test invalid type
        with assertRaises(TypeError):
            deduplicate = S3Duplicate(primary=lambda: None)
        with assertRaises(TypeError):
            deduplicate = S3Duplicate(secondary=17)

# =============================================================================
class MtimeImportTests(unittest.TestCase):

    def setUp(self):

        current.auth.override = True

    def tearDown(self):

        current.auth.override = False
        current.db.rollback()

    # -------------------------------------------------------------------------
    def testMtimeImport(self):
        """
            Verify that create-postprocess does not overwrite
            imported modified_on
        """

        s3db = current.s3db

        assertEqual = self.assertEqual

        # Fixed modified_on date in the past
        mtime = datetime.datetime(1988, 8, 13, 10, 0, 0)

        xmlstr = """
<s3xml>
    <resource name="org_facility" modified_on="%(mtime)s" uuid="MTFAC">
        <data field="name">MtimeTestOffice</data>
        <reference field="organisation_id">
            <resource name="org_organisation" modified_on="%(mtime)s" uuid="MTORG">
                <data field="name">MtimeTestOrg</data>
            </resource>
        </reference>
    </resource>
</s3xml>""" % {"mtime": mtime.isoformat()}

        from lxml import etree
        tree = etree.ElementTree(etree.fromstring(xmlstr))

        # Import the data
        resource = s3db.resource("org_facility")
        result = resource.import_xml(tree)

        # Verify outer resource
        resource = s3db.resource("org_facility", uid="MTFAC")
        row = resource.select(["id", "modified_on"], as_rows=True)[0]
        assertEqual(row.modified_on, mtime)

        # Verify inner resource
        resource = s3db.resource("org_organisation", uid="MTORG")
        row = resource.select(["id", "modified_on"], as_rows=True)[0]
        assertEqual(row.modified_on, mtime)

# =============================================================================
if __name__ == "__main__":

    run_suite(
        ListStringImportTests,
        DefaultApproverOverrideTests,
        ComponentDisambiguationTests,
        PostParseTests,
        FailedReferenceTests,
        DuplicateDetectionTests,
        MtimeImportTests,
    )

# END ========================================================================
