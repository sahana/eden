# -*- coding: utf-8 -*-
#
# S3Resource Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3resource.py
#
import unittest

# =============================================================================
class S3ResourceExportXMLTests(unittest.TestCase):

    def testExportTree(self):

        xml = current.xml

        auth.override = True
        resource = s3mgr.define_resource("org", "office", id=1)
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

    def testExportTreeWithMaxBounds(self):

        xml = current.xml

        auth.override = True
        resource = s3mgr.define_resource("org", "office", id=1)
        tree = resource.export_tree(start=0, limit=1, dereference=False, maxbounds=True)
        root = tree.getroot()
        attrib = root.attrib
        self.assertEqual(len(attrib), 9)
        self.assertTrue("latmin" in attrib)
        self.assertTrue("latmax" in attrib)
        self.assertTrue("lonmin" in attrib)
        self.assertTrue("lonmax" in attrib)

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
