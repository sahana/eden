# -*- coding: utf-8 -*-
#
# S3XML Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3xml.py
#
import unittest
from gluon import *
from gluon.contrib import simplejson as json

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from lxml import etree

from s3 import S3Hierarchy, s3_meta_fields, S3Represent, S3XMLFormat, IS_ONE_OF

# =============================================================================
class TreeBuilderTests(unittest.TestCase):

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
class JSONMessageTests(unittest.TestCase):

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
class XMLFormatTests(unittest.TestCase):
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
class GetFieldOptionsTests(unittest.TestCase):
    """ Test field options introspection method """

    options = {1: "fixed option 1",
               2: "fixed option 2",
               3: "fixed option 3",
               }

    uuids = ("OPTION1", "OPTION2")

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        db = current.db
        s3db = current.s3db

        s3db.define_table("fotest_lookup_table",
                          Field("name"),
                          Field("parent", "reference fotest_lookup_table"),
                          *s3_meta_fields())

        data = ({"name": "option1", "uuid": cls.uuids[0]},
                {"name": "option2", "uuid": cls.uuids[1]},
                )

        table = db.fotest_lookup_table
        for item in data:
            table.insert(**item)

        options = cls.options
        represent = S3Represent(lookup="fotest_lookup_table")
        s3db.define_table("fotest_table",
                          Field("fixed_set", "integer",
                                requires = IS_EMPTY_OR(IS_IN_SET(options)),
                                represent = S3Represent(options=options),
                                ),
                          Field("lookup", "reference fotest_lookup_table",
                                requires = IS_EMPTY_OR(
                                                IS_ONE_OF(db,
                                                          "fotest_lookup_table.id",
                                                          represent,
                                                          )),
                                represent = represent,
                                ),
                          Field("noopts"),
                          *s3_meta_fields())
        db.commit()

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        # Rollback
        db = current.db
        db.fotest_table.drop()
        db.fotest_lookup_table.drop()
        db.commit()

    # -------------------------------------------------------------------------
    def setUp(self):

        # Override Auth
        current.auth.override = True

        db = current.db
        table = db.fotest_lookup_table
        self.records = db(table.uuid.belongs(self.uuids)).select().as_dict()

    # -------------------------------------------------------------------------
    def tearDown(self):

        # Delete child node (if exists)
        db = current.db
        table = db.fotest_lookup_table
        db(table.uuid == "OPTION3").delete()

        # Restore Auth
        current.auth.override = False

    # -------------------------------------------------------------------------
    def testFixedOptionsSet(self):
        """ Test options lookup with fixed options set (dict) """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        table = current.db.fotest_table

        xml = current.xml
        fo = xml.get_field_options(table, "fixed_set")

        assertTrue(isinstance(fo, etree._Element))
        assertEqual(fo.tag, "select")

        ATTRIBUTE = xml.ATTRIBUTE
        VALUE = ATTRIBUTE.value
        options = self.options

        has_empty = False
        self.assertEqual(len(fo), len(options) + 1)
        for opt in fo:
            assertEqual(opt.tag, "option")

            attr = opt.attrib
            assertTrue(VALUE in attr)

            value = attr[VALUE]
            if value == "":
                has_empty = True
                assertEqual(opt.text, "")
                continue
            else:
                value = int(value)

            assertTrue(value in options)
            assertEqual(opt.text, options[value])

        assertTrue(has_empty, msg="Empty-option missing")

    # -------------------------------------------------------------------------
    def testForeignKey(self):
        """ Test options lookup with foreign key constraint """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        table = current.db.fotest_table

        xml = current.xml
        fo = xml.get_field_options(table, "lookup")

        assertTrue(isinstance(fo, etree._Element))
        assertEqual(fo.tag, "select")

        ATTRIBUTE = xml.ATTRIBUTE
        VALUE = ATTRIBUTE.value
        options = self.records

        has_empty = False
        self.assertEqual(len(fo), len(options) + 1)
        for opt in fo:
            assertEqual(opt.tag, "option")

            attr = opt.attrib
            assertTrue(VALUE in attr)

            value = attr[VALUE]
            if value == "":
                has_empty = True
                assertEqual(opt.text, "")
                continue
            else:
                value = int(value)

            assertTrue(value in options)
            assertEqual(opt.text, options[value]["name"])

        assertTrue(has_empty, msg="Empty-option missing")

    # -------------------------------------------------------------------------
    def testFieldWithoutOptions(self):
        """ Test options lookup for field without options """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        table = current.db.fotest_table

        xml = current.xml
        fo = xml.get_field_options(table, "noopts")

        assertTrue(isinstance(fo, etree._Element))
        assertEqual(fo.tag, "select")
        assertEqual(len(fo), 0,
                    msg = "Options reported for field without options")

    # -------------------------------------------------------------------------
    def testShowUIDs(self):
        """ Test options lookup with foreign key constraint including UIDs """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        table = current.db.fotest_table

        xml = current.xml
        fo = xml.get_field_options(table, "lookup", show_uids=True)

        assertTrue(isinstance(fo, etree._Element))
        assertEqual(fo.tag, "select")

        ATTRIBUTE = xml.ATTRIBUTE
        VALUE = ATTRIBUTE.value
        UID = xml.UID
        options = self.records

        has_empty = False
        self.assertEqual(len(fo), len(options) + 1)
        for opt in fo:
            assertEqual(opt.tag, "option")

            attr = opt.attrib
            assertTrue(VALUE in attr)

            value = attr[VALUE]
            if value == "":
                has_empty = True
                self.assertFalse(UID in attr)
                assertEqual(opt.text, "")
                continue
            else:
                value = int(value)

            assertTrue(UID in attr)
            assertEqual(attr[UID], options[value]["uuid"])
            assertTrue(value in options)
            assertEqual(opt.text, options[value]["name"])

        assertTrue(has_empty, msg="Empty-option missing")

    # -------------------------------------------------------------------------
    def testWithHierarchyInfo(self):
        """ Test options lookup with foreign key constraint with hierarchy info """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        db = current.db
        s3db = current.s3db
        table = db.fotest_lookup_table

        # Configure parent-field
        represent = S3Represent(lookup="fotest_lookup_table")
        table.parent.requires = IS_EMPTY_OR(
                                    IS_ONE_OF(db,
                                                "fotest_lookup_table.id",
                                                represent,
                                                ))
        table.parent.requires = represent

        # Configure hierarchy
        s3db.configure("fotest_lookup_table", hierarchy="parent")
        S3Hierarchy.dirty("fotest_lookup_table")

        # Insert a child node
        options = dict(self.records)
        child_node = {"name": "option3",
                      "uuid": "OPTION3",
                      "parent": options.keys()[0],
                      }
        child_id = table.insert(**child_node)
        options[child_id] = child_node

        xml = current.xml
        table = db.fotest_table
        fo = xml.get_field_options(table, "lookup", show_uids=True, hierarchy=True)

        assertTrue(isinstance(fo, etree._Element))
        assertEqual(fo.tag, "select")

        ATTRIBUTE = xml.ATTRIBUTE
        VALUE = ATTRIBUTE.value
        PARENT = ATTRIBUTE.parent
        UID = xml.UID

        has_empty = False
        self.assertEqual(len(fo), len(options) + 1)
        for opt in fo:
            assertEqual(opt.tag, "option")

            attr = opt.attrib
            assertTrue(VALUE in attr)

            value = attr[VALUE]
            if value == "":
                has_empty = True
                self.assertFalse(UID in attr)
                assertEqual(opt.text, "")
                continue
            else:
                value = int(value)

            assertTrue(UID in attr)
            assertEqual(attr[UID], options[value]["uuid"])
            assertTrue(value in options)
            assertEqual(opt.text, options[value]["name"])

            if "parent" in options[value] and options[value]["parent"]:
                assertTrue(PARENT in attr)
                assertEqual(attr[PARENT], str(options[value]["parent"]))

        assertTrue(has_empty, msg="Empty-option missing")

    # -------------------------------------------------------------------------
    def testExportOptionsXML(self):
        """ Test Export Options (all options, XML) """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        options = dict(self.records)

        # Request options
        resource = current.s3db.resource("fotest_table")
        result = resource.export_options(fields=["lookup"])
        fo = etree.XML(result)

        # Inspect result
        xml = current.xml
        ATTRIBUTE = xml.ATTRIBUTE
        VALUE = ATTRIBUTE.value
        UID = xml.UID

        has_empty = False
        self.assertEqual(len(fo), len(options) + 1)
        for opt in fo:
            assertEqual(opt.tag, "option")
            attr = opt.attrib
            assertTrue(VALUE in attr)
            value = attr[VALUE]
            if value == "":
                has_empty = True
                self.assertFalse(UID in attr)
                assertEqual(opt.text, None)
                continue
            else:
                value = int(value)
            assertTrue(value in options)
            assertEqual(opt.text, options[value]["name"])

        assertTrue(has_empty, msg="Empty-option missing")

    # -------------------------------------------------------------------------
    def testExportOptionsXMLHierarchy(self):
        """ Test Export Options (all options, XML+hierarchy) """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        # Configure parent-field
        db = current.db
        table = db.fotest_lookup_table
        represent = S3Represent(lookup="fotest_lookup_table")
        table.parent.requires = IS_EMPTY_OR(
                                    IS_ONE_OF(db,
                                                "fotest_lookup_table.id",
                                                represent,
                                                ))
        table.parent.requires = represent

        # Configure hierarchy
        s3db = current.s3db
        s3db.configure("fotest_lookup_table", hierarchy="parent")
        S3Hierarchy.dirty("fotest_lookup_table")

        # Insert a child node
        options = dict(self.records)
        child_node = {"name": "option3",
                      "uuid": "OPTION3",
                      "parent": options.keys()[0],
                      }
        child_id = table.insert(**child_node)
        options[child_id] = child_node

        # Request options
        resource = s3db.resource("fotest_table")
        result = resource.export_options(fields=["lookup"], hierarchy=True)
        fo = etree.XML(result)

        # Inspect result
        xml = current.xml
        ATTRIBUTE = xml.ATTRIBUTE
        VALUE = ATTRIBUTE.value
        PARENT = ATTRIBUTE.parent
        UID = xml.UID

        has_empty = False
        self.assertEqual(len(fo), len(options) + 1)
        for opt in fo:
            assertEqual(opt.tag, "option")

            attr = opt.attrib
            assertTrue(VALUE in attr)

            value = attr[VALUE]
            if value == "":
                has_empty = True
                self.assertFalse(UID in attr)
                assertEqual(opt.text, None)
                continue
            else:
                value = int(value)

            assertTrue(value in options)
            assertEqual(opt.text, options[value]["name"])

            if "parent" in options[value] and options[value]["parent"]:
                assertTrue(PARENT in attr)
                assertEqual(attr[PARENT], str(options[value]["parent"]))

        assertTrue(has_empty, msg="Empty-option missing")

    # -------------------------------------------------------------------------
    def testExportOptionsAllOptsJSON(self):
        """ Test export options, JSON, all options """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        options = dict(self.records)

        # Request options
        resource = current.s3db.resource("fotest_table")
        result = resource.export_options(fields=["lookup"],
                                         as_json=True)
        fo = json.loads(result)

        # Inspect result
        has_empty = False
        assertTrue(isinstance(fo, dict))
        assertTrue("option" in fo)
        assertTrue(isinstance(fo["option"], list))
        assertEqual(len(fo["option"]), len(options) + 1)
        for opt in fo["option"]:
            value = opt["@value"]
            if value == "":
                has_empty = True
                self.assertFalse("$" in opt)
                continue
            else:
                value = int(value)
            assertTrue(value in options)
            assertEqual(opt["$"], options[value]["name"])
        assertTrue(has_empty, msg="Empty-option missing")

    # -------------------------------------------------------------------------
    def testExportOptionsAllOptsJSONHierarchy(self):
        """ Test export options, JSON, all options+hierarchy """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        # Configure parent-field
        db = current.db
        table = db.fotest_lookup_table
        represent = S3Represent(lookup="fotest_lookup_table")
        table.parent.requires = IS_EMPTY_OR(
                                    IS_ONE_OF(db,
                                                "fotest_lookup_table.id",
                                                represent,
                                                ))
        table.parent.requires = represent

        # Configure hierarchy
        s3db = current.s3db
        s3db.configure("fotest_lookup_table", hierarchy="parent")
        S3Hierarchy.dirty("fotest_lookup_table")

        # Insert a child node
        options = dict(self.records)
        child_node = {"name": "option3",
                      "uuid": "OPTION3",
                      "parent": options.keys()[0],
                      }
        child_id = table.insert(**child_node)
        options[child_id] = child_node

        # Request options
        resource = s3db.resource("fotest_table")
        result = resource.export_options(fields=["lookup"],
                                         hierarchy=True,
                                         as_json=True)
        fo = json.loads(result)

        # Inspect result
        has_empty = False
        assertTrue(isinstance(fo, dict))
        assertTrue("option" in fo)
        assertTrue(isinstance(fo["option"], list))
        assertEqual(len(fo["option"]), len(options) + 1)
        for opt in fo["option"]:
            value = opt["@value"]
            if value == "":
                has_empty = True
                self.assertFalse("$" in opt)
                continue
            else:
                value = int(value)
            assertTrue(value in options)
            assertEqual(opt["$"], options[value]["name"])
            if "parent" in options[value] and options[value]["parent"]:
                assertTrue("@parent" in opt)
                assertEqual(opt["@parent"], str(options[value]["parent"]))

        assertTrue(has_empty, msg="Empty-option missing")

    # -------------------------------------------------------------------------
    def testExportOptionsLastOptJSON(self):
        """ Test export of last option, JSON """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        options = dict(self.records)

        # Get the last record
        db = current.db
        table = db.fotest_lookup_table
        last = db(table.id>0).select(limitby=(0, 1),
                                     orderby=~table.id).first()
        self.assertNotEqual(last, None)

        # Request last option
        resource = current.s3db.resource("fotest_table")
        result = resource.export_options(fields=["lookup"],
                                         only_last=True,
                                         as_json=True)
        fo = json.loads(result)

        # Inspect result
        assertTrue(isinstance(fo, dict))

        assertTrue("option" in fo)
        assertTrue(isinstance(fo["option"], list))
        assertEqual(len(fo["option"]), 1)

        opt = fo["option"][0]
        value = opt["@value"]
        assertEqual(options[value]["uuid"], last.uuid)
        assertEqual(opt["$"], options[value]["name"])

    # -------------------------------------------------------------------------
    def testExportOptionsLastOptJSONHierarchy(self):

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        db = current.db
        s3db = current.s3db

        # Configure parent-field
        table = db.fotest_lookup_table
        represent = S3Represent(lookup="fotest_lookup_table")
        table.parent.requires = IS_EMPTY_OR(
                                    IS_ONE_OF(db,
                                                "fotest_lookup_table.id",
                                                represent,
                                                ))
        table.parent.requires = represent

        # Configure hierarchy
        s3db.configure("fotest_lookup_table", hierarchy="parent")
        S3Hierarchy.dirty("fotest_lookup_table")

        # Insert a child node
        options = dict(self.records)
        child_node = {"name": "option3",
                      "uuid": "OPTION3",
                      "parent": options.keys()[0],
                      }
        child_id = table.insert(**child_node)
        options[child_id] = child_node

        # Get the last record
        table = db.fotest_lookup_table
        last = db(table.id>0).select(limitby=(0, 1),
                                     orderby=~table.id).first()
        self.assertNotEqual(last, None)

        # Request last option
        resource = s3db.resource("fotest_table")
        result = resource.export_options(fields=["lookup"],
                                         only_last=True,
                                         hierarchy=True,
                                         as_json=True)
        fo = json.loads(result)

        # Inspect result
        assertTrue(isinstance(fo, dict))

        assertTrue("option" in fo)
        assertTrue(isinstance(fo["option"], list))
        assertEqual(len(fo["option"]), 1)

        opt = fo["option"][0]
        value = opt["@value"]
        assertEqual(options[value]["uuid"], last.uuid)
        assertEqual(opt["$"], options[value]["name"])

        assertTrue("@parent" in opt)
        assertEqual(opt["@parent"], str(options[value]["parent"]))

