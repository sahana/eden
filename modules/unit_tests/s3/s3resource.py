# -*- coding: utf-8 -*-
#
# S3Resource Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3resource.py
#
import datetime
import json
import unittest

from lxml import etree

from gluon import *
from gluon.storage import Storage

from s3dal import Row
from s3 import *

from unit_tests import run_suite

# =============================================================================
class ComponentJoinConstructionTests(unittest.TestCase):
    """ Test component join construction """

    # -------------------------------------------------------------------------
    def testGetJoinMaster(self):
        """ Master resource has no join """

        resource = current.s3db.resource("pr_person")

        self.assertEqual(resource.get_join(), None)

    # -------------------------------------------------------------------------
    def testGetJoinSimpleComponent(self):
        """ Join for a simple component """

        resource = current.s3db.resource("pr_person")
        component = resource.components["identity"]

        rtable = resource.table
        ctable = component.table
        expected = (ctable.person_id == rtable.id) & \
                   (ctable.deleted != True)

        join = component.get_join()
        self.assertEqual(str(join), str(expected))

    # -------------------------------------------------------------------------
    def testGetJoinSuperComponent(self):
        """ Join for a super-component """

        resource = current.s3db.resource("pr_person")
        component = resource.components["contact"]

        rtable = resource.table
        ctable = component.table
        expected = (rtable.pe_id == ctable.pe_id) & \
                   (ctable.deleted != True)

        join = component.get_join()
        self.assertEqual(str(join), str(expected))

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetJoinLinkTableComponent(self):
        """ Join for a link-table component """

        resource = current.s3db.resource("project_project")
        component = resource.components["task"]

        project_project = resource.table
        project_task_project = component.link.table
        project_task = component.table
        expected = (((project_task_project.project_id == project_project.id) &
                   (project_task_project.deleted != True)) &
                   (project_task_project.task_id == project_task.id))

        join = component.get_join()
        self.assertEqual(str(join), str(expected))

# =============================================================================
class ComponentLeftJoinConstructionTests(unittest.TestCase):
    """ Test component left join construction """

    # -------------------------------------------------------------------------
    def testGetLeftJoinMaster(self):
        """ Master resource has no left join """

        resource = current.s3db.resource("pr_person")
        self.assertEqual(resource.get_left_join(), None)

    # -------------------------------------------------------------------------
    def testGetLeftJoinSimpleComponent(self):
        """ Left Join for a simple component """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        resource = current.s3db.resource("pr_person")
        component = resource.components["identity"]

        rtable = resource.table
        ctable = component.table
        expected = ctable.on((ctable.person_id == rtable.id) &
                             (ctable.deleted != True))

        ljoin = component.get_left_join()
        assertTrue(isinstance(ljoin, list))
        assertEqual(len(ljoin), 1)
        assertEqual(str(ljoin[0]), str(expected))

    # -------------------------------------------------------------------------
    def testGetLeftJoinSuperComponent(self):
        """ Left Join for a super-component """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        resource = current.s3db.resource("pr_person")
        component = resource.components["contact"]

        rtable = resource.table
        ctable = component.table
        expected = ctable.on((rtable.pe_id == ctable.pe_id) &
                             (ctable.deleted != True))

        ljoin = component.get_left_join()
        assertTrue(isinstance(ljoin, list))
        assertEqual(len(ljoin), 1)
        assertEqual(str(ljoin[0]), str(expected))

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetLeftJoinLinkTableComponent(self):
        """ Left Join for a link-table component """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        resource = current.s3db.resource("project_project")
        component = resource.components["task"]

        rtable = resource.table
        ltable = component.link.table
        ctable = component.table

        expected_l = ltable.on((ltable.project_id == rtable.id) &
                               (ltable.deleted != True))
        expected_r = ctable.on(ltable.task_id == ctable.id)

        ljoin = component.get_left_join()
        assertTrue(isinstance(ljoin, list))
        assertEqual(len(ljoin), 2)
        assertEqual(str(ljoin[0]), str(expected_l))
        assertEqual(str(ljoin[1]), str(expected_r))

# =============================================================================
class ResourceAxisFilterTests(unittest.TestCase):
    """ Test Axis Filters """

    def testListTypeFilter(self):
        """ Test list:type axis value filtering """

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        tablename = "axis_filter"
        db = current.db
        db.define_table(tablename,
                        Field("facility_type_id",
                              "list:reference org_facility_type"),
                        *s3_meta_fields())
        table = db[tablename]

        try:

            s3db = current.s3db

            resource = s3db.resource(tablename)
            q = (FS("facility_type_id").contains([1,2,3])) & \
                (~(FS("facility_type_id") == 2))
            resource.add_filter(q)
            query = resource.get_query()
            af = S3AxisFilter(query.as_dict(flat=True), tablename)

            rfield = S3ResourceField(resource, "facility_type_id")

            values, ignore = af.values(rfield)
            assertTrue("1" in values)
            assertFalse("2" in values)
            assertTrue("3" in values)

            resource = s3db.resource(tablename)
            q = (FS("facility_type_id").contains([1,2,3])) & \
                (~(FS("facility_type_id") != 2))
            resource.add_filter(q)
            query = resource.get_query()
            af = S3AxisFilter(query.as_dict(flat=True), tablename)

            values, ignore = af.values(rfield)
            assertTrue("1" in values)
            assertTrue("2" in values)
            assertTrue("3" in values)

            resource = s3db.resource(tablename)
            q = (FS("facility_type_id").contains([1,2,3])) | \
                (~(FS("facility_type_id") == 2))
            resource.add_filter(q)
            query = resource.get_query()
            af = S3AxisFilter(query.as_dict(flat=True), tablename)

            values, ignore = af.values(rfield)
            assertTrue("1" in values)
            assertTrue("2" in values)
            assertTrue("3" in values)

            resource = s3db.resource(tablename)
            q = (FS("facility_type_id").contains([1,2,3])) | \
                (~(FS("facility_type_id") != 2))
            resource.add_filter(q)
            query = resource.get_query()
            af = S3AxisFilter(query.as_dict(flat=True), tablename)

            values, ignore = af.values(rfield)
            assertTrue("1" in values)
            assertTrue("2" in values)
            assertTrue("3" in values)

        finally:
            try:
                table.drop()
            except:
                pass

# =============================================================================
class ResourceDataTableFilterTests(unittest.TestCase):
    """ Test datatable_filter """

    # -------------------------------------------------------------------------
    def testDataTableFilterStandard(self):
        """ Test Standard Data Table """

        resource = current.s3db.resource("hrm_certificate_skill")
        vars = Storage({"bSortable_0": "false",
                        "bSortable_1": "true",
                        "bSortable_2": "true",
                        "sSortDir_0": "asc",
                        "iSortCol_0": "1",
                        "iColumns": "3",
                        "iSortingCols": "1"})
        searchq, orderby, left = resource.datatable_filter(["id",
                                                            "skill_id",
                                                            "competency_id"],
                                                            vars)
        self.assertEqual(orderby, "hrm_skill.name asc")

    # -------------------------------------------------------------------------
    def testDataTableFilterWithBulkColumn(self):
        """ Test De-Duplicator Data Table """

        resource = current.s3db.resource("hrm_certificate_skill")
        vars = Storage({"bSortable_0": "false",
                        "bSortable_1": "false",
                        "bSortable_2": "true",
                        "bSortable_3": "true",
                        "sSortDir_0": "desc",
                        "iSortCol_0": "2",
                        "iColumns": "4",
                        "iSortingCols": "1"})
        searchq, orderby, left = resource.datatable_filter(["id",
                                                            "skill_id",
                                                            "competency_id"],
                                                            vars)
        self.assertEqual(orderby, "hrm_skill.name desc")

    # -------------------------------------------------------------------------
    def testDataTableFilterOther(self):
        """ Test Other Data Table """

        resource = current.s3db.resource("hrm_certificate_skill")
        vars = Storage({"bSortable_0": "false",
                        "bSortable_1": "true",
                        "bSortable_2": "false",
                        "bSortable_3": "true",
                        "sSortDir_0": "desc",
                        "iSortCol_0": "3",
                        "iColumns": "4",
                        "iSortingCols": "1"})
        searchq, orderby, left = resource.datatable_filter(["id",
                                                            "skill_id",
                                                            "competency_id"],
                                                            vars)
        self.assertEqual(orderby, "hrm_competency_rating.priority desc")

