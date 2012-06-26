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

        url_query = {"project.organisation_id$name__like": "*test*",
                     "task.description__like!": "*test*"}

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

        url_query = {"project.organisation_id$name__like": "Test*,Other*"}

        resource = s3mgr.define_resource("project", "project", vars=url_query)

        rfilter = resource.rfilter
        fjoins = rfilter.get_left_joins()
        self.assertNotEqual(fjoins, None)
        self.assertTrue(isinstance(fjoins, list))
        self.assertEqual(fjoins[0], "org_organisation ON "
                                    "(project_project.organisation_id = org_organisation.id)")

        query = rfilter.get_query()
        self.assertEqual(str(query), "(((project_project.deleted <> 'T') AND "
                                     "(project_project.id > 0)) AND "
                                     "((LOWER(org_organisation.name) LIKE 'test%') OR "
                                     "(LOWER(org_organisation.name) LIKE 'other%')))")

    def testParseURLQueryWithAlternativeSelectors(self):

        url_query = {"project.organisation_id$name|task.description__like": "Test*"}

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
        self.assertEqual(str(query), "(((project_project.deleted <> 'T') AND "
                                     "(project_project.id > 0)) AND "
                                     "((LOWER(org_organisation.name) LIKE 'test%') OR "
                                     "(LOWER(project_task.description) LIKE 'test%')))")

    def testSerializeURLQuery(self):

        FS = s3base.S3FieldSelector

        #q = FS("person.date_of_birth") <= datetime.date(2012, 4, 1)

        #u = q.serialize_url()
        #k = "person.date_of_birth__le"
        #self.assertNotEqual(u, None)
        #self.assertTrue(isinstance(u, Storage))
        #self.assertTrue(k in u)
        #self.assertEqual(len(u.keys()), 1)
        #self.assertEqual(u[k], "2012-04-01")

        q = FS("person.first_name") == "Test"

        u = q.serialize_url()
        k = "person.first_name"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test")

        q = FS("person.first_name").lower().like("Test%")

        u = q.serialize_url()
        k = "person.first_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*")

        q = (FS("person.first_name").lower().like("Test%")) | \
            (FS("person.last_name").lower().like("Test%"))

        u = q.serialize_url()
        k = "person.first_name|person.last_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*")

        q = (FS("person.first_name").lower().like("Test%")) | \
            (FS("person.last_name").lower().like("Other%"))

        u = q.serialize_url()
        k = "person.first_name|person.last_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertFalse(k in u)

        q = (FS("person.first_name").lower().like("Test%")) | \
            (~(FS("person.last_name").lower().like("Test%")))

        u = q.serialize_url()
        k = "person.first_name|person.last_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertFalse(k in u)

        q = (~(FS("person.first_name").lower().like("Test%"))) | \
            (~(FS("person.last_name").lower().like("Test%")))

        u = q.serialize_url()
        k = "person.first_name|person.last_name__like!"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*")

        q = (FS("person.first_name").lower().like("Test%")) | \
            (FS("person.first_name").lower().like("Other%"))

        u = q.serialize_url()
        k = "person.first_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*,Other*")

        q = FS("person.first_name").belongs(["Test", "Other"])

        u = q.serialize_url()
        k = "person.first_name__belongs"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test,Other")

        q = FS("first_name").like(["Test%", "Other%"])

        resource = s3mgr.define_resource("pr", "person")
        u = q.serialize_url(resource=resource)
        k = "person.first_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*,Other*")

    def testSerializeResourceFilterURL(self):

        url_query = {"project.organisation_id$name__like": "*test*",
                     "task.description__like!": "*test*"}

        resource = s3mgr.define_resource("project", "project", vars=url_query)
        rfilter = resource.rfilter
        url_vars = rfilter.serialize_url()
        self.assertEqual(len(url_vars), len(url_query))
        for k in url_query:
            self.assertTrue(k in url_vars)
            self.assertEqual(url_vars[k], url_query[k])

        FS = s3base.S3FieldSelector
        q = FS("first_name").like(["Test%", "Other%"])
        resource = s3mgr.define_resource("pr", "person")
        resource.add_filter(q)
        rfilter = resource.rfilter
        u = rfilter.serialize_url()
        k = "person.first_name__like"
        self.assertNotEqual(u, None)
        self.assertTrue(isinstance(u, Storage))
        self.assertTrue(k in u)
        self.assertEqual(len(u.keys()), 1)
        self.assertEqual(u[k], "Test*,Other*")

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
class S3MergeOrganisationsTests(unittest.TestCase):

    def setUp(self):
        """ Set up organisation records """

        auth.override = True

        otable = s3db.org_organisation

        org1 = Storage(name="Merge Test Organisation",
                       acronym="MTO",
                       country="UK",
                       website="http://www.example.org")
        org1_id = otable.insert(**org1)
        org1.update(id=org1_id)
        s3mgr.model.update_super(otable, org1)

        org2 = Storage(name="Merger Test Organisation",
                       acronym="MTOrg",
                       country="US",
                       website="http://www.example.com")
        org2_id = otable.insert(**org2)
        org2.update(id=org2_id)
        s3mgr.model.update_super(otable, org2)

        self.id1 = org1_id
        self.id2 = org2_id

        self.resource = s3mgr.define_resource("org", "organisation")

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

    def testMergeLinkTable(self):
        """ Test merge of link table entries """

        org1, org2 = self.get_records()

        org1_pe_id = s3db.pr_get_pe_id(org1)
        org2_pe_id = s3db.pr_get_pe_id(org2)

        otable = s3db.org_organisation
        btable = s3db.org_organisation_branch

        branch1 = Storage(name="TestBranch1")
        branch1_id = otable.insert(**branch1)
        self.assertNotEqual(branch1_id, None)
        branch1.update(id=branch1_id)
        s3mgr.model.update_super(otable, branch1)
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
        s3mgr.model.update_super(otable, branch2)
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

    def testMergeVirtualReference(self):
        """ Test merge with virtual references """

        utable = auth.settings.table_user
        user = Storage(first_name="Test",
                       last_name="User",
                       password="xyz",
                       email="testuser@example.com",
                       organisation_id=self.id2)
        user_id = utable.insert(**user)

        success = self.resource.merge(self.id1, self.id2)
        self.assertTrue(success)

        user = db(utable.id == user_id).select(limitby=(0, 1)).first()
        self.assertNotEqual(user, None)

        self.assertEqual(str(user.organisation_id), str(self.id1))

    def get_records(self):

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

    def tearDown(self):

        db.rollback()
        auth.override = False

