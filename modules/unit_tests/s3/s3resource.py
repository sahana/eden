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
from gluon.storage import Storage
from gluon.dal import Row
from s3.s3resource import S3FieldSelector, S3ResourceFilter, S3ResourceField

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
        join = component.get_join()
        self.assertEqual(str(join), "((pr_identity.person_id = pr_person.id) AND "
                                    "(pr_identity.deleted <> 'T'))")

    # -------------------------------------------------------------------------
    def testGetJoinSuperComponent(self):
        """ Join for a super-component """

        resource = current.s3db.resource("pr_person")
        component = resource.components["contact"]
        join = component.get_join()
        self.assertEqual(str(join), "((pr_person.pe_id = pr_contact.pe_id) AND "
                                    "(pr_contact.deleted <> 'T'))")

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetJoinLinkTableComponent(self):
        """ Join for a link-table component """

        resource = current.s3db.resource("project_project")
        component = resource.components["task"]
        join = component.get_join()
        self.assertEqual(str(join),
                         "((project_task_project.deleted <> 'T') AND "
                         "((project_task_project.project_id = project_project.id) AND "
                         "(project_task_project.task_id = project_task.id)))")

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

        resource = current.s3db.resource("pr_person")
        component = resource.components["identity"]
        ljoin = component.get_left_join()
        self.assertTrue(isinstance(ljoin, list))
        self.assertEqual(len(ljoin), 1)
        self.assertEqual(str(ljoin[0]), "pr_identity ON "
                                        "((pr_identity.person_id = pr_person.id) AND "
                                        "(pr_identity.deleted <> 'T'))")

    # -------------------------------------------------------------------------
    def testGetLeftJoinSuperComponent(self):
        """ Left Join for a super-component """

        resource = current.s3db.resource("pr_person")
        component = resource.components["contact"]
        ljoin = component.get_left_join()
        self.assertTrue(isinstance(ljoin, list))
        self.assertEqual(len(ljoin), 1)
        self.assertEqual(str(ljoin[0]), "pr_contact ON "
                                        "((pr_person.pe_id = pr_contact.pe_id) AND "
                                        "(pr_contact.deleted <> 'T'))")

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetLeftJoinLinkTableComponent(self):
        """ Left Join for a link-table component """

        resource = current.s3db.resource("project_project")
        component = resource.components["task"]
        ljoin = component.get_left_join()
        self.assertTrue(isinstance(ljoin, list))
        self.assertEqual(len(ljoin), 2)
        self.assertEqual(str(ljoin[0]), "project_task_project ON "
                                        "((project_task_project.project_id = project_project.id) AND "
                                        "(project_task_project.deleted <> 'T'))")
        self.assertEqual(str(ljoin[1]), "project_task ON (project_task_project.task_id = project_task.id)")

