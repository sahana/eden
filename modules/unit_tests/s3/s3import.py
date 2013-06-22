# -*- coding: utf-8 -*-
#
# S3 XML Importer Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3import.py
#
import unittest

from gluon import *

# =============================================================================
class ListStringImportTests(unittest.TestCase):

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

    def tearDown(self):

        current.auth.override = False
        current.db.rollback()
    
# =============================================================================
class DefaultApproverOverrideTests(unittest.TestCase):
    """ Test ability to override default approver in imports """

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

    def tearDown(self):

        current.db.rollback()

# =============================================================================
class ComponentDisambiguationTests(unittest.TestCase):
    """ Test component disambiguation using the alias-attribute """

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

    def tearDown(self):

        current.db.rollback()

# =============================================================================
class PostParseTests(unittest.TestCase):
    """ Test xml_post_parse hook """

    def setUp(self):
    
        current.auth.override = True
        self.pp = current.s3db.get_config("pr_person", "xml_post_parse")

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

    def tearDown(self):

        current.db.rollback()
        current.auth.override = False
        current.s3db.configure("pr_person", xml_post_parse=self.pp)

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
        ListStringImportTests,
        DefaultApproverOverrideTests,
        ComponentDisambiguationTests,
        PostParseTests,
    )

# END ========================================================================
