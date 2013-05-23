# -*- coding: utf-8 -*-
#
# Sync Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3sync.py
#
import unittest
from gluon import current
from gluon.dal import Query
from lxml import etree

# =============================================================================
class S3ExportMergeTests(unittest.TestCase):
    """ Test correct handling of merge information by the exporter """

    def setUp(self):

        current.auth.override = True

        xmlstr = """
<s3xml>
    <resource name="org_organisation" uuid="TESTSYNCORGANISATION">
        <data field="name">TestSyncOrganisation</data>
    </resource>
    <resource name="org_office" uuid="TESTSYNCOFFICE1">
        <data field="name">TestSyncOffice1</data>
        <reference field="organisation_id" resource="org_organisation" uuid="TESTSYNCORGANISATION"/>
    </resource>
    <resource name="org_office" uuid="TESTSYNCOFFICE2">
        <data field="name">TestSyncOffice2</data>
        <reference field="organisation_id" resource="org_organisation" uuid="TESTSYNCORGANISATION"/>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("org_office")
        resource.import_xml(xmltree)
        
    def testExportOfReplacedBy(self):
        """
            Test wether the replaced_by UUID is exported with the deleted
            record after merge
        """

        s3db = current.s3db

        resource = s3db.resource("org_office",
                                 uid=["TESTSYNCOFFICE1", "TESTSYNCOFFICE2"])
                                 
        records = resource.fast_select(["id", "uuid"])["data"]
        self.assertNotEqual(records, None)
        
        ids = dict([(record["org_office.uuid"], record["org_office.id"])
                    for record in records])
        self.assertEqual(len(ids), 2)

        # Merge the records, replace #2 by #1
        success = resource.merge(ids["TESTSYNCOFFICE1"],
                                 ids["TESTSYNCOFFICE2"])
        self.assertTrue(success)

        # Export #2
        resource = s3db.resource("org_office",
                                 uid="TESTSYNCOFFICE2",
                                 include_deleted=True)
        xmlstr = resource.export_xml()

        # Inspect the XML
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        office = xmltree.xpath(
                 "resource[@name='org_office' and @uuid='TESTSYNCOFFICE2']")
        self.assertEqual(len(office), 1)
        office = office[0]

        xml = current.xml
        self.assertEqual(office.get(xml.DELETED).lower(), "true")
        self.assertEqual(office.get(xml.ATTRIBUTE["replaced_by"]),
                         "TESTSYNCOFFICE1")

    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

# =============================================================================
class S3ImportMergeTests(unittest.TestCase):

    def testReadReplacedBy(self):

        parse = current.xml.record

        xmlstr = """
<s3xml>
  <resource name="org_office" uuid="TEST" deleted="true" replaced_by="OTHER" />
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        element = xmltree.xpath("resource[@uuid='TEST']")[0]

        table = current.s3db.org_office
        record = parse(table, element)

        self.assertTrue("uuid" in record)
        self.assertEqual(record["uuid"], "TEST")

        self.assertTrue("deleted" in record)
        self.assertTrue(record["deleted"])

        self.assertTrue("deleted_rb" in record)
        self.assertEqual(record["deleted_rb"], "OTHER")

        xmlstr = """
<s3xml>
  <resource name="org_office" uuid="TEST" deleted="true" />
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        element = xmltree.xpath("resource[@uuid='TEST']")[0]

        record = parse(table, element)

        self.assertTrue("uuid" in record)
        self.assertEqual(record["uuid"], "TEST")

        self.assertTrue("deleted" in record)
        self.assertTrue(record["deleted"])

        self.assertFalse("deleted_rb" in record)

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
        S3ExportMergeTests,
        S3ImportMergeTests
    )

# END ========================================================================
