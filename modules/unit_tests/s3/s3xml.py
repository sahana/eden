# -*- coding: utf-8 -*-
#
# S3XML Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3xml.py
#
import unittest
from gluon import *
from gluon.contrib import simplejson as json

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from lxml import etree

from s3.s3xml import S3XMLFormat

# =============================================================================
class S3TreeBuilderTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    def testEmptyTree(self):

        xml = current.xml

        tree = xml.tree(None)
        root = tree.getroot()

        attrib = root.attrib
        self.assertEqual(root.tag, xml.TAG.root)
        self.assertEqual(len(attrib), 1)
        self.assertEqual(attrib["success"], "false")

    # -------------------------------------------------------------------------
    def testIncludeMaxBounds(self):

        xml = current.xml

        tree = xml.tree(None, maxbounds=True)
        root = tree.getroot()

        attrib = root.attrib
        self.assertEqual(root.tag, xml.TAG.root)
        self.assertEqual(len(attrib), 5)
        self.assertEqual(attrib["success"], "false")
        self.assertTrue("latmin" in attrib)
        self.assertTrue("latmax" in attrib)
        self.assertTrue("lonmin" in attrib)
        self.assertTrue("lonmax" in attrib)

# =============================================================================
class S3JSONMessageTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    def testDefaultSuccessMessage(self):
        """ Test whether 200 issued by default if success=True """

        json_message = current.xml.json_message

        msg = json_message()
        msg = json.loads(msg)
        self.assertEqual(len(msg), 2)
        self.assertEqual(msg["status"], "success")
        self.assertEqual(msg["statuscode"], "200")

    # -------------------------------------------------------------------------
    def testDefaultErrorMessage(self):
        """ Test whether 404 issued by default if success=False """

        json_message = current.xml.json_message

        msg = json_message(False)
        msg = json.loads(msg)
        self.assertEqual(len(msg), 2)
        self.assertEqual(msg["status"], "failed")
        self.assertEqual(msg["statuscode"], "404")

    # -------------------------------------------------------------------------
    def testExtendedSuccessMessage(self):
        """ Test success message with specified message text """

        json_message = current.xml.json_message

        msg = json_message(True, message="Test")
        msg = json.loads(msg)
        self.assertEqual(len(msg), 3)
        self.assertEqual(msg["status"], "success")
        self.assertEqual(msg["statuscode"], "200")
        self.assertEqual(msg["message"], "Test")

    # -------------------------------------------------------------------------
    def testExtendedSuccessMessageWithResultNumber(self):
        """ Test success message with specified message text """

        json_message = current.xml.json_message

        msg = json_message(True, message="Test", results=40)
        msg = json.loads(msg)
        self.assertEqual(len(msg), 4)
        self.assertEqual(msg["status"], "success")
        self.assertEqual(msg["statuscode"], "200")
        self.assertEqual(msg["message"], "Test")
        self.assertEqual(msg["results"], 40)

    # -------------------------------------------------------------------------
    def testExtendedSuccessMessageWithSenderID(self):
        """ Test success message with specified message text """

        json_message = current.xml.json_message

        msg = json_message(True, message="Test", sender="XYZ")
        msg = json.loads(msg)
        self.assertEqual(len(msg), 4)
        self.assertEqual(msg["status"], "success")
        self.assertEqual(msg["statuscode"], "200")
        self.assertEqual(msg["message"], "Test")
        self.assertEqual(msg["sender"], "XYZ")

    # -------------------------------------------------------------------------
    def testExtendedSuccessMessageWithCreatedIDs(self):
        """ Test success message with specified message text """

        json_message = current.xml.json_message

        msg = json_message(True, message="Test", created=[1, 2, 3])
        msg = json.loads(msg)
        self.assertEqual(len(msg), 4)
        self.assertEqual(msg["status"], "success")
        self.assertEqual(msg["statuscode"], "200")
        self.assertEqual(msg["message"], "Test")
        self.assertEqual(msg["created"], [1, 2, 3])

    # -------------------------------------------------------------------------
    def testExtendedSuccessMessageWithUpdatedIDs(self):
        """ Test success message with specified message text """

        json_message = current.xml.json_message

        msg = json_message(True, message="Test", updated=[1, 2, 3])
        msg = json.loads(msg)
        self.assertEqual(len(msg), 4)
        self.assertEqual(msg["status"], "success")
        self.assertEqual(msg["statuscode"], "200")
        self.assertEqual(msg["message"], "Test")
        self.assertEqual(msg["updated"], [1, 2, 3])

    # -------------------------------------------------------------------------
    def testExtendedErrorMessage(self):
        """ Test error message with specified error code and text """

        json_message = current.xml.json_message

        msg = json_message(False, 405, message="Test")
        msg = json.loads(msg)
        self.assertEqual(len(msg), 3)
        self.assertEqual(msg["status"], "failed")
        self.assertEqual(msg["statuscode"], "405")
        self.assertEqual(msg["message"], "Test")

    # -------------------------------------------------------------------------
    def testExtendedErrorMessageWithTree(self):
        """ Test error message with specified error code, text and JSON tree """

        json_message = current.xml.json_message

        msg = json_message(False, 405, message="Test", tree='{"test": "value"}')
        msg = json.loads(msg)
        self.assertEqual(len(msg), 4)
        self.assertEqual(msg["status"], "failed")
        self.assertEqual(msg["statuscode"], "405")
        self.assertEqual(msg["message"], "Test")
        self.assertTrue(isinstance(msg["tree"], dict))
        tree = msg["tree"]
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree["test"], "value")

