# -*- coding: utf-8 -*-
#
# Sync Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3sync.py
#
import json
import unittest

from gluon import current
from lxml import etree

from unit_tests import run_suite
from s3 import S3SyncDataArchive

# =============================================================================
class ExportMergeTests(unittest.TestCase):
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

        records = resource.select(["id", "uuid"], limit=None)["rows"]
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
class ImportMergeTests(unittest.TestCase):
    """ Test correct handling of merge information by S3XML parser """

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
class ImportMergeWithExistingRecords(unittest.TestCase):
    """ Test correct import of merges if both records pre-exist """

    def setUp(self):

        current.auth.override = True

        # Create records
        xmlstr = """
<s3xml>
<resource name="org_organisation" uuid="TESTIMPORTMERGEORG1">
    <data field="name">TestImportMergeOrg1</data>
</resource>
<resource name="org_organisation" uuid="TESTIMPORTMERGEORG2">
    <data field="name">TestImportMergeOrg2</data>
    <resource name="org_office" uuid="TESTIMPORTMERGEOFFICE2">
        <data field="name">TestImportMergeOffice2</data>
    </resource>
</resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("org_organisation")
        resource.import_xml(xmltree)
        self.assertEqual(resource.error, None)

    def testImportMerge(self):

        s3db = current.s3db
        UUID = "org_organisation.uuid"
        DELETED = "org_organisation.deleted"
        REPLACEDBY = "org_organisation.deleted_rb"
        uids = ["TESTIMPORTMERGEORG1", "TESTIMPORTMERGEORG2"]
        test_fields = ["id", "uuid", "deleted", "deleted_rb", "office.name"]

        # Check the existing records
        resource = s3db.resource("org_organisation",
                                 uid =uids, include_deleted = True)
        result = resource.select(test_fields, limit=None)["rows"]
        self.assertEqual(len(result), 2)
        for record in result:
            self.assertTrue(record[UUID] in uids)
            self.assertFalse(record[DELETED])
            self.assertEqual(record[REPLACEDBY], None)
            if record[UUID] == "TESTIMPORTMERGEORG2":
                self.assertEqual(record["org_office.name"], "TestImportMergeOffice2")
            else:
                self.assertEqual(record["org_office.name"], None)

        # Send the merge
        xmlstr = """
<s3xml>
<resource name="org_organisation" uuid="TESTIMPORTMERGEORG1">
    <data field="name">TestImportMergeOrg1</data>
</resource>
<resource name="org_organisation" uuid="TESTIMPORTMERGEORG2"
            deleted="True" replaced_by="TESTIMPORTMERGEORG1" />
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("org_organisation")
        msg = resource.import_xml(xmltree)
        self.assertEqual(resource.error, None)

        # Check the result
        resource = s3db.resource("org_organisation",
                                 uid =uids, include_deleted = True)
        result = resource.select(test_fields, limit=None)["rows"]
        self.assertEqual(len(result), 2)
        for record in result:
            if record[UUID] == "TESTIMPORTMERGEORG1":
                self.assertFalse(record[DELETED])
                self.assertEqual(record[REPLACEDBY], None)
            elif record[UUID] == "TESTIMPORTMERGEORG2":
                self.assertTrue(record[DELETED])
                replaced_by = record[REPLACEDBY]
                row = current.db(resource.table._id == replaced_by) \
                             .select(resource.table.uuid, limitby=(0, 1)) \
                             .first()
                self.assertEqual(row.uuid, "TESTIMPORTMERGEORG1")

    def tearDown(self):

        current.auth.override = False
        current.db.rollback()

