# Eden Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/core/aaa/permission.py
#
import unittest
import re

from gluon import *
from gluon.storage import Storage
from core import S3Permission, MetaFields

from unit_tests import run_suite

# RE to handle IN-tuples in queries
QUERY_PATTERN = re.compile(r"(.*)( IN \(([0-9,]*)\))(.*)")

# =============================================================================
class PermissionFailureTests(unittest.TestCase):
    """ Test authorization failure for RFC1945/2617 compliance """

    def setUp(self):

        self.fmt = current.auth.permission.format

    def tearDown(self):

        auth = current.auth
        auth.s3_impersonate(None)
        auth.permission.format = self.fmt

    # -------------------------------------------------------------------------
    def testFailInterActive(self):

        auth = current.auth

        assertEqual = self.assertEqual
        assertIn = self.assertIn

        # Interactive => redirects to login page
        auth.permission.format = "html"
        auth.s3_impersonate(None)
        try:
            auth.permission.fail()
        except HTTP as e:
            assertEqual(e.status, 303)
            headers = e.headers
            assertIn("Location", headers)
            location = headers["Location"].split("?", 1)[0]
            assertEqual(location, URL(c="default",
                                      f="user",
                                      args=["login"]))
        else:
            raise AssertionError("No HTTP status raised")

    # -------------------------------------------------------------------------
    def testFailNonInteractiveAnonymous(self):

        auth = current.auth

        assertEqual = self.assertEqual
        assertIn = self.assertIn

        # Non-interactive => raises 401 including challenge
        auth.permission.format = "xml"
        auth.s3_impersonate(None)
        try:
            auth.permission.fail()
        except HTTP as e:
            assertEqual(e.status, 401)
            headers = e.headers
            assertIn("WWW-Authenticate", headers)
        else:
            raise AssertionError("No HTTP status raised")

    # -------------------------------------------------------------------------
    def testFailNonInteractiveAuthenticated(self):

        auth = current.auth

        # Non-interactive => raises 403 if logged in
        auth.permission.format = "xml"
        auth.s3_impersonate("admin@example.com")
        try:
            auth.permission.fail()
        except HTTP as e:
            self.assertEqual(e.status, 403)
            headers = e.headers
            # No Auth challenge with 403
            self.assertNotIn("WWW-Authenticate", headers)
        else:
            raise AssertionError("No HTTP status raised")

    # -------------------------------------------------------------------------
    def testFailNoChallenge(self):
        """ auth.s3_logged_in() MUST NOT raise a challenge """

        auth = current.auth

        msg = "s3_logged_in must not raise HTTP Auth challenge"

        auth.permission.format = "xml"
        auth.s3_impersonate(None)
        try:
            auth.s3_logged_in()
        except HTTP:
            raise AssertionError(msg)

        auth.permission.format = "html"
        auth.s3_impersonate(None)
        try:
            auth.s3_logged_in()
        except HTTP:
            raise AssertionError(msg)