# =============================================================================
class ResourceExportTests(unittest.TestCase):
    """ Test XML export of resources """

    # -------------------------------------------------------------------------
    def testExportTree(self):
        """ Test export of a resource as element tree """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        xml = current.xml
        auth = current.auth

        auth.override = True

        xmlstr = """
<s3xml>
    <resource name="org_organisation">
        <data field="name">TestExportTreeOrganisation1</data>
        <resource name="org_office" uuid="ETO1">
            <data field="name">TestExportTreeOffice1</data>
        </resource>
    </resource>
</s3xml>"""

        try:
            xmltree = etree.ElementTree(etree.fromstring(xmlstr))
            resource = current.s3db.resource("org_organisation")
            resource.import_xml(xmltree)

            resource = current.s3db.resource("org_office", uid="ETO1")
            tree = resource.export_tree(start=0, limit=1, dereference=False)

            root = tree.getroot()
            assertEqual(root.tag, xml.TAG.root)

            attrib = root.attrib
            assertEqual(len(attrib), 5)
            assertEqual(attrib["success"], "true")
            assertEqual(attrib["start"], "0")
            assertEqual(attrib["limit"], "1")
            assertEqual(attrib["results"], "1")
            assertTrue("url" in attrib)

            assertEqual(len(root), 1)
            for child in root:
                assertEqual(child.tag, xml.TAG.resource)
                attrib = child.attrib
                assertEqual(attrib["name"], "org_office")
                assertTrue("uuid" in attrib)
        finally:
            current.db.rollback()
            auth.override = False

    # -------------------------------------------------------------------------
    def testExportTreeWithMaxBounds(self):
        """ Text XML output with max bounds """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        xml = current.xml
        auth = current.auth

        auth.override = True

        xmlstr = """
<s3xml>
    <resource name="org_organisation">
        <data field="name">TestExportTreeOrganisation2</data>
        <resource name="org_office" uuid="ETO2">
            <data field="name">TestExportTreeOffice2</data>
        </resource>
    </resource>
</s3xml>"""

        try:
            xmltree = etree.ElementTree(etree.fromstring(xmlstr))
            resource = current.s3db.resource("org_organisation")
            resource.import_xml(xmltree)

            resource = current.s3db.resource("org_office", uid="ETO2")
            tree = resource.export_tree(start=0,
                                        limit=1,
                                        dereference=False,
                                        maxbounds=True)
            root = tree.getroot()
            attrib = root.attrib
            assertEqual(len(attrib), 9)
            assertTrue("latmin" in attrib)
            assertTrue("latmax" in attrib)
            assertTrue("lonmin" in attrib)
            assertTrue("lonmax" in attrib)

        finally:
            current.db.rollback()
            auth.override = False

    # -------------------------------------------------------------------------
    def testExportTreeWithMSince(self):
        """ Test automatic ordering of export items by mtime if msince is given """

        assertEqual = self.assertEqual

        auth = current.auth
        auth.override = True

        xmlstr = """
<s3xml>
    <resource name="hms_hospital" uuid="ORDERTESTHOSPITAL1">
        <data field="name">OrderTestHospital1</data>
    </resource>
    <resource name="hms_hospital" uuid="ORDERTESTHOSPITAL2">
        <data field="name">OrderTestHospital2</data>
    </resource>
</s3xml>"""

        try:
            xmltree = etree.ElementTree(etree.fromstring(xmlstr))
            resource = current.s3db.resource("hms_hospital")
            resource.import_xml(xmltree)

            resource = current.s3db.resource(resource,
                                             uid=["ORDERTESTHOSPITAL1",
                                                  "ORDERTESTHOSPITAL2",
                                                  ])

            # Load the records without orderby
            resource.load(limit=2)
            assertEqual(len(resource), 2)

            # Determine which comes first and which last without orderby
            first = resource._rows[0]["uuid"]
            last = resource._rows[1]["uuid"]

            # Make first older than last
            now = datetime.datetime.utcnow()
            ts = now - datetime.timedelta(seconds=5)
            resource._rows[0].update_record(created_on = ts,
                                            modified_on = ts,
                                            )
            resource._rows[1].update_record(created_on = now,
                                            modified_on = now,
                                            )

            # Without msince, elements should have same order as in load
            msince = msince=datetime.datetime.utcnow() - datetime.timedelta(days=1)
            tree = resource.export_tree(start=0,
                                        limit=1,
                                        dereference=False)
            root = tree.getroot()
            assertEqual(len(root), 1)

            child = root[0]
            uuid = child.get("uuid", None)
            assertEqual(uuid, first)

            # With msince, elements should be ordered by age
            tree = resource.export_tree(start=0,
                                        limit=1,
                                        msince=msince,
                                        dereference=False)
            root = tree.getroot()
            assertEqual(len(root), 1)

            child = root[0]
            uuid = child.get("uuid", None)
            assertEqual(uuid, last)

        finally:
            current.db.rollback()
            auth.override = False

    # -------------------------------------------------------------------------
    def testExportXMLWithSyncFilters(self):
        """ Test XML Export with Sync Filters """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        auth = current.auth
        s3db = current.s3db

        auth.override = True

        xmlstr = """
<s3xml>
    <resource name="org_office_type" uuid="SFT1">
        <data field="name">SFT1</data>
    </resource>
    <resource name="org_office_type" uuid="SFT2">
        <data field="name">SFT2</data>
    </resource>
    <resource name="org_organisation" uuid="SFO1">
        <data field="name">Sync1FilterOrganisation</data>
        <resource name="org_office" uuid="S1FO1">
            <data field="name">Sync1FilterOffice1</data>
            <reference field="office_type_id" resource="org_office_type" uuid="SFT1"/>
        </resource>
    </resource>
    <resource name="org_organisation" uuid="SFO2">
        <data field="name">Sync2FilterOrganisation</data>
        <resource name="org_office" uuid="S1FO2">
            <data field="name">Sync1FilterOffice2</data>
            <reference field="office_type_id" resource="org_office_type" uuid="SFT2"/>
        </resource>
    </resource>
    <resource name="org_organisation" uuid="SFO3">
        <data field="name">Sync3FilterOrganisation</data>
        <resource name="org_office" uuid="S1FO3">
            <data field="name">Sync1FilterOffice3</data>
        </resource>
        <resource name="org_office" uuid="S2FO1">
            <data field="name">Sync2FilterOffice1</data>
        </resource>
    </resource>
</s3xml>"""

        try:
            xmltree = etree.ElementTree(etree.fromstring(xmlstr))
            resource = current.s3db.resource("org_organisation")
            resource.import_xml(xmltree)

            # Filter master by master field
            resource = s3db.resource(resource,
                                     uid=["SFO1", "SFO2", "SFO3"])

            filters = {"org_organisation": {"organisation.name__like": "Sync1*"}}

            xmlexport = resource.export_xml(filters=filters,
                                            mcomponents=["office"],
                                            dereference=False)

            xmltree = etree.ElementTree(etree.fromstring(xmlexport))
            orgs = xmltree.xpath("resource[@name='org_organisation']")
            assertEqual(len(orgs), 1)
            assertEqual(orgs[0].get("uuid"), "SFO1")

            offices = xmltree.xpath("//resource[@name='org_office']")
            assertEqual(len(offices), 1)
            assertEqual(offices[0].get("uuid"), "S1FO1")

            # Filter master by component field
            resource = s3db.resource(resource,
                                     uid=["SFO1", "SFO2", "SFO3"])

            filters = {"org_organisation": {"office.name__like": "Sync2*"}}

            xmlexport = resource.export_xml(filters=filters,
                                            mcomponents=["office"],
                                            dereference=False)

            xmltree = etree.ElementTree(etree.fromstring(xmlexport))
            orgs = xmltree.xpath("resource[@name='org_organisation']")
            assertEqual(len(orgs), 1)
            assertEqual(orgs[0].get("uuid"), "SFO3")

            offices = xmltree.xpath("//resource[@name='org_office']")
            assertEqual(len(offices), 1)
            assertEqual(offices[0].get("uuid"), "S2FO1")

            # Filter component by component field
            resource = s3db.resource(resource,
                                     uid=["SFO1", "SFO2", "SFO3"])

            filters = {"org_office": {"office.name__like": "Sync1*"}}

            xmlexport = resource.export_xml(filters=filters,
                                            mcomponents=["office"],
                                            dereference=False)
            xmltree = etree.ElementTree(etree.fromstring(xmlexport))

            orgs = xmltree.xpath("resource[@name='org_organisation']")
            assertEqual(len(orgs), 3)
            uids = [org.get("uuid") for org in orgs]
            assertTrue("SFO1" in uids)
            assertTrue("SFO2" in uids)
            assertTrue("SFO3" in uids)

            offices = xmltree.xpath("//resource[@name='org_office']")
            assertEqual(len(offices), 3)
            uids = [office.get("uuid") for office in offices]
            assertTrue("S1FO1" in uids)
            assertTrue("S1FO2" in uids)
            assertTrue("S1FO3" in uids)
            assertFalse("S2FO1" in uids)

            # Filter referenced table
            resource = s3db.resource(resource,
                                     uid=["SFO1", "SFO2"])

            xmlexport = resource.export_xml(filters=None,
                                            mcomponents=["office"])
            xmltree = etree.ElementTree(etree.fromstring(xmlexport))

            types = xmltree.xpath("resource[@name='org_office_type']")
            assertEqual(len(types), 2)
            uids = [t.get("uuid") for t in types]
            assertTrue("SFT1" in uids)
            assertTrue("SFT2" in uids)

            resource = s3db.resource(resource,
                                     uid=["SFO1", "SFO2"])

            filters = {"org_office_type": {"office_type.name__like": "SFT1*"}}

            xmlexport = resource.export_xml(filters=filters,
                                            mcomponents=["office"])
            xmltree = etree.ElementTree(etree.fromstring(xmlexport))

            types = xmltree.xpath("resource[@name='org_office_type']")
            assertEqual(len(types), 1)
            assertEqual(types[0].get("uuid"), "SFT1")

        finally:
            current.db.rollback()
            auth.override = False

# =============================================================================
class ResourceImportTests(unittest.TestCase):
    """ Test XML imports into resources """

    @classmethod
    def setUpClass(cls):

        current.auth.override = True

    # -------------------------------------------------------------------------
    def testImportXML(self):
        """ Test JSON message after XML import """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        xmlstr = """
<s3xml>

    <resource name="pr_person">

        <data field="first_name">Jason</data>
        <data field="last_name">Test</data>
        <data field="initials">JT</data>
        <data field="date_of_birth" value="1922-03-15"/>

        <resource name="pr_contact">
            <data field="contact_method">EMAIL</data>
            <data field="value">json@example.com</data>
        </resource>

        <resource name="pr_contact">
            <data field="contact_method">SMS</data>
            <data field="value">+123456789</data>
        </resource>

    </resource>

</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = current.s3db.resource("pr_person")
        msg = resource.import_xml(xmltree)

        msg = json.loads(msg)

        assertEqual(msg["status"], "success")
        assertEqual(msg["statuscode"], "200")
        assertEqual(msg["records"], 1)
        assertTrue("created" in msg)
        assertTrue(isinstance(msg["created"], list))
        assertTrue(len(msg["created"]) == 1)

    # -------------------------------------------------------------------------
    def testImportXMLWithMTime(self):
        """ Test mtime update in imports """

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

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("hms_hospital")
        resource.import_xml(xmltree)
        self.assertEqual(s3_utc(resource.mtime),
                         s3_utc(datetime.datetime(2012, 4, 21, 0, 0, 0)))

    # -------------------------------------------------------------------------
    def testImportXMLWithoutMTime(self):
        """ Test mtime update in imports with no mtime given """

        # If no mtime is given, resource.mtime should be set to current UTC
        xmlstr = """
<s3xml>
    <resource name="hms_hospital" uuid="MTIMETESTHOSPITAL3">
        <data field="name">MTimeTestHospital3</data>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("hms_hospital")
        resource.import_xml(xmltree)
        # Can't compare with exactly utcnow as these would be milliseconds apart,
        # assume equal dates are sufficient for this test
        self.assertEqual(s3_utc(resource.mtime).date(),
                         s3_utc(datetime.datetime.utcnow()).date())

    # -------------------------------------------------------------------------
    def testImportXMLWithPartialMTime(self):
        """ Test mtime update in imports if mtime given in only some records """

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

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("hms_hospital")
        resource.import_xml(xmltree)
        self.assertEqual(s3_utc(resource.mtime).date(),
                         s3_utc(datetime.datetime.utcnow()).date())

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        current.db.rollback()
        current.auth.override = False