# =============================================================================
class ImportMergeWithExistingOriginal(unittest.TestCase):
    """ Test correct import of merge if only the final record pre-exists """

    def setUp(self):

        current.auth.override = True

        # Create records
        xmlstr = """
<s3xml>
<resource name="org_organisation" uuid="TESTIMPORTMERGEORG3">
    <data field="name">TestImportMergeOrg3</data>
</resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("org_organisation")
        resource.import_xml(xmltree)
        self.assertEqual(resource.error, None)

    def testImportMerge(self):

        s3db = current.s3db
        UUID = "org_organisation.uuid"
        DELETED = "org_organisation.deleted"
        REPLACEDBY = "org_organisation.deleted_rb"
        uids = ["TESTIMPORTMERGEORG3", "TESTIMPORTMERGEORG4"]
        test_fields = ["id", "uuid", "deleted", "deleted_rb"]

        # Check the existing record
        resource = s3db.resource("org_organisation",
                                 uid =uids, include_deleted = True)
        result = resource.select(test_fields, limit=None)["rows"]
        self.assertEqual(len(result), 1)
        record = result[0]
        self.assertTrue(record[UUID] in uids)
        self.assertFalse(record[DELETED])
        self.assertEqual(record[REPLACEDBY], None)

        # Send the merge
        xmlstr = """
<s3xml>
<resource name="org_organisation" uuid="TESTIMPORTMERGEORG3">
    <data field="name">TestImportMergeOrg3</data>
</resource>
<resource name="org_organisation" uuid="TESTIMPORTMERGEORG4"
            deleted="True" replaced_by="TESTIMPORTMERGEORG3" />
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("org_organisation")
        msg = resource.import_xml(xmltree)
        self.assertEqual(resource.error, None)

        # Check the result: the duplicate should never be imported
        # Note that no components of the deleted duplicate would ever
        # get exported - hence no need to test the handling of it
        resource = s3db.resource("org_organisation",
                                 uid =uids, include_deleted = True)
        result = resource.select(test_fields, limit=None)["rows"]
        self.assertEqual(len(result), 1)
        record = result[0]
        self.assertEqual(record[UUID], "TESTIMPORTMERGEORG3")
        self.assertFalse(record[DELETED])
        self.assertEqual(record[REPLACEDBY], None)

    def tearDown(self):

        current.auth.override = False
        current.db.rollback()

# =============================================================================
class ImportMergeWithExistingDuplicate(unittest.TestCase):
    """ Test correct import of merge if only the duplicate record pre-exists """

    def setUp(self):

        current.auth.override = True

        # Create records
        xmlstr = """
<s3xml>
<resource name="org_organisation" uuid="TESTIMPORTMERGEORG6">
    <data field="name">TestImportMergeOrg6</data>
    <resource name="org_office" uuid="TESTIMPORTMERGEOFFICE6">
        <data field="name">TestImportMergeOffice6</data>
    </resource>
</resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("org_organisation")
        resource.import_xml(xmltree)
        self.assertEqual(resource.error, None)

    def testImportMerge(self):

        s3db = current.s3db
        UUID = "org_organisation.uuid"
        DELETED = "org_organisation.deleted"
        REPLACEDBY = "org_organisation.deleted_rb"
        uids = ["TESTIMPORTMERGEORG5", "TESTIMPORTMERGEORG6"]
        test_fields = ["id", "uuid", "deleted", "deleted_rb", "office.name"]

        # Check the existing records
        resource = s3db.resource("org_organisation",
                                 uid =uids, include_deleted = True)
        result = resource.select(test_fields, limit=None)["rows"]
        self.assertEqual(len(result), 1)
        record = result[0]
        self.assertTrue(record[UUID] in uids)
        self.assertFalse(record[DELETED])
        self.assertEqual(record[REPLACEDBY], None)
        self.assertEqual(record["org_office.name"], "TestImportMergeOffice6")

        # Send the merge
        xmlstr = """
<s3xml>
<resource name="org_organisation" uuid="TESTIMPORTMERGEORG5">
    <data field="name">TestImportMergeOrg5</data>
