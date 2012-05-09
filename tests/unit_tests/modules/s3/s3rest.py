# -*- coding: utf-8 -*-
#
# REST Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3rest.py
#
import unittest
from gluon.dal import Query

# =============================================================================
class Test_s3mgr_raises_on_nonexistent_modules(unittest.TestCase):
    """ Legacy Test Case """

    def test(test):
        test.assertRaises(Exception, s3mgr.load, "something that doesn't exist")

# =============================================================================
class S3ResourceTests(unittest.TestCase):

    def setUp(self):
        pass

    # -------------------------------------------------------------------------
    # Component Joins Construction
    #
    def testGetJoinSimpleComponent(self):

        resource = s3mgr.define_resource("pr", "person")
        # Master resource has no component join
        self.assertEqual(resource.get_join(), None)
        component = resource.components["identity"]
        ijoin = component.get_join()
        self.assertEqual(str(ijoin), "((pr_identity.person_id = pr_person.id) AND "
                                     "(pr_identity.deleted <> 'T'))")

    def testGetJoinSuperComponent(self):

        resource = s3mgr.define_resource("pr", "person")
        component = resource.components["contact"]
        ijoin = component.get_join()
        self.assertEqual(str(ijoin), "((pr_person.pe_id = pr_contact.pe_id) AND "
                                     "(pr_contact.deleted <> 'T'))")

    def testGetJoinLinkTableComponent(self):

        resource = s3mgr.define_resource("project", "project")
        component = resource.components["task"]
        ijoin = component.get_join()
        self.assertEqual(str(ijoin),
                         "((project_task_project.deleted <> 'T') AND "
                         "((project_task_project.project_id = project_project.id) AND "
                         "(project_task_project.task_id = project_task.id)))")

    def testGetLeftJoinSimpleComponent(self):

        resource = s3mgr.define_resource("pr", "person")
        # Master Resource has no join!
        self.assertEqual(resource.get_left_join(), None)
        component = resource.components["identity"]
        ljoin = component.get_left_join()
        self.assertTrue(isinstance(ljoin, list))
        self.assertEqual(len(ljoin), 1)
        self.assertEqual(str(ljoin[0]), "pr_identity ON "
                                        "((pr_identity.person_id = pr_person.id) AND "
                                        "(pr_identity.deleted <> 'T'))")

    def testGetLeftJoinSuperComponent(self):

        resource = s3mgr.define_resource("pr", "person")
        component = resource.components["contact"]
        ljoin = component.get_left_join()
        self.assertTrue(isinstance(ljoin, list))
        self.assertEqual(len(ljoin), 1)
        self.assertEqual(str(ljoin[0]), "pr_contact ON "
                                        "((pr_person.pe_id = pr_contact.pe_id) AND "
                                        "(pr_contact.deleted <> 'T'))")

    def testGetLeftJoinLinkTableComponent(self):

        resource = s3mgr.define_resource("project", "project")
        component = resource.components["task"]
        ljoin = component.get_left_join()
        self.assertTrue(isinstance(ljoin, list))
        self.assertEqual(len(ljoin), 2)
        self.assertEqual(str(ljoin[0]), "project_task_project ON "
                                        "((project_task_project.project_id = project_project.id) AND "
                                        "(project_task_project.deleted <> 'T'))")
        self.assertEqual(str(ljoin[1]), "project_task ON (project_task_project.task_id = project_task.id)")

    # -------------------------------------------------------------------------
    # Field Selector Resolution
    #
    def testResolveSelectorInnerField(self):

        resource = s3mgr.define_resource("project", "project")
        selector = "name"
        f = resource.resolve_selector(selector)
        self.assertNotEqual(f, None)
        self.assertTrue(isinstance(f, Storage))
        self.assertEqual(f.selector, selector)
        self.assertEqual(str(f.field), "project_project.name")
        self.assertEqual(str(f.tname), "project_project")
        self.assertEqual(str(f.fname), "name")
        self.assertEqual(str(f.colname), "project_project.name")
        self.assertEqual(f.join, Storage())
        self.assertEqual(f.left, Storage())
        self.assertFalse(f.distinct)

    def testResolveSelectorVirtualField(self):

        resource = s3mgr.define_resource("project", "project")
        selector = "virtual"
        f = resource.resolve_selector(selector)
        self.assertNotEqual(f, None)
        self.assertTrue(isinstance(f, Storage))
        self.assertEqual(f.selector, selector)
        self.assertEqual(f.field, None)
        self.assertEqual(str(f.tname), "project_project")
        self.assertEqual(str(f.fname), "virtual")
        self.assertEqual(str(f.colname), "project_project.virtual")
        self.assertEqual(f.join, Storage())
        self.assertEqual(f.left, Storage())
        self.assertFalse(f.distinct)

    def testResolveSelectorComponentField(self):

        resource = s3mgr.define_resource("pr", "person")
        selector = "identity.value"
        f = resource.resolve_selector(selector)
        self.assertNotEqual(f, None)
        self.assertTrue(isinstance(f, Storage))
        self.assertEqual(f.selector, selector)
        self.assertEqual(str(f.field), "pr_identity.value")
        self.assertEqual(str(f.tname), "pr_identity")
        self.assertEqual(str(f.fname), "value")
        self.assertEqual(str(f.colname), "pr_identity.value")
        self.assertTrue(isinstance(f.left["pr_identity"], list))
        self.assertEqual(len(f.left["pr_identity"]), 1)
        self.assertEqual(str(f.left["pr_identity"][0]), "pr_identity ON "
                                                        "((pr_identity.person_id = pr_person.id) AND "
                                                        "(pr_identity.deleted <> 'T'))")
        self.assertEqual(str(f.join["pr_identity"]), "((pr_identity.person_id = pr_person.id) AND "
                                                     "(pr_identity.deleted <> 'T'))")
        self.assertTrue(f.distinct) # Should be true as this is a multiple-component

    def testResolveSelectorLinkedTableField(self):

        resource = s3mgr.define_resource("project", "project")
        selector = "task.description"
        f = resource.resolve_selector(selector)
        self.assertNotEqual(f, None)
        self.assertTrue(isinstance(f, Storage))
        self.assertEqual(f.selector, selector)
        self.assertEqual(str(f.field), "project_task.description")
        self.assertEqual(str(f.tname), "project_task")
        self.assertEqual(str(f.fname), "description")
        self.assertEqual(str(f.colname), "project_task.description")
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
        self.assertTrue(f.distinct)

    def testResolveSelectorReferencedTableField(self):

        resource = s3mgr.define_resource("project", "project")
        selector = "organisation_id$name"
        f = resource.resolve_selector(selector)
        self.assertNotEqual(f, None)
        self.assertTrue(isinstance(f, Storage))
        self.assertEqual(f.selector, selector)
        self.assertEqual(str(f.field), "org_organisation.name")
        self.assertEqual(str(f.tname), "org_organisation")
        self.assertEqual(str(f.fname), "name")
        self.assertEqual(str(f.colname), "org_organisation.name")
        self.assertTrue(isinstance(f.left["org_organisation"], list))
        self.assertEqual(len(f.left["org_organisation"]), 1)
        self.assertEqual(str(f.left["org_organisation"][0]), "org_organisation ON "
                                                             "(project_project.organisation_id = org_organisation.id)")
        self.assertEqual(str(f.join["org_organisation"]), "(project_project.organisation_id = org_organisation.id)")
        self.assertTrue(f.distinct)

    def testResolveSelectorExceptions(self):

        resource = s3mgr.define_resource("project", "project")
        selector = "organisation_id.test"
        self.assertRaises(KeyError,
                          resource.resolve_selector,
                          selector)

    def testResolveSelectors(self):

        resource = s3mgr.define_resource("project", "project")
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

        fields, joins, left, distinct = resource.resolve_selectors(selectors,
                                                                   skip_components=False)
        self.assertEqual(len(fields), 4)
        self.assertEqual(fields[3].colname, "project_task.description")

        self.assertEqual(joins, Storage())

        self.assertTrue(isinstance(left, Storage))
        self.assertEqual(left.keys(), [ "org_organisation", "project_task"])
        self.assertEqual(len(left["project_task"]), 2)
        self.assertEqual(str(left["project_task"][0]), "project_task_project ON "
                                                       "((project_task_project.project_id = project_project.id) AND "
                                                       "(project_task_project.deleted <> 'T'))")
        self.assertEqual(str(left["project_task"][1]), "project_task ON "
                                                       "(project_task_project.task_id = project_task.id)")
        self.assertTrue(distinct)