# =============================================================================
class FieldSelectorResolutionTests(unittest.TestCase):
    """ Test field selector resolution """

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testResolveSelectorsWithoutComponents(self):
        """ Field selector resolution without components"""

        resource = current.s3db.resource("project_project")
        selectors = ["id",
                     "name",
                     "organisation_id$name",
                     "task.description"]
        fields, joins, left, distinct = resource.resolve_selectors(selectors)
        self.assertEqual(len(fields), 3)
        self.assertEqual(fields[0].colname, "project_project.id")
        self.assertEqual(fields[1].colname, "project_project.name")
        self.assertEqual(fields[2].colname, "org_organisation.name")

        self.assertEqual(joins, Storage())

        self.assertTrue(isinstance(left, Storage))
        self.assertEqual(left.keys(), ["org_organisation"])
        self.assertEqual(len(left["org_organisation"]), 1)
        self.assertEqual(str(left["org_organisation"][0]), "org_organisation ON "
                                                           "(project_project.organisation_id = org_organisation.id)")
        self.assertTrue(distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testResolveSelectorsWithComponents(self):
        """ Field selector resolution with components"""

        resource = current.s3db.resource("project_project")
        selectors = ["id",
                     "name",
                     "organisation_id$name",
                     "task.description"]
        fields, joins, left, distinct = resource.resolve_selectors(selectors,
                                                                   skip_components=False)

        self.assertEqual(len(fields), 4)
        self.assertEqual(fields[0].colname, "project_project.id")
        self.assertEqual(fields[1].colname, "project_project.name")
        self.assertEqual(fields[2].colname, "org_organisation.name")
        self.assertEqual(fields[3].colname, "project_task.description")

        self.assertEqual(joins, Storage())

        self.assertTrue(isinstance(left, Storage))
        self.assertEqual(left.keys(), [ "org_organisation", "project_task"])
        self.assertEqual(len(left["org_organisation"]), 1)
        self.assertEqual(str(left["org_organisation"][0]), "org_organisation ON "
                                                           "(project_project.organisation_id = org_organisation.id)")
        self.assertEqual(len(left["project_task"]), 2)
        self.assertEqual(str(left["project_task"][0]), "project_task_project ON "
                                                       "((project_task_project.project_id = project_project.id) AND "
                                                       "(project_task_project.deleted <> 'T'))")
        self.assertEqual(str(left["project_task"][1]), "project_task ON "
                                                       "(project_task_project.task_id = project_task.id)")
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
        q = S3FieldSelector("first_name") == "test"

        joins, distinct = q.joins(resource)
        self.assertEqual(joins, Storage())
        self.assertFalse(distinct)

        joins, distinct = q.joins(resource, left=True)
        self.assertEqual(joins, Storage())
        self.assertFalse(distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetQueryJoinsReferencedTableField(self):
        """ Referenced table field queries use left joins + distinct """

        resource = current.s3db.resource("project_project")
        q = S3FieldSelector("organisation_id$name") == "test"

        joins, distinct = q.joins(resource)
        self.assertEqual(joins, Storage())
        self.assertTrue(distinct)

        joins, distinct = q.joins(resource, left=True)
        self.assertTrue(isinstance(joins, Storage))
        self.assertEqual(joins.keys(), ["org_organisation"])
        self.assertTrue(isinstance(joins["org_organisation"], list))
        self.assertEqual(len(joins["org_organisation"]), 1)
        self.assertEqual(str(joins["org_organisation"][0]), "org_organisation ON "
                                                            "(project_project.organisation_id = org_organisation.id)")
        self.assertTrue(distinct)

    # -------------------------------------------------------------------------
    def testGetQueryJoinsComponentField(self):
        """ Component field queries use left joins + distinct """

        resource = current.s3db.resource("pr_person")
        q = S3FieldSelector("identity.value") == "test"

        joins, distinct = q.joins(resource)
        self.assertEqual(joins, Storage())
        self.assertTrue(distinct)

        joins, distinct = q.joins(resource, left=True)
        self.assertEqual(joins.keys(), ["pr_identity"])
        self.assertTrue(isinstance(joins["pr_identity"], list))
        self.assertEqual(str(joins["pr_identity"][0]), "pr_identity ON "
                                                       "((pr_identity.person_id = pr_person.id) AND "
                                                       "(pr_identity.deleted <> 'T'))")
        self.assertTrue(distinct)

    # -------------------------------------------------------------------------
    def testGetQueryJoinsSuperComponentField(self):
        """ Super component field queries use left joins + distinct """

        resource = current.s3db.resource("pr_person")
        q = S3FieldSelector("contact.value") == "test"

        joins, distinct = q.joins(resource)
        self.assertEqual(joins, Storage())
        self.assertTrue(distinct)

        joins, distinct = q.joins(resource, left=True)
        self.assertEqual(joins.keys(), ["pr_contact"])
        self.assertTrue(isinstance(joins["pr_contact"], list))
        self.assertEqual(str(joins["pr_contact"][0]), "pr_contact ON "
                                                       "((pr_person.pe_id = pr_contact.pe_id) AND "
                                                       "(pr_contact.deleted <> 'T'))")
        self.assertTrue(distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetQueryJoinsLinkedComponentField(self):
        """
            Link table component field queries use chained left
            joins + distinct
        """

        resource = current.s3db.resource("project_project")
        q = S3FieldSelector("task.description") == "test"

        joins, distinct = q.joins(resource)
        self.assertEqual(joins, Storage())
        self.assertTrue(distinct)

        joins, distinct = q.joins(resource, left=True)
        self.assertEqual(joins.keys(), ["project_task"])
        self.assertTrue(isinstance(joins["project_task"], list))
        self.assertEqual(len(joins["project_task"]), 2)
        self.assertEqual(str(joins["project_task"][0]), "project_task_project ON "
                                                        "((project_task_project.project_id = project_project.id) AND "
                                                        "(project_task_project.deleted <> 'T'))")
        self.assertEqual(str(joins["project_task"][1]), "project_task ON "
                                                        "(project_task_project.task_id = project_task.id)")
        self.assertTrue(distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetQueryJoinsCombination(self):
        """ Queries for fields in multiple tables use multiple joins """

        resource = current.s3db.resource("project_project")
        q = (S3FieldSelector("organisation_id$name") == "test") & \
            (S3FieldSelector("task.description") == "test")

        joins, distinct = q.joins(resource)
        self.assertEqual(joins.keys(), [])

        joins, distinct = q.joins(resource, left=True)
        self.assertEqual(joins.keys(), ["org_organisation", "project_task"])

        self.assertTrue(isinstance(joins["org_organisation"], list))
        self.assertEqual(len(joins["org_organisation"]), 1)
        self.assertEqual(str(joins["org_organisation"][0]), "org_organisation ON "
                                                            "(project_project.organisation_id = org_organisation.id)")
        self.assertTrue(isinstance(joins["project_task"], list))
        self.assertEqual(len(joins["project_task"]), 2)
        self.assertEqual(str(joins["project_task"][0]), "project_task_project ON "
                                                        "((project_task_project.project_id = project_project.id) AND "
                                                        "(project_task_project.deleted <> 'T'))")
        self.assertEqual(str(joins["project_task"][1]), "project_task ON "
                                                        "(project_task_project.task_id = project_task.id)")
        self.assertTrue(distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testGetFilterLeftJoins(self):
        """ Check list of left joins in resource filters """

        q = (S3FieldSelector("organisation_id$name") == "test") & \
            (S3FieldSelector("task.description") == "test")
        resource = current.s3db.resource("project_project", filter=q)

        joins = resource.rfilter.get_left_joins()
        self.assertTrue(isinstance(joins, list))

        self.assertEqual(joins[0], "project_task_project ON "
                                   "((project_task_project.project_id = project_project.id) AND "
                                   "(project_task_project.deleted <> 'T'))")
        self.assertEqual(joins[1], "project_task ON "
                                   "(project_task_project.task_id = project_task.id)")

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
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testMasterFilterConstruction(self):
        """ Test master resource filter construction """

        q = (S3FieldSelector("organisation_id$name") == "test") & \
            (S3FieldSelector("task.description") == "test")
        resource = current.s3db.resource("project_project", filter=q)

        rfilter = resource.rfilter
        self.assertNotEqual(rfilter, None)

        # Check master query
        self.assertEqual(str(rfilter.mquery), "((project_project.deleted <> 'T') AND "
                                              "(project_project.id > 0))")

        # Check effective query
        query = rfilter.get_query()
        self.assertEqual(str(query), "(((project_project.deleted <> 'T') AND "
                                     "(project_project.id > 0)) AND "
                                     "((org_organisation.name = 'test') AND "
                                     "(project_task.description = 'test')))")

        # Check joins
        joins = rfilter.joins
        self.assertEqual(joins.keys(), [])

        # Check left joins
        left = rfilter.left
        self.assertEqual(left.keys(), ["project"])
        left = left["project"]
        self.assertEqual(left.keys(), ["org_organisation", "project_task"])
        self.assertTrue(isinstance(left["org_organisation"], list))
        self.assertEqual(len(left["org_organisation"]), 1)
        self.assertEqual(str(left["org_organisation"][0]), "org_organisation ON "
                                                            "(project_project.organisation_id = org_organisation.id)")
        self.assertTrue(isinstance(left["project_task"], list))
        self.assertEqual(len(left["project_task"]), 2)
        self.assertEqual(str(left["project_task"][0]), "project_task_project ON "
                                                       "((project_task_project.project_id = project_project.id) AND "
                                                       "(project_task_project.deleted <> 'T'))")
        self.assertEqual(str(left["project_task"][1]), "project_task ON "
                                                       "(project_task_project.task_id = project_task.id)")

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testCrossComponentFilterConstruction1(self):
        """ Test cross-component effect of master resource filter """

        q1 = (S3FieldSelector("organisation_id$name") == "test")
        q2 = (S3FieldSelector("task.description") == "test")
        resource = current.s3db.resource("project_project", filter=q1)

        resource.add_filter(q2)

        component = resource.components["task"]
        component.build_query()
        rfilter = component.rfilter
        query = rfilter.get_query()

        self.assertEqual(str(query), "(((((project_task.deleted <> 'T') AND "
                                     "(project_task.id > 0)) AND "
                                     "((((project_project.deleted <> 'T') AND "
                                     "(project_project.id > 0)) AND "
                                     "(org_organisation.name = 'test')) AND "
                                     "(project_task.description = 'test'))) AND "
                                     "((project_task_project.deleted <> 'T') AND "
                                     "((project_task_project.project_id = project_project.id) AND "
                                     "(project_task_project.task_id = project_task.id)))) AND "
                                     "(project_project.organisation_id = org_organisation.id))")

        self.assertEqual(rfilter.joins, Storage())
        self.assertEqual(rfilter.left, Storage())
        rows = component.select()

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("hrm"), "hrm module disabled")
    def testCrossComponentFilterConstruction2(self):
        """ Test cross-component effect of master resource filter """

        q1 = (S3FieldSelector("human_resource.organisation_id$name") == "test")
        q2 = (S3FieldSelector("identity.value") == "test")
        resource = current.s3db.resource("pr_person", filter=q1)

        resource.add_filter(q2)

        component = resource.components["identity"]
        component.build_query()
        rfilter = component.rfilter
        query = rfilter.get_query()

        self.assertEqual(str(query), "((((((pr_identity.deleted <> 'T') AND "
                                     "(pr_identity.id > 0)) AND "
                                     "((((pr_person.deleted <> 'T') AND "
                                     "(pr_person.id > 0)) AND "
                                     "(org_organisation.name = 'test')) AND "
                                     "(pr_identity.value = 'test'))) AND "
                                     "((pr_identity.person_id = pr_person.id) AND "
                                     "(pr_identity.deleted <> 'T'))) AND "
                                     "((hrm_human_resource.person_id = pr_person.id) AND "
                                     "(hrm_human_resource.deleted <> 'T'))) AND "
                                     "(hrm_human_resource.organisation_id = org_organisation.id))")

        self.assertEqual(rfilter.joins, Storage())
        self.assertEqual(rfilter.left, Storage())
        rows = component.select()

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testSimpleComponentFilterConstruction1(self):
        """ Test simple component filter construction (check query in filter) """

        resource = current.s3db.resource("project_project", id=1)

        component = resource.components["activity"]
        component.build_query()
        rfilter = component.rfilter
        query = rfilter.get_query()

        # This will fail in 1st run as there is no ADMIN role yet
        self.assertEqual(str(query), "((((project_activity.deleted <> 'T') AND "
                                     "(project_activity.id > 0)) AND "
                                     "(((project_project.deleted <> 'T') AND "
                                     "(project_project.id > 0)) AND "
                                     "(project_project.id = 1))) AND "
                                     "((project_activity.project_id = project_project.id) AND "
                                     "(project_activity.deleted <> 'T')))")

        self.assertEqual(rfilter.joins, Storage())
        self.assertEqual(rfilter.left, Storage())
        rows = component.select()

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("hrm"), "hrm module disabled")
    def testSimpleComponentFilterConstruction2(self):
        """ Test simple component filter construction (check query in resource) """

        resource = current.s3db.resource("pr_person",
                                         id=1,
                                         components=["competency"],
                                         filter=(S3FieldSelector("competency.id") == 1))

        component = resource.components["competency"]
        query = component.get_query()
        self.assertEqual(str(query), "((((hrm_competency.deleted <> 'T') AND "
                                     "(hrm_competency.id > 0)) AND "
                                     "((((pr_person.deleted <> 'T') AND "
                                     "(pr_person.id > 0)) AND "
                                     "(pr_person.id = 1)) AND "
                                     "(hrm_competency.id = 1))) AND "
                                     "((hrm_competency.person_id = pr_person.id) AND "
                                     "(hrm_competency.deleted <> 'T')))")

    # -------------------------------------------------------------------------
    def testAnyOf(self):
        """ Test filter construction with containment methods (contains vs anyof) """

        resource = current.s3db.resource("org_organisation")
        FS = S3FieldSelector
        q = FS("multi_sector_id").contains([1, 2])
        query = q.query(resource)
        self.assertEqual(str(query), "((org_organisation.multi_sector_id LIKE '%|1|%') AND "
                                     "(org_organisation.multi_sector_id LIKE '%|2|%'))")
        q = FS("multi_sector_id").anyof([1, 2])
        query = q.query(resource)
        self.assertEqual(str(query), "((org_organisation.multi_sector_id LIKE '%|1|%') OR "
                                     "(org_organisation.multi_sector_id LIKE '%|2|%'))")

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False

# =============================================================================
class URLQueryParserTests(unittest.TestCase):
    """ Test Parsing of URL queries """

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testParseURLQuery(self):
        """ Test standard URL query parsing """

        url_query = {"project.organisation_id$name__like": "*test*",
                     "task.description__like!": "*test*"}

        resource = current.s3db.resource("project_project", vars=url_query)
        rfilter = resource.rfilter

        # Check joins
        joins = rfilter.get_left_joins()
        self.assertNotEqual(joins, None)
        self.assertTrue(isinstance(joins, list))
        self.assertEqual(joins[0], "org_organisation ON "
                                   "(project_project.organisation_id = org_organisation.id)")
        self.assertEqual(joins[1], "project_task_project ON "
                                   "((project_task_project.project_id = project_project.id) AND "
                                   "(project_task_project.deleted <> 'T'))")
        self.assertEqual(joins[2], "project_task ON "
                                   "(project_task_project.task_id = project_task.id)")

        # Check query
        query = rfilter.get_query()
        self.assertEqual(str(query), "((((project_project.deleted <> 'T') AND "
                                     "(project_project.id > 0)) AND "
                                     "(LOWER(org_organisation.name) LIKE '%test%')) AND "
                                     "(NOT (LOWER(project_task.description) LIKE '%test%')))")

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testParseURLQueryWithAlternativeValues(self):
        """ Test URL query parsing with alternative values (OR) """

        url_query = {"project.organisation_id$name__like": "Test*,Other*"}

        resource = current.s3db.resource("project_project", vars=url_query)
        rfilter = resource.rfilter

        # Check joins
        joins = rfilter.get_left_joins()
        self.assertTrue(isinstance(joins, list))
        self.assertEqual(joins[0], "org_organisation ON "
                                   "(project_project.organisation_id = org_organisation.id)")

        # Check query
        query = rfilter.get_query()
        self.assertEqual(str(query), "(((project_project.deleted <> 'T') AND "
                                     "(project_project.id > 0)) AND "
                                     "((LOWER(org_organisation.name) LIKE 'test%') OR "
                                     "(LOWER(org_organisation.name) LIKE 'other%')))")

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testParseURLQueryWithAlternativeSelectors(self):
        """ Test alternative selectors (OR) in a URL query """

        url_query = {"project.organisation_id$name|task.description__like": "Test*"}

        resource = current.s3db.resource("project_project", vars=url_query)
        rfilter = resource.rfilter

        # Check joins
        joins = rfilter.get_left_joins()
        self.assertTrue(isinstance(joins, list))

        self.assertEqual(joins[0], "org_organisation ON "
                                   "(project_project.organisation_id = org_organisation.id)")
        self.assertEqual(joins[1], "project_task_project ON "
                                   "((project_task_project.project_id = project_project.id) AND "
                                   "(project_task_project.deleted <> 'T'))")
        self.assertEqual(joins[2], "project_task ON "
                                   "(project_task_project.task_id = project_task.id)")

        # Check the query
        query = rfilter.get_query()
        self.assertEqual(str(query), "(((project_project.deleted <> 'T') AND "
                                     "(project_project.id > 0)) AND "
                                     "((LOWER(org_organisation.name) LIKE 'test%') OR "
                                     "(LOWER(project_task.description) LIKE 'test%')))")

    # -------------------------------------------------------------------------
    def testParseValue(self):
        """ Test URL query value parser handling of NONE/None """

        parse_value = S3ResourceFilter._parse_value

        self.assertEqual(parse_value("NONE"), None)
        self.assertEqual(parse_value('"NONE"'), "NONE")
        self.assertEqual(parse_value("None"), None)
        self.assertEqual(parse_value('"None"'), "None")
        self.assertEqual(parse_value("NONE,1"), [None, "1"])
        self.assertEqual(parse_value('"NONE",1'), ["NONE", "1"])
        self.assertEqual(parse_value('"NONE,1"'), "NONE,1")

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.override = False

# =============================================================================
class URLQuerySerializerTests(unittest.TestCase):
    """ Test URL serialization of resource queries """

    # -------------------------------------------------------------------------
    def testSerializeURLQuerySimpleString(self):
        """ Simple string comparison serialization """

        FS = S3FieldSelector
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

        FS = S3FieldSelector
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

        FS = S3FieldSelector
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

        FS = S3FieldSelector
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

        FS = S3FieldSelector
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

        FS = S3FieldSelector
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

        FS = S3FieldSelector
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

        FS = S3FieldSelector
        q = FS("first_name").like(["Test%", "Other%"])

        resource = current.s3db.resource("pr_person")
        u = q.serialize_url(resource=resource)
        k = "person.first_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*,Other*")

    # -------------------------------------------------------------------------
    def testSerializeURLQueryListContainmentOperator(self):
        """ Wildcard string comparison serialization, alternative values, containment operator """

        FS = S3FieldSelector
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

        FS = S3FieldSelector
        q = FS("first_name").like(["Test%", "Other%"])
        resource.add_filter(q)

        rfilter = resource.rfilter
        u = rfilter.serialize_url()

        k = "person.first_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*,Other*")

# =============================================================================
class ResourceFieldTests(unittest.TestCase):
    """ Test field selector resolution with S3ResourceField """

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testResolveSelectorInnerField(self):
        """ Resolution of a selector for a field in master table """

        resource = current.s3db.resource("project_project")
        selector = "name"

        f = S3ResourceField(resource, selector)
        self.assertNotEqual(f, None)

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

        resource = current.s3db.resource("pr_person")
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
        self.assertEqual(str(f.left["pr_identity"][0]), "pr_identity ON "
                                                        "((pr_identity.person_id = pr_person.id) AND "
                                                        "(pr_identity.deleted <> 'T'))")
        self.assertEqual(str(f.join["pr_identity"]), "((pr_identity.person_id = pr_person.id) AND "
                                                     "(pr_identity.deleted <> 'T'))")

        # Check distinct
        self.assertTrue(f.distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testResolveSelectorLinkedTableField(self):
        """ Resolution of a selector for a field in a link-table component """

        resource = current.s3db.resource("project_project")
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
        self.assertEqual(str(f.left["project_task"][0]), "project_task_project ON "
                                                         "((project_task_project.project_id = project_project.id) AND "
                                                         "(project_task_project.deleted <> 'T'))")
        self.assertEqual(str(f.left["project_task"][1]), "project_task ON "
                                                         "(project_task_project.task_id = project_task.id)")
        self.assertEqual(str(f.join["project_task"]), "((project_task_project.deleted <> 'T') AND "
                                                      "((project_task_project.project_id = project_project.id) AND "
                                                      "(project_task_project.task_id = project_task.id)))")

        # Check distinct
        self.assertTrue(f.distinct)

    # -------------------------------------------------------------------------
    @unittest.skipIf(not current.deployment_settings.has_module("project"), "project module disabled")
    def testResolveSelectorReferencedTableField(self):
        """ Resolution of a selector for a field in a referenced table """

        resource = current.s3db.resource("project_project")
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
        self.assertEqual(str(f.left["org_organisation"][0]), "org_organisation ON "
                                                             "(project_project.organisation_id = org_organisation.id)")
        self.assertEqual(str(f.join["org_organisation"]), "(project_project.organisation_id = org_organisation.id)")

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

        from lxml import etree
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = s3db.resource("org_organisation")
        resource.import_xml(xmltree)

    # -------------------------------------------------------------------------
    def testResourceFieldExtract(self):
        """ Test value extraction from rows by S3ResourceFields """

        s3db = current.s3db

        resource = s3db.resource("org_organisation",
                                 uid="DATESTORG")

        rows = resource.select(["name", "office.name"], start=0, limit=1)
        self.assertEqual(len(rows), 1)
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
        """ Test correct handling of ambiguous rows in extract() """

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

        resource = s3db.resource("org_organisation")
        list_fields = ["name", "office.name"]
        lfields = resource.resolve_selectors(list_fields,
                                             skip_components=False)[0]
        collapsed = resource.extract(rows, lfields)
        self.assertEqual(len(collapsed), 1)

        office_names = collapsed[0]["org_office.name"]
        self.assertTrue(isinstance(office_names, list))
        self.assertEqual(len(office_names), 2)
        self.assertTrue("DATestOffice1" in office_names)
        self.assertTrue("DATestOffice2" in office_names)

        collapsed = resource.extract(rows, lfields, represent=True)
        self.assertEqual(len(collapsed), 1)

        office_names = collapsed[0]["org_office.name"]
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
        query = (S3FieldSelector("office.name").like("DATestOffice%"))

        # load() should not load any duplicate rows
        resource = s3db.resource("org_organisation")
        resource.add_filter(query)
        resource.load()
        self.assertEqual(len(resource), 1)
        self.assertEqual(len(resource._rows), 1)
        self.assertEqual(resource._length, 1)

        # Try the same with an additional virtual field filter:
        query = query & (S3FieldSelector("testfield") == "TEST")

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
        query = (S3FieldSelector("office.name").like("DATestOffice%"))

        # load() should not load any duplicate rows
        resource = s3db.resource("org_organisation")
        resource.add_filter(query)
        uid = resource.get_uid()
        self.assertTrue(isinstance(uid, str))
        self.assertEqual(uid, "DATESTORG")

        # Try the same with an additional virtual field filter:
        query = query & (S3FieldSelector("testfield") == "TEST")

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
        query = (S3FieldSelector("office.name").like("DATestOffice%"))

        # count() should properly deduplicate the rows before counting them
        resource = s3db.resource("org_organisation")
        resource.add_filter(query)
        self.assertEqual(resource.count(), 1)

        # Try the same with an additional virtual field filter:
        query = query & (S3FieldSelector("testfield") == "TEST")

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
class ResourceExportTests(unittest.TestCase):
    """ Test XML export of resources """

    # -------------------------------------------------------------------------
    def testExportTree(self):
        """ Test export of a resource as element tree """

        xml = current.xml

        current.auth.override = True
        resource = current.s3db.resource("org_office", id=1)
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
        """ Text XML output with max bounds """

        xml = current.xml

        current.auth.override = True
        resource = current.s3db.resource("org_office", id=1)
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

        try:
            from lxml import etree
            xmltree = etree.ElementTree(etree.fromstring(xmlstr))
            resource = current.s3db.resource("hms_hospital")
            resource.import_xml(xmltree)

            resource = current.s3db.resource(resource,
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

        finally:
            current.db.rollback()

# =============================================================================
class ResourceImportTests(unittest.TestCase):
    """ Test XML imports into resources """

    @classmethod
    def setUpClass(cls):

        current.auth.override = True

    # -------------------------------------------------------------------------
    def testImportXML(self):
        """ Test JSON message after XML import """

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
            <data field="value">123456789</data>
        </resource>

    </resource>

</s3xml>"""

        from lxml import etree
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        current.auth.override = True

        resource = current.s3db.resource("pr_person")
        msg = resource.import_xml(xmltree)
        from gluon.contrib import simplejson as json
        msg = json.loads(msg)
        self.assertEqual(msg["status"], "success")
        self.assertEqual(msg["statuscode"], "200")
        self.assertEqual(msg["records"], 1)
        self.assertTrue("created" in msg)
        self.assertTrue(isinstance(msg["created"], list))
        self.assertTrue(len(msg["created"]) == 1)

    # -------------------------------------------------------------------------
    def testImportXMLWithMTime(self):
        """ Test mtime update in imports """

        manager = current.manager

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
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("hms_hospital")
        resource.import_xml(xmltree)
        self.assertEqual(current.xml.as_utc(resource.mtime),
                         current.xml.as_utc(datetime.datetime(2012, 4, 21, 0, 0, 0)))

    # -------------------------------------------------------------------------
    def testImportXMLWithoutMTime(self):
        """ Test mtime update in imports with no mtime given """

        manager = current.manager

        # If no mtime is given, resource.mtime should be set to current UTC
        xmlstr = """
<s3xml>
    <resource name="hms_hospital" uuid="MTIMETESTHOSPITAL3">
        <data field="name">MTimeTestHospital3</data>
    </resource>
</s3xml>"""

        from lxml import etree
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("hms_hospital")
        resource.import_xml(xmltree)
        # Can't compare with exactly utcnow as these would be milliseconds apart,
        # assume equal dates are sufficient for this test
        self.assertEqual(current.xml.as_utc(resource.mtime).date(),
                         current.xml.as_utc(datetime.datetime.utcnow()).date())

    # -------------------------------------------------------------------------
    def testImportXMLWithPartialMTime(self):
        """ Test mtime update in imports if mtime given in only some records """

        manager = current.manager

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
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("hms_hospital")
        resource.import_xml(xmltree)
        self.assertEqual(current.xml.as_utc(resource.mtime).date(),
                         current.xml.as_utc(datetime.datetime.utcnow()).date())

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        current.db.rollback()
        current.auth.override = False

# =============================================================================
class ResourceDataObjectAPITests(unittest.TestCase):
    """ Test the S3Resource Data Object API """

    # -------------------------------------------------------------------------
    def testLoadStatusIndication(self):
        """ Test load status indication by value of _rows """

        s3db = current.s3db

        # A newly created resource has _rows=None
        resource = s3db.resource("project_time")
        self.assertEqual(resource._rows, None)

        # After load(), this must always be a list
        resource.load()
        self.assertNotEqual(resource._rows, None)
        self.assertTrue(isinstance(resource._rows, list))

        # After clear(), this must be None again
        resource.clear()
        self.assertEqual(resource._rows, None)

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

        success = self.resource.merge(self.id1, self.id2)
        self.assertTrue(success)
        org1, org2 = self.get_records()

        self.assertNotEqual(org1, None)
        self.assertNotEqual(org2, None)

        self.assertFalse(org1.deleted)
        self.assertTrue(org2.deleted)
        self.assertEqual(str(self.id1), str(org2.deleted_rb))

        self.assertEqual(org1.name, "Merge Test Organisation")
        self.assertEqual(org1.acronym, "MTO")
        self.assertEqual(org1.country, "UK")
        self.assertEqual(org1.website, "http://www.example.org")

        self.assertEqual(org2.name, "Merger Test Organisation")
        self.assertEqual(org2.acronym, "MTOrg")
        self.assertEqual(org2.country, "US")
        self.assertEqual(org2.website, "http://www.example.com")

    # -------------------------------------------------------------------------
    def testMergeReplace(self):
        """ Test merge with replace"""

        success = self.resource.merge(self.id1, self.id2,
                                      replace = ["acronym", "website"])
        self.assertTrue(success)
        org1, org2 = self.get_records()

        self.assertNotEqual(org1, None)
        self.assertNotEqual(org2, None)

        self.assertFalse(org1.deleted)
        self.assertTrue(org2.deleted)
        self.assertEqual(str(self.id1), str(org2.deleted_rb))

        self.assertEqual(org1.name, "Merge Test Organisation")
        self.assertEqual(org1.acronym, "MTOrg")
        self.assertEqual(org1.country, "UK")
        self.assertEqual(org1.website, "http://www.example.com")

        self.assertEqual(org2.name, "Merger Test Organisation")
        self.assertEqual(org2.acronym, "MTOrg")
        self.assertEqual(org2.country, "US")
        self.assertEqual(org2.website, "http://www.example.com")

    # -------------------------------------------------------------------------
    def testMergeReplaceAndUpdate(self):
        """ Test merge with replace and Update"""

        success = self.resource.merge(self.id1, self.id2,
                                      replace = ["acronym"],
                                      update = Storage(website = "http://www.example.co.uk"))
        self.assertTrue(success)
        org1, org2 = self.get_records()

        self.assertNotEqual(org1, None)
        self.assertNotEqual(org2, None)

        self.assertFalse(org1.deleted)
        self.assertTrue(org2.deleted)
        self.assertEqual(str(self.id1), str(org2.deleted_rb))

        self.assertEqual(org1.name, "Merge Test Organisation")
        self.assertEqual(org1.acronym, "MTOrg")
        self.assertEqual(org1.country, "UK")
        self.assertEqual(org1.website, "http://www.example.co.uk")

        self.assertEqual(org2.name, "Merger Test Organisation")
        self.assertEqual(org2.acronym, "MTOrg")
        self.assertEqual(org2.country, "US")
        self.assertEqual(org2.website, "http://www.example.com")

    # -------------------------------------------------------------------------
    def testMergeLinkTable(self):
        """ Test merge of link table entries """

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        org1, org2 = self.get_records()

        org1_pe_id = s3db.pr_get_pe_id(org1)
        org2_pe_id = s3db.pr_get_pe_id(org2)

        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        branch1 = Storage(name="TestBranch1")
        branch1_id = otable.insert(**branch1)
        self.assertNotEqual(branch1_id, None)
        branch1.update(id=branch1_id)
        s3db.update_super(otable, branch1)
        branch1_pe_id = s3db.pr_get_pe_id(otable, branch1_id)
        self.assertNotEqual(branch1_pe_id, None)
        link1 = Storage(organisation_id=self.id1, branch_id=branch1_id)
        link1_id = btable.insert(**link1)
        s3db.pr_update_affiliations(btable, link1_id)
        ancestors = s3db.pr_get_ancestors(branch1_pe_id)
        self.assertEqual(ancestors, [str(org1_pe_id)])

        branch2 = Storage(name="TestBranch2")
        branch2_id = otable.insert(**branch2)
        self.assertNotEqual(branch2_id, None)
        branch2.update(id=branch2_id)
        s3db.update_super(otable, branch2)
        branch2_pe_id = s3db.pr_get_pe_id("org_organisation", branch2_id)
        self.assertNotEqual(branch2_pe_id, None)
        link2 = Storage(organisation_id=self.id2, branch_id=branch2_id)
        link2_id = btable.insert(**link2)
        s3db.pr_update_affiliations(btable, link2_id)
        ancestors = s3db.pr_get_ancestors(branch2_pe_id)
        self.assertEqual(ancestors, [str(org2_pe_id)])

        success = self.resource.merge(self.id1, self.id2)
        self.assertTrue(success)

        link1 = db(btable._id == link1_id).select(limitby=(0, 1)).first()
        link2 = db(btable._id == link2_id).select(limitby=(0, 1)).first()

        self.assertEqual(str(link1.organisation_id), str(self.id1))
        self.assertEqual(str(link2.organisation_id), str(self.id1))

        ancestors = s3db.pr_get_ancestors(branch1_pe_id)
        self.assertEqual(ancestors, [str(org1_pe_id)])

        ancestors = s3db.pr_get_ancestors(branch2_pe_id)
        self.assertEqual(ancestors, [str(org1_pe_id)])

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

        org1, org2 = self.get_records()

        s3db = current.s3db
        org1_pe_id = s3db.pr_get_pe_id(org1)
        org2_pe_id = s3db.pr_get_pe_id(org2)

        person = Storage(first_name="Nxthga",
                         realm_entity=org2_pe_id)
        ptable = s3db.pr_person
        person_id = ptable.insert(**person)

        person = ptable[person_id]
        self.assertEqual(person.realm_entity, org2_pe_id)

        success = self.resource.merge(self.id1, self.id2)
        self.assertTrue(success)

        person = ptable[person_id]
        self.assertEqual(person.realm_entity, org1_pe_id)

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

        auth.override = False
        auth.s3_impersonate(None)
        self.assertRaises(current.auth.permission.error,
                          self.resource.merge, self.id1, self.id2)
        # Check for proper rollback
        ptable = s3db.pr_person
        query = ptable._id.belongs((self.id1, self.id2))
        rows = db(query).select(ptable._id, limitby=(0, 2))
        self.assertEqual(len(rows), 0)
        current.auth.override = True

    # -------------------------------------------------------------------------
    def testOriginalNotFoundError(self):
        """ Check for exception if record not found """
        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        self.assertRaises(KeyError, self.resource.merge, 0, self.id2)
        # Check for proper rollback
        ptable = s3db.pr_person
        query = ptable._id.belongs((self.id1, self.id2))
        rows = db(query).select(ptable._id, limitby=(0, 2))
        self.assertEqual(len(rows), 0)

    # -------------------------------------------------------------------------
    def testNotDuplicateFoundError(self):
        """ Check for exception if record not found """
        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        self.assertRaises(KeyError, self.resource.merge, self.id1, 0)
        # Check for proper rollback
        ptable = s3db.pr_person
        query = ptable._id.belongs((self.id1, self.id2))
        rows = db(query).select(ptable._id, limitby=(0, 2))
        self.assertEqual(len(rows), 0)

    # -------------------------------------------------------------------------
    def testMerge(self):
        """ Test merge """

        # Merge records
        success = self.resource.merge(self.id1, self.id2)
        self.assertTrue(success)

        # Check the merged records
        person1, person2 = self.get_records()
        self.assertNotEqual(person1, None)
        self.assertNotEqual(person2, None)

        # Check deleted status
        self.assertFalse(person1.deleted)
        self.assertTrue(person2.deleted)
        self.assertEqual(str(self.id1), str(person2.deleted_rb))

        # Check values
        self.assertEqual(person1.first_name, "Test")
        self.assertEqual(person1.last_name, "Person")

        self.assertEqual(person2.first_name, "Test")
        self.assertEqual(person2.last_name, "Person")

    # -------------------------------------------------------------------------
    def testMergeWithUpdate(self):
        """ Test merge with update """

        success = self.resource.merge(self.id1, self.id2,
                                      update = Storage(first_name = "Changed"))
        self.assertTrue(success)
        person1, person2 = self.get_records()

        self.assertNotEqual(person1, None)
        self.assertNotEqual(person2, None)

        self.assertFalse(person1.deleted)
        self.assertTrue(person2.deleted)
        self.assertEqual(str(self.id1), str(person2.deleted_rb))

        self.assertEqual(person1.first_name, "Changed")
        self.assertEqual(person1.last_name, "Person")

        self.assertEqual(person2.first_name, "Test")
        self.assertEqual(person2.last_name, "Person")

    # -------------------------------------------------------------------------
    def testMergeSingleComponent(self):
        """ Test merge of single-component """

        db = current.db
        auth = current.auth
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

        self.assertTrue(success)

        pd1 = db(dtable._id == pd1_id).select(limitby=(0, 1)).first()
        self.assertNotEqual(pd1, None)
        self.assertFalse(pd1.deleted)
        self.assertEqual(pd1.blood_type, "B-")
        self.assertEqual(pd1.pe_id, person1.pe_id)

        pd2 = db(dtable._id == pd2_id).select(limitby=(0, 1)).first()
        self.assertNotEqual(pd2, None)
        self.assertTrue(pd2.deleted)
        self.assertEqual(str(pd2.deleted_rb), str(pd1.id))

    # -------------------------------------------------------------------------
    def testMergeMultiComponent(self):
        """ Test merge of multiple-component """

        db = current.db
        auth = current.auth
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
        self.assertTrue(success)

        id1 = db(itable._id == id1_id).select(limitby=(0, 1)).first()
        self.assertNotEqual(id1, None)
        self.assertFalse(id1.deleted)
        self.assertEqual(id1.person_id, self.id1)

        id2 = db(itable._id == id2_id).select(limitby=(0, 1)).first()
        self.assertNotEqual(id2, None)
        self.assertFalse(id2.deleted)
        self.assertEqual(id2.person_id, self.id1)

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

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        auth.override = True

        ltable = s3db.gis_location

        location1 = Storage(name="TestLocation")
        location1_id = ltable.insert(**location1)
        location1.update(id=location1_id)
        s3db.update_super(ltable, location1)

        location2 = Storage(name="TestLocation")
        location2_id = ltable.insert(**location2)
        location2.update(id=location2_id)
        s3db.update_super(ltable, location2)

        self.id1 = location1_id
        self.id2 = location2_id

        self.resource = s3db.resource("gis_location")

    # -------------------------------------------------------------------------
    def testMerge(self):
        """ Test merge """

        success = self.resource.merge(self.id1, self.id2)
        self.assertTrue(success)
        location1, location2 = self.get_records()

        self.assertNotEqual(location1, None)
        self.assertNotEqual(location2, None)

        self.assertFalse(location1.deleted)
        self.assertTrue(location2.deleted)
        self.assertEqual(str(self.id1), str(location2.deleted_rb))

        self.assertEqual(location1.name, "TestLocation")
        self.assertEqual(location2.name, "TestLocation")

    # -------------------------------------------------------------------------
    def testMergeSimpleReference(self):
        """ Test merge of a simple reference including super-entity """

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
        self.assertTrue(success)

        # Check the location_id in office is now location 1
        office = db(otable._id == office.id).select(limitby=(0, 1)).first()
        self.assertNotEqual(office, None)
        self.assertEqual(office.location_id, self.id1)

        # Check the location_id in the org_site super record is also location 1
        stable = s3db.org_site
        site = db(stable.site_id == office.site_id).select(limitby=(0, 1)).first()
        self.assertNotEqual(site, None)
        self.assertEqual(site.location_id, self.id1)

    # -------------------------------------------------------------------------
    def testMergeReferenceLists(self):
        """ Test merge of a list of references """

        db = current.db
        auth = current.auth
        s3db = current.s3db
        deployment_settings = current.deployment_settings

        ptable = s3db.project_project
        project = Storage(name="Test Project",
                          countries_id=[self.id1, self.id2])
        project_id = ptable.insert(**project)
        project.update(id=project_id)
        s3db.update_super(ptable, project)

        # Merge location 2 into 1
        success = self.resource.merge(self.id1, self.id2)
        self.assertTrue(success)

        project = db(ptable.id == project_id).select(limitby=(0, 1)).first()
        self.assertNotEqual(project, None)

        self.assertEqual(project.countries_id, [self.id1])

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

        from lxml import etree
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))
        resource = current.s3db.resource("org_organisation")
        resource.import_xml(xmltree)

    # -------------------------------------------------------------------------
    def setUp(self):

        otable = current.s3db.org_organisation
        row = current.db(otable.uuid == "GETTESTORG").select(otable.id,
                                                            limitby=(0, 1)).first()
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

        resource = current.s3db.resource("org_organisation",
                                         uid="GETTESTORG")
        record = resource.get(self.org_id)
        self.assertNotEqual(record, None)

        self.assertTrue(isinstance(record, Row))
        self.assertEqual(record.id, self.org_id)
        self.assertEqual(record.uuid, "GETTESTORG")
        self.assertEqual(record.name, "GetTestOrg")

    # -------------------------------------------------------------------------
    def testGetMasterFail(self):
        """ get() with an ID raises a KeyError, if not accessible """

        resource = current.s3db.resource("org_organisation",
                                         uid="OTHERTESTORG")
        self.assertRaises(KeyError, resource.get, self.org_id)

    # -------------------------------------------------------------------------
    def testGetComponent(self):
        """ get() with ID and component alias returns the components records """

        resource = current.s3db.resource("org_organisation",
                                         uid="GETTESTORG")
        records = resource.get(self.org_id, "office")
        self.assertNotEqual(records, None)

        self.assertTrue(len(records), 1)
        record = records[0]
        self.assertTrue(isinstance(record, Row))
        self.assertEqual(record.organisation_id, self.org_id)
        self.assertEqual(record.uuid, "GETTESTOFFICE")
        self.assertEqual(record.name, "GetTestOffice")

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        current.db.rollback()
        current.auth.override = False

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
        ComponentJoinConstructionTests,
        ComponentLeftJoinConstructionTests,

        FieldSelectorResolutionTests,

        ResourceFilterJoinTests,
        ResourceFilterQueryTests,

        URLQueryParserTests,

        URLQuerySerializerTests,
        URLFilterSerializerTests,

        ResourceFieldTests,

        ResourceDataObjectAPITests,

        ResourceDataAccessTests,
        ResourceGetTests,
        #ResourceInsertTest,
        #ResourceSelectTests,
        #ResourceUpdateTests,
        #ResourceDeleteTests,

        #ResourceApproveTests,
        #ResourceRejectTests,

        #ResourceMergeTests,
        MergeOrganisationsTests,
        MergePersonsTests,
        MergeLocationsTests,

        ResourceExportTests,
        ResourceImportTests,
    )

# END ========================================================================