</resource>
<resource name="org_organisation" uuid="TESTIMPORTMERGEORG6"
            deleted="True" replaced_by="TESTIMPORTMERGEORG5" />
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("org_organisation")
        msg = resource.import_xml(xmltree)
        self.assertEqual(resource.error, None)

        # Check the result: new record gets imported, duplicate merged into it
        resource = s3db.resource("org_organisation",
                                 uid =uids, include_deleted = True)
        result = resource.select(test_fields, limit=None)["rows"]
        self.assertEqual(len(result), 2)
        for record in result:
            if record[UUID] == "TESTIMPORTMERGEORG5":
                self.assertFalse(record[DELETED])
                self.assertEqual(record[REPLACEDBY], None)
                self.assertEqual(record["org_office.name"], "TestImportMergeOffice6")
            elif record[UUID] == "TESTIMPORTMERGEORG6":
                self.assertTrue(record[DELETED])
                replaced_by = record[REPLACEDBY]
                row = current.db(resource.table._id == replaced_by) \
                             .select(resource.table.uuid, limitby=(0, 1)) \
                             .first()
                self.assertEqual(row.uuid, "TESTIMPORTMERGEORG5")
                self.assertEqual(record["org_office.name"], None)

    def tearDown(self):

        current.auth.override = False
        current.db.rollback()

# =============================================================================
class ImportMergeWithoutExistingRecords(unittest.TestCase):
    """ Test correct import of merge if none of the records pre-exists """

    def setUp(self):

        current.auth.override = True

    def testImportMerge(self):

        s3db = current.s3db
        UUID = "org_organisation.uuid"
        DELETED = "org_organisation.deleted"
        REPLACEDBY = "org_organisation.deleted_rb"
        uids = ["TESTIMPORTMERGEORG7", "TESTIMPORTMERGEORG8"]
        test_fields = ["id", "uuid", "deleted", "deleted_rb"]

        # Check the existing records
        resource = s3db.resource("org_organisation",
                                 uid =uids, include_deleted = True)
        result = resource.select(test_fields, limit=None)["rows"]
        self.assertEqual(len(result), 0)

        # Send the merge
        xmlstr = """
<s3xml>
<resource name="org_organisation" uuid="TESTIMPORTMERGEORG7">
    <data field="name">TestImportMergeOrg7</data>
</resource>
<resource name="org_organisation" uuid="TESTIMPORTMERGEORG8"
            deleted="True" replaced_by="TESTIMPORTMERGEORG7" />
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("org_organisation")
        msg = resource.import_xml(xmltree)
        self.assertEqual(resource.error, None)

        # Check the result: only the final record gets imported
        # Note that no components of the deleted duplicate would ever
        # get exported - hence no need to test the handling of it
        resource = s3db.resource("org_organisation",
                                 uid =uids, include_deleted = True)
        result = resource.select(test_fields, limit=None)["rows"]
        self.assertEqual(len(result), 1)
        for record in result:
            self.assertEqual(record[UUID], "TESTIMPORTMERGEORG7")
            self.assertFalse(record[DELETED])
            self.assertEqual(record[REPLACEDBY], None)

    def tearDown(self):

        current.auth.override = False
        current.db.rollback()

# =============================================================================
class DataArchiveTests(unittest.TestCase):
    """ Tests for S3SyncDataArchive API """

    def testArchive(self):
        """ Test archiving of str objects"""

        assertEqual = self.assertEqual

        # Create a new archive
        archive = S3SyncDataArchive()

        # Add two XML strings to it
        xmlstr1 = "<example>First Example</example>"
        xmlstr2 = "<example>Second Example</example>"
        archive.add("test1.xml", xmlstr1)
        archive.add("test2.xml", xmlstr2)

        # Close the archive
        fileobj = archive.close()

        # Open the archive
        archive = S3SyncDataArchive(fileobj)

        # Verify archive contents
        extracted = archive.extract("test1.xml").read()
        assertEqual(extracted, xmlstr1)
        extracted = archive.extract("test2.xml").read()
        assertEqual(extracted, xmlstr2)

# =============================================================================
if __name__ == "__main__":

    run_suite(
        ExportMergeTests,
        ImportMergeTests,
        ImportMergeWithExistingRecords,
        ImportMergeWithExistingOriginal,
        ImportMergeWithExistingDuplicate,
        ImportMergeWithoutExistingRecords,
        DataArchiveTests,
        )

# END ========================================================================