# =============================================================================
class ResourceDataObjectAPITests (unittest.TestCase):
    """ Test the S3Resource Data Object API """

    # -------------------------------------------------------------------------
    def testLoadStatusIndication(self):
        """ Test load status indication by value of _rows """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        # A newly created resource has _rows=None
        resource = current.s3db.resource("project_time")
        assertEqual(resource._rows, None)

        # After load(), this must always be a list
        resource.load()
        assertNotEqual(resource._rows, None)
        assertTrue(isinstance(resource._rows, list))

        # After clear(), this must be None again
        resource.clear()
        assertEqual(resource._rows, None)

    # -------------------------------------------------------------------------
    def testLoadFieldSelection(self):
        """ Test selection of fields in load() with fields and skip """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        s3db = current.s3db
        auth = current.auth
        auth.override = True

        xmlstr = """
<s3xml>
    <resource name="org_office" uuid="LOADTESTOFFICE">
        <data field="name">LoadTestOffice</data>
        <reference field="organisation_id" resource="org_organisation">
            <resource name="org_organisation">
                <data field="name">LoadTestOrganisation</data>
            </resource>
        </reference>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        try:
            resource = s3db.resource("org_office")
            resource.import_xml(xmltree)

            resource = s3db.resource("org_office", uid="LOADTESTOFFICE")

            # Restrict field selection
            rows = resource.load(fields=["name"])
            assertEqual(len(rows), 1)
            row = rows[0]
            assertTrue(hasattr(row, "id"))
            assertTrue(hasattr(row, "name"))
            assertTrue(hasattr(row, "created_on")) # meta-field
            assertTrue(hasattr(row, "pe_id")) # super-key
            assertFalse(hasattr(row, "organisation_id"))

            # Skip field
            rows = resource.load(skip=["name"])
            assertEqual(len(rows), 1)
            row = rows[0]
            assertTrue(hasattr(row, "id"))
            assertFalse(hasattr(row, "name"))
            assertTrue(hasattr(row, "created_on"))
            assertTrue(hasattr(row, "pe_id"))
            assertTrue(hasattr(row, "organisation_id"))

            # skip overrides fields
            rows = resource.load(fields=["name", "organisation_id"],
                                 skip=["organisation_id"])
            assertEqual(len(rows), 1)
            row = rows[0]
            assertTrue(hasattr(row, "id"))
            assertTrue(hasattr(row, "name"))
            assertTrue(hasattr(row, "created_on"))
            assertTrue(hasattr(row, "pe_id"))
            assertFalse(hasattr(row, "organisation_id"))

            # Can't skip meta-fields
            rows = resource.load(fields=["name", "organisation_id"],
                                 skip=["created_on"])
            assertEqual(len(rows), 1)
            row = rows[0]
            assertTrue(hasattr(row, "id"))
            assertTrue(hasattr(row, "name"))
            assertTrue(hasattr(row, "created_on"))
            assertTrue(hasattr(row, "pe_id"))
            assertTrue(hasattr(row, "organisation_id"))

            # Can't skip record ID
            rows = resource.load(fields=["name", "organisation_id"],
                                 skip=["id"])
            assertEqual(len(rows), 1)
            row = rows[0]
            assertTrue(hasattr(row, "id"))
            assertTrue(hasattr(row, "name"))
            assertTrue(hasattr(row, "created_on"))
            assertTrue(hasattr(row, "pe_id"))
            assertTrue(hasattr(row, "organisation_id"))

            # Can't skip super-keys
            rows = resource.load(fields=["name", "organisation_id"],
                                 skip=["pe_id"])
            assertEqual(len(rows), 1)
            row = rows[0]
            assertTrue(hasattr(row, "id"))
            assertTrue(hasattr(row, "name"))
            assertTrue(hasattr(row, "created_on"))
            assertTrue(hasattr(row, "pe_id"))
            assertTrue(hasattr(row, "organisation_id"))

        finally:
            auth.override = False
            current.db.rollback()

# =============================================================================
class MergeOrganisationsTests(unittest.TestCase):
    """ Test merging org_organisation records """

    # -------------------------------------------------------------------------
    def setUp(self):
        """ Set up organisation records """

        s3db = current.s3db

        otable = s3db.org_organisation

        org1 = Storage(name="Merge Test Organisation",
                       acronym="MTO",
                       country="UK",
                       website="http://www.example.org")
        org1_id = otable.insert(**org1)
        org1.update(id=org1_id)
        s3db.update_super(otable, org1)

        org2 = Storage(name="Merger Test Organisation",
                       acronym="MTOrg",
                       country="US",
                       website="http://www.example.com")
        org2_id = otable.insert(**org2)
        org2.update(id=org2_id)
        s3db.update_super(otable, org2)

        self.id1 = org1_id
        self.id2 = org2_id

        self.resource = s3db.resource("org_organisation",
                                      id=[self.id1, self.id2])
        current.auth.override = True

    # -------------------------------------------------------------------------
    def testMerge(self):
        """ Test merge """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        success = self.resource.merge(self.id1, self.id2)
        assertTrue(success)
        org1, org2 = self.get_records()

        assertNotEqual(org1, None)
        assertNotEqual(org2, None)

        assertFalse(org1.deleted)
        assertTrue(org2.deleted)
        assertEqual(str(self.id1), str(org2.deleted_rb))

        assertEqual(org1.name, "Merge Test Organisation")
        assertEqual(org1.acronym, "MTO")
        assertEqual(org1.country, "UK")
        assertEqual(org1.website, "http://www.example.org")

        assertEqual(org2.name, "Merger Test Organisation")
        assertEqual(org2.acronym, "MTOrg")
        assertEqual(org2.country, "US")
        assertEqual(org2.website, "http://www.example.com")

    # -------------------------------------------------------------------------
    def testMergeMissingOriginalSE(self):
        """ Test merge where original record lacks SEs """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        resource = self.resource
        get_records = self.get_records

        org1, org2 = get_records()
        success = current.s3db.delete_super(resource.table, org1)
        assertTrue(success)
        org1, org2 = get_records()
        assertEqual(org1.pe_id, None)

        success = resource.merge(self.id1, self.id2)
        assertTrue(success)
        org1, org2 = get_records()

        assertNotEqual(org1, None)
        assertNotEqual(org2, None)

        self.assertFalse(org1.deleted)
        assertTrue(org2.deleted)
        assertEqual(str(self.id1), str(org2.deleted_rb))

        assertNotEqual(org1.pe_id, None)

    # -------------------------------------------------------------------------
    def testMergeMissingDuplicateSE(self):
        """ Test merge where duplicate record lacks SEs """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        resource = self.resource
        get_records = self.get_records

        org1, org2 = get_records()
        success = current.s3db.delete_super(resource.table, org2)
        assertTrue(success)
        org1, org2 = get_records()
        assertEqual(org2.pe_id, None)

        success = resource.merge(self.id1, self.id2)
        assertTrue(success)
        org1, org2 = get_records()

        assertNotEqual(org1, None)
        assertNotEqual(org2, None)

        assertFalse(org1.deleted)
        assertTrue(org2.deleted)
        assertEqual(str(self.id1), str(org2.deleted_rb))

        assertEqual(org2.pe_id, None)

    # -------------------------------------------------------------------------
    def testMergeMissingSE(self):
        """ Test merge where both records lack SEs """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        resource = self.resource
        get_records = self.get_records

        org1, org2 = get_records()
        success = current.s3db.delete_super(resource.table, org1)
        success = current.s3db.delete_super(resource.table, org2)
        assertTrue(success)
        org1, org2 = get_records()
        assertEqual(org1.pe_id, None)
        assertEqual(org2.pe_id, None)

        success = resource.merge(self.id1, self.id2)
        assertTrue(success)
        org1, org2 = get_records()

        assertNotEqual(org1, None)
        assertNotEqual(org2, None)

        assertFalse(org1.deleted)
        assertTrue(org2.deleted)
        assertEqual(str(self.id1), str(org2.deleted_rb))

        assertNotEqual(org1.pe_id, None)
        assertEqual(org2.pe_id, None)

    # -------------------------------------------------------------------------
    def testMergeReplace(self):
        """ Test merge with replace """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        success = self.resource.merge(self.id1, self.id2,
                                      replace = ["acronym", "website"])
        assertTrue(success)
        org1, org2 = self.get_records()

        assertNotEqual(org1, None)
        assertNotEqual(org2, None)

        assertFalse(org1.deleted)
        assertTrue(org2.deleted)
        assertEqual(str(self.id1), str(org2.deleted_rb))

        assertEqual(org1.name, "Merge Test Organisation")
        assertEqual(org1.acronym, "MTOrg")
        assertEqual(org1.country, "UK")
        assertEqual(org1.website, "http://www.example.com")

        assertEqual(org2.name, "Merger Test Organisation")
        assertEqual(org2.acronym, "MTOrg")
        assertEqual(org2.country, "US")
        assertEqual(org2.website, "http://www.example.com")

    # -------------------------------------------------------------------------
    def testMergeReplaceAndUpdate(self):
        """ Test merge with replace and Update"""

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        success = self.resource.merge(self.id1, self.id2,
                                      replace = ["acronym"],
                                      update = Storage(website = "http://www.example.co.uk"))
        assertTrue(success)
        org1, org2 = self.get_records()

        assertNotEqual(org1, None)
        assertNotEqual(org2, None)

        assertFalse(org1.deleted)
        assertTrue(org2.deleted)
        assertEqual(str(self.id1), str(org2.deleted_rb))

        assertEqual(org1.name, "Merge Test Organisation")
        assertEqual(org1.acronym, "MTOrg")
        assertEqual(org1.country, "UK")
        assertEqual(org1.website, "http://www.example.co.uk")

        assertEqual(org2.name, "Merger Test Organisation")
        assertEqual(org2.acronym, "MTOrg")
        assertEqual(org2.country, "US")
        assertEqual(org2.website, "http://www.example.com")

    # -------------------------------------------------------------------------
    def testMergeLinkTable(self):
        """ Test merge of link table entries """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        db = current.db
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        org1, org2 = self.get_records()

        org1_pe_id = s3db.pr_get_pe_id(org1)
        org2_pe_id = s3db.pr_get_pe_id(org2)

        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        branch1 = Storage(name="TestBranch1")
        branch1_id = otable.insert(**branch1)
        assertNotEqual(branch1_id, None)

        branch1.update(id=branch1_id)
        s3db.update_super(otable, branch1)
        branch1_pe_id = s3db.pr_get_pe_id(otable, branch1_id)
        assertNotEqual(branch1_pe_id, None)

        link1 = Storage(organisation_id=self.id1, branch_id=branch1_id)
        link1_id = btable.insert(**link1)
        s3db.pr_update_affiliations(btable, link1_id)
        ancestors = s3db.pr_get_ancestors(branch1_pe_id)
        assertEqual(ancestors, [str(org1_pe_id)])

        branch2 = Storage(name="TestBranch2")
        branch2_id = otable.insert(**branch2)
        assertNotEqual(branch2_id, None)

        branch2.update(id=branch2_id)
        s3db.update_super(otable, branch2)
        branch2_pe_id = s3db.pr_get_pe_id("org_organisation", branch2_id)
        assertNotEqual(branch2_pe_id, None)

        link2 = Storage(organisation_id=self.id2, branch_id=branch2_id)
        link2_id = btable.insert(**link2)
        s3db.pr_update_affiliations(btable, link2_id)
        ancestors = s3db.pr_get_ancestors(branch2_pe_id)
        assertEqual(ancestors, [str(org2_pe_id)])

        success = self.resource.merge(self.id1, self.id2)
        assertTrue(success)

        link1 = db(btable._id == link1_id).select(limitby=(0, 1)).first()
        link2 = db(btable._id == link2_id).select(limitby=(0, 1)).first()

        assertEqual(str(link1.organisation_id), str(self.id1))
        assertEqual(str(link2.organisation_id), str(self.id1))

        ancestors = s3db.pr_get_ancestors(branch1_pe_id)
        assertEqual(ancestors, [str(org1_pe_id)])

        ancestors = s3db.pr_get_ancestors(branch2_pe_id)
        assertEqual(ancestors, [str(org1_pe_id)])

    # -------------------------------------------------------------------------
    def testMergeVirtualReference(self):
        """ Test merge with virtual references """

        utable = current.auth.settings.table_user
        user = Storage(first_name="Test",
                       last_name="User",
                       password="xyz",
                       email="testuser@example.com",
                       organisation_id=self.id2)
        user_id = utable.insert(**user)

        success = self.resource.merge(self.id1, self.id2)
        self.assertTrue(success)

        user = current.db(utable.id == user_id).select(limitby=(0, 1)).first()
        self.assertNotEqual(user, None)

        self.assertEqual(str(user.organisation_id), str(self.id1))

    # -------------------------------------------------------------------------
    def testMergeRealms(self):
        """ Test merge of realms when merging two person entities """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        org1, org2 = self.get_records()

        s3db = current.s3db
        org1_pe_id = s3db.pr_get_pe_id(org1)
        org2_pe_id = s3db.pr_get_pe_id(org2)

        person = Storage(first_name="Nxthga",
                         realm_entity=org2_pe_id)
        ptable = s3db.pr_person
        person_id = ptable.insert(**person)

        person = ptable[person_id]
        assertEqual(person.realm_entity, org2_pe_id)

        success = self.resource.merge(self.id1, self.id2)
        assertTrue(success)

        person = ptable[person_id]
        assertEqual(person.realm_entity, org1_pe_id)

    # -------------------------------------------------------------------------
    def get_records(self):

        table = self.resource.table
        query = (table._id.belongs(self.id1, self.id2))
        rows = current.db(query).select(limitby=(0, 2))
        row1 = row2 = None
        for row in rows:
            row_id = row[table._id]
            if row_id == self.id1:
                row1 = row
            elif row_id == self.id2:
                row2 = row
        return (row1, row2)

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

# =============================================================================
class MergePersonsTests(unittest.TestCase):
    """ Test merging pr_person records """

    # -------------------------------------------------------------------------
    def setUp(self):
        """ Set up person records """

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        auth.override = True

        ptable = s3db.pr_person

        person1 = Storage(first_name="Test",
                          last_name="Person")
        person1_id = ptable.insert(**person1)
        person1.update(id=person1_id)
        s3db.update_super(ptable, person1)

        person2 = Storage(first_name="Test",
                          last_name="Person")
        person2_id = ptable.insert(**person2)
        person2.update(id=person2_id)
        s3db.update_super(ptable, person2)

        self.id1 = person1_id
        self.id2 = person2_id

        self.resource = s3db.resource("pr_person")

    # -------------------------------------------------------------------------
    def testPermissionError(self):
        """ Check for exception if not authorized """

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        # Anonymous
        auth.override = False
        auth.s3_impersonate(None)

        with self.assertRaises(current.auth.permission.error):
            self.resource.merge(self.id1, self.id2)

        # Check for proper rollback
        ptable = s3db.pr_person
        query = ptable._id.belongs((self.id1, self.id2))
        rows = db(query).select(ptable._id, limitby=(0, 2))
        self.assertEqual(len(rows), 0)

    # -------------------------------------------------------------------------
    def testOriginalNotFoundError(self):
        """ Check for exception if record not found """

        db = current.db
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        with self.assertRaises(KeyError):
            self.resource.merge(0, self.id2)

        # Check for proper rollback
        ptable = s3db.pr_person
        query = ptable._id.belongs((self.id1, self.id2))
        rows = db(query).select(ptable._id, limitby=(0, 2))
        self.assertEqual(len(rows), 0)

    # -------------------------------------------------------------------------
    def testNotDuplicateFoundError(self):
        """ Check for exception if record not found """

        db = current.db
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        with self.assertRaises(KeyError):
            self.resource.merge(self.id1, 0)

        # Check for proper rollback
        ptable = s3db.pr_person
        query = ptable._id.belongs((self.id1, self.id2))
        rows = db(query).select(ptable._id, limitby=(0, 2))
        self.assertEqual(len(rows), 0)

    # -------------------------------------------------------------------------
    def testMerge(self):
        """ Test merge """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        # Merge records
        success = self.resource.merge(self.id1, self.id2)
        assertTrue(success)

        # Check the merged records
        person1, person2 = self.get_records()
        assertNotEqual(person1, None)
        assertNotEqual(person2, None)

        # Check deleted status
        assertFalse(person1.deleted)
        assertTrue(person2.deleted)
        assertEqual(str(self.id1), str(person2.deleted_rb))

        # Check values
        assertEqual(person1.first_name, "Test")
        assertEqual(person1.last_name, "Person")

        assertEqual(person2.first_name, "Test")
        assertEqual(person2.last_name, "Person")

    # -------------------------------------------------------------------------
    def testMergeWithUpdate(self):
        """ Test merge with update """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        success = self.resource.merge(self.id1, self.id2,
                                      update = Storage(first_name = "Changed"))
        assertTrue(success)
        person1, person2 = self.get_records()

        assertNotEqual(person1, None)
        assertNotEqual(person2, None)

        assertFalse(person1.deleted)
        assertTrue(person2.deleted)
        assertEqual(str(self.id1), str(person2.deleted_rb))

        assertEqual(person1.first_name, "Changed")
        assertEqual(person1.last_name, "Person")

        assertEqual(person2.first_name, "Test")
        assertEqual(person2.last_name, "Person")

    # -------------------------------------------------------------------------
    def testMergeSingleComponent(self):
        """ Test merge of single-component """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        db = current.db
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        person1, person2 = self.get_records()

        dtable = s3db.pr_physical_description

        pd1 = Storage(pe_id=person1.pe_id,
                      blood_type="B+")
        pd1_id = dtable.insert(**pd1)
        pd1.update(id=pd1_id)
        s3db.update_super(dtable, pd1)

        pd2 = Storage(pe_id=person2.pe_id,
                      blood_type="B-")
        pd2_id = dtable.insert(**pd2)
        pd2.update(id=pd2_id)
        s3db.update_super(dtable, pd2)

        success = self.resource.merge(self.id1, self.id2,
                                      replace = ["physical_description.blood_type"])

        assertTrue(success)

        pd1 = db(dtable._id == pd1_id).select(limitby=(0, 1)).first()
        assertNotEqual(pd1, None)
        assertFalse(pd1.deleted)
        assertEqual(pd1.blood_type, "B-")
        assertEqual(pd1.pe_id, person1.pe_id)

        pd2 = db(dtable._id == pd2_id).select(limitby=(0, 1)).first()
        assertNotEqual(pd2, None)
        assertTrue(pd2.deleted)
        assertEqual(str(pd2.deleted_rb), str(pd1.id))

    # -------------------------------------------------------------------------
    def testMergeMultiComponent(self):
        """ Test merge of multiple-component """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        db = current.db
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        person1, person2 = self.get_records()

        itable = s3db.pr_identity

        id1 = Storage(person_id=person1.id,
                      type=1,
                      value="TEST1")
        id1_id = itable.insert(**id1)
        id1.update(id=id1_id)
        s3db.update_super(itable, id1)

        id2 = Storage(person_id=person2.id,
                      type=1,
                      value="TEST2")
        id2_id = itable.insert(**id2)
        id2.update(id=id2_id)
        s3db.update_super(itable, id2)

        success = self.resource.merge(self.id1, self.id2)
        assertTrue(success)

        id1 = db(itable._id == id1_id).select(limitby=(0, 1)).first()
        assertNotEqual(id1, None)
        assertFalse(id1.deleted)
        assertEqual(id1.person_id, self.id1)

        id2 = db(itable._id == id2_id).select(limitby=(0, 1)).first()
        assertNotEqual(id2, None)
        assertFalse(id2.deleted)
        assertEqual(id2.person_id, self.id1)

    # -------------------------------------------------------------------------
    def get_records(self):

        db = current.db
        table = self.resource.table
        query = (table._id.belongs(self.id1, self.id2))
        rows = db(query).select(limitby=(0, 2))
        row1 = row2 = None
        for row in rows:
            row_id = row[table._id]
            if row_id == self.id1:
                row1 = row
            elif row_id == self.id2:
                row2 = row
        return (row1, row2)

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

# =============================================================================
class MergeLocationsTests(unittest.TestCase):
    """ Test merging gis_locations """

    # -------------------------------------------------------------------------
    def setUp(self):
        """ Set up location records """

        auth = current.auth
        s3db = current.s3db

        auth.override = True

        ltable = s3db.gis_location

        location1 = Storage(name="TestLocation")
        location1_id = ltable.insert(**location1)

        location2 = Storage(name="TestLocation")
        location2_id = ltable.insert(**location2)

        self.id1 = location1_id
        self.id2 = location2_id

        self.resource = s3db.resource("gis_location")

    # -------------------------------------------------------------------------
    def testMerge(self):
        """ Test merge """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        success = self.resource.merge(self.id1, self.id2)
        assertTrue(success)
        location1, location2 = self.get_records()

        assertNotEqual(location1, None)
        assertNotEqual(location2, None)

        assertFalse(location1.deleted)
        assertTrue(location2.deleted)
        assertEqual(str(self.id1), str(location2.deleted_rb))

        assertEqual(location1.name, "TestLocation")
        assertEqual(location2.name, "TestLocation")

    # -------------------------------------------------------------------------
    def testMergeSimpleReference(self):
        """ Test merge of a simple reference including super-entity """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        db = current.db
        s3db = current.s3db

        # Create an office referencing location 2
        otable = s3db.org_office
        office = Storage(name="Test Office",
                         location_id = self.id2)
        office_id = otable.insert(**office)
        office.update(id=office_id)
        s3db.update_super(otable, office)

        # Merge location 2 into 1
        success = self.resource.merge(self.id1, self.id2)
        assertTrue(success)

        # Check the location_id in office is now location 1
        office = db(otable._id == office.id).select(limitby=(0, 1)).first()
        assertNotEqual(office, None)
        assertEqual(office.location_id, self.id1)

        # Check the location_id in the org_site super record is also location 1
        stable = s3db.org_site
        site = db(stable.site_id == office.site_id).select(limitby=(0, 1)).first()
        assertNotEqual(site, None)
        assertEqual(site.location_id, self.id1)

    # -------------------------------------------------------------------------
    #def testMergeLocationHierarchy(self):
        #""" Test update of the location hierarchy when merging locations """
        #pass

    # -------------------------------------------------------------------------
    #def testMergeDeduplicateComponents(self):
        #""" Test merged components deduplication """
        ## Test by gis_location_tags
        #pass

    # -------------------------------------------------------------------------
    def get_records(self):

        table = self.resource.table
        query = (table._id.belongs(self.id1, self.id2))
        rows = current.db(query).select(limitby=(0, 2))
        row1 = row2 = None
        for row in rows:
            row_id = row[table._id]
            if row_id == self.id1:
                row1 = row
            elif row_id == self.id2:
                row2 = row
        return (row1, row2)

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

# =============================================================================
class MergeUniqueFieldTest(unittest.TestCase):
    """ Test merge of records with a unique field """

    tablename = "test_merge_unique"

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        current.db.define_table(cls.tablename,
                                Field("name", length=64, unique=True),
                                *s3_meta_fields())

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        try:
            current.db[cls.tablename].drop()
        except:
            pass

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

        db = current.db
        tablename = self.tablename
        table = db[tablename]

        self.id1 = table.insert(name="TestRecord1")
        self.id2 = table.insert(name="TestRecord2")

        if not self.id1 or not self.id2:
            raise RuntimeError("Could not create test records")

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

    # -------------------------------------------------------------------------
    def testMergeReplaceUnique(self):
        """ Test merge with replace of a unique-field """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        tablename = self.tablename

        resource = current.s3db.resource(tablename)
        success = resource.merge(self.id1, self.id2, replace = ["name"])

        assertTrue(success)

        db = current.db
        table = db[tablename]

        row1 = db(table.id == self.id1).select(table.name,
                                               table.deleted,
                                               table.deleted_rb,
                                               limitby=(0, 1),
                                               ).first()
        row2 = db(table.id == self.id2).select(table.name,
                                               table.deleted,
                                               table.deleted_rb,
                                               limitby=(0, 1),
                                               ).first()

        assertNotEqual(row1, None)
        assertNotEqual(row2, None)

        assertFalse(row1.deleted)
        assertTrue(row2.deleted)

        assertEqual(str(self.id1), str(row2.deleted_rb))

        assertEqual(row1.name, "TestRecord2")
        assertEqual(row2.name, "TestRecord1")

# =============================================================================
class MergeReferenceListsTest(unittest.TestCase):

    # -------------------------------------------------------------------------
    def setUp(self):

        tablename = self.tablename = "merge_list_reference"
        db = current.db
        db.define_table(tablename,
                        Field("facility_type_id",
                              "list:reference org_facility_type"),
                        *s3_meta_fields())

        xmlstr = """
