# -*- coding: utf-8 -*-
#
# S3Resource Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3resource.py
#
import unittest
import datetime
from gluon import *

# =============================================================================
class S3ResourceExportXMLTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    def testExportTree(self):

        xml = current.xml

        current.auth.override = True
        resource = current.manager.define_resource("org", "office", id=1)
        tree = resource.export_tree(start=0, limit=1, dereference=False)

        root = tree.getroot()
        self.assertEqual(root.tag, xml.TAG.root)

        attrib = root.attrib
        self.assertEqual(len(attrib), 5)
        self.assertEqual(attrib["success"], "true")
        self.assertEqual(attrib["start"], "0")
        self.assertEqual(attrib["limit"], "1")
        self.assertEqual(attrib["results"], "1")
        self.assertTrue("url" in attrib)

        self.assertEqual(len(root), 1)
        for child in root:
            self.assertEqual(child.tag, xml.TAG.resource)
            attrib = child.attrib
            self.assertEqual(attrib["name"], "org_office")
            self.assertTrue("uuid" in attrib)

    # -------------------------------------------------------------------------
    def testExportTreeWithMaxBounds(self):

        xml = current.xml

        current.auth.override = True
        resource = current.manager.define_resource("org", "office", id=1)
        tree = resource.export_tree(start=0, limit=1, dereference=False, maxbounds=True)
        root = tree.getroot()
        attrib = root.attrib
        self.assertEqual(len(attrib), 9)
        self.assertTrue("latmin" in attrib)
        self.assertTrue("latmax" in attrib)
        self.assertTrue("lonmin" in attrib)
        self.assertTrue("lonmax" in attrib)

    # -------------------------------------------------------------------------
    def testExportTreeWithMSince(self):
        """ Test automatic ordering of export items by mtime if msince is given """

        manager = current.manager
        current.auth.override = True

        xmlstr = """
<s3xml>
    <resource name="hms_hospital" uuid="ORDERTESTHOSPITAL1">
        <data field="name">OrderTestHospital1</data>
    </resource>
    <resource name="hms_hospital" uuid="ORDERTESTHOSPITAL2">
        <data field="name">OrderTestHospital2</data>
    </resource>
</s3xml>"""

        from lxml import etree
        self.xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = manager.define_resource("hms", "hospital")
        resource.import_xml(self.xmltree)

        resource = manager.define_resource("hms", "hospital",
                                           uid=["ORDERTESTHOSPITAL1",
                                                "ORDERTESTHOSPITAL2"])
        resource.load()
        self.assertEqual(len(resource), 2)
        first = resource._rows[0]["uuid"]
        last = resource._rows[1]["uuid"]

        import time
        time.sleep(2) # Wait 2 seconds to change mtime
        resource._rows[0].update_record(name="OrderTestHospital1")

        msince = msince=datetime.datetime.utcnow() - datetime.timedelta(days=1)

        tree = resource.export_tree(start=0,
                                    limit=1,
                                    dereference=False)
        root = tree.getroot()
        self.assertEqual(len(root), 1)

        child = root[0]
        uuid = child.get("uuid", None)
        self.assertEqual(uuid, first)

        tree = resource.export_tree(start=0,
                                    limit=1,
                                    msince=msince,
                                    dereference=False)
        root = tree.getroot()
        self.assertEqual(len(root), 1)

        child = root[0]
        uuid = child.get("uuid", None)
        self.assertEqual(uuid, last)

        current.db.rollback()

    # -------------------------------------------------------------------------
    def testImportXMLWithMTime(self):
        """ Test mtime update in imports """

        manager = current.manager
        current.auth.override = True

        # If mtime is given in the import XML, then resource.mtime should
        # get updated to the youngest entry
        xmlstr = """
<s3xml>
    <resource name="hms_hospital" uuid="MTIMETESTHOSPITAL1" modified_on="2012-03-31T00:00:00">
        <data field="name">MTimeTestHospital1</data>
    </resource>
    <resource name="hms_hospital" uuid="MTIMETESTHOSPITAL2" modified_on="2012-04-21T00:00:00">
        <data field="name">MTimeTestHospital2</data>
    </resource>
</s3xml>"""

        from lxml import etree
        self.xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = manager.define_resource("hms", "hospital")
        resource.import_xml(self.xmltree)
        self.assertEqual(current.xml.as_utc(resource.mtime),
                         current.xml.as_utc(datetime.datetime(2012, 4, 21, 0, 0, 0)))

        current.auth.override = False
        current.db.rollback()

    # -------------------------------------------------------------------------
    def testImportXMLWithoutMTime(self):
        """ Test mtime update in imports with no mtime given """

        manager = current.manager
        current.auth.override = True

        # If no mtime is given, resource.mtime should be set to current UTC
        xmlstr = """
<s3xml>
    <resource name="hms_hospital" uuid="MTIMETESTHOSPITAL3">
        <data field="name">MTimeTestHospital3</data>
    </resource>
</s3xml>"""

        from lxml import etree
        self.xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = manager.define_resource("hms", "hospital")
        resource.import_xml(self.xmltree)
        # Can't compare with exactly utcnow as these would be milliseconds apart,
        # assume equal dates are sufficient for this test
        self.assertEqual(current.xml.as_utc(resource.mtime).date(),
                         current.xml.as_utc(datetime.datetime.utcnow()).date())

        current.auth.override = False
        current.db.rollback()

    # -------------------------------------------------------------------------
    def testImportXMLWithPartialMTime(self):
        """ Test mtime update in imports if mtime given in only some records """

        manager = current.manager
        current.auth.override = True

        # If mixed, then we should still get current UTC
        xmlstr = """
<s3xml>
    <resource name="hms_hospital" uuid="MTIMETESTHOSPITAL4" modified_on="2012-03-31T00:00:00">
        <data field="name">MTimeTestHospital4</data>
    </resource>
    <resource name="hms_hospital" uuid="MTIMETESTHOSPITAL5">
        <data field="name">MTimeTestHospital5</data>
    </resource>
</s3xml>"""

        from lxml import etree
        self.xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = manager.define_resource("hms", "hospital")
        resource.import_xml(self.xmltree)
        self.assertEqual(current.xml.as_utc(resource.mtime).date(),
                         current.xml.as_utc(datetime.datetime.utcnow()).date())

        current.auth.override = False
        current.db.rollback()

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
        S3ResourceExportXMLTests,
    )

# END ========================================================================
