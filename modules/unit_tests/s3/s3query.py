# -*- coding: utf-8 -*-
#
# S3Query Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3query.py
#
import unittest
import datetime
from lxml import etree
from gluon import *
from gluon.storage import Storage
from s3 import *

try:
    import pyparsing
except ImportError:
    PYPARSING = False
else:
    PYPARSING = True

# =============================================================================
class FieldSelectorResolutionTests(unittest.TestCase):
    """ Test field selector resolution """

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testResolveSelectorsWithoutComponents(self):
        """ Field selector resolution without components"""

        s3db = current.s3db

        resource = s3db.resource("project_project")
        selectors = ["id",
                     "name",
                     "organisation_id$name",
                     "task.description"]
        fields, joins, left, distinct = resource.resolve_selectors(selectors,
                                                                   skip_components=True)

        project_project = resource.table
        org_organisation = s3db.org_organisation

        expected = org_organisation.on(
                        project_project.organisation_id == org_organisation.id)

        self.assertEqual(len(fields), 3)
        self.assertEqual(fields[0].colname, "project_project.id")
        self.assertEqual(fields[1].colname, "project_project.name")
        self.assertEqual(fields[2].colname, "org_organisation.name")

        self.assertEqual(joins, {})

        self.assertTrue(isinstance(left, dict))
        self.assertEqual(left.keys(), ["org_organisation"])
        self.assertEqual(len(left["org_organisation"]), 1)
        self.assertEqual(str(left["org_organisation"][0]), str(expected))

        self.assertTrue(distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testResolveSelectorsWithComponents(self):
        """ Field selector resolution with components"""

        s3db = current.s3db

        resource = s3db.resource("project_project")
        selectors = ["id",
                     "name",
                     "organisation_id$name",
                     "task.description"]
        fields, joins, left, distinct = resource.resolve_selectors(selectors)

        project_project = resource.table
        org_organisation = s3db.org_organisation
        project_task_project = s3db.project_task_project
        project_task = s3db.project_task

        expected = org_organisation.on(
                        project_project.organisation_id == org_organisation.id)

        expected_l = project_task_project.on(
                        (project_task_project.project_id == project_project.id) &
                        (project_task_project.deleted != True))

        expected_r = project_task.on(
                        project_task_project.task_id == project_task.id)

        self.assertEqual(len(fields), 4)
        self.assertEqual(fields[0].colname, "project_project.id")
        self.assertEqual(fields[1].colname, "project_project.name")
        self.assertEqual(fields[2].colname, "org_organisation.name")
        self.assertEqual(fields[3].colname, "project_task.description")

        self.assertEqual(joins, {})

        self.assertTrue(isinstance(left, dict))
        self.assertEqual(left.keys(), [ "org_organisation", "project_task"])
        self.assertEqual(len(left["org_organisation"]), 1)
        self.assertEqual(str(left["org_organisation"][0]), str(expected))
        self.assertEqual(len(left["project_task"]), 2)
        self.assertEqual(str(left["project_task"][0]), str(expected_l))
        self.assertEqual(str(left["project_task"][1]), str(expected_r))

        self.assertTrue(distinct)

# =============================================================================
class ResourceFilterJoinTests(unittest.TestCase):
    """ Test query construction from S3ResourceQueries """

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

    # -------------------------------------------------------------------------
    def testGetQueryJoinsInnerField(self):
        """ Inner field queries don't contain joins """

        resource = current.s3db.resource("pr_person")
        q = FS("first_name") == "test"

        # Test joins
        joins, distinct = q._joins(resource)
        self.assertEqual(joins, {})
        self.assertFalse(distinct)

        # Test left joins
        joins, distinct = q._joins(resource, left=True)
        self.assertEqual(joins, {})
        self.assertFalse(distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetQueryJoinsReferencedTableField(self):
        """ Referenced table field queries use left joins + distinct """

        s3db = current.s3db

        resource = s3db.resource("project_project")
        q = FS("organisation_id$name") == "test"

        # Test joins
        joins, distinct = q._joins(resource)
        self.assertEqual(joins, {})
        self.assertTrue(distinct)

        # Test left joins
        project_project = resource.table
        org_organisation = s3db.org_organisation
        expected = org_organisation.on(
                        project_project.organisation_id == org_organisation.id)

        joins, distinct = q._joins(resource, left=True)
        self.assertTrue(isinstance(joins, dict))
        self.assertEqual(joins.keys(), ["org_organisation"])
        self.assertTrue(isinstance(joins["org_organisation"], list))
        self.assertEqual(len(joins["org_organisation"]), 1)
        self.assertEqual(str(joins["org_organisation"][0]), str(expected))
        self.assertTrue(distinct)

    # -------------------------------------------------------------------------
    def testGetQueryJoinsComponentField(self):
        """ Component field queries use left joins + distinct """

        s3db = current.s3db

        resource = s3db.resource("pr_person")
        q = FS("identity.value") == "test"

        # Test joins
        joins, distinct = q._joins(resource)
        self.assertEqual(joins, {})
        self.assertTrue(distinct)

        pr_person = resource.table
        pr_identity = s3db.pr_identity
        expected = pr_identity.on(
                        (pr_identity.person_id == pr_person.id) &
                        (pr_identity.deleted != True))

        # Test left joins
        joins, distinct = q._joins(resource, left=True)
        self.assertEqual(joins.keys(), ["pr_identity"])
        self.assertTrue(isinstance(joins["pr_identity"], list))
        self.assertEqual(str(joins["pr_identity"][0]), str(expected))
        self.assertTrue(distinct)

    # -------------------------------------------------------------------------
    def testGetQueryJoinsSuperComponentField(self):
        """ Super component field queries use left joins + distinct """

        s3db = current.s3db

        resource = s3db.resource("pr_person")
        q = FS("contact.value") == "test"

        # Test joins
        joins, distinct = q._joins(resource)
        self.assertEqual(joins, {})
        self.assertTrue(distinct)

        # Test left joins
        pr_person = resource.table
        pr_contact = s3db.pr_contact
        expected = pr_contact.on(
                        (pr_person.pe_id == pr_contact.pe_id) &
                        (pr_contact.deleted != True))

        joins, distinct = q._joins(resource, left=True)
        self.assertEqual(joins.keys(), ["pr_contact"])
        self.assertTrue(isinstance(joins["pr_contact"], list))
        self.assertEqual(str(joins["pr_contact"][0]), str(expected))
        self.assertTrue(distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetQueryJoinsLinkedComponentField(self):
        """
            Link table component field queries use chained left
            joins + distinct
        """

        s3db = current.s3db

        resource = s3db.resource("project_project")
        q = FS("task.description") == "test"

        # Test joins
        joins, distinct = q._joins(resource)
        self.assertEqual(joins, {})
        self.assertTrue(distinct)

        # Test left joins
        project_project = resource.table
        project_task_project = s3db.project_task_project
        project_task = s3db.project_task

        expected_l = project_task_project.on(
                        (project_task_project.project_id == project_project.id) &
                        (project_task_project.deleted != True))

        expected_r = project_task.on(
                        project_task_project.task_id == project_task.id)

        joins, distinct = q._joins(resource, left=True)
        self.assertEqual(joins.keys(), ["project_task"])
        self.assertTrue(isinstance(joins["project_task"], list))
        self.assertEqual(len(joins["project_task"]), 2)
        self.assertEqual(str(joins["project_task"][0]), str(expected_l))
        self.assertEqual(str(joins["project_task"][1]), str(expected_r))
        self.assertTrue(distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetQueryJoinsCombination(self):
        """ Queries for fields in multiple tables use multiple joins """

        s3db = current.s3db

        resource = s3db.resource("project_project")
        q = (FS("organisation_id$name") == "test") & \
            (FS("task.description") == "test")

        # Test joins
        joins, distinct = q._joins(resource)
        self.assertEqual(joins.keys(), [])

        # Test left joins
        project_project = resource.table
        project_task_project = s3db.project_task_project
        project_task = s3db.project_task
        org_organisation = s3db.org_organisation

        expected = org_organisation.on(
                        project_project.organisation_id == org_organisation.id)

        expected_l = project_task_project.on(
                        (project_task_project.project_id == project_project.id) &
                        (project_task_project.deleted != True))

        expected_r = project_task.on(
                        project_task_project.task_id == project_task.id)

        joins, distinct = q._joins(resource, left=True)
        self.assertEqual(joins.keys(), ["org_organisation", "project_task"])

        self.assertTrue(isinstance(joins["org_organisation"], list))
        self.assertEqual(len(joins["org_organisation"]), 1)
        self.assertEqual(str(joins["org_organisation"][0]), str(expected))
        self.assertTrue(isinstance(joins["project_task"], list))
        self.assertEqual(len(joins["project_task"]), 2)
        self.assertEqual(str(joins["project_task"][0]), str(expected_l))
        self.assertEqual(str(joins["project_task"][1]), str(expected_r))
        self.assertTrue(distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetQueryMixedQueryType(self):
        """ Test combinations of web2py Queries with S3ResourceQueries """

        s3db = current.s3db

        resource = s3db.resource("project_project")
        q = (FS("organisation_id$name") == "test") & \
            (resource.table.name == "test")

        # Test joins
        joins, distinct = q._joins(resource)
        self.assertEqual(joins.keys(), [])

        # Test left joins
        project_project = resource.table
        project_task_project = s3db.project_task_project
        project_task = s3db.project_task
        org_organisation = s3db.org_organisation

        expected = org_organisation.on(
                        project_project.organisation_id == org_organisation.id)

        joins, distinct = q._joins(resource, left=True)
        self.assertEqual(joins.keys(), ["org_organisation"])

        self.assertTrue(isinstance(joins["org_organisation"], list))
        self.assertEqual(len(joins["org_organisation"]), 1)
        self.assertEqual(str(joins["org_organisation"][0]), str(expected))
        self.assertTrue(distinct)

        # Test split and query
        qq, qf = q.split(resource)
        self.assertEqual(qf, None)
        query = qq.query(resource)
        expected = ((org_organisation.name == "test") & \
                    (project_project.name == "test"))
        self.assertEqual(str(query), str(expected))

        # Test get_query
        resource.add_filter(q)
        query = resource.get_query()
        expected = (((project_project.deleted != True) & \
                     (project_project.id > 0)) & \
                    ((org_organisation.name == "test") & \
                     (project_project.name == "test")))
        self.assertEqual(str(query), str(expected))

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetQueryMixedQueryTypeVirtual(self):
        """ Test combinations of web2py Queries with virtual field filter """

        s3db = current.s3db

        resource = s3db.resource("project_project")
        q = (FS("virtualfield") == "test") & \
            (resource.table.name == "test")

        project_project = resource.table

        # Test joins
        joins, distinct = q._joins(resource)
        self.assertEqual(joins, {})

        # Test left joins
        joins, distinct = q._joins(resource, left=True)
        self.assertEqual(joins, {})

        # Test split and query
        qq, qf = q.split(resource)
        expected = (project_project.name == "test")
        self.assertEqual(str(qq), str(expected))
        self.assertTrue(isinstance(qf, S3ResourceQuery))

        # Test get_query
        resource.add_filter(q)
        query = resource.get_query()
        expected =  (((project_project.deleted != True) & \
                    (project_project.id > 0)) & \
                    (project_project.name == "test"))
        self.assertEqual(str(query), str(expected))

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetFilterLeftJoins(self):
        """ Check list of left joins in resource filters """

        s3db = current.s3db

        q = (FS("organisation_id$name") == "test") & \
            (FS("task.description") == "test")
        resource = s3db.resource("project_project", filter=q)

        # Test left joins
        project_project = resource.table
        project_task_project = s3db.project_task_project
        project_task = s3db.project_task
        org_organisation = s3db.org_organisation

        expected1 = org_organisation.on(
                        project_project.organisation_id == org_organisation.id)

        expected2 = project_task_project.on(
                        (project_task_project.project_id == project_project.id) &
                        (project_task_project.deleted != True))

        expected3 = project_task.on(project_task_project.task_id == project_task.id)

        joins = resource.rfilter.get_joins(left=True)
        self.assertTrue(isinstance(joins, list))
        self.assertEqual(len(joins), 3)

        self.assertEqual(str(joins[0]), str(expected1))
        self.assertEqual(str(joins[1]), str(expected2))
        self.assertEqual(str(joins[2]), str(expected3))

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False

# =============================================================================
class ResourceFilterQueryTests(unittest.TestCase):
    """ Test resource filter query construction """

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("org"), "org module disabled")
    def testTextOperatorWithNonTextField(self):
        """ Test query construction for non-text fields with text operator """

        s3db = current.s3db

        q = (FS("id").lower().like("%123%"))
        resource = s3db.resource("org_organisation", filter=q)
        query = resource.rfilter.get_query()
        org_organisation = resource.table
        expected = (((org_organisation.deleted != True) &
                     (org_organisation.id > 0)) &
                    (org_organisation.id.like("%123%")))
        self.assertEqual(str(query), str(expected))

        q = (FS("id").lower().like("%12%3%"))
        resource = s3db.resource("org_organisation", filter=q)
        query = resource.rfilter.get_query()
        org_organisation = resource.table
        expected = (((org_organisation.deleted != True) &
                     (org_organisation.id > 0)) &
                    (org_organisation.id.like("%12%3%")))
        self.assertEqual(str(query), str(expected))

        q = (FS("id").lower().like("%abc%"))
        resource = s3db.resource("org_organisation", filter=q)
        query = resource.rfilter.get_query()
        org_organisation = resource.table
        expected = (((org_organisation.deleted != True) &
                     (org_organisation.id > 0)) &
                    (org_organisation.id.like("%abc%")))
        self.assertEqual(str(query), str(expected))

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testMasterFilterConstruction(self):
        """ Test master resource filter construction """

        s3db = current.s3db

        project_project = s3db.project_project
        org_organisation = s3db.org_organisation
        project_task_project = s3db.project_task_project
        project_task = s3db.project_task

        q = (FS("organisation_id$name") == "test") & \
            (FS("task.description") == "test")
        resource = current.s3db.resource("project_project", filter=q)

        rfilter = resource.rfilter
        self.assertNotEqual(rfilter, None)

        # Check master query
        expected = ((project_project.deleted != True) &
                    (project_project.id > 0))
        self.assertEqual(str(rfilter.mquery), str(expected))

        # Check effective query
        expected = (((project_project.deleted != True) &
                     (project_project.id > 0)) &
                     ((org_organisation.name == "test") &
                      (project_task.description == "test")))
        query = rfilter.get_query()
        self.assertEqual(str(query), str(expected))

        # Check joins
        join = rfilter.get_joins(left=False, as_list=False)
        self.assertEqual(join, {})

        # Check left joins
        expected = org_organisation.on(
                        project_project.organisation_id == org_organisation.id)

        expected_l = project_task_project.on(
                        (project_task_project.project_id == project_project.id) &
                        (project_task_project.deleted != True))

        expected_r = project_task.on(
                        project_task_project.task_id == project_task.id)

        left = rfilter.get_joins(left=True, as_list=False)
        self.assertEqual(left.keys(), ["org_organisation", "project_task"])
        self.assertTrue(isinstance(left["org_organisation"], list))
        self.assertEqual(len(left["org_organisation"]), 1)
        self.assertEqual(str(left["org_organisation"][0]), str(expected))
        self.assertTrue(isinstance(left["project_task"], list))
        self.assertEqual(len(left["project_task"]), 2)
        self.assertEqual(str(left["project_task"][0]), str(expected_l))
        self.assertEqual(str(left["project_task"][1]), str(expected_r))

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testCrossComponentFilterConstruction1(self):
        """ Test cross-component effect of master resource filter """

        s3db = current.s3db

        project_project = s3db.project_project
        org_organisation = s3db.org_organisation
        project_task_project = s3db.project_task_project
        project_task = s3db.project_task

        q1 = (FS("organisation_id$name") == "test")
        q2 = (FS("task.description") == "test")
        resource = s3db.resource("project_project", filter=q1)
        resource.add_filter(q2)

        component = resource.components["task"]
        component.build_query()
        rfilter = component.rfilter
        query = rfilter.get_query()

        expected = (((project_task.deleted != True) &
                   (project_task.id > 0)) &
                   (((project_project.deleted != True) &
                   (project_project.id > 0)) &
                   ((org_organisation.name == "test") &
                   (project_task.description == "test"))))

        self.assertEqual(query, expected)

        # No inner joins
        join = rfilter.get_joins(left=False, as_list=False)
        self.assertEqual(join, {})

        # Left joins for cross-component filters
        left = rfilter.get_joins(left=True, as_list=False)
        tablenames = left.keys()
        self.assertEqual(len(tablenames), 2)
        self.assertTrue("org_organisation" in tablenames)
        self.assertTrue("project_project" in tablenames)

        self.assertTrue(isinstance(left["org_organisation"], list))
        self.assertEqual(len(left["org_organisation"]), 1)
        expected = org_organisation.on(
                        project_project.organisation_id == org_organisation.id)
        self.assertEqual(str(left["org_organisation"][0]), str(expected))

        self.assertTrue(isinstance(left["project_project"], list))
        self.assertEqual(len(left["project_project"]), 2)
        expected = project_task_project.on(project_task_project.task_id == project_task.id)
        self.assertEqual(str(left["project_project"][0]), str(expected))
        expected = project_project.on((project_task_project.project_id == project_project.id) &
                                      (project_task_project.deleted != True))
        self.assertEqual(str(left["project_project"][1]), str(expected))

        # Try to select rows
        rows = component.select(None, limit=1, as_rows=True)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("hrm"), "hrm module disabled")
    def testCrossComponentFilterConstruction2(self):
        """ Test cross-component effect of master resource filter """

        s3db = current.s3db

        pr_identity = s3db.pr_identity
        pr_person = s3db.pr_person
        org_organisation = s3db.org_organisation
        hrm_human_resource = s3db.hrm_human_resource

        q1 = (FS("human_resource.organisation_id$name") == "test")
        q2 = (FS("identity.value") == "test")
        resource = s3db.resource("pr_person", filter=q1)

        resource.add_filter(q2)

        component = resource.components["identity"]
        component.build_query()
        rfilter = component.rfilter
        query = rfilter.get_query()

        expected = (((pr_identity.deleted != True) &
                   (pr_identity.id > 0)) &
                   (((pr_person.deleted != True) &
                   (pr_person.id > 0)) &
                   ((org_organisation.name == "test") &
                   (pr_identity.value == "test"))))

        self.assertEqual(query, expected)

        # No inner joins
        join = rfilter.get_joins(left=False, as_list=False)
        self.assertEqual(join, {})

        # Left joins for cross-component filters
        expected_h = hrm_human_resource.on(
                        (hrm_human_resource.person_id == pr_person.id) &
                        (hrm_human_resource.deleted != True))
        expected_o = org_organisation.on(
                        hrm_human_resource.organisation_id == org_organisation.id)
        expected_p = pr_person.on(pr_identity.person_id == pr_person.id)

        left = rfilter.get_joins(left=True, as_list=False)
        tablenames = left.keys()
        self.assertEqual(len(tablenames), 3)
        self.assertTrue("hrm_human_resource" in tablenames)
        self.assertTrue("org_organisation" in tablenames)
        self.assertTrue("pr_person" in tablenames)

        self.assertTrue(isinstance(left["hrm_human_resource"], list))
        self.assertEqual(len(left["hrm_human_resource"]), 1)
        self.assertEqual(str(left["hrm_human_resource"][0]), str(expected_h))
        self.assertTrue(isinstance(left["org_organisation"], list))
        self.assertEqual(len(left["org_organisation"]), 1)
        self.assertEqual(str(left["org_organisation"][0]), str(expected_o))
        self.assertEqual(len(left["pr_person"]), 1)
        self.assertEqual(str(left["pr_person"][0]), str(expected_p))

        # Try to select rows
        rows = component.select(None, limit=1, as_rows=True)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testSimpleComponentFilterConstruction1(self):
        """ Test simple component filter construction (check query in filter) """

        s3db = current.s3db

        project_project = s3db.project_project
        project_activity = s3db.project_activity

        resource = s3db.resource("project_project", id=1)

        component = resource.components["activity"]
        component.build_query()
        rfilter = component.rfilter
        query = rfilter.get_query()

        # This will fail in 1st run as there is no ADMIN role yet

        expected = (((project_activity.deleted != True) &
                     (project_activity.id > 0)) &
                    (((project_project.deleted != True) &
                      (project_project.id > 0)) &
                     (project_project.id == 1)))

        self.assertEqual(str(query), str(expected))

        join = rfilter.get_joins(left=False, as_list=False)

        expected = project_project.on(
                    project_activity.project_id == project_project.id)

        tablenames = join.keys()
        self.assertEqual(len(tablenames), 1)
        self.assertTrue("project_project" in tablenames)


        self.assertTrue(isinstance(join["project_project"], list))
        self.assertEqual(len(join["project_project"]), 1)
        self.assertEqual(str(join["project_project"][0]), str(expected))

        left = rfilter.get_joins(left=True, as_list=False)
        self.assertEqual(left, {})

        # Try to select rows
        rows = component.select(None, limit=1, as_rows=True)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("hrm"), "hrm module disabled")
    def testSimpleComponentFilterConstruction2(self):
        """ Test simple component filter construction (check query in resource) """

        s3db = current.s3db

        pr_person = s3db.pr_person
        hrm_competency = s3db.hrm_competency

        resource = current.s3db.resource("pr_person",
                                         id=1,
                                         components=["competency"],
                                         filter=(FS("competency.id") == 1))

        component = resource.components["competency"]
        query = component.get_query()

        expected = (((hrm_competency.deleted != True) &
                     (hrm_competency.id > 0)) &
                    ((((pr_person.deleted != True) &
                       (pr_person.id > 0)) &
                      (pr_person.id == 1)) &
                    (hrm_competency.id == 1)))

        self.assertEqual(str(query), str(expected))

        rfilter = component.rfilter

        # No inner joins
        join = rfilter.get_joins(left=False, as_list=False)
        self.assertEqual(join, {})

        # Reverse left join for the filter of the master table
        left = rfilter.get_joins(left=True, as_list=False)
        tablenames = left.keys()
        self.assertEqual(len(tablenames), 1)
        self.assertTrue("pr_person" in tablenames)
        expected = pr_person.on(
                    (pr_person.id == hrm_competency.person_id))
        self.assertTrue(isinstance(left["pr_person"], list))
        self.assertEqual(len(left["pr_person"]), 1)
        self.assertEqual(str(left["pr_person"][0]), str(expected))


    # -------------------------------------------------------------------------
    def testAnyOf(self):
        """ Test filter construction with containment methods (contains vs anyof) """

        resource = current.s3db.resource("req_req_skill")
        req_req_skill = resource.table

        q = FS("skill_id").contains([1, 2])
        query = q.query(resource)
        expected = (req_req_skill.skill_id.contains([1, 2], all=True))
        self.assertEqual(str(query), str(expected))

        q = FS("skill_id").anyof([1, 2])
        query = q.query(resource)
        expected = (req_req_skill.skill_id.contains([1, 2], all=False))
        self.assertEqual(str(query), str(expected))

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False

# =============================================================================
class ResourceContextFilterTests(unittest.TestCase):
    """ Test global context filter """

    def setUp(self):

        # Two organisations with offices and human resources,
        # one person record linked to both organisation contexts
        xmlstr = """
<s3xml>
    <resource name="org_organisation" uuid="CONTEXTORG1">
        <data field="name">ContextFilterTestOrg1</data>
        <resource name="org_office" uuid="CONTEXT1OFFICE1">
            <data field="name">Context1Office1</data>
        </resource>
        <resource name="org_office" uuid="CONTEXT1OFFICE2">
            <data field="name">Context1Office2</data>
        </resource>
        <resource name="hrm_human_resource" uuid="CONTEXT1HR1">
            <reference field="person_id" resource="pr_person">
                <resource name="pr_person" uuid="CONTEXT1PERSON">
                    <data field="first_name">Context1</data>
                    <data field="last_name">Person</data>
                </resource>
            </reference>
        </resource>
        <resource name="hrm_human_resource" uuid="CONTEXT1HR2">
            <reference field="person_id" resource="pr_person">
                <resource name="pr_person" uuid="CONTEXT12PERSON">
                    <data field="first_name">Context12</data>
                    <data field="last_name">Person</data>
                </resource>
            </reference>
        </resource>
    </resource>
    <resource name="org_organisation" uuid="CONTEXTORG2">
        <data field="name">ContextFilterTestOrg2</data>
        <resource name="org_office" uuid="CONTEXT2OFFICE1">
            <data field="name">Context2Office1</data>
        </resource>
        <resource name="hrm_human_resource" uuid="CONTEXT2HR1">
            <reference field="person_id" resource="pr_person">
                <resource name="pr_person" uuid="CONTEXT2PERSON">
                    <data field="first_name">Context2</data>
                    <data field="last_name">Person</data>
                </resource>
            </reference>
        </resource>
        <resource name="hrm_human_resource" uuid="CONTEXT2HR2">
            <reference field="person_id" resource="pr_person" uuid="CONTEXT12PERSON"/>
        </resource>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        current.auth.override = True
        resource = current.s3db.resource("org_organisation")
        resource.import_xml(xmltree)

    # -------------------------------------------------------------------------
    def testContextFilter(self):
        """ Test global context filter """

        s3db = current.s3db

        # Configure contexts
        s3db.configure("org_office",
                       context = {"organisation":
                                  "organisation_id"})
        s3db.configure("pr_person",
                       context = {"organisation":
                                  "human_resource.organisation_id"})

        # Without global context filter
        s3db.context = None

        resource = s3db.resource("org_office",
                                 uid=["CONTEXT1OFFICE1",
                                      "CONTEXT1OFFICE2",
                                      "CONTEXT2OFFICE1"],
                                 context=True)
        data = resource.select(["name"], limit=None)
        items = data["rows"]
        self.assertEqual(len(items), 3)
        names = [item.values()[0] for item in items]
        self.assertTrue("Context1Office1" in names)
        self.assertTrue("Context1Office2" in names)
        self.assertTrue("Context2Office1" in names)

        resource = s3db.resource("pr_person",
                                 uid=["CONTEXT1PERSON",
                                      "CONTEXT2PERSON",
                                      "CONTEXT12PERSON"],
                                 context=True)
        data = resource.select(["first_name"], limit=None)
        items = data["rows"]
        self.assertEqual(len(items), 3)
        names = [item.values()[0] for item in items]
        self.assertTrue("Context1" in names)
        self.assertTrue("Context2" in names)
        self.assertTrue("Context12" in names)

        # Global context filter 1
        s3db.context = FS("(organisation)$uuid").belongs(["CONTEXTORG1"])

        resource = s3db.resource("org_office",
                                 uid=["CONTEXT1OFFICE1",
                                      "CONTEXT1OFFICE2",
                                      "CONTEXT2OFFICE1"],
                                 context=True)
        data = resource.select(["name"], limit=None)
        items = data["rows"]
        self.assertEqual(len(items), 2)
        names = [item.values()[0] for item in items]
        self.assertTrue("Context1Office1" in names)
        self.assertTrue("Context1Office2" in names)
        self.assertFalse("Context2Office1" in names)

        resource = s3db.resource("pr_person",
                                 uid=["CONTEXT1PERSON",
                                      "CONTEXT2PERSON",
                                      "CONTEXT12PERSON"],
                                 context=True)
        data = resource.select(["first_name"], limit=None)
        items = data["rows"]
        self.assertEqual(len(items), 2)
        names = [item.values()[0] for item in items]
        self.assertTrue("Context1" in names)
        self.assertFalse("Context2" in names)
        self.assertTrue("Context12" in names)

        # Global context filter 2
        s3db.context = FS("(organisation)$uuid").belongs(["CONTEXTORG2"])

        resource = s3db.resource("org_office",
                                 uid=["CONTEXT1OFFICE1",
                                      "CONTEXT1OFFICE2",
                                      "CONTEXT2OFFICE1"],
                                 context=True)
        data = resource.select(["name"], limit=None)
        items = data["rows"]
        self.assertEqual(len(items), 1)
        names = [item.values()[0] for item in items]
        self.assertFalse("Context1Office1" in names)
        self.assertFalse("Context1Office2" in names)
        self.assertTrue("Context2Office1" in names)

        resource = s3db.resource("pr_person",
                                 uid=["CONTEXT1PERSON",
                                      "CONTEXT2PERSON",
                                      "CONTEXT12PERSON"],
                                 context=True)
        data = resource.select(["first_name"], limit=None)
        items = data["rows"]
        self.assertEqual(len(items), 2)
        names = [item.values()[0] for item in items]
        self.assertFalse("Context1" in names)
        self.assertTrue("Context2" in names)
        self.assertTrue("Context12" in names)

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.s3db.context = None
        current.db.rollback()
        current.auth.override = False

# =============================================================================
class URLQuerySerializerTests(unittest.TestCase):
    """ Test URL serialization of resource queries """

    # -------------------------------------------------------------------------
    def testSerializeURLQuerySimpleString(self):
        """ Simple string comparison serialization """

        q = FS("person.first_name") == "Test"

        u = q.serialize_url()
        k = "person.first_name"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test")

    # -------------------------------------------------------------------------
    def testSerializeURLQueryWildcardString(self):
        """ Wildcard string comparison serialization """

        q = FS("person.first_name").lower().like("Test%")

        u = q.serialize_url()
        k = "person.first_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*")

    # -------------------------------------------------------------------------
    def testSerializeURLQueryMultiSelectorMatch(self):
        """ Wildcard string comparison serialization, multiple selectors """

        q = (FS("person.first_name").lower().like("Test%")) | \
            (FS("person.last_name").lower().like("Test%"))

        u = q.serialize_url()
        k = "person.first_name|person.last_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*")

    # -------------------------------------------------------------------------
    def testSerializeURLQueryMultiSelectorValueMismatch(self):
        """ Wildcard string comparison serialization, multiple selectors, value mismatch """

        q = (FS("person.first_name").lower().like("Test%")) | \
            (FS("person.last_name").lower().like("Other%"))

        u = q.serialize_url()
        k = "person.first_name|person.last_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertFalse(k in u)

    # -------------------------------------------------------------------------
    def testSerializeURLQueryMultiSelectorOperatorMismatch(self):
        """ Wildcard string comparison serialization, multiple selectors, operator mismatch """

        q = (FS("person.first_name").lower().like("Test%")) | \
            (~(FS("person.last_name").lower().like("Test%")))

        u = q.serialize_url()
        k = "person.first_name|person.last_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertFalse(k in u)

    # -------------------------------------------------------------------------
    def testSerializeURLQueryMultiSelectorMatchNegated(self):
        """ Wildcard string comparison serialization, multiple selectors, negation """

        q = (~(FS("person.first_name").lower().like("Test%"))) | \
            (~(FS("person.last_name").lower().like("Test%")))

        u = q.serialize_url()
        k = "person.first_name|person.last_name__like!"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*")

    # -------------------------------------------------------------------------
    def testSerializeURLQueryAlternativeValues(self):
        """ Wildcard string comparison serialization, alternative values, OR """

        q = (FS("person.first_name").lower().like("Test%")) | \
            (FS("person.first_name").lower().like("Other%"))

        u = q.serialize_url()
        k = "person.first_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*,Other*")

    # -------------------------------------------------------------------------
    def testSerializeURLQueryAlternativeValuesSingleOperator(self):
        """ Wildcard string comparison serialization, alternative values, single operator """

        q = FS("first_name").like(["Test%", "Other%"])

        resource = current.s3db.resource("pr_person")
        u = q.serialize_url(resource=resource)
        # Field selector does not use a prefix, but master resource
        # is known, so should be using ~ wildcard here
        k = "~.first_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*,Other*")

    # -------------------------------------------------------------------------
    def testSerializeURLQueryListContainmentOperator(self):
        """ Wildcard string comparison serialization, alternative values, containment operator """

        q = FS("person.first_name").belongs(["Test", "Other"])

        u = q.serialize_url()
        k = "person.first_name__belongs"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test,Other")

# =============================================================================
class URLFilterSerializerTests(unittest.TestCase):
    """ Test URL serialization of resource filter """

    # -------------------------------------------------------------------------
    def testSerializeURLFilterEcho(self):
        """ Check that parse->serialize echoes the original URL filter """

        url_query = {"project.organisation_id$name__like": "*test*",
                     "task.description__like!": "*test*"}

        resource = current.s3db.resource("project_project", vars=url_query)

        rfilter = resource.rfilter
        url_vars = rfilter.serialize_url()
        self.assertEqual(len(url_vars), len(url_query))
        for k in url_query:
            self.assertTrue(k in url_vars)
            self.assertEqual(url_vars[k], url_query[k])

    # -------------------------------------------------------------------------
    def testSerializeURLFilter(self):
        """ Check serialization of a back-end-constructed resource filter """

        resource = current.s3db.resource("pr_person")

        q = FS("first_name").like(["Test%", "Other%"])
        resource.add_filter(q)

        rfilter = resource.rfilter
        u = rfilter.serialize_url()

        # Field selector does not use a prefix, but master resource
        # is known (from rfilter), so should be using ~ wildcard here
        k = "~.first_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*,Other*")

# =============================================================================
class ResourceFieldTests(unittest.TestCase):
    """ Test field selector resolution with S3ResourceField """

    # -------------------------------------------------------------------------
    def testResolveContextSimple(self):

        s3db = current.s3db

        org_office = s3db.org_office
        org_organisation = s3db.org_organisation

        resource = s3db.resource("org_office")
        resource.configure(context = {"organisation": "organisation_id"})

        selector = "(organisation)$name"

        f = S3ResourceField(resource, selector)

        # Check field
        self.assertEqual(f.selector, selector)
        self.assertEqual(str(f.field), "org_organisation.name")
        self.assertEqual(f.tname, "org_organisation")
        self.assertEqual(f.fname, "name")
        self.assertEqual(f.colname, "org_organisation.name")

        tname = f.tname

        # Check join
        join = f.join
        self.assertTrue(isinstance(join, dict))
        self.assertTrue(tname in join)
        expected = (org_office.organisation_id == org_organisation.id)
        self.assertEqual(str(join[tname]), str(expected))

        # Check left join
        left = f.left
        self.assertTrue(isinstance(left, dict))
        self.assertTrue(tname in left)
        self.assertTrue(isinstance(left[tname], list))

        expected = org_organisation.on(org_office.organisation_id == org_organisation.id)
        self.assertEqual(len(f.left[tname]), 1)
        self.assertEqual(str(f.left[tname][0]), str(expected))

        # Check distinct
        self.assertTrue(f.distinct)

    # -------------------------------------------------------------------------
    def testResolveContextComplex(self):

        s3db = current.s3db

        hrm_human_resource = s3db.hrm_human_resource
        org_organisation = s3db.org_organisation

        resource = current.s3db.resource("pr_person")
        resource.configure(context = {"organisation": "person_id:hrm_human_resource.organisation_id"})

        selector = "(organisation)$name"

        f = S3ResourceField(resource, selector)

        # Check field
        self.assertEqual(f.selector, selector)
        self.assertEqual(str(f.field), "org_organisation.name")
        self.assertEqual(f.tname, "org_organisation")
        self.assertEqual(f.fname, "name")
        self.assertEqual(f.colname, "org_organisation.name")

        tname = f.tname

        # Check join
        join = f.join
        self.assertTrue(isinstance(join, dict))
        self.assertTrue(tname in join)
        expected = (hrm_human_resource.organisation_id == org_organisation.id)
        self.assertEqual(str(join[tname]), str(expected))

        # Check left join
        left = f.left
        self.assertTrue(isinstance(left, dict))
        self.assertTrue(tname in left)
        self.assertTrue(isinstance(left[tname], list))

        expected = org_organisation.on(hrm_human_resource.organisation_id == org_organisation.id)
        self.assertEqual(len(f.left[tname]), 1)
        self.assertEqual(str(f.left[tname][0]), str(expected))

        # Check distinct
        self.assertTrue(f.distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testResolveSelectorInnerField(self):
        """ Resolution of a selector for a field in master table """

        resource = current.s3db.resource("project_project")
        selector = "name"

        f = S3ResourceField(resource, selector)

        # Check field
        self.assertEqual(f.selector, selector)
        self.assertEqual(str(f.field), "project_project.name")
        self.assertEqual(str(f.tname), "project_project")
        self.assertEqual(str(f.fname), "name")
        self.assertEqual(str(f.colname), "project_project.name")

        # Check join (no join)
        self.assertEqual(f.join, Storage())
        self.assertEqual(f.left, Storage())

        # Check distinct (no join - no distinct)
        self.assertFalse(f.distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("org"), "org module disabled")
    def testResolveMasterWildcard(self):
        """ Resolution of a selector with a master wildcard """

        resource = current.s3db.resource("org_organisation")
        selector = "~.name"

        f = S3ResourceField(resource, selector)
        self.assertNotEqual(f, None)

        # Check field
        self.assertEqual(f.selector, selector)
        self.assertEqual(str(f.field), "org_organisation.name")
        self.assertEqual(str(f.tname), "org_organisation")
        self.assertEqual(str(f.fname), "name")
        self.assertEqual(str(f.colname), "org_organisation.name")

        # Check join (no join)
        self.assertEqual(f.join, Storage())
        self.assertEqual(f.left, Storage())

        # Check distinct (no join - no distinct)
        self.assertFalse(f.distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testResolveSelectorVirtualField(self):
        """ Resolution of a selector for a virtual field in master table """

        resource = current.s3db.resource("project_project")
        selector = "virtual"

        f = S3ResourceField(resource, selector)
        self.assertNotEqual(f, None)

        # Check field
        self.assertEqual(f.selector, selector)
        self.assertEqual(f.field, None)
        self.assertEqual(str(f.tname), "project_project")
        self.assertEqual(str(f.fname), "virtual")
        self.assertEqual(str(f.colname), "project_project.virtual")

        # Check join (no join)
        self.assertEqual(f.join, Storage())
        self.assertEqual(f.left, Storage())

        # No join - no distinct
        self.assertFalse(f.distinct)

    # -------------------------------------------------------------------------
    def testResolveSelectorComponentField(self):
        """ Resolution of a selector for a field in a component """

        s3db = current.s3db

        pr_identity = s3db.pr_identity
        pr_person = s3db.pr_person

        resource = s3db.resource("pr_person")
        selector = "identity.value"

        f = S3ResourceField(resource, selector)
        self.assertNotEqual(f, None)

        # Check field
        self.assertEqual(f.selector, selector)
        self.assertEqual(str(f.field), "pr_identity.value")
        self.assertEqual(str(f.tname), "pr_identity")
        self.assertEqual(str(f.fname), "value")
        self.assertEqual(str(f.colname), "pr_identity.value")

        # Check join
        self.assertTrue(isinstance(f.left["pr_identity"], list))
        self.assertEqual(len(f.left["pr_identity"]), 1)
        expected = pr_identity.on(
                        (pr_identity.person_id == pr_person.id) &
                        (pr_identity.deleted != True))
        self.assertEqual(str(f.left["pr_identity"][0]), str(expected))

        expected = (pr_identity.person_id == pr_person.id) & \
                   (pr_identity.deleted != True)
        self.assertEqual(str(f.join["pr_identity"]), str(expected))

        # Check distinct
        self.assertTrue(f.distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testResolveSelectorLinkedTableField(self):
        """ Resolution of a selector for a field in a link-table component """

        s3db = current.s3db

        project_project = s3db.project_project
        project_task_project = s3db.project_task_project
        project_task = s3db.project_task

        resource = s3db.resource("project_project")
        selector = "task.description"

        f = S3ResourceField(resource, selector)
        self.assertNotEqual(f, None)

        # Check field
        self.assertEqual(f.selector, selector)
        self.assertEqual(str(f.field), "project_task.description")
        self.assertEqual(str(f.tname), "project_task")
        self.assertEqual(str(f.fname), "description")
        self.assertEqual(str(f.colname), "project_task.description")

        # Check join
        self.assertTrue(isinstance(f.left["project_task"], list))
        self.assertEqual(len(f.left["project_task"]), 2)

        expected_l = project_task_project.on(
                        (project_task_project.project_id == project_project.id) &
                        (project_task_project.deleted != True))

        expected_r = project_task.on(
                        project_task_project.task_id == project_task.id)

        self.assertEqual(str(f.left["project_task"][0]), str(expected_l))
        self.assertEqual(str(f.left["project_task"][1]), str(expected_r))

        expected = (((project_task_project.project_id == project_project.id) &
                     (project_task_project.deleted != True)) &
                    (project_task_project.task_id == project_task.id))

        self.assertEqual(str(f.join["project_task"]), str(expected))

        # Check distinct
        self.assertTrue(f.distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testResolveSelectorReferencedTableField(self):
        """ Resolution of a selector for a field in a referenced table """

        s3db = current.s3db

        project_project = s3db.project_project
        org_organisation = s3db.org_organisation

        resource = s3db.resource("project_project")
        selector = "organisation_id$name"

        f = S3ResourceField(resource, selector)
        self.assertNotEqual(f, None)

        # Check field
        self.assertEqual(f.selector, selector)
        self.assertEqual(str(f.field), "org_organisation.name")
        self.assertEqual(str(f.tname), "org_organisation")
        self.assertEqual(str(f.fname), "name")
        self.assertEqual(str(f.colname), "org_organisation.name")

        # Check join
        self.assertTrue(isinstance(f.left["org_organisation"], list))
        self.assertEqual(len(f.left["org_organisation"]), 1)
        expected = org_organisation.on(
                    project_project.organisation_id == org_organisation.id)
        self.assertEqual(str(f.left["org_organisation"][0]), str(expected))

        expected = (project_project.organisation_id == org_organisation.id)
        self.assertEqual(str(f.join["org_organisation"]), str(expected))

        # Check distinct
        self.assertTrue(f.distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testResolveSelectorExceptions(self):
        """ Exception for invalid selectors """

        resource = current.s3db.resource("project_project")
        selector = "organisation_id.test"
        self.assertRaises(AttributeError, S3ResourceField, resource, selector)

# =============================================================================
class ResourceDataAccessTests(unittest.TestCase):
    """ Test data access via resources """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db
        current.auth.override = True

        xmlstr = """
<s3xml>
    <resource name="org_organisation" uuid="DATESTORG">
        <data field="name">DATestOrg</data>
        <resource name="org_office" uuid="DATESTOFFICE1">
            <data field="name">DATestOffice1</data>
        </resource>
        <resource name="org_office" uuid="DATESTOFFICE2">
            <data field="name">DATestOffice2</data>
        </resource>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = s3db.resource("org_organisation")
        resource.import_xml(xmltree)

    # -------------------------------------------------------------------------
    def testResourceFieldExtract(self):
        """ Test value extraction from rows by S3ResourceFields """

        s3db = current.s3db

        resource = s3db.resource("org_organisation",
                                 uid="DATESTORG")

        rows = resource.select(["name", "office.name"],
                               limit=1, as_rows=True)
        self.assertEqual(len(rows), 2)
        row = rows[0]

        rf = S3ResourceField(resource, "name")
        value = rf.extract(row)
        self.assertEqual(value, "DATestOrg")

        rf = S3ResourceField(resource, "office.name")
        value = rf.extract(row)
        self.assertEqual(value[:-1], "DATestOffice")

    # -------------------------------------------------------------------------
    def testResourceJSON(self):
        """ Test simple JSON export of a resource """

        s3db = current.s3db
        resource = s3db.resource("org_organisation", uid="DATESTORG")
        jstr = resource.json(["name", "office.name"])

        from gluon.contrib import simplejson as json
        data = json.loads(jstr)
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 1)
        record = data[0]
        self.assertTrue("org_organisation.name" in record)
        self.assertTrue("org_office.name" in record)
        self.assertTrue(isinstance(record["org_office.name"], list))
        self.assertEqual(len(record["org_office.name"]), 2)
        self.assertTrue("DATestOffice1" in record["org_office.name"])
        self.assertTrue("DATestOffice2" in record["org_office.name"])
        self.assertEqual(record["org_organisation.name"], "DATestOrg")

    # -------------------------------------------------------------------------
    def testCollapseRows(self):
        """ Test correct handling of ambiguous rows in select """

        s3db = current.s3db

        otable = s3db.org_organisation
        ftable = s3db.org_office
        query = (otable.uuid == "DATESTORG") & \
                (ftable.organisation_id == otable.id)

        rows = current.db(query).select(otable.id,
                                        otable.name,
                                        ftable.id,
                                        ftable.name)
        self.assertEqual(len(rows), 2)

        resource = s3db.resource("org_organisation", uid="DATESTORG")
        list_fields = ["name", "office.name"]

        rows = resource.select(list_fields)["rows"]
        self.assertEqual(len(rows), 1)

        office_names = rows[0]["org_office.name"]
        self.assertTrue(isinstance(office_names, list))
        self.assertEqual(len(office_names), 2)
        self.assertTrue("DATestOffice1" in office_names)
        self.assertTrue("DATestOffice2" in office_names)

        rows = resource.select(list_fields,
                                    represent=True)["rows"]
        self.assertEqual(len(rows), 1)

        office_names = rows[0]["org_office.name"]
        self.assertTrue(isinstance(office_names, basestring))
        office_names = [s.strip() for s in office_names.split(",")]
        self.assertEqual(len(office_names), 2)
        self.assertTrue("DATestOffice1" in office_names)
        self.assertTrue("DATestOffice2" in office_names)

    # -------------------------------------------------------------------------
    def testLoadRows(self):
        """ Test loading rows with ambiguous query """

        s3db = current.s3db

        # This filter query produces ambiguous rows (=the same
        # organisation record appears once for each office):
        query = (FS("office.name").like("DATestOffice%"))

        # load() should not load any duplicate rows
        resource = s3db.resource("org_organisation")
        resource.add_filter(query)
        resource.load()
        self.assertEqual(len(resource), 1)
        self.assertEqual(len(resource._rows), 1)
        self.assertEqual(resource._length, 1)

        # Try the same with an additional virtual field filter:
        query = query & (FS("testfield") == "TEST")

        # Should still not give any duplicates:
        resource = s3db.resource("org_organisation")
        class FakeVirtualFields(object):
            def testfield(self):
                return "TEST"
        resource.table.virtualfields.append(FakeVirtualFields())
        resource.add_filter(query)
        resource.load()
        self.assertEqual(len(resource), 1)
        self.assertEqual(len(resource._rows), 1)
        self.assertEqual(resource._length, 1)

    # -------------------------------------------------------------------------
    def testLoadIds(self):
        """ Test loading IDs with ambiguous query """

        s3db = current.s3db

        # This filter query produces ambiguous rows (=the same
        # organisation record appears once for each office):
        query = (FS("office.name").like("DATestOffice%"))

        # load() should not load any duplicate rows
        resource = s3db.resource("org_organisation")
        resource.add_filter(query)
        uid = resource.get_uid()
        self.assertTrue(isinstance(uid, str))
        self.assertEqual(uid, "DATESTORG")

        # Try the same with an additional virtual field filter:
        query = query & (FS("testfield") == "TEST")

        # Should still not give any duplicates:
        resource = s3db.resource("org_organisation")
        class FakeVirtualFields(object):
            def testfield(self):
                return "TEST"
        resource.table.virtualfields.append(FakeVirtualFields())
        resource.add_filter(query)
        uid = resource.get_uid()
        self.assertTrue(isinstance(uid, str))
        self.assertEqual(uid, "DATESTORG")

    # -------------------------------------------------------------------------
    def testCountRows(self):
        """ Test counting rows with ambiguous query """

        s3db = current.s3db

        # This filter query produces ambiguous rows (=the same
        # organisation record appears once for each office):
        query = (FS("office.name").like("DATestOffice%"))

        # count() should properly deduplicate the rows before counting them
        resource = s3db.resource("org_organisation")
        resource.add_filter(query)
        self.assertEqual(resource.count(), 1)

        # Try the same with an additional virtual field filter:
        query = query & (FS("testfield") == "TEST")

        # Should still not give any duplicates:
        resource = s3db.resource("org_organisation")
        class FakeVirtualFields(object):
            def testfield(self):
                return "TEST"
        resource.table.virtualfields.append(FakeVirtualFields())
        resource.add_filter(query)
        self.assertEqual(resource.count(), 1)

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        current.db.rollback()
        current.auth.override = False

# =============================================================================
class URLQueryTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

    # -------------------------------------------------------------------------
    def testParseExpression(self):
        """ Test URL Expression parsing """

        parse = S3URLQuery.parse_expression

        items = [
            # Correct syntax
            ("s", ["s"], "eq", False),
            ("s!", ["s"], "eq", True),
            ("s__op", ["s"], "op", False),
            ("s__op!", ["s"], "op", True),
            ("s1|s2|s3", ["s1", "s2", "s3"], "eq", False),
            ("s1|s2|s3!", ["s1", "s2", "s3"], "eq", True),
            ("s1|s2|s3__op", ["s1", "s2", "s3"], "op", False),
            ("s1|s2|s3__op!", ["s1", "s2", "s3"], "op", True),
            # Incorrect syntax
            ("s__", ["s"], "eq", False),
            ("s___", ["s"], "eq", False),
            ("s_____ne", ["s"], "ne", False),
            ("s__!", ["s"], "eq", True),
            ("s!__op", ["s!"], "op", False),
            ("s__!op", ["s"], "!op", False),
            ("s1||s3", ["s1", "s3"], "eq", False),
            ("s1|s2|s3__", ["s1", "s2", "s3"], "eq", False),
            ("s1|s2|s3__!", ["s1", "s2", "s3"], "eq", True),
            ("s1|s2|s3!__op", ["s1", "s2", "s3!"], "op", False),
            ("s1|s2|s3__!op", ["s1", "s2", "s3"], "!op", False),
        ]

        for key, selectors, op, invert in items:
            s, o, i = parse(key)
            self.assertEqual((key, s, o, i), (key, selectors, op, invert))

    # -------------------------------------------------------------------------
    def testParseValue(self):
        """ Test URL value parsing """

        parse = S3URLQuery.parse_value

        items = [
            ("Liquiçá,Other", ["Liquiçá", "Other"]),
            ("123", "123"),
            ("1,2,3", ["1", "2", "3"]),
            ('"1,2",3', ["1,2", "3"]),
            (["1,2", "3"], ["1", "2", "3"]),
            ("NONE", None),
            ('"NONE"', "NONE"),
            ("None", None),
            ('"None"', "None"),
            ("NONE,1", [None, "1"]),
            ('"NONE",1', ["NONE", "1"]),
            ('"NONE,1"', "NONE,1"),
            ('"NONE",NONE,1,"Test\\""', ['NONE', None, "1", 'Test"']),
            (['"NONE",NONE,1','"Test\\"",None'], ['NONE', None, "1", 'Test"', None])
        ]
        for v, r in items:
            self.assertEqual((v, parse(v)), (v, r))

    # -------------------------------------------------------------------------
    def testParseURL(self):
        """ Test URL get_vars parsing """

        parse = S3URLQuery.parse_url

        items = [
            (None, Storage()),
            ("", Storage()),
            ("test", Storage()),
            ("x/y/z?", Storage()),
            ("x/z/z?a=b", Storage(a="b")),
            ("?a=b", Storage(a="b")),
            ("a=b", Storage(a="b")),
            ("a=b&a=c", Storage(a=["b", "c"])),
            ("a=b,c&a=d", Storage(a=["b,c", "d"])),
        ]
        for v, r in items:
            self.assertEqual((v, parse(v)), (v, r))

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testParseURLQuery(self):
        """ Test standard URL query parsing """

        s3db = current.s3db

        project_project = s3db.project_project
        org_organisation = s3db.org_organisation
        project_task_project = s3db.project_task_project
        project_task = s3db.project_task

        url_query = {"project.organisation_id$name__like": "*test*",
                     "task.description__like!": "*test*"}

        resource = current.s3db.resource("project_project", vars=url_query)
        rfilter = resource.rfilter

        # Check joins
        joins = rfilter.get_joins(left=True)
        self.assertNotEqual(joins, None)
        self.assertTrue(isinstance(joins, list))

        expected = org_organisation.on(
                        project_project.organisation_id == org_organisation.id)
        self.assertEqual(joins[0], str(expected))

        expected_l = project_task_project.on(
                        (project_task_project.project_id == project_project.id) &
                        (project_task_project.deleted != True))
        expected_r = project_task.on(
                        project_task_project.task_id == project_task.id)
        self.assertEqual(joins[1], str(expected_l))
        self.assertEqual(joins[2], str(expected_r))

        # Check query
        query = rfilter.get_query()
        expected = (((project_project.deleted != True) &
                     (project_project.id > 0)) &
                    ((org_organisation.name.lower().like("%test%")) &
                    (~(project_task.description.lower().like("%test%")))))

        self.assertEqual(str(query), str(expected))

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testParseURLQueryWithAlternativeValues(self):
        """ Test URL query parsing with alternative values (OR) """

        s3db = current.s3db

        project_project = s3db.project_project
        org_organisation = s3db.org_organisation
        project_task_project = s3db.project_task_project
        project_task = s3db.project_task

        url_query = {"project.organisation_id$name__like": "Test*,Other*"}

        resource = current.s3db.resource("project_project", vars=url_query)
        rfilter = resource.rfilter

        # Check joins
        joins = rfilter.get_joins(left=True)
        self.assertTrue(isinstance(joins, list))
        expected = org_organisation.on(
                        project_project.organisation_id == org_organisation.id)
        self.assertEqual(joins[0], str(expected))

        # Check query
        query = rfilter.get_query()
        expected = (((project_project.deleted != True) &
                     (project_project.id > 0)) &
                    ((org_organisation.name.lower().like("test%")) |
                     (org_organisation.name.lower().like("other%"))))
        self.assertEqual(str(query), str(expected))

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testParseURLQueryWithMultipleValues(self):
        """ Test URL query parsing with multiple values (AND) """

        s3db = current.s3db

        project_project = s3db.project_project
        org_organisation = s3db.org_organisation
        project_task_project = s3db.project_task_project
        project_task = s3db.project_task

        url_query = {"project.organisation_id$name__like": ["Test*", "Other*"]}

        resource = current.s3db.resource("project_project", vars=url_query)
        rfilter = resource.rfilter

        # Check joins
        joins = rfilter.get_joins(left=True)
        self.assertTrue(isinstance(joins, list))
        expected = org_organisation.on(
                        project_project.organisation_id == org_organisation.id)
        self.assertEqual(joins[0], str(expected))

        # Check query
        query = rfilter.get_query()
        expected = (((project_project.deleted != True) &
                     (project_project.id > 0)) &
                    ((org_organisation.name.lower().like("other%")) &
                     (org_organisation.name.lower().like("test%"))))
        self.assertEqual(str(query), str(expected))

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testParseURLQueryWithAlternativeSelectors(self):
        """ Test alternative selectors (OR) in a URL query """

        s3db = current.s3db

        project_project = s3db.project_project
        org_organisation = s3db.org_organisation
        project_task_project = s3db.project_task_project
        project_task = s3db.project_task

        url_query = {"project.organisation_id$name|task.description__like": "Test*"}

        resource = s3db.resource("project_project", vars=url_query)
        rfilter = resource.rfilter

        # Check joins
        joins = rfilter.get_joins(left=True)
        self.assertTrue(isinstance(joins, list))

        expected = org_organisation.on(
                        project_project.organisation_id == org_organisation.id)
        self.assertEqual(joins[0], str(expected))

        expected_l = project_task_project.on(
                        (project_task_project.project_id == project_project.id) &
                        (project_task_project.deleted != True))
        expected_r = project_task.on(
                        project_task_project.task_id == project_task.id)
        self.assertEqual(joins[1], str(expected_l))
        self.assertEqual(joins[2], str(expected_r))

        # Check the query
        query = rfilter.get_query()
        expected = (((project_project.deleted != True) &
                     (project_project.id > 0)) &
                    ((org_organisation.name.lower().like("test%")) |
                     (project_task.description.lower().like("test%"))))
        self.assertEqual(str(query), str(expected))

    # -------------------------------------------------------------------------
    def testBBOXFilterDirectLink(self):
        """ Test URL query with BBOX filter, location_id """

        s3db = current.s3db

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        org_office = s3db.org_office
        gis_location = s3db.gis_location

        # Remove any location context
        context = s3db.get_config("org_office", "context")
        s3db.configure("org_office", context={})

        try:
            url_query = {"bbox": "119.80,12.86,122.27,15.10"}

            resource = s3db.resource("org_office", vars=url_query)
            rfilter = resource.rfilter

            # Parse the bbox
            bbox, joins = rfilter.parse_bbox_query(resource, url_query)

            expected_bbox = None
            if current.deployment_settings.get_gis_spatialdb():
                polygon = "POLYGON((119.8 12.86, 119.8 15.1, 122.27 15.1, 122.27 12.86, 119.8 12.86))"
                try:
                    expected_bbox = gis_location.the_geom.st_intersects(polygon)
                except:
                    # Not supported
                    pass

            if expected_bbox is None:
                expected_bbox = ((((gis_location.lon > 119.8) & \
                                (gis_location.lon < 122.27)) & \
                                (gis_location.lat > 12.86)) & \
                                (gis_location.lat < 15.1))

            assertEqual(bbox, expected_bbox)

            # Check the joins
            assertTrue(isinstance(joins, dict))
            assertEqual(len(joins), 1)

            subjoins = joins.get("gis_location")
            assertNotEqual(subjoins, None)
            assertEqual(len(subjoins), 1)
            expected_join = gis_location.on(org_office.location_id == gis_location.id)
            assertEqual(str(subjoins[0]), str(expected_join))

            # Check the query
            query = rfilter.get_query()
            expected = (((org_office.deleted != True) & (org_office.id > 0)) & expected_bbox)
            assertEqual(str(query), str(expected))

        finally:
            # Restore context configuration
            resource.configure(context=context)

    # -------------------------------------------------------------------------
    def testBBOXFilterLocationContext(self):
        """ Test URL query with BBOX filter, location context """

        s3db = current.s3db

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        org_office = s3db.org_office
        gis_location = s3db.gis_location
        org_organisation = s3db.org_organisation
        org_organisation_location = s3db.org_organisation_location

        # Define a location context
        context = s3db.get_config("org_office", "context")
        s3db.configure("org_office",
                       context={"location": "organisation_id$organisation_location.location_id"})

        try:
            url_query = {"bbox": "119.80,12.86,122.27,15.10"}

            resource = s3db.resource("org_office", vars=url_query)
            rfilter = resource.rfilter

            # Parse the bbox
            bbox, joins = rfilter.parse_bbox_query(resource, url_query)

            expected_bbox = None
            if current.deployment_settings.get_gis_spatialdb():
                polygon = "POLYGON((119.8 12.86, 119.8 15.1, 122.27 15.1, 122.27 12.86, 119.8 12.86))"
                try:
                    expected_bbox = gis_location.the_geom.st_intersects(polygon)
                except:
                    # Not supported
                    pass

            if expected_bbox is None:
                expected_bbox = ((((gis_location.lon > 119.8) & \
                                (gis_location.lon < 122.27)) & \
                                (gis_location.lat > 12.86)) & \
                                (gis_location.lat < 15.1))

            assertEqual(bbox, expected_bbox)

            # Check the joins
            assertTrue(isinstance(joins, dict))
            assertEqual(len(joins), 3)

            subjoins = joins.get("gis_location")
            assertNotEqual(subjoins, None)
            assertEqual(len(subjoins), 1)
            expected_join = gis_location.on(org_organisation_location.location_id == gis_location.id)
            assertEqual(str(subjoins[0]), str(expected_join))

            subjoins = joins.get("org_organisation")
            assertNotEqual(subjoins, None)
            assertEqual(len(subjoins), 1)
            expected_join = org_organisation.on(org_office.organisation_id == org_organisation.id)
            assertEqual(str(subjoins[0]), str(expected_join))

            subjoins = joins.get("org_organisation_location")
            assertNotEqual(subjoins, None)
            assertEqual(len(subjoins), 1)
            expected_join = org_organisation_location.on(
                                (org_organisation_location.organisation_id == org_organisation.id) &
                                (org_organisation_location.deleted != True)
                            )
            assertEqual(str(subjoins[0]), str(expected_join))

            # Check the query
            query = rfilter.get_query()
            expected = (((org_office.deleted != True) & (org_office.id > 0)) & expected_bbox)
            assertEqual(str(query), str(expected))

        finally:
            # Restore context configuration
            resource.configure(context=context)

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False

# =============================================================================
class JoinResolutionTests(unittest.TestCase):

    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testPreferredSet(self):
        """ Test resolution of duplicate inner/left joins """

        s3db = current.s3db
        ptable = s3db.project_project
        ltable = s3db.project_task_project
        ttable = s3db.project_task

        ptable_join = ptable.on(ltable.project_id == ptable.id)
        ltable_join = ltable.on(ltable.task_id == ttable.id)

        # Define a set of inner joins for one table
        ijoins = S3Joins("project_task")
        ijoins.extend({"project_project": [ptable_join, ltable_join]})

        # Define a sub-join of the inner joins as a left join
        ljoins = S3Joins("project_task")
        ljoins.extend({"project_task_project": [ltable_join]})

        # Request joins for both tables from both sets, prefer the left joins
        tablenames = ["project_project", "project_task_project"]
        join = ijoins.as_list(tablenames=tablenames, prefer=ljoins)
        left = ljoins.as_list(tablenames=tablenames)

        # Joins should be moved to the left joins set
        self.assertEqual(join, [])
        self.assertEqual(len(left), 2)
        # Mind the order! (must be ordered by dependency)
        self.assertEqual(str(left[0]), str(ltable_join))
        self.assertEqual(str(left[1]), str(ptable_join))

# =============================================================================
class URLQueryParserTests(unittest.TestCase):
    """ URL Query Parser Tests """

    # -------------------------------------------------------------------------
    def testConstruction(self):
        """ Test parser instantiation """

        p = S3URLQueryParser()

        if PYPARSING:
            self.assertNotEqual(p.parser, None)
        else:
            self.assertEqual(p.parser, None,
                             msg = "Unexpected Parser Instance")

    # -------------------------------------------------------------------------
    def testParser(self):
        """ Test parser response and error logging """

        # Turn on logging (otherwise no point in recording)
        settings = current.deployment_settings
        debug = settings.base.debug
        settings.base.debug = True
        from s3log import S3Log
        del current.log
        S3Log.setup()

        try:
            p = S3URLQueryParser()

            log_recorder = current.log.recorder()

            # Test with valid expression
            expr = "~.test eq 1"
            q = p.parse(expr)
            log_messages = log_recorder.read()

            self.assertTrue(isinstance(q, dict))
            if PYPARSING:
                self.assertTrue(None in q)
                self.assertNotIn("Invalid URL Filter Expression", log_messages)
            else:
                self.assertEqual(q, {})

            # Test with invalid expression
            # => should succeed, but not return any query
            expr = "invalidexpression"

            log_recorder.clear()
            q = p.parse(expr)
            log_messages = log_recorder.read()

            self.assertEqual(q, {})
            if PYPARSING:
                self.assertIn("Invalid URL Filter Expression", log_messages)

            # Test with empty expression
            # => should succeed, but not return any query
            expr = ""

            log_recorder.clear()
            q = p.parse(expr)
            log_messages = log_recorder.read()

            self.assertEqual(q, {})
            if PYPARSING:
                self.assertNotIn("Invalid URL Filter Expression", log_messages)

            # Test without expression
            # => should succeed, but not return any query
            expr = None

            log_recorder.clear()
            q = p.parse(expr)
            log_messages = log_recorder.stop()

            self.assertEqual(q, {})
            if PYPARSING:
                self.assertNotIn("Invalid URL Filter Expression", log_messages)

        finally:
            settings.base.debug = debug
            del current.log
            S3Log.setup()

    # -------------------------------------------------------------------------
    def testAlias(self):
        """ Test alias extraction """

        p = S3URLQueryParser()
        assertEqual = self.assertEqual

        selectors = (("~.example$sub", None),
                     ("other.example", "other"),
                     ("another", None),
                     (".no prefix", None),
                     ("test.~.~", "test"),
                     )

        for selector, expected in selectors:
            alias = p._alias(FS(selector))
            assertEqual(alias, expected,
                        msg = "Expected '%s' for '%s', but got '%s'" %
                              (expected, selector, alias))

        assertEqual(p._alias(None), None)

    # -------------------------------------------------------------------------
    def testQuery(self):
        """ Test query construction """

        p = S3URLQueryParser()
        assertTrue = self.assertTrue
        assertEqual = self.assertEqual
        assertIn = self.assertIn

        examples = (
            (("example", "eq", "1"), True, None, "1"),
            (("test.example", "contains", "ab,cd,ef"), True, "test", ["ab","cd","ef"]),
            ((None, "gt", "1"), False, None, None),
            (("~.example", "like", "Ex*mple"), True, None, "ex%mple"),
        )

        for example, success, alias, pvalue in examples:

            selector, op, value = example
            if selector is None:
                qdict = p._query(op, None, value)
            else:
                qdict = p._query(op, FS(selector), value)

            if success:
                assertTrue(isinstance(qdict, dict))
                assertEqual(len(qdict), 1)
                assertIn(alias, qdict)
                query = qdict[alias]
                assertTrue(isinstance(query, S3ResourceQuery))
                assertTrue(isinstance(query.left, S3FieldSelector))
                assertEqual(query.left.name, selector)
                assertEqual(query.op, op)
                assertEqual(query.right, pvalue)
            else:
                assertEqual(qdict, {})

    # -------------------------------------------------------------------------
    def testNot(self):
        """ Test negation of query dicts """

        p = S3URLQueryParser()

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertIn = self.assertIn

        # Single query, simple
        q = S3FieldSelector("example.test") == 1
        qdict = {"example": q}

        result = p._not(qdict)
        assertTrue(isinstance(result, dict))
        assertEqual(len(result), 1)
        assertIn("example", result)
        query = result["example"]
        assertEqual(query.op, query.NOT)
        assertEqual(query.left, q)

        # Single query, OR (inhomogeneous)
        q1 = S3FieldSelector("~.field") != "a"
        q2 = S3FieldSelector("example.test") > 1
        qdict = {None: q1 | q2}

        result = p._not(qdict)
        assertTrue(isinstance(result, dict))
        assertEqual(len(result), 2)
        assertIn(None, result)
        query = result[None]
        assertEqual(query.op, query.NOT)
        assertEqual(query.left, q1)
        assertIn("example", result)
        query = result["example"]
        assertEqual(query.op, query.NOT)
        assertEqual(query.left, q2)

        # Single query, OR (homogeneous)
        q1 = S3FieldSelector("example.other").like("a*")
        q2 = S3FieldSelector("example.test") > 1
        qdict = {"example": q1 | q2}

        result = p._not(qdict)
        assertTrue(isinstance(result, dict))
        assertEqual(len(result), 1)
        assertIn("example", result)
        query = result["example"]
        assertEqual(query.op, query.NOT)
        query = query.left
        assertEqual(query.op, query.OR)
        assertEqual(query.left, q1)
        assertEqual(query.right, q2)

        # Single query, AND
        q1 = S3FieldSelector("~.other").like("x*")
        q2 = S3FieldSelector("~.test") < 1
        qdict = {None: q1 & q2}

        result = p._not(qdict)
        assertTrue(isinstance(result, dict))
        assertEqual(len(result), 1)
        assertIn(None, result)
        query = result[None]
        assertEqual(query.op, query.NOT)
        query = query.left
        assertEqual(query.op, query.AND)
        assertEqual(query.left, q1)
        assertEqual(query.right, q2)

        # Single query, NOT
        q = S3FieldSelector("test.other").like("x*")
        qdict = {"test": ~q}

        result = p._not(qdict)
        assertTrue(isinstance(result, dict))
        assertEqual(len(result), 1)
        assertIn("test", result)
        query = result["test"]
        assertEqual(query, q)

        # Multiple Queries, AND
        q1 = S3FieldSelector("test.other").like("y*")
        q2 = S3FieldSelector("~.test") != 1
        qdict = {"test": q1, None: q2}

        result = p._not(qdict)
        assertTrue(isinstance(result, dict))
        assertEqual(len(result), 1)
        assertIn(None, result)
        query = result[None]
        assertEqual(query.op, query.NOT)
        query = query.left
        assertEqual(query.op, query.AND)
        assertEqual(query.left, q1)
        assertEqual(query.right, q2)

    # -------------------------------------------------------------------------
    def testAnd(self):
        """ Test conjunction of query dicts """

        p = S3URLQueryParser()

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertIn = self.assertIn

        q1 = S3FieldSelector("~.test1") == "A"
        q2 = S3FieldSelector("x.test2") == "B"
        q3 = S3FieldSelector("x.test3") == "C"
        q4 = S3FieldSelector("y.test4") == "D"

        qdict1 = {None: q1, "x": q2}
        qdict2 = {"x": q3, "y": q4}

        result = p._and(qdict1, qdict2)

        assertTrue(isinstance(result, dict))
        assertEqual(len(result), 3)
        assertIn(None, result)
        assertEqual(result[None], q1)
        assertIn("x", result)
        query = result["x"]
        assertEqual(query.op, query.AND)
        operands = (query.left, query.right)
        assertIn(q2, operands)
        assertIn(q3, operands)
        assertIn("y", result)
        assertEqual(result["y"], q4)

    # -------------------------------------------------------------------------
    def testOr(self):
        """ Test disjunction of query dicts """

        p = S3URLQueryParser()

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertIn = self.assertIn

        q1 = S3FieldSelector("~.test1") == "A"
        q2 = S3FieldSelector("x.test2") == "B"
        q3 = S3FieldSelector("x.test3") == "C"
        q4 = S3FieldSelector("y.test4") == "D"

        # Test single+single (homogeneous)
        qdict1 = {"x": q2}
        qdict2 = {"x": q3}
        result = p._or(qdict1, qdict2)
        assertTrue(isinstance(result, dict))
        assertEqual(len(result), 1)
        assertIn("x", result)
        query = result["x"]
        assertEqual(query.op, query.OR)
        operands = (query.left, query.right)
        assertIn(q2, operands)
        assertIn(q3, operands)

        # Test single+single (inhomogeneous)
        qdict1 = {"x": q2}
        qdict2 = {"y": q4}
        result = p._or(qdict1, qdict2)
        assertTrue(isinstance(result, dict))
        assertEqual(len(result), 1)
        assertIn(None, result)
        query = result[None]
        assertEqual(query.op, query.OR)
        operands = (query.left, query.right)
        assertIn(q2, operands)
        assertIn(q4, operands)

        # Test single+multiple
        qdict1 = {"x": q2}
        qdict2 = {"x": q3, "y": q4}
        result = p._or(qdict1, qdict2)
        assertTrue(isinstance(result, dict))
        assertEqual(len(result), 1)
        assertIn(None, result)
        query = result[None]
        assertEqual(query.op, query.OR)
        assertIn(q2, (query.left, query.right))
        query = query.right if query.left == q2 else query.right
        assertEqual(query.op, query.AND)
        operands = (query.left, query.right)
        assertIn(q3, operands)
        assertIn(q4, operands)

        # Test single+empty
        qdict1 = {}
        qdict2 = {"x": q3}
        result = p._or(qdict1, qdict2)
        assertTrue(isinstance(result, dict))
        assertEqual(len(result), 1)
        assertIn("x", result)
        query = result["x"]
        assertEqual(query, q3)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not PYPARSING, "PyParsing not available")
    def testParsing(self):
        """ Test expression parsing (not comprehensive) """

        p = S3URLQueryParser()

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        examples = (
            ("pr_person",
             'first_name eq "Test"',
             {None: '(pr_person.first_name == "Test")',
              },
             ),
            ("pr_person",
             'last_name like "User*" or lower(contact.value) like "*example.com"',
             {None: '((pr_person.last_name like "user%") or (pr_contact.value.lower() like "%example.com"))',
              },
             ),
            ("pr_person",
             'last_name like "User*" and not(contact.value like "*example.com" or first_name like "Norm*")',
             {None: '((pr_person.last_name like "user%") and (not (pr_person.first_name like "norm%")))',
              "contact": '(not (pr_contact.value like "%example.com"))',
              },
             ),
            ("pr_person",
             '',
             {},
             ),
            ("org_organisation",
             None,
             {},
             ),
            ("org_office",
             'not a valid expression',
             {},
             ),
        )

        s3db = current.s3db
        for i, example in enumerate(examples):

            resource_name, expression, expected = example

            result = p.parse(expression)
            assertTrue(isinstance(result, dict),
                       msg = "Example %s failed: no dict returned")
            ealiases = set(expected.keys())
            raliases = set(result.keys())
            assertEqual(ealiases ^ raliases, set(),
                        msg = "Example %s failed: mismatching aliases %s!=%s" %
                              (i, str(list(ealiases)), str(list(raliases))),
                        )

            resource = s3db.resource(resource_name)
            for k, v in expected.items():
                actual = result[k].represent(resource)
                assertEqual(v, actual,
                            msg = "Example %s inconsistent result: "
                                  "expected '%s' for alias '%s' but found '%s'" %
                                  (i, v, k, actual),
                            )

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
        FieldSelectorResolutionTests,

        ResourceFilterJoinTests,
        ResourceFilterQueryTests,
        ResourceContextFilterTests,
        JoinResolutionTests,

        URLQueryTests,
        URLQueryParserTests,

        URLQuerySerializerTests,
        URLFilterSerializerTests,

        ResourceFieldTests,
        ResourceDataAccessTests,
    )

# END ========================================================================