<s3xml>
    <resource name="org_facility_type" uuid="TESTMERGEFACTYPE1">
        <data field="name">TestMergeFacilityType1</data>
    </resource>
    <resource name="org_facility_type" uuid="TESTMERGEFACTYPE2">
        <data field="name">TestMergeFacilityType2</data>
    </resource>
    <resource name="%(tablename)s" uuid="TESTMERGEFACILITY">
        <reference field="facility_type_id" resource="org_facility_type"
                   uuid="[&quot;TESTMERGEFACTYPE1&quot;, &quot;TESTMERGEFACTYPE2&quot;]"/>
    </resource>
</s3xml>""" % dict(tablename=tablename)

        current.auth.override = True
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource(tablename)
        resource.import_xml(xmltree)

    # -------------------------------------------------------------------------
    def testMergeListReference(self):

        assertEqual = self.assertEqual

        s3db = current.s3db

        resource = s3db.resource("org_facility_type",
                                 uid=["TESTMERGEFACTYPE1", "TESTMERGEFACTYPE2"])

        rows = resource.select(["id"], limit=2, as_rows=True)
        assertEqual(len(rows), 2)

        original = rows[0].id
        duplicate = rows[1].id
        resource.merge(original, duplicate)

        resource = s3db.resource(self.tablename,
                                 uid="TESTMERGEFACILITY")
        rows = resource.select(["id", "facility_type_id"],
                               limit=None, as_rows=True)
        assertEqual(len(rows), 1)
        assertEqual(rows[0].facility_type_id, [original])

    # -------------------------------------------------------------------------
    def tearDown(self):

        db = current.db
        db.rollback()
        try:
            db[self.tablename].drop()
        except:
            pass
        current.auth.override = False

# =============================================================================
class ResourceGetTests(unittest.TestCase):
    """ Test S3Resource.get """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        current.auth.override = True

        xmlstr = """
<s3xml>
    <resource name="org_organisation" uuid="GETTESTORG">
        <data field="name">GetTestOrg</data>
        <resource name="org_office" uuid="GETTESTOFFICE">
            <data field="name">GetTestOffice</data>
        </resource>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("org_organisation")
        resource.import_xml(xmltree)

    # -------------------------------------------------------------------------
    def setUp(self):

        otable = current.s3db.org_organisation
        row = current.db(otable.uuid == "GETTESTORG") \
                     .select(otable.id, limitby=(0, 1)).first()
        self.org_id = row.id

    # -------------------------------------------------------------------------
    def testGetError(self):
        """ get() without ID raises a KeyError """

        resource = current.s3db.resource("org_organisation",
                                         uid="GETTESTORG")
        self.assertRaises(KeyError, resource.get, None)

    # -------------------------------------------------------------------------
    def testGetMaster(self):
        """ get() with an ID returns the record, if accessible """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        resource = current.s3db.resource("org_organisation",
                                         uid="GETTESTORG")
        record = resource.get(self.org_id)
        assertNotEqual(record, None)

        assertTrue(isinstance(record, Row))
        assertEqual(record.id, self.org_id)
        assertEqual(record.uuid, "GETTESTORG")
        assertEqual(record.name, "GetTestOrg")

    # -------------------------------------------------------------------------
    def testGetMasterFail(self):
        """ get() with an ID raises a KeyError, if not accessible """

        resource = current.s3db.resource("org_organisation",
                                         uid="OTHERTESTORG")

        with self.assertRaises(KeyError):
            resource.get(self.org_id)

    # -------------------------------------------------------------------------
    def testGetComponent(self):
        """ get() with ID and component alias returns the components records """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        resource = current.s3db.resource("org_organisation",
                                         uid="GETTESTORG")
        records = resource.get(self.org_id, "office")
        assertNotEqual(records, None)

        assertTrue(len(records), 1)
        record = records[0]
        assertTrue(isinstance(record, Row))
        assertEqual(record.organisation_id, self.org_id)
        assertEqual(record.uuid, "GETTESTOFFICE")
        assertEqual(record.name, "GetTestOffice")

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        current.db.rollback()
        current.auth.override = False