# =============================================================================
class S3ResourceFilterTests(unittest.TestCase):

    def setUp(self):
        auth.s3_impersonate("admin@example.com")

    def testGetQueryJoinsInnerField(self):

        resource = s3mgr.define_resource("pr", "person")
        q = s3base.S3FieldSelector("first_name") == "test"

        joins, distinct = q.joins(resource)
        self.assertEqual(joins, Storage())
        self.assertFalse(distinct)

        joins, distinct = q.joins(resource, left=True)
        self.assertEqual(joins, Storage())
        self.assertFalse(distinct)

    def testGetQueryJoinsReferencedTableField(self):

        resource = s3mgr.define_resource("project", "project")
        q = s3base.S3FieldSelector("organisation_id$name") == "test"

        joins, distinct = q.joins(resource)
        self.assertEqual(joins, Storage())

        joins, distinct = q.joins(resource, left=True)
        self.assertTrue(isinstance(joins, Storage))
        self.assertEqual(joins.keys(), ["org_organisation"])
        self.assertTrue(isinstance(joins["org_organisation"], list))
        self.assertEqual(len(joins["org_organisation"]), 1)
        self.assertEqual(str(joins["org_organisation"][0]), "org_organisation ON "
                                                            "(project_project.organisation_id = org_organisation.id)")
        self.assertTrue(distinct)

    def testGetQueryJoinsComponentField(self):

        resource = s3mgr.define_resource("pr", "person")
        q = s3base.S3FieldSelector("identity.value") == "test"

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

    def testGetQueryJoinsSuperComponentField(self):

        resource = s3mgr.define_resource("pr", "person")
        q = s3base.S3FieldSelector("contact.value") == "test"

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

    def testGetQueryJoinsLinkedComponentField(self):

        resource = s3mgr.define_resource("project", "project")
        q = s3base.S3FieldSelector("task.description") == "test"

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

    def testGetQueryJoinsCombination(self):

        resource = s3mgr.define_resource("project", "project")
        q = (s3base.S3FieldSelector("organisation_id$name") == "test") & \
            (s3base.S3FieldSelector("task.description") == "test")

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

    def testResourceFilterConstruction(self):

        q = (s3base.S3FieldSelector("organisation_id$name") == "test") & \
            (s3base.S3FieldSelector("task.description") == "test")
        resource = s3mgr.define_resource("project", "project",
                                         filter=q)

        rfilter = resource.rfilter
        self.assertNotEqual(rfilter, None)

        # This will fail in 1st run as there is no ADMIN role yet
        self.assertEqual(str(rfilter.mquery), "((project_project.deleted <> 'T') AND "
                                              "(project_project.id > 0))")

        query = rfilter.get_query()
        self.assertEqual(str(query), "(((project_project.deleted <> 'T') AND "
                                     "(project_project.id > 0)) AND "
                                     "((org_organisation.name = 'test') AND "
                                     "(project_task.description = 'test')))")

        joins = rfilter.joins
        self.assertEqual(joins.keys(), [])

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

    def testComponentFilterConstruction1(self):

        q1 = (s3base.S3FieldSelector("organisation_id$name") == "test")
        q2 = (s3base.S3FieldSelector("task.description") == "test")
        resource = s3mgr.define_resource("project", "project", filter=q1)

        resource.add_filter(q2)

        component = resource.components["task"]
        component.build_query()
        rfilter = component.rfilter
        query = rfilter.get_query()
        # This will fail in 1st run as there is no ADMIN role yet
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
        rows = component.sqltable(as_rows=True)

    def testComponentFilterConstruction2(self):

        q1 = (s3base.S3FieldSelector("human_resource.organisation_id$name") == "test")
        q2 = (s3base.S3FieldSelector("identity.value") == "test")
        resource = s3mgr.define_resource("pr", "person", filter=q1)

        resource.add_filter(q2)

        component = resource.components["identity"]
        component.build_query()
        rfilter = component.rfilter
        query = rfilter.get_query()

        # This will fail in 1st run as there is no ADMIN role yet
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
        rows = component.sqltable(as_rows=True)

    def testComponentFilterConstruction3(self):

        resource = s3mgr.define_resource("project", "project", id=1)

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
        rows = component.sqltable(as_rows=True)

    def testComponentFilterConstruction4(self):

        resource = s3mgr.define_resource("pr", "person",
                                         id=1,
                                         components=["competency"],
                                         filter=(s3base.S3FieldSelector("competency.id") == 1))

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

    def testGetLeftJoins(self):

        q = (s3base.S3FieldSelector("organisation_id$name") == "test") & \
            (s3base.S3FieldSelector("task.description") == "test")
        resource = s3mgr.define_resource("project", "project", filter=q)

        fjoins = resource.rfilter.get_left_joins()
        self.assertNotEqual(fjoins, None)
        self.assertTrue(isinstance(fjoins, list))

        self.assertEqual(fjoins[0], "project_task_project ON "
                                    "((project_task_project.project_id = project_project.id) AND "
                                    "(project_task_project.deleted <> 'T'))")
        self.assertEqual(fjoins[1], "project_task ON "
                                    "(project_task_project.task_id = project_task.id)")

    def testParseURLQuery(self):

        url_query = {"project.organisation_id$name__like": "test",
                     "task.description__like!": "test"}

        resource = s3mgr.define_resource("project", "project", vars=url_query)

        rfilter = resource.rfilter
        fjoins = rfilter.get_left_joins()
        self.assertNotEqual(fjoins, None)
        self.assertTrue(isinstance(fjoins, list))
        self.assertEqual(fjoins[0], "org_organisation ON "
                                    "(project_project.organisation_id = org_organisation.id)")
        self.assertEqual(fjoins[1], "project_task_project ON "
                                    "((project_task_project.project_id = project_project.id) AND "
                                    "(project_task_project.deleted <> 'T'))")
        self.assertEqual(fjoins[2], "project_task ON "
                                    "(project_task_project.task_id = project_task.id)")

        query = rfilter.get_query()
        self.assertEqual(str(query), "((((project_project.deleted <> 'T') AND "
                                     "(project_project.id > 0)) AND "
                                     "(LOWER(org_organisation.name) LIKE '%test%')) AND "
                                     "(NOT (LOWER(project_task.description) LIKE '%test%')))")

    def testParseValue(self):

        parse_value = s3base.S3ResourceFilter._parse_value

        self.assertEqual(parse_value("NONE"), None)
        self.assertEqual(parse_value('"NONE"'), "NONE")
        self.assertEqual(parse_value("None"), None)
        self.assertEqual(parse_value('"None"'), "None")
        self.assertEqual(parse_value("NONE,1"), [None, "1"])
        self.assertEqual(parse_value('"NONE",1'), ["NONE", "1"])
        self.assertEqual(parse_value('"NONE,1"'), "NONE,1")

    def tearDown(self):
        auth.s3_impersonate(None)

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
        S3ResourceTests,
        S3ResourceFilterTests,
    )

# END ========================================================================