# =============================================================================
class ACLManagementTests(unittest.TestCase):
    """ Test ACL management/lookup functions """

    def setUp(self):

        # Stash security policy
        self.policy = current.deployment_settings.get_security_policy()

    def tearDown(self):

        # Restore security policy
        current.deployment_settings.security.policy = self.policy

        # Restore permissions service
        auth = current.auth
        auth.permission = S3Permission(auth)

    # -------------------------------------------------------------------------
    def testRequiredACL(self):
        """ Test lambda to compute the required ACL """

        p = current.auth.permission
        assertEqual = self.assertEqual
        assertEqual(p.required_acl(["read"]), p.READ)
        assertEqual(p.required_acl(["create"]), p.CREATE)
        assertEqual(p.required_acl(["update"]), p.UPDATE)
        assertEqual(p.required_acl(["delete"]), p.DELETE)
        assertEqual(p.required_acl(["create", "update"]), p.CREATE | p.UPDATE)
        assertEqual(p.required_acl([]), p.NONE)
        assertEqual(p.required_acl(["invalid"]), p.NONE)

    # -------------------------------------------------------------------------
    def testMostPermissive(self):
        """ Test lambda to compute the most permissive ACL """

        p = current.auth.permission
        self.assertEqual(p.most_permissive([(p.NONE, p.READ),
                                            (p.READ, p.READ)]),
                                           (p.READ, p.READ))
        self.assertEqual(p.most_permissive([(p.NONE, p.ALL),
                                            (p.CREATE, p.ALL),
                                            (p.READ, p.ALL)]),
                                           (p.READ | p.CREATE, p.ALL))

    # -------------------------------------------------------------------------
    def testMostRestrictive(self):
        """ Test lambda to compute the most restrictive ACL """

        p = current.auth.permission
        self.assertEqual(p.most_restrictive([(p.NONE, p.READ),
                                             (p.READ, p.READ)]),
                                            (p.NONE, p.READ))
        self.assertEqual(p.most_restrictive([(p.CREATE, p.ALL),
                                             (p.READ, p.READ)]),
                                            (p.NONE, p.READ))

    # -------------------------------------------------------------------------
    def testUpdateControllerACL(self):
        """ Test update/delete of a controller ACL """

        auth = current.auth

        table = auth.permission.table
        self.assertNotEqual(table, None)

        group_id = auth.s3_create_role("Test Role", uid="TEST")
        acl_id = None

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        try:
            assertTrue(group_id is not None and group_id != 0)

            c = "pr"
            f = "person"
            uacl = auth.permission.NONE
            oacl = auth.permission.ALL


            acl_id = auth.permission.update_acl(group_id,
                                                c=c, f=f,
                                                uacl=uacl, oacl=oacl)
            assertNotEqual(acl_id, None)
            assertNotEqual(acl_id, 0)
            acl = table[acl_id]
            assertNotEqual(acl, None)
            assertEqual(acl.controller, c)
            assertEqual(acl.function, f)
            assertEqual(acl.tablename, None)
            assertEqual(acl.unrestricted, False)
            assertEqual(acl.entity, None)
            assertEqual(acl.uacl, uacl)
            assertEqual(acl.oacl, oacl)
            assertFalse(acl.deleted)

            success = auth.permission.delete_acl(group_id,
                                                 c=c, f=f)
            assertTrue(success is not None and success > 0)
            acl = table[acl_id]
            assertNotEqual(acl, None)
            assertTrue(acl.deleted)
            assertTrue(acl.deleted_fk, '{"group_id": %d}' % group_id)
        finally:
            if acl_id:
                del table[acl_id]
            auth.s3_delete_role(group_id)

    # -------------------------------------------------------------------------
    def testUpdateTableACL(self):
        """ Test update/delete of a table-ACL """

        auth = current.auth

        table = auth.permission.table
        self.assertNotEqual(table, None)

        group_id = auth.s3_create_role("Test Role", uid="TEST")
        acl_id = None

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        try:
            assertTrue(group_id is not None and group_id != 0)

            c = "pr"
            f = "person"
            t = "pr_person"
            uacl = auth.permission.NONE
            oacl = auth.permission.ALL


            acl_id = auth.permission.update_acl(group_id,
                                                c=c, f=f, t=t,
                                                uacl=uacl, oacl=oacl)
            assertNotEqual(acl_id, None)
            assertNotEqual(acl_id, 0)
            acl = table[acl_id]
            assertNotEqual(acl, None)
            assertEqual(acl.controller, None)
            assertEqual(acl.function, None)
            assertEqual(acl.tablename, t)
            assertEqual(acl.unrestricted, False)
            assertEqual(acl.entity, None)
            assertEqual(acl.uacl, uacl)
            assertEqual(acl.oacl, oacl)
            assertFalse(acl.deleted)

            success = auth.permission.delete_acl(group_id,
                                                 c=c, f=f, t=t)
            assertTrue(success is not None and success > 0)
            acl = table[acl_id]
            assertNotEqual(acl, None)
            assertTrue(acl.deleted)
            assertTrue(acl.deleted_fk, '{"group_id": %d}' % group_id)
        finally:
            if acl_id:
                del table[acl_id]
            auth.s3_delete_role(group_id)