# =============================================================================
class ResourceSelectTests(unittest.TestCase):
    """ Tests for S3Resource.select """

    test_data = (
        ("select0", "C"),
        ("select1", "A"),
        ("select2", "B"),
        ("select3", "A"),
        ("select4", "A"),
        ("select5", "C"),
        ("select6", "B"),
        ("select7", "A"),
        ("select8", "B"),
        ("select9", "A"),
    )

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db

        # Create a simple table
        s3db.define_table("select_master",
                          Field("name"),
                          Field("status"),
                          *s3_meta_fields())

        # Insert test records
        table = s3db.select_master
        for name, status in cls.test_data:
            table.insert(name=name, status=status)

        # Define a virtual field
        table.code = Field.Method("code", lambda row: row["select_master.status"])

        current.db.commit()

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        db = current.db

        # Drop the table
        db.select_master.drop()
        db.commit()

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False

    # -------------------------------------------------------------------------
    def testApplyExtraFilter(self):
        """ Test application of extra filters """

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual

        test_expression = "test filter expression"
        seen = []

        def test_filter(resource, ids, expression):
            """ Test filter method """

            # Check resource
            assertNotEqual(resource, None)
            assertEqual(resource.tablename, "select_master")

            # Verify that the resource has no extra filters while
            # extra filters are applied
            efilters = resource.rfilter.efilters
            assertEqual(efilters, [])

            # Check ids
            assertTrue(type(ids) is list)
            assertNotEqual(len(ids), 0)

            # Remember ids to verify that no unnecessary items are passed
            #print "called with %s" % str(ids)
            seen.extend(ids)

            # Verify correct expression is passed
            assertEqual(expression, test_expression)

            # Filter ids to verify that filter is effective
            result = [item for item in ids if item > 3 and item % 2 == 0]

            # Add a duplicate to verify that duplicates do not affect
            # match counting and do not appear in the subset
            if result:
                result.insert(0, result[-1])

            # Reverse result list to verify that original order is restored
            result.reverse()

            return result

        # Define resource, add test filter as extra filter
        resource = current.s3db.resource("select_master")
        resource.add_extra_filter(test_filter, test_expression)

        apply_extra_filters = resource.rfilter.apply_extra_filters

        # Fake set of record IDs
        test_set = [1, 2, 3, 4, 5, 6, 7, 8]

        # Test without limit
        seen = []
        subset = apply_extra_filters(test_set)
        assertEqual(subset, [4, 6, 8])
        assertEqual(seen, test_set)

        # Test with limit < len(test_set)
        seen = []
        subset = apply_extra_filters(test_set, limit=2)
        assertEqual(subset, [4, 6])
        assertEqual(seen, [1, 2, 3, 4, 5, 6])

        # Test with limit > len(test_set)
        seen = []
        subset = apply_extra_filters(test_set, limit=10)
        assertEqual(subset, [4, 6, 8])
        assertEqual(seen, test_set)

    # -------------------------------------------------------------------------
    def testSelectAll(self):
        """ Test selecting all records """

        s3db = current.s3db

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Number of expected matches
        numitems = len(self.test_data)

        # Define resource
        resource = s3db.resource("select_master")

        # Simple select
        data = resource.select(["name", "status"])
        assertEqual(len(data.rows), numitems)

        # Select with counting
        data = resource.select(["name", "status"], count=True)
        assertEqual(len(data.rows), numitems)
        assertEqual(data.numrows, numitems)

        # Select with getids
        data = resource.select(["id", "name", "status"], getids=True)
        rows = data.rows
        ids = data.ids
        assertEqual(len(rows), numitems)
        assertEqual(len(ids), numitems)
        assertTrue(all(row["select_master.id"] in ids for row in rows))

    # -------------------------------------------------------------------------
    def testSelectFilter(self):
        """ Test selection with filter """

        s3db = current.s3db

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Number of expected matches
        numitems = len([item for item in self.test_data if item[1] == "A"])

        # Define resource
        query = FS("status") == "A"
        resource = s3db.resource("select_master", filter=query)

        # Simple select
        data = resource.select(["name", "status"])
        rows = data.rows
        # - Rows properly filtered
        assertEqual(len(rows), numitems)
        assertTrue(all(row["select_master.status"] == "A" for row in rows))

        # Select with counting
        data = resource.select(["name", "status"], count=True)
        # - Rows correctly counted
        assertEqual(len(data.rows), data.numrows)

        # Select with getids
        data = resource.select(["id", "name", "status"], getids=True)
        rows = data.rows
        ids = data.ids
        # - ids complete
        assertEqual(len(rows), len(ids))
        # - ...and in same order as the rows
        for index, row in enumerate(rows):
            assertEqual(row["select_master.id"], ids[index])

    # -------------------------------------------------------------------------
    def testSelectVirtualFilter(self):
        """ Test selection with virtual filter """

        s3db = current.s3db

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Number of expected matches
        numitems = len([item for item in self.test_data if item[1] == "A"])

        # Define resource
        query = FS("code") == "A"
        resource = s3db.resource("select_master", filter=query)

        # Simple select
        data = resource.select(["name", "status"])
        rows = data.rows
        # - Rows properly filtered
        assertEqual(len(rows), numitems)
        assertTrue(all(row["select_master.status"] == "A" for row in rows))

        # Select with counting
        data = resource.select(["name", "status"], count=True)
        # - Rows correctly counted
        assertEqual(len(data.rows), data.numrows)

        # Select with getids
        data = resource.select(["id", "name", "status"], getids=True)
        rows = data.rows
        ids = data.ids
        # - ids complete
        assertEqual(len(rows), len(ids))
        # - ...and in same order as the rows
        for index, row in enumerate(rows):
            assertEqual(row["select_master.id"], ids[index])

    # -------------------------------------------------------------------------
    def testSelectExtraFilter(self):
        """ Test selection with extra filter """

        s3db = current.s3db

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        test_expression = "A"

        # Number of expected matches
        numitems = len([item for item in self.test_data if item[1] == test_expression])

        def test_filter(resource, ids, expression):
            """ Test filter function """

            assertEqual(expression, test_expression)

            table = resource.table
            query = (table.id.belongs(ids)) & \
                    (table.status == expression)
            rows = db(query).select(table.id)

            return [row.id for row in rows]

        # Define resource
        resource = s3db.resource("select_master",
                                 extra_filters = [(test_filter, test_expression)],
                                 )

        # Simple select
        data = resource.select(["name", "status"])
        rows = data.rows
        # - Rows properly filtered
        assertEqual(len(rows), numitems)
        assertTrue(all(row["select_master.status"] == test_expression for row in rows))

        # Select with counting
        data = resource.select(["name", "status"], count=True)
        # - Rows correctly counted
        assertEqual(len(data.rows), data.numrows)

        # Select with getids
        data = resource.select(["id", "name", "status"], getids=True)
        rows = data.rows
        ids = data.ids
        # - ids complete
        assertEqual(len(rows), len(ids))
        # - ...and in same order as the rows
        for index, row in enumerate(rows):
            assertEqual(row["select_master.id"], ids[index])

    # -------------------------------------------------------------------------
    def testSelectSubset(self):
        """ Test selection of unfiltered subset (pagination) """

        s3db = current.s3db

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Define subset
        subset = self.test_data
        numitems = len(subset)
        names = [item[0] for item in subset]

        # Define resource
        resource = s3db.resource("select_master")

        # Page limits
        start = 2
        limit = 2
        subset_names = names[start:start+limit]

        # Simple select
        data = resource.select(["name", "status"],
                               start = start,
                               limit = limit,
                               orderby = "select_master.name",
                               )
        # - returns only rows in page
        rows = data.rows
        assertEqual(len(rows), min(numitems - start, limit))
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))

        # Page with only start
        start = 2
        limit = None
        subset_names = names[start:]

        # Simple select
        data = resource.select(["name", "status"],
                               start = start,
                               limit = limit,
                               orderby = "select_master.name",
                               )
        # - returns only rows in page
        rows = data.rows
        assertEqual(len(rows), numitems - start)
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))

        # Page with only limit
        start = None
        limit = 3
        subset_names = names[:limit]

        # Simple select
        data = resource.select(["name", "status"],
                               start = start,
                               limit = limit,
                               orderby = "select_master.name",
                               )
        # - returns only rows in page
        rows = data.rows
        assertEqual(len(rows), limit)
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))

        # Page limits
        start = 4
        limit = 5
        subset_names = names[start:start+limit]

        # Select with counting
        data = resource.select(["name", "status"],
                               start = start,
                               limit = limit,
                               count = True,
                               orderby = "select_master.name",
                               )
        # - returns only rows in page
        rows = data.rows
        assertEqual(len(rows), min(numitems - start, limit))
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))
        # - counts all matching records, however
        assertEqual(data.numrows, numitems)

        # Select with getids
        data = resource.select(["id", "name", "status"],
                               start = start,
                               limit = limit,
                               getids = True,
                               orderby = "select_master.name",
                               )
        # - returns only rows in page
        rows = data.rows
        assertEqual(len(rows), min(numitems - start, limit))
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))
        # - returns all matching record ids, however
        assertEqual(len(data.ids), numitems)

        # Page beyond subset
        start = numitems
        limit = 10

        # Select with counting
        data = resource.select(["name", "status"],
                               start = start,
                               limit = limit,
                               count = True,
                               orderby = "select_master.name",
                               )
        # - gives no rows
        assertEqual(len(data.rows), 0)
        # - counts all matching records, however
        assertEqual(data.numrows, numitems)

        # Select with getids
        data = resource.select(["id", "name", "status"],
                               start = start,
                               limit = limit,
                               getids = True,
                               orderby = "select_master.name",
                               )
        # - gives no rows
        assertEqual(len(data.rows), 0)
        # - returns all matching record ids, however
        assertEqual(len(data.ids), numitems)

    # -------------------------------------------------------------------------
    def testSelectSubsetFilter(self):
        """ Test selection of filtered subset (pagination) """

        s3db = current.s3db

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Define subset
        subset = [item for item in self.test_data if item[1] == "A"]
        numitems = len(subset)
        names = [item[0] for item in subset]

        # Define resource
        query = (FS("status") == "A")
        resource = s3db.resource("select_master",
                                 filter = query,
                                 )

        # Page limits
        start = 2
        limit = 2
        subset_names = names[start:start+limit]

        # Simple select
        data = resource.select(["name", "status"],
                               start = start,
                               limit = limit,
                               orderby = "select_master.name",
                               )
        # - returns only rows in page
        rows = data.rows
        assertEqual(len(rows), min(numitems - start, limit))
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))

        # Page limits
        start = 4
        limit = 5
        subset_names = names[start:start+limit]

        # Select with counting
        data = resource.select(["name", "status"],
                               start = start,
                               limit = limit,
                               count = True,
                               orderby = "select_master.name",
                               )
        # - returns only rows in page
        rows = data.rows
        assertEqual(len(rows), min(numitems - start, limit))
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))
        # - counts all matching records, however
        assertEqual(data.numrows, numitems)

        # Select with getids
        data = resource.select(["id", "name", "status"],
                               start = start,
                               limit = limit,
                               getids = True,
                               orderby = "select_master.name",
                               )
        # - returns only rows in page
        rows = data.rows
        assertEqual(len(rows), min(numitems - start, limit))
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))
        # - returns all matching record ids, however
        assertEqual(len(data.ids), numitems)

        # Page beyond subset
        start = numitems
        limit = 10

        # Select with counting
        data = resource.select(["name", "status"],
                               start = start,
                               limit = limit,
                               count = True,
                               orderby = "select_master.name",
                               )
        # - gives no rows
        assertEqual(len(data.rows), 0)
        # - counts all matching records, however
        assertEqual(data.numrows, numitems)

        # Select with getids
        data = resource.select(["id", "name", "status"],
                               start = start,
                               limit = limit,
                               getids = True,
                               orderby = "select_master.name",
                               )
        # - gives no rows
        assertEqual(len(data.rows), 0)
        # - returns all matching record ids, however
        assertEqual(len(data.ids), numitems)

    # -------------------------------------------------------------------------
    def testSelectSubsetVirtualFilter(self):
        """ Test selection of subset (pagination) with virtual filter """

        s3db = current.s3db

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        # Define subset
        subset = [item for item in self.test_data if item[1] == "A"]
        numitems = len(subset)
        names = [item[0] for item in subset]

        # Define resource
        query = (FS("code") == "A")
        resource = s3db.resource("select_master",
                                 filter = query,
                                 )

        # Page limits
        start = 2
        limit = 2
        subset_names = names[start:start+limit]

        # Simple select
        data = resource.select(["name", "status"],
                               start = start,
                               limit = limit,
                               orderby = "select_master.name",
                               )
        # - returns only rows in the page
        rows = data.rows
        assertEqual(len(rows), min(numitems - start, limit))
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))

        # Page limits:
        start = 1
        limit = 3
        subset_names = names[start:start+limit]

        # Select with counting
        data = resource.select(["name", "status"],
                               start = start,
                               limit = limit,
                               count = True,
                               orderby = "select_master.name",
                               )
        # - returns only rows in the page
        rows = data.rows
        assertEqual(len(rows), min(numitems - start, limit))
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))
        # - counts all matching records, however
        assertEqual(data.numrows, numitems)

        # Select with getids
        data = resource.select(["id", "name", "status"],
                               start = start,
                               limit = limit,
                               getids = True,
                               orderby = "select_master.name",
                               )
        # - returns only rows in the page
        assertEqual(len(data.rows), min(numitems - start, limit))
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))
        # - returns all matching record ids, however
        assertEqual(len(data.ids), numitems)

    # -------------------------------------------------------------------------
    def testSelectSubsetExtraFilter(self):
        """ Test selection of subset (pagination) with extra filter """

        s3db = current.s3db

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        test_expression = "A"

        def test_filter(resource, ids, expression):
            """ Test filter function """

            assertEqual(expression, test_expression)

            table = resource.table
            query = (table.id.belongs(ids)) & \
                    (table.status == expression)
            rows = db(query).select(table.id)

            return [row.id for row in rows]

        # Define subset
        subset = [item for item in self.test_data if item[1] == test_expression]
        numitems = len(subset)
        names = [item[0] for item in subset]

        # Define resource
        resource = s3db.resource("select_master",
                                 extra_filters = [(test_filter, test_expression)],
                                 )

        # Page limits
        start = 2
        limit = 2
        subset_names = names[start:start+limit]

        # Simple select
        data = resource.select(["name", "status"],
                               start = start,
                               limit = limit,
                               orderby = "select_master.name",
                               )
        # - returns only rows in the page
        rows = data.rows
        assertEqual(len(rows), min(numitems - start, limit))
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))

        # Page limits:
        start = 1
        limit = 3
        subset_names = names[start:start+limit]

        # Select with counting
        data = resource.select(["name", "status"],
                               start = start,
                               limit = limit,
                               count = True,
                               orderby = "select_master.name",
                               )
        # - returns only rows in the page
        rows = data.rows
        assertEqual(len(rows), min(numitems - start, limit))
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))
        # - counts all matching records, however
        assertEqual(data.numrows, numitems)

        # Select with getids
        data = resource.select(["id", "name", "status"],
                               start = start,
                               limit = limit,
                               getids = True,
                               orderby = "select_master.name",
                               )
        # - returns only rows in the page
        assertEqual(len(data.rows), min(numitems - start, limit))
        assertTrue(all(row["select_master.name"] in subset_names for row in rows))
        # - returns all matching record ids, however
        assertEqual(len(data.ids), numitems)