# =============================================================================
class S3XMLFormatTests(unittest.TestCase):
    """ Test S3XMLFormat helper class """

    # -------------------------------------------------------------------------
    def setUp(self):

        xmlstr = """<?xml version="1.0"?><s3xml/>"""
        
        stylesheet = """<?xml version="1.0"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:s3="http://eden.sahanafoundation.org/wiki/S3">
    
    <xsl:output method="xml"/>

    <s3:fields tables="gis_location" select="ALL"/>
    <s3:fields tables="org_office" exclude="site_id"/>
    <s3:fields tables="pr_person" select="ALL" exclude="last_name"/>
    <s3:fields tables="pr_*" select="pe_id" exclude="pe_label"/>
    <s3:fields tables="pr_c*" select="ALL"/>
    <s3:fields tables="ANY" select="location_id,site_id"/>

    <xsl:template match="/">
        <test>Test</test>
    </xsl:template>
</xsl:stylesheet>"""

        self.tree = etree.ElementTree(etree.fromstring(xmlstr))
        self.stylesheet = S3XMLFormat(StringIO(stylesheet))

    # -------------------------------------------------------------------------
    def testSelectAllFields(self):

        include, exclude = self.stylesheet.get_fields("gis_location")
        
        self.assertEqual(include, None)
        self.assertEqual(exclude, [])

    # -------------------------------------------------------------------------
    def testSelectedFields(self):

        include, exclude = self.stylesheet.get_fields("org_facility")

        self.assertTrue("location_id" in include)
        self.assertTrue("site_id" in include)
        self.assertEqual(len(include), 2)

        self.assertEqual(exclude, [])

    # -------------------------------------------------------------------------
    def testExcludedFields(self):

        include, exclude = self.stylesheet.get_fields("pr_person")

        self.assertEqual(include, None)
        self.assertEqual(exclude, ["last_name"])

    # -------------------------------------------------------------------------
    def testCombinedSelectedAndExcludedFields(self):

        include, exclude = self.stylesheet.get_fields("org_office")

        self.assertEqual(include, ["location_id"])
        self.assertEqual(exclude, [])

    # -------------------------------------------------------------------------
    def testWildcard(self):
        
        include, exclude = self.stylesheet.get_fields("pr_address")
        self.assertEqual(include, ["pe_id"])
        self.assertEqual(exclude, ["pe_label"])
        
        include, exclude = self.stylesheet.get_fields("pr_contact")
        self.assertEqual(include, None)
        self.assertEqual(exclude, ["pe_label"])

    # -------------------------------------------------------------------------
    def testTransformation(self):

        result = self.stylesheet.transform(self.tree)
        root = result.getroot()
        self.assertEqual(root.tag, "test")
        self.assertEqual(len(root), 0)
        self.assertEqual(root.text, "Test")

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
        S3TreeBuilderTests,
        S3JSONMessageTests,
        S3XMLFormatTests,
    )

# END ========================================================================