# =============================================================================
class HasPermissionTests(unittest.TestCase):
    """ Test permission check method """

    @classmethod
    def setUpClass(cls):

        # Create test table
        db = current.db
        tablename = "org_permission_test"
        db.define_table(tablename,
                        Field("name"),
                        *MetaFields())

        # Create test roles and ACLs
        auth = current.auth
        acl = auth.permission

        READ = acl.READ
        CREATE = acl.READ|acl.CREATE
        UPDATE = acl.READ|acl.UPDATE
        WRITE = acl.READ|acl.CREATE|acl.UPDATE
        ALL = acl.ALL

        TESTREADER = "TESTREADER"
        auth.s3_create_role(TESTREADER, None,
                            dict(c="org",
                                 uacl=READ, oacl=UPDATE),
                            dict(c="org", f="permission_test",
                                 uacl=CREATE, oacl=UPDATE),
                            dict(t="org_permission_test",
                                 uacl=WRITE, oacl=UPDATE),
                            uid=TESTREADER)

        TESTEDITOR = "TESTEDITOR"
        auth.s3_create_role(TESTEDITOR, None,
                            dict(c="org",
                                 uacl=WRITE, oacl=UPDATE),
                            dict(c="org", f="permission_test",
                                 uacl=WRITE, oacl=UPDATE),
                            dict(t="org_permission_test",
                                 uacl=WRITE, oacl=UPDATE),
                            uid=TESTEDITOR)

        TESTADMIN = "TESTADMIN"
        auth.s3_create_role(TESTADMIN, None,
                            dict(c="org",
                                 uacl=ALL, oacl=ALL),
                            dict(c="org", f="permission_test",
                                 uacl=ALL, oacl=ALL),
                            dict(t="org_permission_test",
                                 uacl=ALL, oacl=ALL),
                            uid=TESTADMIN)

        db.commit()

    @classmethod
    def tearDownClass(cls):

        # Remove test roles
        s3_delete_role = current.auth.s3_delete_role
        s3_delete_role("TESTREADER")
        s3_delete_role("TESTEDITOR")
        s3_delete_role("TESTADMIN")

        # Remove test table
        table = current.db.org_permission_test
        table.drop()

        current.db.commit()

    # -------------------------------------------------------------------------
    def setUp(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db

        # Store current security policy
        settings = current.deployment_settings
        self.policy = settings.get_security_policy()

        # Get the role IDs
        gtable = auth.settings.table_group
        row = db(gtable.uuid=="TESTREADER").select(limitby=(0, 1)).first()
        self.reader = row.id
        row = db(gtable.uuid=="TESTEDITOR").select(limitby=(0, 1)).first()
        self.editor = row.id
        row = db(gtable.uuid=="TESTADMIN").select(limitby=(0, 1)).first()
        self.admin = row.id

        # Impersonate Admin
        auth.s3_impersonate("admin@example.com")

        # Create test entities
        table = s3db.org_organisation
        self.org = []
        for i in range(3):
            record_id = table.insert(name="PermissionTestOrganisation%s" % i)
            record =  Storage(id=record_id)
            s3db.update_super(table, record)
            self.org.append(record.pe_id)

        # Create test records
        table = current.db.org_permission_test
        self.record1 = table.insert(name="TestRecord1",
                                    owned_by_user=auth.user.id,
                                    realm_entity=self.org[0])

        self.record2 = table.insert(name="TestRecord2",
                                    owned_by_user=auth.user.id,
                                    realm_entity=self.org[1])

        self.record3 = table.insert(name="TestRecord3",
                                    owned_by_user=auth.user.id,
                                    realm_entity=self.org[2])

        # Remove session ownership
        auth.s3_clear_session_ownership()

        # Logout + turn override off
        auth.s3_impersonate(None)
        auth.override = False

    def tearDown(self):

        table = current.s3db.org_organisation

        # Rollback
        current.db.rollback()

        # Remove test records
        table = current.s3db.org_permission_test
        table.truncate()

        # Logout + turn override off
        auth = current.auth
        auth.s3_impersonate(None)
        auth.override = False

        # Restore security policy
        current.deployment_settings.security.policy = self.policy
        auth.permission = S3Permission(auth)

    # -------------------------------------------------------------------------
    def testPolicy1(self):
        """ Test permission check with policy 1 """

        auth = current.auth

        current.deployment_settings.security.policy = 1
        auth.permission = S3Permission(auth)

        has_permission = auth.s3_has_permission
        tablename = "org_permission_test"

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        # Check anonymous
        auth.s3_impersonate(None)
        permitted = has_permission("read", table=tablename)
        assertTrue(permitted)
        permitted = has_permission("update", table=tablename)
        assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", table=tablename)
        assertTrue(permitted)
        permitted = has_permission("update", table=tablename)
        assertTrue(permitted)

    # -------------------------------------------------------------------------
    def testPolicy3(self):
        """ Test permission check with policy 3 """

        auth = current.auth

        current.deployment_settings.security.policy = 3
        auth.permission = S3Permission(auth)

        has_permission = auth.s3_has_permission
        c = "org"
        f = "permission_test"
        tablename = "org_permission_test"

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        # Check anonymous
        auth.s3_impersonate(None)
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertFalse(permitted)

        # Test with TESTREADER
        auth.s3_assign_role(auth.user.id, self.reader)
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertTrue(permitted)
        permitted = has_permission("create", c=c, f=f, table=tablename)
        assertFalse(permitted) # Function ACL not applicable in policy 3
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        permitted = has_permission("delete", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        auth.s3_remove_role(auth.user.id, self.reader)

        # Test with TESTEDITOR
        auth.s3_assign_role(auth.user.id, self.editor)
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertTrue(permitted)
        permitted = has_permission("create", c=c, f=f, table=tablename)
        assertTrue(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        permitted = has_permission("delete", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        auth.s3_remove_role(auth.user.id, self.editor)

    # -------------------------------------------------------------------------
    def testPolicy4(self):
        """ Test permission check with policy 4 """

        auth = current.auth

        current.deployment_settings.security.policy = 4
        auth.permission = S3Permission(auth)

        has_permission = auth.s3_has_permission
        c = "org"
        f = "permission_test"
        tablename = "org_permission_test"

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        # Check anonymous
        auth.s3_impersonate(None)
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertFalse(permitted)

        # Test with TESTREADER
        auth.s3_assign_role(auth.user.id, self.reader)
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertTrue(permitted)
        permitted = has_permission("create", c=c, f=f, table=tablename)
        assertTrue(permitted) # Function ACL overrides controller ACL
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        permitted = has_permission("delete", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        auth.s3_remove_role(auth.user.id, self.reader)

        # Test with TESTEDITOR
        auth.s3_assign_role(auth.user.id, self.editor)
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertTrue(permitted)
        permitted = has_permission("create", c=c, f=f, table=tablename)
        assertTrue(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        permitted = has_permission("delete", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        auth.s3_remove_role(auth.user.id, self.editor)

    # -------------------------------------------------------------------------
    def testPolicy5(self):
        """ Test permission check with policy 5 """

        auth = current.auth

        current.deployment_settings.security.policy = 5
        auth.permission = S3Permission(auth)

        has_permission = auth.s3_has_permission
        accessible_url = auth.permission.accessible_url
        c = "org"
        f = "permission_test"
        tablename = "org_permission_test"

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse


        # Check anonymous
        auth.s3_impersonate(None)
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertFalse(permitted)
        url = accessible_url(c=c, f=f)
        assertEqual(url, False)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertFalse(permitted)
        url = accessible_url(c=c, f=f)
        assertEqual(url, False)

        # Test with TESTREADER
        auth.s3_assign_role(auth.user.id, self.reader)
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertTrue(permitted)
        permitted = has_permission("create", c=c, f=f, table=tablename)
        assertTrue(permitted) # Function ACL overrides controller ACL
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted) # Page ACL blocks Table ACL

        # Toggle page ACL
        acl = auth.permission
        auth.permission.update_acl("TESTREADER", c=c, f=f,
                                   uacl=acl.READ|acl.CREATE|acl.UPDATE,
                                   oacl=acl.READ|acl.CREATE|acl.UPDATE)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        auth.permission.update_acl("TESTREADER", c=c, f=f,
                                   uacl=acl.READ|acl.CREATE,
                                   oacl=acl.READ|acl.CREATE|acl.UPDATE)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)

        url = accessible_url(c=c, f=f)
        assertNotEqual(url, False)
        auth.s3_remove_role(auth.user.id, self.reader)

        # Test with TESTEDITOR
        auth.s3_assign_role(auth.user.id, self.editor)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        permitted = has_permission("delete", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        auth.s3_remove_role(auth.user.id, self.editor)

    # -------------------------------------------------------------------------
    def testPolicy6(self):
        """ Test permission check with policy 6 """

        auth = current.auth

        current.deployment_settings.security.policy = 6
        auth.permission = S3Permission(auth)

        has_permission = auth.s3_has_permission
        c = "org"
        f = "permission_test"
        tablename = "org_permission_test"

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        # Check anonymous
        auth.s3_impersonate(None)
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertFalse(permitted)

        # Test with TESTREADER
        auth.s3_assign_role(auth.user.id, self.reader, for_pe=0)
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertTrue(permitted)
        permitted = has_permission("create", c=c, f=f, table=tablename)
        assertTrue(permitted) # Function ACL overrides controller ACL
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted) # Page ACL blocks Table ACL
        auth.s3_remove_role(auth.user.id, self.reader, for_pe=[])

        # Test with TESTEDITOR with universal realm
        auth.s3_assign_role(auth.user.id, self.editor, for_pe=0)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        permitted = has_permission("delete", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertTrue(permitted)
        permitted = has_permission("delete", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertFalse(permitted)
        auth.s3_remove_role(auth.user.id, self.editor, for_pe=[])

        # Test with TESTEDITOR with limited realm
        auth.s3_assign_role(auth.user.id, self.editor, for_pe=self.org[0])
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        permitted = has_permission("delete", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertFalse(permitted)
        permitted = has_permission("delete", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertFalse(permitted)

        # Extend realm
        auth.s3_assign_role(auth.user.id, self.editor, for_pe=self.org[1])
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertTrue(permitted)

        # Withdraw role for one realm
        auth.s3_remove_role(auth.user.id, self.editor, for_pe=self.org[0])
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertTrue(permitted)

        # Withdraw role for all realms
        auth.s3_remove_role(auth.user.id, self.editor, for_pe=[])
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertFalse(permitted)

    # -------------------------------------------------------------------------
    def testPolicy7(self):
        """ Test permission check with policy 7 """

        auth = current.auth
        s3db = current.s3db

        current.deployment_settings.security.policy = 7
        auth.permission = S3Permission(auth)

        has_permission = auth.s3_has_permission
        c = "org"
        f = "permission_test"
        tablename = "org_permission_test"

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        # Check anonymous
        auth.s3_impersonate(None)
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c=c, f=f, table=tablename)
        assertFalse(permitted)

        # Test with TESTEDITOR with limited realm
        auth.s3_assign_role(auth.user.id, self.editor, for_pe=self.org[0])
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertFalse(permitted)

        # Make org[1] a sub-entity of org[0]
        s3db.pr_add_affiliation(self.org[0], self.org[1], role="TestOrgUnit")

        # Reload realms and test again
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertTrue(permitted) # Should now have access
        s3db.pr_remove_affiliation(self.org[0], self.org[1], role="TestOrgUnit")

        # Make org[0] a sub-entity of org[1]
        s3db.pr_add_affiliation(self.org[1], self.org[0], role="TestOrgUnit")

        # Reload realms
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertFalse(permitted) # Should no longer have access

        # Switch realm
        auth.s3_remove_role(auth.user.id, self.editor, for_pe=self.org[0])
        auth.s3_assign_role(auth.user.id, self.editor, for_pe=self.org[1])

        # Reload realms
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertTrue(permitted) # Should have access again

        # Remove org[0] from realm
        s3db.pr_remove_affiliation(self.org[1], self.org[0], role="TestOrgUnit")

        # Reload realms
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted) # Should no longer have access
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertTrue(permitted)

        # Withdraw TESTEDITOR role
        auth.s3_remove_role(auth.user.id, self.editor, for_pe=[])
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertFalse(permitted)

    # -------------------------------------------------------------------------
    def testWithUnavailableTable(self):

        auth = current.auth

        has_permission = auth.s3_has_permission
        c = "org"
        f = "permission_test"
        tablename = "org_permission_unavailable"

        auth.s3_impersonate(None)
        permitted = has_permission("read", c=c, f=f, table=tablename)

        # Should return None if the table doesn't exist
        self.assertEqual(permitted, None)

# =============================================================================
class AccessibleQueryTests(unittest.TestCase):
    """ Test accessible query for all policies """

    @classmethod
    def setUpClass(cls):

        # Create test table
        db = current.db
        tablename = "org_permission_test"
        db.define_table(tablename,
                        Field("name"),
                        *MetaFields())

        # Create test roles and ACLs
        auth = current.auth
        acl = auth.permission

        #NONE = acl.NONE
        READ = acl.READ
        CREATE = acl.READ|acl.CREATE
        UPDATE = acl.READ|acl.UPDATE
        WRITE = acl.READ|acl.CREATE|acl.UPDATE
        ALL = acl.ALL

        TESTREADER = "TESTREADER"
        auth.s3_create_role(TESTREADER, None,
                            dict(c="org",
                                 uacl=READ, oacl=READ),
                            dict(c="org", f="permission_test",
                                 uacl=CREATE, oacl=ALL),
                            dict(t="org_permission_test",
                                 uacl=WRITE, oacl=UPDATE),
                            uid=TESTREADER)

        TESTEDITOR = "TESTEDITOR"
        auth.s3_create_role(TESTEDITOR, None,
                            dict(c="org",
                                 uacl=WRITE, oacl=UPDATE),
                            dict(c="org", f="permission_test",
                                 uacl=WRITE, oacl=UPDATE),
                            dict(t="org_permission_test",
                                 uacl=WRITE, oacl=UPDATE),
                            uid=TESTEDITOR)

        TESTADMIN = "TESTADMIN"
        auth.s3_create_role(TESTADMIN, None,
                            dict(c="org",
                                 uacl=ALL, oacl=ALL),
                            dict(c="org", f="permission_test",
                                 uacl=ALL, oacl=ALL),
                            dict(t="org_permission_test",
                                 uacl=ALL, oacl=ALL),
                            uid=TESTADMIN)

        db.commit()

    @classmethod
    def tearDownClass(cls):

        # Remove test roles
        s3_delete_role = current.auth.s3_delete_role
        s3_delete_role("TESTREADER")
        s3_delete_role("TESTEDITOR")
        s3_delete_role("TESTADMIN")

        # Remove test table
        table = current.db.org_permission_test
        table.drop()

        current.db.commit()

    # -------------------------------------------------------------------------
    def setUp(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db

        # Store current security policy
        settings = current.deployment_settings
        self.policy = settings.get_security_policy()

        # Store current ownership rule
        self.strict = settings.get_security_strict_ownership()
        settings.security.strict_ownership = False

        # Get the role IDs
        gtable = auth.settings.table_group
        row = db(gtable.uuid=="TESTREADER").select(limitby=(0, 1)).first()
        self.reader = row.id
        row = db(gtable.uuid=="TESTEDITOR").select(limitby=(0, 1)).first()
        self.editor = row.id
        row = db(gtable.uuid=="TESTADMIN").select(limitby=(0, 1)).first()
        self.admin = row.id

        # Impersonate Admin
        auth.s3_impersonate("admin@example.com")

        # Create test entities
        table = s3db.org_organisation
        self.org = []
        for i in range(3):
            record_id = table.insert(name="PermissionTestOrganisation%s" % i)
            record =  Storage(id=record_id)
            s3db.update_super(table, record)
            self.org.append(record.pe_id)

        # Create test records
        table = current.db.org_permission_test
        self.record1 = table.insert(name="TestRecord1",
                                    owned_by_user=auth.user.id,
                                    realm_entity=self.org[0])

        self.record2 = table.insert(name="TestRecord2",
                                    owned_by_user=auth.user.id,
                                    realm_entity=self.org[1])

        self.record3 = table.insert(name="TestRecord3",
                                    owned_by_user=auth.user.id,
                                    realm_entity=self.org[2])

        # Remove session ownership
        auth.s3_clear_session_ownership()

        # Logout + turn override off
        auth.s3_impersonate(None)
        auth.override = False

    def tearDown(self):

        # Rollback
        current.db.rollback()

        # Remove test records
        table = current.s3db.org_permission_test
        table.truncate()

        # Logout + turn override off
        auth = current.auth
        auth.s3_impersonate(None)
        auth.override = False

        # Restore security policy
        current.deployment_settings.security.policy = self.policy
        auth.permission = S3Permission(auth)

        # Restore current ownership rule
        current.deployment_settings.security.strict_ownership = self.strict

    # -------------------------------------------------------------------------
    def testPolicy3(self):
        """ Test accessible query with policy 3 """

        auth = current.auth

        current.deployment_settings.security.policy = 3
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        c = "org"
        f = "permission_test"
        table = current.s3db.org_permission_test

        assertEqual = self.assertEqual

        ALL = (table.id > 0)
        NONE = (table.id == 0)

        # Check anonymous
        auth.s3_impersonate(None)
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, NONE)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, NONE)

        # Test with TESTREADER
        auth.s3_assign_role(auth.user.id, self.reader)
        query = accessible_query("read", "org_permission_test", c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("update", table, c=c, f=f)
        assertEqual(query, NONE)
        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)
        auth.s3_remove_role(auth.user.id, self.reader)

        # Test with TESTEDITOR
        auth.s3_assign_role(auth.user.id, self.editor)
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("update", table, c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)
        auth.s3_remove_role(auth.user.id, self.editor)

    # -------------------------------------------------------------------------
    def testPolicy4(self):
        """ Test accessible query with policy 4 """

        auth = current.auth

        current.deployment_settings.security.policy = 4
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        c = "org"
        f = "permission_test"
        table = current.s3db.org_permission_test

        assertEqual = self.assertEqual

        ALL = (table.id > 0)
        NONE = (table.id == 0)

        # Check anonymous
        auth.s3_impersonate(None)
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, NONE)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, NONE)

        # Test with TESTREADER
        auth.s3_assign_role(auth.user.id, self.reader)
        query = accessible_query("read", "org_permission_test", c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("update", table, c=c, f=f)
        roles = set(r for r in auth.user.realms if r is not None)
        OWNED = (((table.owned_by_user == auth.user.id) | \
                ((table.owned_by_user == None) & \
                (table.owned_by_group == None))) | \
                (table.owned_by_group.belongs(roles)))
        assertEqual(query, OWNED)
        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, OWNED)
        auth.s3_remove_role(auth.user.id, self.reader)

        # Test with TESTEDITOR
        auth.s3_assign_role(auth.user.id, self.editor)
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("update", table, c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)
        auth.s3_remove_role(auth.user.id, self.editor)

    # -------------------------------------------------------------------------
    def testPolicy5(self):
        """ Test accessible query with policy 5 """

        auth = current.auth

        current.deployment_settings.security.policy = 5
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        c = "org"
        f = "permission_test"
        table = current.s3db.org_permission_test

        assertEqual = self.assertEqual

        ALL = (table.id > 0)
        NONE = (table.id == 0)

        # Check anonymous
        auth.s3_impersonate(None)
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, NONE)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, NONE)

        # Test with TESTREADER
        auth.s3_assign_role(auth.user.id, self.reader)
        query = accessible_query("read", "org_permission_test", c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("update", table, c=c, f=f)
        roles = set(r for r in auth.user.realms if r is not None)
        OWNED = (((table.owned_by_user == auth.user.id) | \
                ((table.owned_by_user == None) & \
                (table.owned_by_group == None))) | \
                (table.owned_by_group.belongs(roles)))
        assertEqual(query, OWNED)
        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)
        auth.s3_remove_role(auth.user.id, self.reader)

        # Test with TESTEDITOR
        auth.s3_assign_role(auth.user.id, self.editor)
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("update", table, c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)
        auth.s3_remove_role(auth.user.id, self.editor)

    # -------------------------------------------------------------------------
    def testPolicy6(self):
        """ Test accessible query with policy 6 """

        auth = current.auth

        current.deployment_settings.security.policy = 6
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        c = "org"
        f = "permission_test"
        table = current.s3db.org_permission_test

        assertEqual = self.assertEqual

        #ALL = (table.id > 0)
        NONE = (table.id == 0)

        # Check anonymous
        auth.s3_impersonate(None)
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, NONE)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, NONE)

        # Test with TESTREADER
        auth.s3_assign_role(auth.user.id, self.reader, for_pe=self.org[0])
        roles = {2, 3}
        expected = (((table.realm_entity == self.org[0]) | \
                   (table.realm_entity == None)) | \
                   ((((table.owned_by_user == None) & \
                   (table.owned_by_group == None)) & \
                   (table.realm_entity == None)) | \
                   (table.owned_by_group.belongs(roles))))
        query = accessible_query("read", "org_permission_test", c=c, f=f)
        assertEqual(query, expected)
        query = accessible_query("update", table, c=c, f=f)
        expected = ((((table.owned_by_user == auth.user.id) & \
                   ((table.realm_entity == self.org[0]) | \
                   (table.realm_entity == None))) | \
                   (((table.owned_by_user == None) & \
                   (table.owned_by_group == None)) & \
                   (table.realm_entity == None))) | \
                   (((table.owned_by_group == self.reader) & \
                   (table.realm_entity.belongs([self.org[0]]))) | \
                   (table.owned_by_group.belongs(roles))))
        assertEqual(query, expected)
        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)
        auth.s3_remove_role(auth.user.id, self.reader)

        # Test with TESTEDITOR
        auth.s3_assign_role(auth.user.id, self.editor, for_pe=self.org[0])
        roles = {2, 3}
        query = accessible_query("read", table, c=c, f=f)
        expected = (((table.realm_entity == self.org[0]) | \
                   (table.realm_entity == None)) | \
                   ((((table.owned_by_user == None) & \
                   (table.owned_by_group == None)) & \
                   (table.realm_entity == None)) | \
                   (table.owned_by_group.belongs(roles))))
        assertEqual(query, expected)
        query = accessible_query("update", table, c=c, f=f)
        assertEqual(query, expected)
        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)
        auth.s3_remove_role(auth.user.id, self.editor)

        # Logout
        auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testPolicy7(self):
        """ Test accessible query with policy 7 """

        auth = current.auth
        s3db = current.s3db

        current.deployment_settings.security.policy = 7
        auth.permission = S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        c = "org"
        f = "permission_test"
        table = current.s3db.org_permission_test

        assertEqual = self.assertEqual
        assertSameQuery = self.assertSameQuery

        #ALL = (table.id > 0)
        NONE = (table.id == 0)

        # Check anonymous
        auth.s3_impersonate(None)
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, NONE)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, NONE)


        # Test with TESTREADER
        # Add unrestricted oACLs (to verify that they give owner
        # permissions without restriction to realms)
        acl = auth.permission
        auth.permission.update_acl(self.reader,
                                   c="org",
                                   f="permission_test",
                                   uacl=acl.NONE,
                                   oacl=acl.CREATE|acl.READ|acl.UPDATE,
                                   entity="any",
                                   )
        auth.permission.update_acl(self.reader,
                                   t="org_permission_test",
                                   uacl=acl.NONE,
                                   oacl=acl.CREATE|acl.READ|acl.UPDATE,
                                   entity="any",
                                   )
        auth.s3_assign_role(auth.user.id, self.reader, for_pe=self.org[0])
        roles = {3, 2, self.reader}

        # Strict ownership: user has access to records within the
        # realms of the role, or which he owns either individually or
        # as member of the owner group
        current.deployment_settings.security.strict_ownership = True
        query = accessible_query("read", table, c=c, f=f)
        expected = (((table.realm_entity == self.org[0]) | \
                   (table.realm_entity == None)) | \
                   ((table.owned_by_user == auth.user.id) | \
                   (table.owned_by_group.belongs(roles))))
        #assertEqual(query, expected)
        assertSameQuery(query, expected)

        # Loose ownership: user has access to records within the realm
        # of the role, or which he owns either individually or as
        # member of the owner group, as well as all records which are
        # not owned by anyone
        current.deployment_settings.security.strict_ownership = False
        query = accessible_query("read", table, c=c, f=f)
        expected = (((table.realm_entity == self.org[0]) | \
                   (table.realm_entity == None)) | \
                   (((table.owned_by_user == auth.user.id) | \
                   ((table.owned_by_user == None) & \
                   (table.owned_by_group == None))) | \
                   (table.owned_by_group.belongs(roles))))
        #assertEqual(query, expected)
        assertSameQuery(query, expected)

        # Update permission is limited to owned records
        query = accessible_query("update", table, c=c, f=f)
        expected = (((table.owned_by_user == auth.user.id) | \
                   ((table.owned_by_user == None) & \
                   (table.owned_by_group == None))) | \
                   (table.owned_by_group.belongs(roles)))
        #assertEqual(query, expected)
        assertSameQuery(query, expected)

        # No delete-permission on any record
        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)

        # Make org[1] a sub-entity of org[0]
        s3db.pr_add_affiliation(self.org[0], self.org[1], role="TestOrgUnit")
        # Reload realms and delegations
        auth.s3_impersonate("normaluser@example.com")

        # Re-check queries
        query = accessible_query("read", table, c=c, f=f)
        expected = (((table.realm_entity.belongs([self.org[0], self.org[1]])) | \
                   (table.realm_entity == None)) | \
                   (((table.owned_by_user == auth.user.id) | \
                   ((table.owned_by_user == None) & \
                   (table.owned_by_group == None))) | \
                   (table.owned_by_group.belongs(roles))))
        #assertEqual(query, expected)
        assertSameQuery(query, expected)

        query = accessible_query("update", table, c=c, f=f)
        expected = (((table.owned_by_user == auth.user.id) | \
                   ((table.owned_by_user == None) & \
                   (table.owned_by_group == None))) | \
                   (table.owned_by_group.belongs(roles)))
        #assertEqual(query, expected)
        assertSameQuery(query, expected)

        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)

        # Remove affiliation and role
        s3db.pr_remove_affiliation(self.org[0], self.org[1], role="TestOrgUnit")
        auth.s3_remove_role(auth.user.id, self.reader, for_pe=self.org[0])

        # Test with TESTEDITOR
        auth.s3_assign_role(auth.user.id, self.editor, for_pe=self.org[0])
        roles = {3, 2}
        query = accessible_query("read", table, c=c, f=f)
        expected = (((table.realm_entity == self.org[0]) | \
                   (table.realm_entity == None)) | \
                   ((((table.owned_by_user == None) & \
                   (table.owned_by_group == None)) & \
                   (table.realm_entity == None)) | \
                   (table.owned_by_group.belongs(roles))))
        #assertEqual(query, expected)
        assertSameQuery(query, expected)

        query = accessible_query("update", table, c=c, f=f)
        #assertEqual(query, expected)
        assertSameQuery(query, expected)

        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)

        # Make org[1] a sub-entity of org[0]
        s3db.pr_add_affiliation(self.org[0], self.org[1], role="TestOrgUnit")
        # Reload realms and delegations
        auth.s3_impersonate("normaluser@example.com")

        # Re-check queries
        expected = (((table.realm_entity.belongs([self.org[0], self.org[1]])) | \
                   (table.realm_entity == None)) | \
                   ((((table.owned_by_user == None) & \
                   (table.owned_by_group == None)) & \
                   (table.realm_entity == None)) | \
                   (table.owned_by_group.belongs(roles))))
        query = accessible_query("read", table, c=c, f=f)
        #assertEqual(query, expected)
        assertSameQuery(query, expected)

        query = accessible_query("update", table, c=c, f=f)
        #assertEqual(query, expected)
        assertSameQuery(query, expected)

        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)

        # Remove affiliation and role
        s3db.pr_remove_affiliation(self.org[0], self.org[1], role="TestOrgUnit")
        auth.s3_remove_role(auth.user.id, self.editor)

    # -------------------------------------------------------------------------
    @classmethod
    def assertSameQuery(cls, l, r, msg=None):
        """
            Custom assertion that two queries are equal

            @param l: the first query
            @param r: the second query
        """

        l, r = repr(l), repr(r)
        if l == r:
            return

        equal = cls.compare_queries(l, r)
        if not equal:
            if msg is None:
                msg = "Queries differ: %s != %s" % (l, r)
            raise AssertionError(msg)

    # -------------------------------------------------------------------------
    @classmethod
    def compare_queries(cls, l, r):
        """
            Helper function to compare two queries, handles arbitrary
            order of ' IN (x,y,z)' tuples.

            @param l: the first query
            @param r: the second query

            @returns: True if the queries are equal, otherwise False
        """

        ml = QUERY_PATTERN.match(l)
        mr = QUERY_PATTERN.match(r)
        if ml and mr and \
           ml.group(1) == mr.group(1) and \
           set(ml.group(3).split(",")) == set(mr.group(3).split(",")):
            return ml.group(4) == mr.group(4) or \
                   cls.compare_queries(ml.group(4), mr.group(4))

        return False

# =============================================================================
if __name__ == "__main__":

    run_suite(
        PermissionFailureTests,
        ACLManagementTests,
        HasPermissionTests,
        AccessibleQueryTests,
        )

# END ========================================================================