# =============================================================================
class ResourceLazyVirtualFieldsSupportTests(unittest.TestCase):
    """ Test support for lazy virtual fields """

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True
        s3db = current.s3db
        table = s3db.pr_person
        if not hasattr(table, "name"):
            table.name = Field.Method("name", self.lazy_name)
            s3db.configure("pr_person",
                           extra_fields=["first_name", "last_name"])
        self.record_id = None

    # -------------------------------------------------------------------------
    def lazy_name(self, row):
        """ Dummy lazy field """

        self.record_id = row.pr_person.id
        return "%s %s" % (row.pr_person.first_name,
                          row.pr_person.last_name)

    # -------------------------------------------------------------------------
    def testLazyVirtualFieldsResolve(self):
        """
            Test whether field selectors for lazy virtual fields
            can be properly resolved
        """

        assertEqual = self.assertEqual

        resource = current.s3db.resource("pr_person")

        from s3 import S3ResourceField
        rfield = S3ResourceField(resource, "name")
        assertEqual(rfield.field, None)
        assertEqual(rfield.ftype, "virtual")

    # -------------------------------------------------------------------------
    def testLazyVirtualFieldsExtract(self):
        """
            Test whether values for lazy virtual fields can be extracted
        """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        self.record_id = None

        resource = current.s3db.resource("pr_person")

        # Select raw rows
        rows = resource.select(["name", "first_name", "last_name"],
                               limit=1, as_rows=True)
        row = rows[0]
        assertTrue("name" in row)
        assertTrue(callable(row["name"]))
        # lazy field not called
        assertEqual(self.record_id, None)

        name = "%s %s" % (row.first_name, row.last_name)

        # Select with value extraction
        data = resource.select(["name"], limit=1)
        item = data["rows"][0]
        assertTrue("pr_person.name" in item)
        # lazy field called
        assertEqual(self.record_id, row.id)

        assertEqual(item["pr_person.name"], name)

    # -------------------------------------------------------------------------
    def testLazyVirtualFieldsFilter(self):
        """
            Test whether S3ResourceQueries work with lazy virtual fields
        """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        resource = current.s3db.resource("pr_person")

        from s3 import FS
        query = FS("name").like("Admin%")
        resource.add_filter(query)

        data = resource.select(["name", "first_name", "last_name"],
                               limit=None)
        rows = data["rows"]
        for item in rows:
            assertTrue("pr_person.name" in item)
            assertEqual(item["pr_person.name"][:5], "Admin")
            assertEqual(item["pr_person.name"], "%s %s" % (
                        item["pr_person.first_name"],
                        item["pr_person.last_name"]))

    # -------------------------------------------------------------------------
    def testLazyVirtualFieldsURLFilter(self):
        """
            Test whether URL filters work with lazy virtual fields
        """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        vars = Storage({"person.name__like": "Admin*"})
        resource = current.s3db.resource("pr_person", vars=vars)

        data = resource.select(["name", "first_name", "last_name"],
                               limit=None)
        rows = data["rows"]
        for item in rows:
            assertTrue("pr_person.name" in item)
            assertEqual(item["pr_person.name"][:5], "Admin")
            assertEqual(item["pr_person.name"], "%s %s" % (
                        item["pr_person.first_name"],
                        item["pr_person.last_name"]))

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False