# =============================================================================
class S3MergePersonsTests(unittest.TestCase):

    def setUp(self):
        """ Set up person records """

        auth.override = True

        ptable = s3db.pr_person

        person1 = Storage(first_name="Test",
                          last_name="Person")
        person1_id = ptable.insert(**person1)
        person1.update(id=person1_id)
        s3mgr.model.update_super(ptable, person1)

        person2 = Storage(first_name="Test",
                          last_name="Person")
        person2_id = ptable.insert(**person2)
        person2.update(id=person2_id)
        s3mgr.model.update_super(ptable, person2)

        self.id1 = person1_id
        self.id2 = person2_id

        self.resource = s3mgr.define_resource("pr", "person")

    def testMerge(self):
        """ Test merge """

        # Must raise exception if not authorized
        auth.override = False
        auth.s3_impersonate(None)
        self.assertRaises(auth.permission.error,
                          self.resource.merge, self.id1, self.id2)

        # Must raise exception for non-existent records
        auth.override = True
        self.assertRaises(KeyError, self.resource.merge, 0, self.id2)
        self.assertRaises(KeyError, self.resource.merge, self.id1, 0)

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

    def testMergeSingleComponent(self):
        """ Test merge of single-component """

        person1, person2 = self.get_records()

        dtable = s3db.pr_physical_description

        pd1 = Storage(pe_id=person1.pe_id,
                      blood_type="B+")
        pd1_id = dtable.insert(**pd1)
        pd1.update(id=pd1_id)
        s3mgr.model.update_super(dtable, pd1)

        pd2 = Storage(pe_id=person2.pe_id,
                      blood_type="B-")
        pd2_id = dtable.insert(**pd2)
        pd2.update(id=pd2_id)
        s3mgr.model.update_super(dtable, pd2)

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

    def testMergeMultiComponent(self):
        """ Test merge of multiple-component """

        person1, person2 = self.get_records()

        itable = s3db.pr_identity

        id1 = Storage(person_id=person1.id,
                      type=1,
                      value="TEST1")
        id1_id = itable.insert(**id1)
        id1.update(id=id1_id)
        s3mgr.model.update_super(itable, id1)

        id2 = Storage(person_id=person2.id,
                      type=1,
                      value="TEST2")
        id2_id = itable.insert(**id2)
        id2.update(id=id2_id)
        s3mgr.model.update_super(itable, id2)

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

    def get_records(self):

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

    def tearDown(self):

        db.rollback()
        auth.override = False

# =============================================================================
class S3MergeLocationsTests(unittest.TestCase):

    def setUp(self):
        """ Set up location records """

        auth.override = True

        ltable = s3db.gis_location

        location1 = Storage(name="TestLocation")
        location1_id = ltable.insert(**location1)
        location1.update(id=location1_id)
        s3mgr.model.update_super(ltable, location1)

        location2 = Storage(name="TestLocation")
        location2_id = ltable.insert(**location2)
        location2.update(id=location2_id)
        s3mgr.model.update_super(ltable, location2)

        self.id1 = location1_id
        self.id2 = location2_id

        self.resource = s3mgr.define_resource("gis", "location")

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

    def testMergeSimpleReference(self):
        """ Test merge of a simple reference including super-entity """

        # Create an office referencing location 2
        otable = s3db.org_office
        office = Storage(name="Test Office",
                         location_id = self.id2)
        office_id = otable.insert(**office)
        office.update(id=office_id)
        s3mgr.model.update_super(otable, office)

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

    def testMergeReferenceLists(self):

        ptable = s3db.project_project
        project = Storage(name="Test Project",
                          countries_id=[self.id1, self.id2])
        project_id = ptable.insert(**project)
        project.update(id=project_id)
        s3mgr.model.update_super(ptable, project)

        # Merge location 2 into 1
        success = self.resource.merge(self.id1, self.id2)
        self.assertTrue(success)

        project = db(ptable.id == project_id).select(limitby=(0, 1)).first()
        self.assertNotEqual(project, None)

        self.assertEqual(project.countries_id, [self.id1])

    #def testMergeLocationHierarchy(self):
        #""" Test update of the location hierarchy when merging locations """
        #pass

    #def testMergeDeduplicateComponents(self):
        #""" Test merged components deduplication """
        ## Test by gis_location_tags
        #pass

    def get_records(self):

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

    def tearDown(self):

        db.rollback()
        auth.override = False

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
        S3MergeOrganisationsTests,
        S3MergePersonsTests,
        S3MergeLocationsTests,
    )

# END ========================================================================