# =============================================================================
class S3JSONParsingTests(unittest.TestCase):
    """ Tests for S3JSON Parsing """

    # -------------------------------------------------------------------------
    def testValueParsing(self):
        """ Test handling of S3JSON @value attribute """

        assertEqual = self.assertEqual

        json_str = """{
"$_test_resource": [
    {
        "valuelist": {
            "@value": ["value1", "value2"]
        },
        "jsonlist": {
            "@value": "[\\"value1\\", \\"value2\\"]"
        },
        "valuestring": {
            "@value": "value1"
        },
        "valueinteger": {
            "@value": 2
        }
    }
]}"""
        tree = current.xml.json2tree(StringIO(json_str))
        root = tree.getroot()

        # A value list gives a JSON string with a list
        value_list = root.findall('resource/data[@field="valuelist"]')[0]
        v = value_list.get("value")
        assertEqual(v, '["value1", "value2"]')
        assertEqual(json.loads(v), ["value1", "value2"])

        # A JSON list gives the same JSON string
        value_list = root.findall('resource/data[@field="jsonlist"]')[0]
        v = value_list.get("value")
        assertEqual(v, '["value1", "value2"]')
        assertEqual(json.loads(v), ["value1", "value2"])

        # A string gives the same string
        value_list = root.findall('resource/data[@field="valuestring"]')[0]
        v = value_list.get("value")
        assertEqual(v, "value1")

        # A numeric value gives its string representation
        value_list = root.findall('resource/data[@field="valueinteger"]')[0]
        v = value_list.get("value")
        assertEqual(v, "2")

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
        TreeBuilderTests,
        JSONMessageTests,
        XMLFormatTests,
        GetFieldOptionsTests,
        S3JSONParsingTests,
    )

# END ========================================================================