# =============================================================================
class ResourceFilteredComponentTests(unittest.TestCase):
    """ Test components from the same table but different aliases """

    @unittest.skipIf(not current.deployment_settings.has_module("org"), "org module disabled")
    def testAttachFilteredComponent(self):
        """ Test instantiation of filtered component """

        assertEqual = self.assertEqual

        s3db = current.s3db

        # Define a filtered component with single value
        s3db.add_components("org_organisation",
                            org_office = {"name": "test",
                                          "joinby": "organisation_id",
                                          "filterby": {
                                              "office_type_id": 5,
                                              },
                                         },
                           )

        # Define the resource
        resource = s3db.resource("org_organisation", components=["test"])

        # Check the component
        component = resource.components["test"]
        table = component.table
        assertEqual(component.tablename, "org_office")
        assertEqual(component._alias, "org_test_office")
        assertEqual(table._tablename, "org_test_office")
        assertEqual(str(component.filter),
                    str((table.office_type_id == 5)))

        # Define a filtered component with single value in list
        s3db.add_components("org_organisation",
                            org_office = {"name": "test",
                                          "joinby": "organisation_id",
                                          "filterby": {
                                              "office_type_id": [5],
                                              },
                                         },
                           )
        resource = s3db.resource("org_organisation", components=["test"])
        component = resource.components["test"]
        table = component.table
        assertEqual(str(component.filter),
                    str((table.office_type_id == 5)))

        # Define a filtered component with value tuple
        s3db.add_components("org_organisation",
                            org_office = {"name": "test",
                                          "joinby": "organisation_id",
                                          "filterby": {
                                              "office_type_id": (4, 5),
                                              },
                                         },
                           )
        resource = s3db.resource("org_organisation", components=["test"])
        component = resource.components["test"]
        table = component.table
        assertEqual(str(component.filter),
                    str((table.office_type_id.belongs(4,5))))

        # Define a filtered component with empty filter value list
        s3db.add_components("org_organisation",
                            org_office = {"name": "test",
                                          "joinby": "organisation_id",
                                          "filterby": {
                                              "office_type_id": [],
                                              },
                                         },
                           )
        resource = s3db.resource("org_organisation", components=["test"])
        component = resource.components["test"]
        assertEqual(component.filter, None)

        # Remove the component hook
        del current.model.components["org_organisation"]["test"]

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("org"), "org module disabled")
    def testResolveSelectorWithFilteredComponent(self):
        """ Test resolution of field selectors for filtered components """

        assertEqual = self.assertEqual

        s3db = current.s3db

        # Define a filtered component
        s3db.add_components("org_organisation",
                            org_office = {"name": "test",
                                          "joinby": "organisation_id",
                                          "filterby": {
                                              "office_type_id": 5,
                                              },
                                         },
                           )

        # Define the resource
        resource = s3db.resource("org_organisation")

        # Make sure an S3ResourceField of the component is using the
        # correct table alias (critical for data extraction from Rows)
        rfield = S3ResourceField(resource, "test.name")
        assertEqual(rfield.tname, "org_test_office")
        assertEqual(rfield.colname, "org_test_office.name")

        # Remove the component hook
        del current.model.components["org_organisation"]["test"]

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("org"), "org module disabled")
    def testURLQueryWithFilteredComponent(self):
        """ Test resolution of URL queries for fields in filtered components """

        assertEqual = self.assertEqual

        auth = current.auth
        s3db = current.s3db

        org_organisation = s3db.org_organisation
        org_test_office = s3db.org_office.with_alias("org_test_office")

        # Define a filtered component
        s3db.add_components("org_organisation",
                            org_office = {"name": "test",
                                          "joinby": "organisation_id",
                                          "filterby": {
                                              "office_type_id": 5,
                                              },
                                         },
                           )

        # Define the resource
        resource = s3db.resource("org_organisation")

        # Translate a URL query into a DAL query, check that
        # the correct table alias is used
        query = S3URLQuery.parse(resource, {"test.name__like": "xyz*"})
        assertEqual(str(query.test[0].query(resource)),
                    str(org_test_office.name.lower().like("xyz%")))

        # Add the query to the resource
        auth.override = True
        resource.add_filter(query.test[0])
        rfilter = resource.rfilter

        # Check that the aliased table is properly joined
        expected = org_test_office.on(
                        ((org_test_office.organisation_id == org_organisation.id) &
                         (org_test_office.deleted != True)) &
                        (org_test_office.office_type_id == 5))
        assertEqual(str(rfilter.get_joins(left=True)[0]), str(expected))

        # ...and the effective query of the master contains the filter
        # and is using the correct alias
        expected = (((org_organisation.deleted != True) &
                     (org_organisation.id > 0)) &
                    (org_test_office.name.lower().like("xyz%")))
        assertEqual(str(resource.get_query()), str(expected))

        # Check the query of the component
        component = resource.components["test"]
        expected = (((org_test_office.deleted != True) &
                    (org_test_office.id > 0)) &
                    (((org_organisation.deleted != True) &
                    (org_organisation.id > 0)) &
                    (org_test_office.name.lower().like("xyz%"))))
        assertEqual(str(component.get_query()), str(expected))

        rfilter = component.rfilter
        expected = org_organisation.on(
                        (org_test_office.organisation_id == org_organisation.id) &
                        (org_test_office.office_type_id == 5))
        assertEqual(str(rfilter.get_joins(left=True)[0]), str(expected))

        # Remove the component hook
        del current.model.components["org_organisation"]["test"]

        auth.override = False

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("org"), "org module disabled")
    def testDataTableFilterWithFilteredComponent(self):
        """
            Test translation of datatable filter/sorting for fields in
            filtered components
        """

        assertEqual = self.assertEqual

        s3db = current.s3db

        org_organisation = s3db.org_organisation
        org_office_type = s3db.org_office_type
        org_test_office = s3db.org_office.with_alias("org_test_office")

        s3db.add_components("org_organisation",
                            org_office = {"name": "test",
                                          "joinby": "organisation_id",
                                          "filterby": {
                                              "office_type_id": 5,
                                              },
                                         },
                           )

        resource = s3db.resource("org_organisation")
        fields = ["id", "name", "test.name", "test.office_type_id$name"]
        vars = Storage({"bSortable_0": "false", # action column
                        "bSortable_1": "true",
                        "bSortable_2": "true",
                        "bSortable_3": "true",
                        "sSortDir_0": "asc",
                        "iSortCol_0": "2",
                        "sSortDir_1": "desc",
                        "iSortCol_1": "3",
                        "iColumns": "4",
                        "iSortingCols": "2",
                        "sSearch": "test"})
        searchq, orderby, left = resource.datatable_filter(fields, vars)
        expected = (((org_organisation.name.lower().like("%test%")) |
                     (org_test_office.name.lower().like("%test%"))) |
                    (org_office_type.name.lower().like("%test%")))
        assertEqual(str(searchq), str(expected))
        assertEqual(orderby,
                    "org_test_office.name asc, org_office_type.name desc")

        # Remove the component hook
        del current.model.components["org_organisation"]["test"]

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("org"), "org module disabled")
    def testSelectWithFilteredComponent(self):
        """ Test S3Resource.select with fields in a filtered component """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        s3db = current.s3db
        auth = current.auth

        xmlstr = """
<s3xml>
    <resource name="org_organisation" uuid="FCTESTORG">
        <data field="name">FilteredComponentsTestOrg</data>
        <resource name="org_office" uuid="FCTESTOFFICE">
            <data field="name">FilteredComponentsTestOffice</data>
            <reference field="office_type_id" resource="org_office_type">
                <resource name="org_office_type" uuid="FCTESTTYPE">
                    <data field="name">FilteredComponentsTestType</data>
                </resource>
            </reference>
        </resource>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        auth.override = True

        resource = s3db.resource("org_organisation")
        resource.import_xml(xmltree)

        resource = s3db.resource("org_office_type", uid="FCTESTTYPE")
        row = resource.select(["id"], limit=1, as_rows=True)[0]
        type_id = row.id

        s3db.add_components("org_organisation",
                            org_office = {"name": "test",
                                          "joinby": "organisation_id",
                                          "filterby": {
                                              "office_type_id": type_id,
                                              },
                                         },
                           )

        resource = current.s3db.resource("org_organisation", uid="FCTESTORG")
        fields = ["id", "name", "test.name", "test.office_type_id$name"]
        data = resource.select(fields, limit=None)
        result = data["rows"]

        assertEqual(len(result), 1)
        result = result[0]
        assertTrue("org_organisation.name" in result)
        assertEqual(result["org_organisation.name"], "FilteredComponentsTestOrg")
        assertTrue("org_test_office.name" in result)
        assertEqual(result["org_test_office.name"], "FilteredComponentsTestOffice")
        assertTrue("org_office_type.name" in result)
        assertEqual(result["org_office_type.name"], "FilteredComponentsTestType")

        # Remove the component hook
        del current.model.components["org_organisation"]["test"]

        current.db.rollback()
        auth.override = False

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("hrm"), "hrm module disabled")
    def testGetJoinLinkTableComponentAlias(self):
        """ Join for a link-table component with alias """

        assertEqual = self.assertEqual

        s3db = current.s3db

        hrm_human_resource = s3db.hrm_human_resource
        pr_person = s3db.pr_person
        pr_email_contact = s3db.pr_contact.with_alias("pr_email_contact")
        pr_phone_contact = s3db.pr_contact.with_alias("pr_phone_contact")

        resource = current.s3db.resource("hrm_human_resource")

        component = resource.components["email"]
        join = component.get_join()
        expected = (((hrm_human_resource.person_id == pr_person.id) &
                   (pr_person.deleted != True)) &
                   ((pr_person.pe_id == pr_email_contact.pe_id) &
                   (pr_email_contact.contact_method == "EMAIL")))
        assertEqual(str(join), str(expected))

        component = resource.components["phone"]
        join = component.get_join()
        expected = (((hrm_human_resource.person_id == pr_person.id) &
                   (pr_person.deleted != True)) &
                   ((pr_person.pe_id == pr_phone_contact.pe_id) &
                   (pr_phone_contact.contact_method == "SMS")))
        assertEqual(str(join), str(expected))

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("hrm"), "hrm module disabled")
    def testGetLeftJoinLinkTableComponentAlias(self):
        """ Left Join for a link-table component with alias """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        s3db = current.s3db
        resource = s3db.resource("hrm_human_resource")

        pr_person = s3db.pr_person
        hrm_human_resource = s3db.hrm_human_resource
        pr_contact = s3db.pr_contact

        component = resource.components["email"]
        pr_email_contact = pr_contact.with_alias("pr_email_contact")
        ljoin = component.get_left_join()

        assertTrue(isinstance(ljoin, list))
        assertEqual(len(ljoin), 2)
        assertEqual(str(ljoin[0]), str(pr_person.on(
                        (hrm_human_resource.person_id == pr_person.id) &
                        (pr_person.deleted != True))))

        assertEqual(str(ljoin[1]), str(pr_email_contact.on(
                        (pr_person.pe_id == pr_email_contact.pe_id) &
                        (pr_email_contact.contact_method == "EMAIL"))))

        component = resource.components["phone"]
        pr_phone_contact = pr_contact.with_alias("pr_phone_contact")
        ljoin = component.get_left_join()

        assertTrue(isinstance(ljoin, list))
        assertEqual(len(ljoin), 2)
        assertEqual(str(ljoin[0]), str(pr_person.on(
                        (hrm_human_resource.person_id == pr_person.id) &
                        (pr_person.deleted != True))))

        assertEqual(str(ljoin[1]), str(pr_phone_contact.on(
                        (pr_person.pe_id == pr_phone_contact.pe_id) &
                        (pr_phone_contact.contact_method == "SMS"))))

    # -------------------------------------------------------------------------
    # Disabled - @todo: must create test records (otherwise component can be
    # empty regardless) - and check the actual office_type_ids (can not assume 4/5)
    @unittest.skip("disabled until fixed")
    @unittest.skipIf(not current.deployment_settings.has_module("org"), "org module disabled")
    def testExportTreeWithComponentAlias(self):
        """ Test export of a resource that has components from the same table but different aliases """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        current.auth.override = True
        s3db = current.s3db
        s3db.add_components("org_organisation",
                            org_office = ({"name": "fieldoffice",
                                           "joinby": "organisation_id",
                                           "filterby": {
                                               "office_type_id": 5,
                                               },
                                          },
                                          {"name": "hq",
                                           "joinby": "organisation_id",
                                           "filterby": {
                                               "office_type_id": 4,
                                               },
                                          },
                                         ),
                           )

        resource = s3db.resource("org_organisation")
        assertEqual(str(resource.components.fieldoffice.filter), \
                    "(org_fieldoffice_office.office_type_id = 5)")
        assertEqual(str(resource.components.hq.filter), \
                    "(org_hq_office.office_type_id = 4)")

        tree = resource.export_tree(mcomponents=["fieldoffice","hq"])
        assertTrue(resource.components.fieldoffice._length > 0)
        assertTrue(resource.components.hq._length > 0)
        assertTrue(resource.components.office._length is None)

        tree = resource.export_tree(mcomponents=["office","fieldoffice","hq"])
        assertTrue(resource.components.office._length > 0)
        assertTrue(resource.components.fieldoffice._length is None)
        assertTrue(resource.components.hq._length is None)

# =============================================================================
class ResourceDeleteTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db

        # Create super-entity
        s3db.super_entity("del_super",
                          "del_super_id",
                          {"del_master": "DEL Master"})

        # Define master table
        s3db.define_table("del_master",
                          s3db.super_link("del_super_id",
                                          "del_super"),
                          *s3_meta_fields())

        current.db.commit()

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        # Drop test tables
        db = current.db
        db.del_master.drop()
        db.del_super.drop()

        current.db.commit()

    # -------------------------------------------------------------------------
    def setUp(self):

        s3db = current.s3db

        # Make master instance type of super
        s3db.configure("del_master", super_entity = "del_super")

        # Create the master record and link it to the SE
        master_table = s3db.del_master
        master_id = master_table.insert()
        s3db.update_super(master_table, {"id": master_id})
        self.master_id = master_id

        self.master_deleted = 0
        self.super_deleted = 0
        self.component_deleted = 0

        # Configure callbacks
        s3db.configure("del_master",
                       ondelete = self.master_ondelete)

        s3db.configure("del_super",
                       ondelete = self.super_ondelete)

        s3db.configure("del_component",
                       ondelete = self.component_ondelete)

        current.db.commit()
        current.auth.override = True

    # -------------------------------------------------------------------------
    def tearDown(self):

        # Remove test records
        db = current.db
        db(db.del_master._id>0).delete()
        db(db.del_super._id>0).delete()
        db.commit()

        current.auth.override = False

    # -------------------------------------------------------------------------
    def master_ondelete(self, row):
        """ Dummy ondelete-callback """

        self.master_deleted = row.id
        return

    # -------------------------------------------------------------------------
    def super_ondelete(self, row):
        """ Dummy ondelete-callback """

        self.super_deleted = row.id
        return

    # -------------------------------------------------------------------------
    def component_ondelete(self, row):
        """ Dummy ondelete-callback """

        self.component_deleted = row.id
        return

    # -------------------------------------------------------------------------
    def testArchiveSimple(self):
        """ Test archiving of a record """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        s3db = current.s3db
        s3db.clear_config("del_master", "super_entity")

        master_id = self.master_id

        # Delete the master record
        resource = s3db.resource("del_master", id=master_id)
        success = resource.delete()
        assertEqual(success, 1)
        assertEqual(resource.error, None)

        # Master record is deleted
        table = s3db.del_master
        record = table[master_id]
        assertTrue(record.deleted)

        # Check callbacks
        assertEqual(self.master_deleted, master_id)
        assertEqual(self.super_deleted, 0)
        assertEqual(self.component_deleted, 0)

    # -------------------------------------------------------------------------
    def testArchiveCascade(self):
        """
            Test archiving of a record which is referenced by
            other records
        """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        s3db = current.s3db
        s3db.clear_config("del_master", "super_entity")

        master_id = self.master_id

        # Define component table
        s3db.define_table("del_component",
                          Field("del_master_id",
                                s3db.del_master,
                                ondelete="CASCADE"),
                          *s3_meta_fields())
        component = s3db["del_component"]
        s3db.add_components("del_master",
                            del_component="del_master_id")

        try:
            # Create a component record
            component_id = component.insert(del_master_id=master_id)
            component_record = component[component_id]
            assertNotEqual(component_record, None)
            current.db.commit()

            # Delete the master record
            resource = s3db.resource("del_master", id=master_id)
            success = resource.delete()
            assertEqual(success, 1)
            assertEqual(resource.error, None)

            # Master record is deleted
            table = s3db.del_master
            record = table[master_id]
            assertTrue(record.deleted)

            # Component record is deleted and unlinked
            component_record = component[component_id]
            assertTrue(component_record.deleted)
            assertEqual(component_record.del_master_id, None)

            # Check callbacks
            assertEqual(self.master_deleted, master_id)
            assertEqual(self.super_deleted, 0)
            assertEqual(self.component_deleted, component_id)

        finally:
            component.drop()
            del current.model.components["del_master"]["component"]

    # -------------------------------------------------------------------------
    def testArchiveSetNull(self):
        """
            Test archiving of a record which is referenced by
            other records
        """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        s3db = current.s3db
        s3db.clear_config("del_master", "super_entity")

        master_id = self.master_id

        # Define component table
        s3db.define_table("del_component",
                          Field("del_master_id",
                                s3db.del_master,
                                ondelete="SET NULL"),
                          *s3_meta_fields())
        component = s3db["del_component"]
        s3db.add_components("del_master",
                            del_component="del_master_id")

        try:
            # Create a component record
            component_id = component.insert(del_master_id=master_id)
            component_record = component[component_id]
            assertNotEqual(component_record, None)
            current.db.commit()

            # Delete the master record
            resource = s3db.resource("del_master", id=master_id)
            success = resource.delete()
            assertEqual(success, 1)
            assertEqual(resource.error, None)

            # Master record is deleted
            table = s3db.del_master
            record = table[master_id]
            assertTrue(record.deleted)

            # Component record is not deleted, but unlinked
            component_record = component[component_id]
            assertFalse(component_record.deleted)
            assertEqual(component_record.del_master_id, None)

            # Check callbacks
            assertEqual(self.master_deleted, master_id)
            assertEqual(self.super_deleted, 0)
            assertEqual(self.component_deleted, 0)

        finally:
            component.drop()
            del current.model.components["del_master"]["component"]

    # -------------------------------------------------------------------------
    def testArchiveRestrict(self):
        """
            Test archiving of a record which is referenced by
            other records
        """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        s3db = current.s3db
        s3db.clear_config("del_master", "super_entity")

        master_id = self.master_id

        # Define component table
        s3db.define_table("del_component",
                          Field("del_master_id",
                                s3db.del_master,
                                ondelete="RESTRICT"),
                          *s3_meta_fields())
        component = s3db["del_component"]
        s3db.add_components("del_master",
                            del_component="del_master_id")

        try:
            # Create a component record
            component_id = component.insert(del_master_id=master_id)
            component_record = component[component_id]
            assertNotEqual(component_record, None)
            current.db.commit()

            # Delete the master record
            resource = s3db.resource("del_master", id=master_id)
            success = resource.delete()
            assertEqual(success, 0)
            assertEqual(resource.error, current.ERROR.INTEGRITY_ERROR)

            # Master record is not deleted
            table = s3db.del_master
            record = table[master_id]
            assertFalse(record.deleted)

            # Component record is not deleted and still linked
            component_record = component[component_id]
            assertFalse(component_record.deleted)
            assertEqual(component_record.del_master_id, master_id)

            # Check callbacks
            assertEqual(self.master_deleted, 0)
            assertEqual(self.super_deleted, 0)
            assertEqual(self.component_deleted, 0)

        finally:
            component.drop()
            del current.model.components["del_master"]["component"]

    # -------------------------------------------------------------------------
    def testArchiveSuper(self):
        """
            Test archiving of a super-entity instance record
        """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        s3db = current.s3db

        master_id = self.master_id

        # Get the super_id
        table = s3db.del_master
        record = table[master_id]
        super_id = record["del_super_id"]

        # Delete the master record
        resource = s3db.resource("del_master", id=master_id)
        success = resource.delete()
        assertEqual(success, 1)
        assertEqual(resource.error, None)

        # Master record is deleted
        record = table[master_id]
        assertTrue(record.deleted)
        assertEqual(record.del_super_id, None)

        # Super-record is deleted
        stable = s3db.del_super
        srecord = stable[super_id]
        assertTrue(srecord.deleted)

        # Check callbacks
        assertEqual(self.master_deleted, master_id)
        assertEqual(self.super_deleted, super_id)
        assertEqual(self.component_deleted, 0)

    # -------------------------------------------------------------------------
    def testArchiveSuperCascade(self):
        """
            Test archiving of a super-entity instance record
            where the super-record is referenced by other records
            with CASCADE constraint
        """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        s3db = current.s3db

        master_id = self.master_id

        # Define component table
        s3db.define_table("del_component",
                          s3db.super_link("del_super_id",
                                          "del_super",
                                          ondelete="CASCADE"),
                          *s3_meta_fields())
        component = s3db["del_component"]
        s3db.add_components("del_super",
                            del_component="del_super_id")

        try:
            # Get the super_id
            table = s3db.del_master
            record = table[master_id]
            super_id = record["del_super_id"]

            # Create a component record
            component_id = component.insert(del_super_id=super_id)
            component_record = component[component_id]
            assertNotEqual(component_record, None)
            current.db.commit()

            # Delete the master record
            resource = s3db.resource("del_master", id=master_id)
            success = resource.delete()
            assertEqual(success, 1)
            assertEqual(resource.error, None)

            # Master record is deleted
            record = table[master_id]
            assertTrue(record.deleted)
            assertEqual(record.del_super_id, None)

            # Super-record is deleted
            stable = s3db.del_super
            srecord = stable[super_id]
            assertTrue(srecord.deleted)

            # Component record is deleted
            crecord = component[component_id]
            assertTrue(crecord.deleted)
            assertEqual(crecord.del_super_id, None)

            # Check callbacks
            assertEqual(self.master_deleted, master_id)
            assertEqual(self.super_deleted, super_id)
            assertEqual(self.component_deleted, component_id)

        finally:
            component.drop()
            del current.model.components["del_super"]["component"]

    # -------------------------------------------------------------------------
    def testArchiveSuperSetNull(self):
        """
            Test archiving of a super-entity instance record
            where the super-record is referenced by other records
            with SET NULL constraint
        """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        s3db = current.s3db

        master_id = self.master_id

        # Define component table
        s3db.define_table("del_component",
                          s3db.super_link("del_super_id",
                                          "del_super",
                                          ondelete="SET NULL"),
                          *s3_meta_fields())
        component = s3db["del_component"]
        s3db.add_components("del_super",
                            del_component="del_super_id")

        try:
            # Get the super_id
            table = s3db.del_master
            record = table[master_id]
            super_id = record["del_super_id"]

            # Create a component record
            component_id = component.insert(del_super_id=super_id)
            component_record = component[component_id]
            assertNotEqual(component_record, None)
            current.db.commit()

            # Delete the master record
            resource = s3db.resource("del_master", id=master_id)
            success = resource.delete()
            assertEqual(success, 1)
            assertEqual(resource.error, None)

            # Master record is deleted
            record = table[master_id]
            assertTrue(record.deleted)
            assertEqual(record.del_super_id, None)

            # Super-record is deleted
            stable = s3db.del_super
            srecord = stable[super_id]
            assertTrue(srecord.deleted)

            # Component record is not deleted, but unlinked
            crecord = component[component_id]
            assertFalse(crecord.deleted)
            assertEqual(crecord.del_super_id, None)

            # Check callbacks
            assertEqual(self.master_deleted, master_id)
            assertEqual(self.super_deleted, super_id)
            assertEqual(self.component_deleted, 0)

        finally:
            component.drop()
            del current.model.components["del_super"]["component"]

    # -------------------------------------------------------------------------
    def testArchiveSuperRestrict(self):
        """
            Test archiving of a super-entity instance record
            where the super-record is referenced by other records
            with RESTRICT constraint
        """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        s3db = current.s3db

        master_id = self.master_id

        # Define component table
        s3db.define_table("del_component",
                          s3db.super_link("del_super_id",
                                          "del_super",
                                          ondelete="RESTRICT"),
                          *s3_meta_fields())
        component = s3db["del_component"]
        s3db.add_components("del_super",
                            del_component="del_super_id")

        try:
            # Get the super_id
            table = s3db.del_master
            record = table[master_id]
            super_id = record["del_super_id"]

            # Create a component record
            component_id = component.insert(del_super_id=super_id)
            component_record = component[component_id]
            assertNotEqual(component_record, None)
            current.db.commit()

            # Delete the master record
            resource = s3db.resource("del_master", id=master_id)
            success = resource.delete()
            assertEqual(success, 0)
            assertEqual(resource.error, current.ERROR.INTEGRITY_ERROR)

            # Master record is not deleted
            record = table[master_id]
            assertFalse(record.deleted)
            assertEqual(record.del_super_id, super_id)

            # Super-record is not deleted
            stable = s3db.del_super
            srecord = stable[super_id]
            assertFalse(srecord.deleted)

            # Component record is not deleted and still unlinked
            crecord = component[component_id]
            assertFalse(crecord.deleted)
            assertEqual(crecord.del_super_id, super_id)

            # Check callbacks
            assertEqual(self.master_deleted, 0)
            assertEqual(self.super_deleted, 0)
            assertEqual(self.component_deleted, 0)

        finally:
            component.drop()
            del current.model.components["del_super"]["component"]

    # -------------------------------------------------------------------------
    def testArchiveWithJoinedExtraFields(self):
        """
            Test archiving if there are mandatory extra fields
            which require a join
        """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        s3db = current.s3db

        master_id = self.master_id

        # Define component table
        # @note: not really a component relationship here, but
        #        using component table for its foreign key in
        #        order to construct an extra_fields join
        s3db.define_table("del_component",
                          Field("del_master_id",
                                s3db.del_master,
                                ondelete="CASCADE"),
                          *s3_meta_fields())
        component = s3db["del_component"]

        # Define joined extra fields
        s3db.configure("del_component",
                       extra_fields = ["del_master_id$id"],
                       )

        try:
            # Create a component record
            component_id = component.insert(del_master_id=master_id)
            component_record = component[component_id]
            assertNotEqual(component_record, None)
            current.db.commit()

            # Delete the component record
            # => this crashes if delete doesn't catch joined Rows
            resource = s3db.resource("del_component", id=component_id)
            success = resource.delete()
            assertEqual(success, 1)
            assertEqual(resource.error, None)

            # Component record is deleted and unlinked
            component_record = component[component_id]
            assertTrue(component_record.deleted)
            assertEqual(component_record.del_master_id, None)

            # Check callbacks
            # => this fails if the callback doesn't receive
            #    the correct sub-Row (...instead of the joined Row)
            assertEqual(self.component_deleted, component_id)

        finally:
            component.drop()

    ## -------------------------------------------------------------------------
    #def testDeleteSimple(self):
        #""" Test hard deletion of a record """

        #raise NotImplementedError

    ## -------------------------------------------------------------------------
    #def testDeleteCascade(self):
        #"""
            #Test hard deletion of a record which is referenced by
            #other records
        #"""

        #raise NotImplementedError

    ## -------------------------------------------------------------------------
    #def testDeleteSuper(self):
        #""" Test hard deletion of a super-entity instance record """

        #raise NotImplementedError

    ## -------------------------------------------------------------------------
    #def testDeleteSuperCascade(self):
        #"""
            #Test hard deletion of a super-entity instance record
            #where the super-record is referenced by other records
        #"""

        #raise NotImplementedError

# =============================================================================
class LinkDeletionTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db

        # Define master table
        s3db.define_table("link_master",
                          *s3_meta_fields())

        # Define component table
        s3db.define_table("link_component",
                          *s3_meta_fields())

        # Define link table
        s3db.define_table("link_link",
                          Field("master_id", "reference link_master"),
                          Field("component_id", "reference link_component"),
                          *s3_meta_fields())

        # Define link table component
        s3db.add_components("link_master",
                            link_component = {"link": "link_link",
                                              "joinby": "master_id",
                                              "key": "component_id",
                                              "actuate": "hide"
                                              },
                            )

        current.db.commit()

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        # Drop test tables
        db = current.db
        db.link_link.drop()
        db.link_master.drop()
        db.link_component.drop()

        current.db.commit()

    # -------------------------------------------------------------------------
    def setUp(self):

        db = current.db

        # Create records
        table = db.link_master
        self.master = table.insert()

        table = db.link_component
        self.component1 = table.insert()
        self.component2 = table.insert()

        table = db.link_link
        self.link1 = table.insert(master_id = self.master,
                                  component_id = self.component1)
        self.link2 = table.insert(master_id = self.master,
                                  component_id = self.component2)

        db.commit()
        current.auth.override = True

    # -------------------------------------------------------------------------
    def tearDown(self):

        db = current.db

        # Delete all records
        db(db.link_link._id>0).delete()
        db(db.link_master._id>0).delete()
        db(db.link_component._id>0).delete()
        db.commit()

    # -------------------------------------------------------------------------
    def testLinkDeletion(self):
        """ Test deletion of link table entry """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual

        db = current.db
        resource = current.s3db.resource("link_master")

        # Filter for a particular component record
        query = FS("component.id") == self.component1
        resource.add_filter(query)

        link = resource.links["link"]

        # Test resolution of field selector
        rfield = link.resolve_selector("component.id")
        msg = "Link table could not resolve component field selector"
        assertNotEqual(rfield.field, None, msg=msg)
        assertEqual(rfield.colname, "link_component.id", msg=msg)

        # Delete the link
        result = link.delete()

        # Should delete exactly one link
        assertEqual(result, 1)

        # Should have deleted the link for component1, but not for component2
        table = db.link_link
        row = db((table.component_id == self.component1) & \
                 (table.deleted != True)).select(table.id,
                                                 limitby=(0, 1)).first()
        assertEqual(row, None, msg = "Link not deleted")

        row = db((table.component_id == self.component2) & \
                 (table.deleted != True)).select(table.id,
                                                 limitby=(0, 1)).first()
        assertNotEqual(row, None, msg = "Unrelated link deleted")

        # The component records should still be available
        table = db.link_component
        row = db((table.id == self.component1) & \
                 (table.deleted != True)).select(table.id,
                                                 limitby=(0, 1)).first()
        assertNotEqual(row, None,
                       msg = "Component record deleted instead of just unlinking it")

        row = db((table.id == self.component2) & \
                 (table.deleted != True)).select(table.id,
                                                 limitby=(0, 1)).first()
        assertNotEqual(row, None,
                       msg = "Unrelated component record deleted")

# =============================================================================
if __name__ == "__main__":

    run_suite(
        ComponentJoinConstructionTests,
        ComponentLeftJoinConstructionTests,

        ResourceLazyVirtualFieldsSupportTests,
        ResourceDataObjectAPITests,

        ResourceAxisFilterTests,
        ResourceDataTableFilterTests,
        ResourceGetTests,
        #ResourceInsertTest,
        ResourceSelectTests,
        #ResourceUpdateTests,
        ResourceDeleteTests,

        #ResourceApproveTests,
        #ResourceRejectTests,

        #ResourceMergeTests,
        MergeOrganisationsTests,
        MergePersonsTests,
        MergeLocationsTests,
        MergeUniqueFieldTest,
        MergeReferenceListsTest,

        ResourceExportTests,
        ResourceImportTests,
        ResourceFilteredComponentTests,
        LinkDeletionTests,
    )

# END ========================================================================
