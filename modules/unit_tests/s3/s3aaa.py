# -*- coding: utf-8 -*-
#
# S3AAA Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3aaa.py
#
import unittest
import re

from gluon import *
from gluon.storage import Storage
from s3.s3aaa import S3EntityRoleManager, S3Permission
from s3.s3fields import s3_meta_fields

from unit_tests import run_suite

# RE to handle IN-tuples in queries
QUERY_PATTERN = re.compile(r"(.*)( IN \(([0-9,]*)\))(.*)")

# =============================================================================
class AuthUtilsTests(unittest.TestCase):
    """ S3Auth Utility Methods Tests """

    # -------------------------------------------------------------------------
    def testSystemRoles(self):
        """ Test if system roles are present """

        sr = current.auth.get_system_roles()

        assertTrue = self.assertTrue

        assertTrue(isinstance(sr, Storage))
        assertTrue("ADMIN" in sr)
        assertTrue(sr.ADMIN is not None)
        assertTrue("AUTHENTICATED" in sr)
        assertTrue(sr.AUTHENTICATED is not None)
        assertTrue("ANONYMOUS" in sr)
        assertTrue(sr.ANONYMOUS is not None)

    # -------------------------------------------------------------------------
    def testGetUserIDByEmail(self):
        """ Test user account identification by email """

        user_id = current.auth.s3_get_user_id("normaluser@example.com")
        self.assertTrue(user_id is not None)

    # -------------------------------------------------------------------------
    def testImpersonate(self):
        """ Test s3_impersonate """

        auth = current.auth
        session = current.session

        sr = auth.get_system_roles()
        ADMIN = sr.ADMIN
        ANONYMOUS = sr.ANONYMOUS

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse
        assertRaises = self.assertRaises

        # Test-login as system administrator
        auth.s3_impersonate("admin@example.com")
        assertTrue(auth.s3_logged_in())
        assertTrue(auth.user is not None)
        assertTrue(ADMIN in session.s3.roles)
        assertTrue(ANONYMOUS in session.s3.roles)
        assertTrue(ADMIN in auth.user.realms)

        # Test with nonexistent user
        with assertRaises(ValueError):
            auth.s3_impersonate("NonExistentUser")
        # => should still be logged in as ADMIN
        assertTrue(auth.s3_logged_in())
        assertTrue(ADMIN in session.s3.roles)

        # Test with None => should logout and reset the roles
        auth.s3_impersonate(None)
        assertFalse(auth.s3_logged_in())
        assertTrue(session.s3.roles == [] or ANONYMOUS in session.s3.roles)

        # Logout
        auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testFail(self):
        """ Test authorization failure for RFC1945/2617 compliance """

        auth = current.auth

        # Save current request format
        f = auth.permission.format

        assertEqual = self.assertEqual
        assertIn = self.assertIn
        try:
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

            # Non-interactive => raises 403 if logged in
            auth.permission.format = "xml"
            auth.s3_impersonate("admin@example.com")
            try:
                auth.permission.fail()
            except HTTP as e:
                assertEqual(e.status, 403)
                headers = e.headers
                # No Auth challenge with 403
                self.assertNotIn("WWW-Authenticate", headers)
            else:
                raise AssertionError("No HTTP status raised")

            # auth.s3_logged_in() MUST NOT raise a challenge
            msg = "s3_logged_in must not raise HTTP Auth challenge"
            auth.permission.format = "xml"
            auth.s3_impersonate(None)
            try:
                basic = auth.s3_logged_in()
            except HTTP:
                raise AssertionError(msg)
            # ...especially not in interactive requests!
            auth.permission.format = "html"
            auth.s3_impersonate(None)
            try:
                basic = auth.s3_logged_in()
            except HTTP:
                raise AssertionError(msg)

        finally:
            auth.s3_impersonate(None)
            auth.permission.format = f

# =============================================================================
class SetRolesTests(unittest.TestCase):
    """ Test AuthS3.set_roles """

    def setUp(self):

        # Create test organisations
        xmlstr = """
<s3xml>
    <resource name="org_organisation" uuid="SRTO1">
        <data field="name">SetRoleTestsOrg1</data>
    </resource>
    <resource name="org_organisation" uuid="SRTO2">
        <data field="name">SetRoleTestsOrg2</data>
    </resource>
    <resource name="org_organisation" uuid="SRTO3">
        <data field="name">SetRoleTestsOrg3</data>
    </resource>
</s3xml>"""

        try:
            auth = current.auth
            auth.override = True
            from lxml import etree
            xmltree = etree.ElementTree(etree.fromstring(xmlstr))
            s3db = current.s3db
            resource = s3db.resource("org_organisation")
            resource.import_xml(xmltree)

            resource = s3db.resource("org_organisation",
                                     uid=["SRTO1", "SRTO2", "SRTO3"])
            rows = resource.select(["pe_id", "uuid"], as_rows=True)

            orgs = {row.uuid: row.pe_id for row in rows}
            self.org1 = orgs["SRTO1"]
            self.org2 = orgs["SRTO2"]
            self.org3 = orgs["SRTO3"]
            auth.override = False
        except:
            current.db.rollback()
            auth.override = False
            raise

        # Stash security policy
        settings = current.deployment_settings
        self.policy = settings.get_security_policy()

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()

        auth = current.auth
        auth.override = False

        # Restore security policy
        current.deployment_settings.security.policy = self.policy
        auth.permission = S3Permission(auth)

    # -------------------------------------------------------------------------
    def testSetRolesPolicy3(self):
        """ Test set_roles with policy 3 """

        auth = current.auth
        settings = current.deployment_settings

        settings.security.policy = 3
        auth.permission = S3Permission(auth)

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        auth.s3_impersonate("normaluser@example.com")
        realms = list(auth.user.realms.keys())
        assertEqual(len(realms), 2)
        assertTrue(2 in realms)
        assertTrue(3 in realms)
        for r in auth.user.realms:
            assertEqual(auth.user.realms[r], None)

        auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testSetRolesPolicy4(self):
        """ Test set_roles with policy 4 """

        auth = current.auth
        settings = current.deployment_settings

        settings.security.policy = 4
        auth.permission = S3Permission(auth)

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        auth.s3_impersonate("normaluser@example.com")
        realms = list(auth.user.realms.keys())
        assertTrue(2 in realms)
        assertTrue(3 in realms)
        assertEqual(len(realms), 2)
        for r in auth.user.realms:
            assertEqual(auth.user.realms[r], None)

        auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testSetRolesPolicy5(self):
        """ Test set_roles with policy 5 """

        auth = current.auth
        settings = current.deployment_settings

        settings.security.policy = 5
        auth.permission = S3Permission(auth)

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        auth.s3_impersonate("normaluser@example.com")
        realms = list(auth.user.realms.keys())
        assertTrue(2 in realms)
        assertTrue(3 in realms)
        assertEqual(len(realms), 2)
        for r in auth.user.realms:
            assertEqual(auth.user.realms[r], None)

        auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testSetRolesPolicy6(self):
        """ Test set_roles with policy 6 """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        settings.security.policy = 6
        auth.permission = S3Permission(auth)

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        try:
            # Create a test role
            role = auth.s3_create_role("Example Role", uid="TESTROLE")

            # Assign normaluser this role for a realm
            user_id = auth.s3_get_user_id("normaluser@example.com")
            auth.s3_assign_role(user_id, role, for_pe=self.org1)

            auth.s3_impersonate("normaluser@example.com")
            realms = list(auth.user.realms.keys())
            assertEqual(len(realms), 3)
            assertTrue(2 in realms)
            assertTrue(3 in realms)
            assertTrue(role in realms)
            for r in auth.user.realms:
                if r == role:
                    assertEqual(auth.user.realms[r], [self.org1])
                else:
                    assertEqual(auth.user.realms[r], None)

        finally:
            auth.s3_impersonate(None)
            auth.s3_delete_role("TESTROLE")
            current.db.rollback()

    # -------------------------------------------------------------------------
    def testSetRolesPolicy7(self):
        """ Test set_roles with policy 7 """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        settings.security.policy = 7
        auth.permission = S3Permission(auth)

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        try:
            # Create a test role
            role = auth.s3_create_role("Example Role", uid="TESTROLE")

            # Create an OU-affiliation for two organisations
            org1 = self.org1
            org2 = self.org2
            s3db.pr_add_affiliation(org1, org2, role="TestRole")

            # Assign normaluser this role for the realm of the parent org
            user_id = auth.s3_get_user_id("normaluser@example.com")
            auth.s3_assign_role(user_id, role, for_pe=org1)

            auth.s3_impersonate("normaluser@example.com")
            realms = list(auth.user.realms.keys())
            assertTrue(2 in realms)
            assertTrue(3 in realms)
            assertTrue(role in realms)
            assertEqual(len(realms), 3)
            for r in auth.user.realms:
                if r == role:
                    assertTrue(org1 in auth.user.realms[r])
                    assertTrue(org2 in auth.user.realms[r])
                else:
                    assertEqual(auth.user.realms[r], None)

        finally:
            auth.s3_impersonate(None)
            auth.s3_delete_role("TESTROLE")
            current.db.rollback()

    # -------------------------------------------------------------------------
    def testSetRolesPolicy8(self):
        """ Test set_roles with policy 8 """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        settings.security.policy = 8
        auth.permission = S3Permission(auth)

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        try:
            # Create a test role
            role = auth.s3_create_role("Test Group", uid="TESTGROUP")

            # Have two orgs, set org2 as OU descendant of org1
            org1 = self.org1
            org2 = self.org2
            s3db.pr_add_affiliation(org1, org2, role="TestOrgUnit")

            # Have a third org
            org3 = self.org3

            # Add the user as OU descendant of org3
            user_id = auth.s3_get_user_id("normaluser@example.com")
            user_pe = auth.s3_user_pe_id(user_id)
            s3db.pr_add_affiliation(org3, user_pe, role="TestStaff")

            # Assign normaluser the test role for org3
            auth.s3_assign_role(user_id, role, for_pe=org3)

            # Delegate the test role for org1 to org3
            auth.s3_delegate_role("TESTGROUP", org1, receiver=org3)

            # Impersonate as normal user
            auth.s3_impersonate("normaluser@example.com")

            # Check the realms
            realms = list(auth.user.realms.keys())
            assertTrue(2 in realms)
            assertTrue(3 in realms)
            assertTrue(role in realms)
            assertEqual(len(realms), 3)

            for r in auth.user.realms:
                if r == role:
                    assertTrue(org3 in auth.user.realms[r])
                else:
                    assertEqual(auth.user.realms[r], None)

            # Check the delegations
            delegations = list(auth.user.delegations.keys())
            assertTrue(role in delegations)
            assertEqual(len(delegations), 1)

            realms = auth.user.delegations[role]
            assertTrue(org3 in realms)
            assertEqual(len(realms), 1)
            assertTrue(org1 in realms[org3])
            assertTrue(org2 in realms[org3])

            # Remove the delegations
            auth.s3_remove_delegation("TESTGROUP", org1, receiver=org3)

            # Check the delegations again
            delegations = list(auth.user.delegations.keys())
            assertFalse(role in delegations)
            assertEqual(len(delegations), 0)

        finally:
            s3db.pr_remove_affiliation(org1, org2, role="TestOrgUnit")
            s3db.pr_remove_affiliation(org1, org2, role="TestStaff")
            auth.s3_delete_role("TESTGROUP")
            current.db.rollback()
            auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    #def testPerformance(self):

        #MAX_RUNTIME = 18 # Maximum acceptable runtime per request in milliseconds
        ##MAX_RUNTIME = 3 # Maximum acceptable runtime per request in milliseconds (up to policy 7)

        #deployment_settings.security.policy = 8
        #from s3.s3aaa import S3Permission
        #auth.permission = S3Permission(auth)

        #try:
            #org1 = s3db.pr_get_pe_id("org_organisation", 1)
            #org2 = s3db.pr_get_pe_id("org_organisation", 2)
            #s3db.pr_add_affiliation(org1, org2, role="TestOrgUnit")
            #org3 = s3db.pr_get_pe_id("org_organisation", 3)
            #partners = s3db.pr_add_affiliation(org1, org3, role="TestPartners", role_type=9)
            #user = auth.s3_user_pe_id(auth.s3_get_user_id("normaluser@example.com"))
            #s3db.pr_add_affiliation(org3, user, role="TestStaff")
            #role = auth.s3_create_role("Test Group", uid="TESTGROUP")
            #dtable = s3db.pr_delegation
            #record = dtable.insert(role_id=partners, group_id=role)

            #def setRoles():
                #auth.s3_impersonate("normaluser@example.com")

            #import timeit
            #runtime = timeit.Timer(setRoles).timeit(number=100)
            #if runtime > (MAX_RUNTIME / 10.0):
                #raise AssertionError("s3_impersonate: maximum acceptable run time exceeded (%sms > %sms)" % (int(runtime * 10), MAX_RUNTIME))
            ## Logout
            #auth.s3_impersonate(None)

        #finally:
            #s3db.pr_remove_affiliation(org1, org2, role="TestOrgUnit")
            #s3db.pr_remove_affiliation(org1, org2, role="TestStaff")
            #s3db.pr_remove_affiliation(org1, org3, role="TestPartners")
            #auth.s3_delete_role("TESTGROUP")
            #current.db.rollback()

# =============================================================================
class RoleAssignmentTests(unittest.TestCase):
    """ Test role assignments """

    # -------------------------------------------------------------------------
    def testAssignRole(self):
        """ Test role assignment to a user """

        db = current.db
        auth = current.auth

        UUID1 = "TESTAUTOCREATEDROLE1"
        UUID2 = "TESTAUTOCREATEDROLE2"

        uuids = [UUID1, UUID2]

        table = auth.settings.table_group
        query1 = (table.deleted != True) & (table.uuid == UUID1)
        query2 = (table.deleted != True) & (table.uuid == UUID2)

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        auth.s3_impersonate("admin@example.com")
        user_id = auth.user.id

        row = db(query1).select(limitby=(0, 1)).first()
        assertEqual(row, None)
        row = db(query2).select(limitby=(0, 1)).first()
        assertEqual(row, None)

        auth.s3_assign_role(user_id, uuids, for_pe=0)
        row = db(query1).select(limitby=(0, 1)).first()
        assertNotEqual(row, None)
        assertTrue(row.id > 0)
        assertTrue(row.role == UUID1)
        assertTrue(row.uuid == UUID1)
        row = db(query2).select(limitby=(0, 1)).first()
        assertNotEqual(row, None)
        assertTrue(row.id > 0)
        assertTrue(row.role == UUID2)
        assertTrue(row.uuid == UUID2)

        auth.s3_delete_role(UUID1)
        row = db(query1).select(limitby=(0, 1)).first()
        assertEqual(row, None)
        row = db(query2).select(limitby=(0, 1)).first()
        assertNotEqual(row, None)
        assertTrue(row.id > 0)
        assertTrue(row.role == UUID2)
        assertTrue(row.uuid == UUID2)

        auth.s3_delete_role(UUID2)
        row = db(query1).select(limitby=(0, 1)).first()
        assertEqual(row, None)
        row = db(query2).select(limitby=(0, 1)).first()
        assertEqual(row, None)

    # -------------------------------------------------------------------------
    def testGetRoles(self):
        """ Test role lookup for a user """

        auth = current.auth
        UUID = "TESTAUTOCREATEDROLE"
        role_id = auth.s3_create_role(UUID, uid=UUID)

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        try:
            auth.s3_impersonate("normaluser@example.com")
            user_id = auth.user.id

            auth.s3_assign_role(user_id, role_id, for_pe=None)
            roles = auth.s3_get_roles(user_id)
            assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=None)
            assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=0)
            assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=1)
            assertFalse(role_id in roles)
            auth.s3_withdraw_role(user_id, role_id, for_pe=None)

            auth.s3_assign_role(user_id, role_id, for_pe=0)
            roles = auth.s3_get_roles(user_id)
            assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=None)
            assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=0)
            assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=1)
            assertFalse(role_id in roles)
            auth.s3_withdraw_role(user_id, role_id, for_pe=0)

            auth.s3_assign_role(user_id, role_id, for_pe=1)
            roles = auth.s3_get_roles(user_id)
            assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=None)
            assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=0)
            assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=1)
            assertTrue(role_id in roles)
            auth.s3_withdraw_role(user_id, role_id, for_pe=1)

        finally:

            auth.s3_delete_role(UUID)
            auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()

# =============================================================================
class RecordOwnershipTests(unittest.TestCase):
    """ Test record ownership """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        tablename = "ownership_test_table"
        current.db.define_table(tablename,
                                Field("name"),
                                *s3_meta_fields())

    @classmethod
    def tearDownClass(cls):

        table = current.db.ownership_test_table
        table.drop()

    # -------------------------------------------------------------------------
    def setUp(self):

        auth = current.auth

        # Create Test Role
        ROLE = "OWNERSHIPTESTROLE"
        self.role_id = auth.s3_create_role(ROLE, uid=ROLE)

        # Create a record which is not owned by any user, role or entity
        auth.s3_impersonate(None)
        self.table = current.db.ownership_test_table
        self.table.owned_by_user.default = None
        self.record_id = self.table.insert(name="Test")

    def tearDown(self):

        auth = current.auth

        # Delete test record
        current.db(self.table.id == self.record_id).delete()

        # Remove Test Role
        auth.s3_delete_role(self.role_id)

        # Logout
        auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testOwnershipRequiredController(self):
        """ Test ownership required for controller """

        auth = current.auth
        permission = auth.permission

        deployment_settings = current.deployment_settings

        policies = {
            1: False,
            2: False,
            3: True,
            4: True,
            5: True,
            6: True,
            7: True,
            8: True,
            0: True,
        }

        current_policy = deployment_settings.get_security_policy()

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        # Controller ACL
        auth.permission.update_acl(self.role_id,
                                   c="pr", f="person",
                                   uacl=auth.permission.NONE,
                                   oacl=auth.permission.ALL)

        # Assign Test Role to normaluser@example.com
        auth.s3_impersonate("normaluser@example.com")
        auth.s3_assign_role(auth.user.id, self.role_id)

        try:
            for policy in policies:
                deployment_settings.security.policy = policy
                permission = S3Permission(auth)
                ownership_required = permission.ownership_required
                o = ownership_required("update",
                                       "ownership_test_table",
                                       c="pr",
                                       f="person")
                required = policies[policy]
                msg = "ownership_required failed " \
                      "in policy %s (%s instead of %s)" % \
                      (policy, not required, required)
                if policies[policy]:
                    assertTrue(o, msg=msg)
                else:
                    assertFalse(o, msg=msg)
        finally:
            deployment_settings.security.policy = current_policy
            auth.permission.delete_acl(self.role_id, c="pr", f="person")

    # -------------------------------------------------------------------------
    def testOwnershipRequiredTable(self):
        """ Test ownership required for table """

        auth = current.auth
        permission = auth.permission

        deployment_settings = current.deployment_settings

        policies = {
            1: False,
            2: False,
            3: False, # doesn't use table ACLs
            4: False, # doesn't use table ACLs
            5: True,
            6: True,
            7: True,
            8: True,
            0: True,
        }

        current_policy = deployment_settings.get_security_policy()

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        # Table ACL
        auth.permission.update_acl(self.role_id,
                                   t="ownership_test_table",
                                   uacl=auth.permission.NONE,
                                   oacl=auth.permission.ALL)

        # Assign Test Role to normaluser@example.com
        auth.s3_impersonate("normaluser@example.com")
        auth.s3_assign_role(auth.user.id, self.role_id)

        try:
            for policy in policies:
                deployment_settings.security.policy = policy
                permission = S3Permission(auth)
                ownership_required = permission.ownership_required
                o = ownership_required("update", "ownership_test_table")
                required = policies[policy]
                msg = "ownership_required failed " \
                      "in policy %s (%s instead of %s)" % \
                      (policy, not required, required)
                if policies[policy]:
                    assertTrue(o, msg=msg)
                else:
                    assertFalse(o, msg=msg)
        finally:
            deployment_settings.security.policy = current_policy
            auth.permission.delete_acl(self.role_id, t="ownership_test_table")

    # -------------------------------------------------------------------------
    def testSessionOwnership(self):
        """ Test session ownership methods """

        db = current.db
        auth = current.auth

        # Pick two tables
        # (no real DB access here, so records don't need to exist)
        s3db = current.s3db
        ptable = s3db.pr_person
        otable = s3db.org_organisation

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        # Logout + clear_session_ownership before testing
        auth.s3_impersonate(None)
        auth.s3_clear_session_ownership()

        # Check general session ownership rules
        auth.s3_make_session_owner(ptable, 1)
        # No record ID should always return False
        assertFalse(auth.s3_session_owns(ptable, None))
        # Check for non-owned record
        assertFalse(auth.s3_session_owns(ptable, 2))
        # Check for owned record
        assertTrue(auth.s3_session_owns(ptable, 1))
        # If user is logged-in, session ownership is always False
        auth.s3_impersonate("normaluser@example.com")
        assertFalse(auth.s3_session_owns(ptable, 1))

        # Check record-wise clear_session_ownership
        auth.s3_impersonate(None)
        auth.s3_make_session_owner(ptable, 1)
        auth.s3_make_session_owner(ptable, 2)
        assertTrue(auth.s3_session_owns(ptable, 1))
        assertTrue(auth.s3_session_owns(ptable, 2))
        auth.s3_clear_session_ownership(ptable, 1)
        assertFalse(auth.s3_session_owns(ptable, 1))
        assertTrue(auth.s3_session_owns(ptable, 2))

        # Check table-wise clear_session_ownership
        auth.s3_make_session_owner(ptable, 1)
        auth.s3_make_session_owner(ptable, 2)
        auth.s3_make_session_owner(otable, 1)
        auth.s3_make_session_owner(otable, 2)
        assertTrue(auth.s3_session_owns(ptable, 1))
        assertTrue(auth.s3_session_owns(ptable, 2))
        assertTrue(auth.s3_session_owns(otable, 1))
        assertTrue(auth.s3_session_owns(otable, 2))
        auth.s3_clear_session_ownership(ptable)
        assertFalse(auth.s3_session_owns(ptable, 1))
        assertFalse(auth.s3_session_owns(ptable, 2))
        assertTrue(auth.s3_session_owns(otable, 1))
        assertTrue(auth.s3_session_owns(otable, 2))

        # Check global clear_session_ownership
        auth.s3_make_session_owner(ptable, 1)
        auth.s3_make_session_owner(ptable, 2)
        auth.s3_make_session_owner(otable, 1)
        auth.s3_make_session_owner(otable, 2)
        assertTrue(auth.s3_session_owns(ptable, 1))
        assertTrue(auth.s3_session_owns(ptable, 2))
        assertTrue(auth.s3_session_owns(otable, 1))
        assertTrue(auth.s3_session_owns(otable, 2))
        auth.s3_clear_session_ownership()
        assertFalse(auth.s3_session_owns(ptable, 1))
        assertFalse(auth.s3_session_owns(ptable, 2))
        assertFalse(auth.s3_session_owns(otable, 1))
        assertFalse(auth.s3_session_owns(otable, 2))

    # -------------------------------------------------------------------------
    def testOwnershipPublicRecord(self):
        """ Test ownership for a public record """

        auth = current.auth
        s3_impersonate = auth.s3_impersonate
        is_owner = auth.permission.is_owner

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        auth.s3_clear_session_ownership()

        table = self.table
        record_id = self.record_id

        # Admin owns all records
        s3_impersonate("admin@example.com")
        assertTrue(is_owner(table, record_id))

        # Normal owns all public records
        s3_impersonate("normaluser@example.com")
        assertTrue(is_owner(table, record_id))

        # Unauthenticated users never own a record
        s3_impersonate(None)
        assertFalse(is_owner(table, record_id))

        # ...unless the session owns the record
        auth.s3_make_session_owner(table, record_id)
        assertTrue(is_owner(table, record_id))

    # -------------------------------------------------------------------------
    def testOwnershipAdminOwnedRecord(self):
        """ Test ownership for an Admin-owned record """

        auth = current.auth
        s3_impersonate = auth.s3_impersonate
        is_owner = auth.permission.is_owner

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        auth.s3_clear_session_ownership()

        table = self.table
        record_id = self.record_id

        # Make Admin owner of the record
        user_id = auth.s3_get_user_id("admin@example.com")
        current.db(table.id == record_id).update(owned_by_user=user_id)

        # Admin owns all records
        s3_impersonate("admin@example.com")
        assertTrue(is_owner(table, record_id))

        # Normal does not own this record
        s3_impersonate("normaluser@example.com")
        assertFalse(is_owner(table, record_id))

        # Unauthenticated does not own this record
        s3_impersonate(None)
        assertFalse(is_owner(table, record_id))

        # ...unless the session owns the record
        auth.s3_make_session_owner(table, record_id)
        assertTrue(is_owner(table, record_id))

    # -------------------------------------------------------------------------
    def testOwnershipUserOwnedRecord(self):
        """ Test ownership for a user-owned record """

        auth = current.auth
        s3_impersonate = auth.s3_impersonate
        is_owner = auth.permission.is_owner

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        auth.s3_clear_session_ownership()

        table = self.table
        record_id = self.record_id

        # Change the record owner to admin
        user_id = auth.s3_get_user_id("normaluser@example.com")
        current.db(table.id == record_id).update(owned_by_user=user_id)

        # Admin owns all records
        s3_impersonate("admin@example.com")
        assertTrue(is_owner(table, record_id))

        # Normal owns this record
        s3_impersonate("normaluser@example.com")
        assertTrue(is_owner(table, record_id))

        # Unauthenticated does not own a record
        s3_impersonate(None)
        assertFalse(is_owner(table, record_id))

        # ...unless the session owns the record
        auth.s3_make_session_owner(table, record_id)
        assertTrue(is_owner(table, record_id))

    # -------------------------------------------------------------------------
    def testOwnershipGroupOwnedRecord(self):
        """ Test ownership for a collectively owned record """

        auth = current.auth
        s3_impersonate = auth.s3_impersonate
        is_owner = auth.permission.is_owner

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        auth.s3_clear_session_ownership()

        table = self.table
        record_id = self.record_id

        sr = auth.get_system_roles()
        user_id = auth.s3_get_user_id("admin@example.com")
        current.db(table.id == record_id).update(owned_by_user=user_id,
                                                 owned_by_group=sr.AUTHENTICATED)

        # Admin owns all records
        s3_impersonate("admin@example.com")
        assertTrue(is_owner(table, record_id))

        # Normal owns this record as member of AUTHENTICATED
        s3_impersonate("normaluser@example.com")
        assertTrue(is_owner(table, record_id))

        # Unauthenticated does not own this record
        s3_impersonate(None)
        assertFalse(is_owner(table, record_id))

        # ...unless the session owns the record
        auth.s3_make_session_owner(table, record_id)
        assertTrue(is_owner(table, record_id))

    # -------------------------------------------------------------------------
    def testOwnershipOrganisationOwnedRecord(self):
        """ Test group-ownership for an entity-owned record """

        auth = current.auth
        s3_impersonate = auth.s3_impersonate
        is_owner = auth.permission.is_owner

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        auth.s3_clear_session_ownership()

        table = self.table
        record_id = self.record_id

        # Assume we have at least one org
        org = current.s3db.pr_get_pe_id("org_organisation", 1)

        role = self.role_id

        # Make test role owner of the record and add to org's realm
        user_id = auth.s3_get_user_id("admin@example.com")
        current.db(table.id == record_id).update(owned_by_user=user_id,
                                                 owned_by_group=role,
                                                 realm_entity=org)

        # Admin owns all records
        s3_impersonate("admin@example.com")
        assertTrue(is_owner(table, record_id))

        # Normal user does not own the record
        s3_impersonate("normaluser@example.com")
        user_id = auth.user.id
        assertFalse(is_owner(table, record_id))

        # ...unless they have the role for this org
        auth.s3_assign_role(user_id, role, for_pe=org)
        assertTrue(is_owner(table, record_id))
        auth.s3_withdraw_role(user_id, role, for_pe=[])
        assertFalse(is_owner(table, record_id))

        # ....or have the role without limitation (any org)
        auth.s3_assign_role(user_id, role, for_pe=0)
        assertTrue(is_owner(table, record_id))
        auth.s3_withdraw_role(user_id, role, for_pe=[])
        assertFalse(is_owner(table, record_id))

        # Unauthenticated does not own this record
        s3_impersonate(None)
        assertFalse(is_owner(table, record_id))

        # ...unless the session owns the record
        auth.s3_make_session_owner(table, record_id)
        assertTrue(is_owner(table, record_id))

    # -------------------------------------------------------------------------
    def testOwnershipOverride(self):
        """ Test override of owners in is_owner """

        auth = current.auth
        s3_impersonate = auth.s3_impersonate
        is_owner = auth.permission.is_owner

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        auth.s3_clear_session_ownership()

        table = self.table
        record_id = self.record_id

        org = current.s3db.pr_get_pe_id("org_organisation", 1)
        role = self.role_id

        user_id = auth.s3_get_user_id("admin@example.com")
        current.db(table.id == record_id).update(realm_entity=org,
                                                 owned_by_group=role,
                                                 owned_by_user=user_id)

        # Normal user does not own the record
        auth.s3_impersonate("normaluser@example.com")
        assertFalse(auth.permission.is_owner(table, record_id))

        # ...unless we override the record's owner stamp
        owners_override = (None, None, None)
        assertTrue(is_owner(table, record_id, owners=owners_override))

    # -------------------------------------------------------------------------
    def testGetOwners(self):
        """ Test lookup of record owners """

        auth = current.auth
        s3_impersonate = auth.s3_impersonate
        is_owner = auth.permission.is_owner
        assertEqual = self.assertEqual

        auth.s3_clear_session_ownership()

        table = self.table
        record_id = self.record_id

        user = auth.s3_get_user_id("admin@example.com")
        role = self.role_id
        org = current.s3db.pr_get_pe_id("org_organisation", 1)

        e, r, u = auth.permission.get_owners(table, None)
        assertEqual(e, None)
        assertEqual(r, None)
        assertEqual(u, None)

        e, r, u = auth.permission.get_owners(None, record_id)
        assertEqual(e, None)
        assertEqual(r, None)
        assertEqual(u, None)

        e, r, u = auth.permission.get_owners(None, None)
        assertEqual(e, None)
        assertEqual(r, None)
        assertEqual(u, None)

        e, r, u = auth.permission.get_owners(table, record_id)
        assertEqual(e, None)
        assertEqual(r, None)
        assertEqual(u, None)

        current.db(table.id == record_id).update(owned_by_user=user,
                                                 owned_by_group=role,
                                                 realm_entity=org)

        e, r, u = auth.permission.get_owners(table, record_id)
        assertEqual(e, org)
        assertEqual(r, role)
        assertEqual(u, user)

        e, r, u = auth.permission.get_owners(table._tablename, record_id)
        assertEqual(e, org)
        assertEqual(r, role)
        assertEqual(u, user)

# =============================================================================
class ACLManagementTests(unittest.TestCase):
    """ Test ACL management/lookup functions """

    # -------------------------------------------------------------------------
    def setUp(self):

        # Stash security policy
        self.policy = current.deployment_settings.get_security_policy()

    # -------------------------------------------------------------------------
    def tearDown(self):

        # Restore security policy
        current.deployment_settings.security.policy = self.policy
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

    # -------------------------------------------------------------------------
    def testApplicableACLsPolicy8(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db

        # Create 3 test organisations
        xmlstr = """
<s3xml>
    <resource name="org_organisation" uuid="TAAO1">
        <data field="name">TestApplicableACLsOrg1</data>
    </resource>
    <resource name="org_organisation" uuid="TAAO2">
        <data field="name">TestApplicableACLsOrg2</data>
    </resource>
    <resource name="org_organisation" uuid="TAAO3">
        <data field="name">TestApplicableACLsOrg3</data>
    </resource>
</s3xml>"""

        try:
            auth.override = True
            from lxml import etree
            xmltree = etree.ElementTree(etree.fromstring(xmlstr))
            resource = s3db.resource("org_organisation")
            resource.import_xml(xmltree)

            resource = s3db.resource("org_organisation",
                                     uid=["TAAO1", "TAAO2", "TAAO3"])
            rows = resource.select(["pe_id", "uuid"], as_rows=True)
            orgs = dict((row.uuid, row.pe_id) for row in rows)
            org1 = orgs["TAAO1"]
            org2 = orgs["TAAO2"]
            org3 = orgs["TAAO3"]
            auth.override = False
        except:
            db.rollback()
            auth.override = False
            raise

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        try:
            # Have two orgs, set org2 as OU descendant of org1
            s3db.pr_add_affiliation(org1, org2, role="TestOrgUnit")

            # Set org3 as non-OU (role_type=9) partner of org1
            partners = s3db.pr_add_affiliation(org1, org3, role="TestPartners", role_type=9)
            assertNotEqual(partners, None)

            # Add the user as OU descendant of org3
            user_id = auth.s3_get_user_id("normaluser@example.com")
            user_pe = auth.s3_user_pe_id(user_id)
            assertNotEqual(user_pe, None)
            s3db.pr_add_affiliation(org3, user_pe, role="TestStaff")

            # Create a TESTGROUP and assign a table ACL
            acl = auth.permission
            role = auth.s3_create_role("Test Group", None,
                                       dict(c="org", f="office", uacl=acl.ALL, oacl=acl.ALL),
                                       dict(t="org_office", uacl=acl.READ, oacl=acl.ALL),
                                       uid="TESTGROUP")

            auth.s3_assign_role(user_id, role)

            # We use delegations (policy 8)
            current.deployment_settings.security.policy = 8
            from s3.s3aaa import S3Permission
            auth.permission = S3Permission(auth)

            # Impersonate as normal user
            auth.s3_impersonate("normaluser@example.com")
            realms = auth.user.realms
            delegations = auth.user.delegations

            # Check permissions
            acls = auth.permission.applicable_acls(acl.DELETE,
                                                   realms,
                                                   delegations,
                                                   c="org",
                                                   f="office",
                                                   t="org_office",
                                                   entity=org2)
            assertTrue(isinstance(acls, dict))
            assertEqual(acls, {})

            # Delegate TESTGROUP to the TestPartners
            auth.s3_delegate_role(role, org1, role="TestPartners")

            # Update realms and delegations
            auth.s3_impersonate("normaluser@example.com")
            realms = auth.user.realms
            delegations = auth.user.delegations

            # Check permissions again
            acls = auth.permission.applicable_acls(acl.DELETE,
                                                   realms,
                                                   delegations,
                                                   c="org",
                                                   f="office",
                                                   t="org_office",
                                                   entity=org2)

            assertTrue(isinstance(acls, dict))
            assertTrue(org2 in acls)
            assertEqual(acls[org2], (acl.READ, acl.ALL))

        finally:
            s3db.pr_remove_affiliation(org1, org2, role="TestOrgUnit")
            s3db.pr_remove_affiliation(org1, org2, role="TestStaff")
            s3db.pr_remove_affiliation(org1, org3, role="TestPartners")
            auth.s3_delete_role("TESTGROUP")
            db.rollback()

# =============================================================================
class HasPermissionTests(unittest.TestCase):
    """ Test permission check method """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        # Create test table
        db = current.db
        tablename = "org_permission_test"
        db.define_table(tablename,
                        Field("name"),
                        *s3_meta_fields())

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

    # -------------------------------------------------------------------------
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
        auth.s3_withdraw_role(auth.user.id, self.reader)

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
        auth.s3_withdraw_role(auth.user.id, self.editor)

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
        auth.s3_withdraw_role(auth.user.id, self.reader)

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
        auth.s3_withdraw_role(auth.user.id, self.editor)

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
        auth.s3_withdraw_role(auth.user.id, self.reader)

        # Test with TESTEDITOR
        auth.s3_assign_role(auth.user.id, self.editor)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        permitted = has_permission("delete", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        auth.s3_withdraw_role(auth.user.id, self.editor)

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
        auth.s3_withdraw_role(auth.user.id, self.reader, for_pe=[])

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
        auth.s3_withdraw_role(auth.user.id, self.editor, for_pe=[])

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
        auth.s3_withdraw_role(auth.user.id, self.editor, for_pe=self.org[0])
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertTrue(permitted)

        # Withdraw role for all realms
        auth.s3_withdraw_role(auth.user.id, self.editor, for_pe=[])
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
        auth.s3_withdraw_role(auth.user.id, self.editor, for_pe=self.org[0])
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
        auth.s3_withdraw_role(auth.user.id, self.editor, for_pe=[])
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertFalse(permitted)

    # -------------------------------------------------------------------------
    def testPolicy8(self):
        """ Test permission check with policy 8 """

        auth = current.auth
        s3db = current.s3db

        current.deployment_settings.security.policy = 8
        auth.permission = S3Permission(auth)

        user = auth.s3_user_pe_id(auth.s3_get_user_id("normaluser@example.com"))

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

        # Add the user as staff member (=OU) of org[2]
        s3db.pr_add_affiliation(self.org[2], user, role="TestStaff")
        auth.s3_assign_role(auth.user.id, self.editor, for_pe=self.org[2])

        # User should not be able to read record1 or record2 (no access),
        # but record3 (as editor for org[2])
        permitted = has_permission("read", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        permitted = has_permission("read", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertFalse(permitted)
        permitted = has_permission("read", c=c, f=f, table=tablename,
                                   record_id=self.record3)
        assertTrue(permitted)

        # User should not be able to update record1 or record2 (no access),
        # but record3 (as editor for org[2])
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertFalse(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record3)
        assertTrue(permitted)

        # Make org[2] and OU of org[1]
        s3db.pr_add_affiliation(self.org[1], self.org[2], role="TestOrgUnit")

        # Delegate TESTREADER from org[0] to org[1]
        auth.s3_delegate_role(self.reader, self.org[0], receiver=self.org[1])

        # Update realms
        auth.s3_impersonate("normaluser@example.com")

        # User should be able to read record1 (reader delegated)
        # and record3 (as editor for org[2]), but not record2 (no access)
        permitted = has_permission("read", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertTrue(permitted)
        permitted = has_permission("read", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertFalse(permitted)
        permitted = has_permission("read", c=c, f=f, table=tablename,
                                   record_id=self.record3)
        assertTrue(permitted)

        # User should be able to update record3 (as editor for org[2]),
        # but not record1 (only reader delegated) or record2 (no access)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record1)
        assertFalse(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record2)
        assertFalse(permitted)
        permitted = has_permission("update", c=c, f=f, table=tablename,
                                   record_id=self.record3)
        assertTrue(permitted)

        auth.s3_remove_delegation(self.reader, self.org[0], receiver=self.org[1])
        s3db.pr_remove_affiliation(self.org[1], self.org[2], role="TestOrgUnit")
        s3db.pr_remove_affiliation(self.org[2], user, role="TestStaff")
        auth.s3_withdraw_role(auth.user.id, self.editor, for_pe=[])

    # -------------------------------------------------------------------------
    def testWithUnavailableTable(self):

        auth = current.auth
        s3db = current.s3db

        has_permission = auth.s3_has_permission
        c = "org"
        f = "permission_test"
        tablename = "org_permission_unavailable"

        auth.s3_impersonate(None)
        permitted = has_permission("read", c=c, f=f, table=tablename)

        # Should return None if the table doesn't exist
        self.assertEqual(permitted, None)

    ## -------------------------------------------------------------------------
    #def testPerformance(self):
        #""" Test has_permission performance """

        #MAX_RUNTIME = 1 # Maximum acceptable runtime per request in milliseconds

        #auth = current.auth
        #current.deployment_settings.security.policy = 8
        #from s3.s3aaa import S3Permission
        #auth.permission = S3Permission(auth)

        #has_permission = auth.s3_has_permission
        #c = "org"
        #f = "permission_test"
        #tablename = "org_permission_test"
        #assertTrue = self.assertTrue
        #assertFalse = self.assertFalse

        #auth.s3_impersonate("normaluser@example.com")
        #auth.s3_assign_role(auth.user.id, self.editor, for_pe=self.org[0])

        #def hasPermission():
            #permitted = has_permission("update", c=c, f=f, table=tablename,
                                       #record_id=self.record1)
        #import timeit
        #runtime = timeit.Timer(hasPermission).timeit(number=1000)
        #if runtime > MAX_RUNTIME:
            #raise AssertionError("has_permission: maximum acceptable run time "
                                 #"exceeded (%.2fms > %.2fms)" %
                                 #(runtime, MAX_RUNTIME))

        #auth.s3_withdraw_role(auth.user.id, self.editor, for_pe=[])

# =============================================================================
class AccessibleQueryTests(unittest.TestCase):
    """ Test accessible query for all policies """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        # Create test table
        db = current.db
        tablename = "org_permission_test"
        db.define_table(tablename,
                        Field("name"),
                        *s3_meta_fields())

        # Create test roles and ACLs
        auth = current.auth
        acl = auth.permission

        NONE = acl.NONE
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

    # -------------------------------------------------------------------------
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
        auth.s3_withdraw_role(auth.user.id, self.reader)

        # Test with TESTEDITOR
        auth.s3_assign_role(auth.user.id, self.editor)
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("update", table, c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)
        auth.s3_withdraw_role(auth.user.id, self.editor)

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
        auth.s3_withdraw_role(auth.user.id, self.reader)

        # Test with TESTEDITOR
        auth.s3_assign_role(auth.user.id, self.editor)
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("update", table, c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)
        auth.s3_withdraw_role(auth.user.id, self.editor)

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
        auth.s3_withdraw_role(auth.user.id, self.reader)

        # Test with TESTEDITOR
        auth.s3_assign_role(auth.user.id, self.editor)
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("update", table, c=c, f=f)
        assertEqual(query, ALL)
        query = accessible_query("delete", table, c=c, f=f)
        assertEqual(query, NONE)
        auth.s3_withdraw_role(auth.user.id, self.editor)

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
        auth.s3_withdraw_role(auth.user.id, self.reader)

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
        auth.s3_withdraw_role(auth.user.id, self.editor)

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
        auth.s3_withdraw_role(auth.user.id, self.reader, for_pe=self.org[0])

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
        auth.s3_withdraw_role(auth.user.id, self.editor)

    # -------------------------------------------------------------------------
    def testPolicy8(self):
        """ Test accessible query with policy 8 """

        s3db = current.s3db
        auth = current.auth

        current.deployment_settings.security.policy = 8
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

        record = None

        # Add the user as staff member (=OU) of org[2] and assign TESTEDITOR
        user = auth.s3_user_pe_id(auth.s3_get_user_id("normaluser@example.com"))
        s3db.pr_add_affiliation(self.org[2], user, role="TestStaff")
        auth.s3_assign_role(auth.user.id, self.editor, for_pe=self.org[2])
        roles = {3, 2}

        # User should only be able to access records of org[2]
        expected = (((table.realm_entity == self.org[2]) | \
                   (table.realm_entity == None)) | \
                   ((((table.owned_by_user == None) & \
                   (table.owned_by_group == None)) & \
                   (table.realm_entity == None)) | \
                   (table.owned_by_group.belongs(roles))))
        query = accessible_query("read", table, c=c, f=f)
        assertEqual(query, expected)
        query = accessible_query("update", table, c=c, f=f)
        assertEqual(query, expected)

        # Make org[2] and OU of org[1]
        s3db.pr_add_affiliation(self.org[1], self.org[2], role="TestOrgUnit")

        # Delegate TESTREADER from org[0] to org[1]
        auth.s3_delegate_role(self.reader, self.org[0], receiver=self.org[1])

        # Update realms
        auth.s3_impersonate("normaluser@example.com")

        # User should now be able to read records of org[0] (delegated
        # reader role) and org[2] (editor role), but update only org[2]
        query = accessible_query("read", table, c=c, f=f)
        expected = (((table.realm_entity.belongs([self.org[0], self.org[2]])) | \
                   (table.realm_entity == None)) | \
                   ((((table.owned_by_user == None) & \
                   (table.owned_by_group == None)) & \
                   (table.realm_entity == None)) | \
                   (table.owned_by_group.belongs(roles))))
        assertEqual(query, expected)
        query = accessible_query("update", table, c=c, f=f)
        expected = (((table.realm_entity == self.org[2]) | \
                   (table.realm_entity == None)) | \
                   ((((table.owned_by_user == auth.user.id) & \
                   ((table.realm_entity == self.org[0]) | \
                   (table.realm_entity == None))) | \
                   (((table.owned_by_user == None) & \
                   (table.owned_by_group == None)) & \
                   (table.realm_entity == None)) | \
                   (table.owned_by_group.belongs(roles)))))
        assertEqual(query, expected)

        # Remove the affiliation org org[2] with org[1]
        s3db.pr_remove_affiliation(self.org[1],
                                   self.org[2],
                                   role="TestOrgUnit")

        # Update realms
        auth.s3_impersonate("normaluser@example.com")

        # Check queries again, user should now only have access to
        # records of org[2] (editor role)
        query = accessible_query("read", table, c=c, f=f)
        expected = (((table.realm_entity == self.org[2]) | \
                   (table.realm_entity == None)) | \
                   ((((table.owned_by_user == None) & \
                   (table.owned_by_group == None)) & \
                   (table.realm_entity == None)) | \
                   (table.owned_by_group.belongs(roles))))
        assertEqual(query, expected)
        query = accessible_query("update", table, c=c, f=f)
        assertEqual(query, expected)

        # Remove delegation, affiliation and role
        s3db.pr_remove_affiliation(self.org[2], user, role="TestStaff")
        s3db.pr_remove_affiliation(self.org[1], self.org[2],
                                   role="TestOrgUnit")
        auth.s3_withdraw_role(user, self.reader, for_pe=self.org[2])

    ## -------------------------------------------------------------------------
    #def testPerformance(self):
        #""" Test accessible query performance """

        #auth = current.auth

        ## Maximum acceptable runtime per request in milliseconds
        #MAX_RUNTIME = 1.5

        #current.deployment_settings.security.policy = 8
        #from s3.s3aaa import S3Permission
        #auth.permission = S3Permission(auth)

        #accessible_query = auth.s3_accessible_query
        #c = "org"
        #f = "permission_test"
        #table = current.s3db.org_permission_test
        #assertEqual = self.assertEqual

        #auth.s3_impersonate("normaluser@example.com")
        #auth.s3_assign_role(auth.user.id, self.editor, for_pe=self.org[0])

        #def accessibleQuery():
            #query = accessible_query("update", table, c=c, f=f)
        #import timeit
        #runtime = timeit.Timer(accessibleQuery).timeit(number=1000)
        #if runtime > MAX_RUNTIME:
            #raise AssertionError("accessible_query: maximum acceptable "
                                 #"run time exceeded (%.2fms > %.2fms)" %
                                 #(runtime, MAX_RUNTIME))
        #auth.s3_withdraw_role(auth.user.id, self.editor, for_pe=[])

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
class DelegationTests(unittest.TestCase):
    """ Test delegation of roles """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        # Create test roles
        s3_create_role = current.auth.s3_create_role
        TESTREADER = "TESTREADER"
        s3_create_role(TESTREADER, None, uid=TESTREADER)
        TESTEDITOR = "TESTEDITOR"
        s3_create_role(TESTEDITOR, None, uid=TESTEDITOR)
        TESTADMIN = "TESTADMIN"
        s3_create_role(TESTADMIN, None, uid=TESTADMIN)
        current.db.commit()

    @classmethod
    def tearDownClass(cls):

        # Remove test roles
        s3_delete_role = current.auth.s3_delete_role
        s3_delete_role("TESTREADER")
        s3_delete_role("TESTEDITOR")
        s3_delete_role("TESTADMIN")
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

        # Remove session ownership
        auth.s3_clear_session_ownership()

        # Logout + turn override off
        auth.s3_impersonate(None)
        auth.override = False

    # -------------------------------------------------------------------------
    def tearDown(self):

        # Rollback
        current.db.rollback()

        # Logout + turn override off
        auth = current.auth
        auth.s3_impersonate(None)
        auth.override = False

        # Restore security policy
        current.deployment_settings.security.policy = self.policy
        auth.permission = S3Permission(auth)

    # -------------------------------------------------------------------------
    def testRoleDelegation(self):
        """ Test delegation of a role """

        s3db = current.s3db
        auth = current.auth

        current.deployment_settings.security.policy = 8
        auth.permission = S3Permission(auth)

        auth.s3_impersonate("normaluser@example.com")
        user = auth.user.pe_id

        org1 = self.org[0]
        org2 = self.org[1]
        org3 = self.org[2]

        pr_add_affiliation = s3db.pr_add_affiliation
        pr_remove_affiliation = s3db.pr_remove_affiliation
        s3_delegate_role = auth.s3_delegate_role
        s3_remove_delegation = auth.s3_remove_delegation

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse
        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual

        READER = self.reader
        EDITOR = self.editor

        # Add the user as staff member (=OU) of org3 and assign TESTEDITOR
        pr_add_affiliation(org3, user, role="TestStaff")
        auth.s3_assign_role(auth.user.id, EDITOR, for_pe=org3)

        # Make org3 an OU descendant of org2
        pr_add_affiliation(org2, org3, role="TestOrgUnit")

        # Delegate the TESTREADER role for org1 to org2
        s3_delegate_role(READER, org1, receiver=org2)

        # Check the delegations
        delegations = auth.user.delegations
        assertTrue(READER in delegations)
        assertTrue(org3 in delegations[READER])
        assertTrue(org1 in delegations[READER][org3])

        s3_remove_delegation(READER, org1, receiver=org2)

        # Check the delegations
        delegations = auth.user.delegations
        assertEqual(list(delegations.keys()), [])

        # Delegate the TESTREADER and TESTEDITOR roles for org1 to org2
        s3_delegate_role([READER, EDITOR], org1, receiver=org2)

        delegations = auth.s3_get_delegations(org1)
        assertNotEqual(delegations, None)
        assertTrue(isinstance(delegations, Storage))
        assertTrue(org2 in delegations)
        assertTrue(isinstance(delegations[org2], list))
        assertEqual(len(delegations[org2]), 2)
        assertTrue(READER in delegations[org2])
        assertTrue(EDITOR in delegations[org2])

        # Check the delegations
        delegations = auth.user.delegations
        assertTrue(READER in delegations)
        assertTrue(EDITOR in delegations)
        assertTrue(org3 in delegations[READER])
        assertTrue(org1 in delegations[READER][org3])
        assertTrue(org3 in delegations[EDITOR])
        assertTrue(org1 in delegations[EDITOR][org3])

        s3_remove_delegation(EDITOR, org1, receiver=org2)

        delegations = auth.s3_get_delegations(org1)
        assertNotEqual(delegations, None)
        assertTrue(isinstance(delegations, Storage))
        assertTrue(org2 in delegations)
        assertTrue(isinstance(delegations[org2], list))
        assertEqual(len(delegations[org2]), 1)
        assertTrue(READER in delegations[org2])

        # Check the delegations
        delegations = auth.user.delegations
        assertTrue(READER in delegations)
        assertFalse(EDITOR in delegations)
        assertTrue(org3 in delegations[READER])
        assertTrue(org1 in delegations[READER][org3])

        s3_remove_delegation(READER, org1, receiver=org2)

        delegations = auth.s3_get_delegations(org1)
        assertNotEqual(delegations, None)
        assertTrue(isinstance(delegations, Storage))
        assertEqual(list(delegations.keys()), [])

        # Check the delegations
        delegations = auth.user.delegations
        assertEqual(list(delegations.keys()), [])

        # Remove delegation, affiliation and role
        pr_remove_affiliation(org3, user, role="TestStaff")
        pr_remove_affiliation(org2, org3, role="TestOrgUnit")
        auth.s3_withdraw_role(user, READER, for_pe=org3)

# =============================================================================
class RecordApprovalTests(unittest.TestCase):
    """ Tests for the record approval framework """

    # -------------------------------------------------------------------------
    def setUp(self):

        auth = current.auth
        settings = current.deployment_settings

        sr = auth.get_system_roles()
        auth.permission.update_acl(sr.AUTHENTICATED,
                                   c="org",
                                   uacl=auth.permission.READ,
                                   oacl=auth.permission.READ|auth.permission.UPDATE)

        auth.permission.update_acl(sr.AUTHENTICATED,
                                   t="org_organisation",
                                   uacl=auth.permission.READ|auth.permission.CREATE,
                                   oacl=auth.permission.READ|auth.permission.UPDATE)

        self.policy = settings.get_security_policy()
        settings.security.policy = 5
        auth.permission = S3Permission(auth)

        self.approval = settings.get_auth_record_approval()
        settings.auth.record_approval = False

        self.approval_for = settings.get_auth_record_approval_required_for()
        settings.auth.record_approval_required_for = None

        auth.override = False
        auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def tearDown(self):

        settings = current.deployment_settings

        settings.auth.record_approval = self.approval
        settings.auth.record_approval_required_for = self.approval_for

        current.auth.s3_impersonate(None)

        # Restore security policy
        settings.security.policy = self.policy
        current.auth.permission = S3Permission(current.auth)

        current.db.rollback()

    # -------------------------------------------------------------------------
    def testRecordApprovedBy(self):
        """ Test whether a new record is unapproved by default """

        db = current.db
        auth = current.auth
        s3db = current.s3db
        settings = current.deployment_settings

        try:
            # Set record approval on
            settings.auth.record_approval = True

            # Impersonate as admin
            auth.s3_impersonate("admin@example.com")

            # Create test record
            otable = s3db.org_organisation
            otable.approved_by.default = None
            org = Storage(name="Test Approval Organisation")
            org_id = otable.insert(**org)
            self.assertTrue(org_id > 0)
            org.update(id=org_id)
            s3db.update_super(otable, org)

            # Check record
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            self.assertNotEqual(row, None)
            self.assertEqual(row.approved_by, None)

        finally:
            db.rollback()
            settings.auth.record_approval = False
            auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testRequiresApproval(self):
        """ Test requires_approval settings """

        s3db = current.s3db
        settings = current.deployment_settings

        approval = settings.get_auth_record_approval()
        tables = settings.get_auth_record_approval_required_for()

        org_approval = s3db.get_config("org_organisation", "requires_approval")

        approval_required = current.auth.permission.requires_approval

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        try:

            # Approval globally turned off
            settings.auth.record_approval = False
            settings.auth.record_approval_required_for = []
            s3db.configure("org_organisation", requires_approval=True)
            assertFalse(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, but set to no tables and table=off
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = []
            s3db.configure("org_organisation", requires_approval=False)
            assertFalse(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, but set to no tables yet table=on
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = []
            s3db.configure("org_organisation", requires_approval=True)
            assertFalse(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, but set to any tables and table=on
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = None
            s3db.configure("org_organisation", requires_approval=True)
            assertTrue(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, but set to different tables and table=on
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = ["project_project"]
            s3db.configure("org_organisation", requires_approval=True)
            assertFalse(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, set to this table and table=off
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = ["org_organisation"]
            s3db.configure("org_organisation", requires_approval=False)
            assertTrue(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, set to any table and table=off
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = None
            s3db.configure("org_organisation", requires_approval=False)
            assertFalse(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

            # Approval globally turned on, set to any table and no table config
            settings.auth.record_approval = True
            settings.auth.record_approval_required_for = None
            s3db.clear_config("org_organisation", "requires_approval")
            assertFalse(approval_required("org_organisation"))
            s3db.clear_config("org_organisation", "requires_approval")

        finally:
            settings.auth.record_approval = approval
            settings.auth.record_approval_required_for = tables
            if org_approval is not None:
                s3db.configure("org_organisation",
                               requires_approval = org_approval)
            current.auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testSetDefaultApprover(self):
        """
            Test whether default approver is set if current user has
            permission to approve records in a table
        """

        auth = current.auth
        acl = auth.permission

        AUTHENTICATED = auth.get_system_roles().AUTHENTICATED

        otable = current.s3db.org_organisation

        otable.approved_by.default = None

        assertEqual = self.assertEqual

        # With record_approval off, and not logged in, default approver is 0
        acl.set_default_approver(otable, force=True)
        assertEqual(otable.approved_by.default, 0)

        auth.s3_impersonate("normaluser@example.com")

        # With record approval off, current user is default approver
        acl.set_default_approver(otable, force=True)
        assertEqual(otable.approved_by.default, auth.user.id)

        current.deployment_settings.auth.record_approval = True

        # With record approval on, default approver depends on permission
        acl.set_default_approver(otable, force=True)
        assertEqual(otable.approved_by.default, None)

        # Give user review and approve permissions on this table
        acl.update_acl(AUTHENTICATED,
                       c="org",
                       uacl=acl.READ|acl.REVIEW|acl.APPROVE,
                       oacl=acl.READ|acl.UPDATE|acl.REVIEW|acl.APPROVE)
        acl.update_acl(AUTHENTICATED,
                       t="org_organisation",
                       uacl=acl.READ|acl.CREATE|acl.REVIEW|acl.APPROVE,
                       oacl=acl.READ|acl.UPDATE|acl.REVIEW|acl.APPROVE)

        auth.s3_impersonate("normaluser@example.com")
        acl.set_default_approver(otable, force=True)
        assertEqual(otable.approved_by.default, auth.user.id)

        auth.s3_impersonate("admin@example.com")
        acl.set_default_approver(otable, force=True)
        assertEqual(otable.approved_by.default, auth.user.id)

        auth.s3_impersonate(None)
        acl.set_default_approver(otable, force=True)
        assertEqual(otable.approved_by.default, None)

    # -------------------------------------------------------------------------
    def testRecordApprovalWithComponents(self):
        """ Test record approval including components """

        db = current.db
        auth = current.auth
        s3db = current.s3db
        settings = current.deployment_settings

        # Set record approval on
        settings.auth.record_approval = True

        self.approved_org = None
        def org_onapprove_test(record):
            self.approved_org = record.id
        org_onapprove = s3db.get_config("org_organisation", "onapprove")
        otable_requires_approval = s3db.get_config("org_organisation", "requires_approval", False)
        s3db.configure("org_organisation",
                       onapprove=org_onapprove_test,
                       requires_approval=True)

        self.approved_office = None
        def office_onapprove_test(record):
            self.approved_office = record.id
        office_onapprove = s3db.get_config("org_office", "onapprove")
        ftable_requires_approval = s3db.get_config("org_office", "requires_approval", False)
        s3db.configure("org_office",
                       onapprove=office_onapprove_test,
                       requires_approval=True)

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        try:
            # Impersonate as admin
            auth.s3_impersonate("admin@example.com")

            # Create test record
            otable = s3db.org_organisation
            otable.approved_by.default = None
            org = Storage(name="Test Approval Organisation")
            org_id = otable.insert(**org)
            assertTrue(org_id > 0)
            org.update(id=org_id)
            s3db.update_super(otable, org)

            # Create test component
            ftable = s3db.org_office
            ftable.approved_by.default = None
            office = Storage(name="Test Approval Office",
                             organisation_id=org_id)
            office_id = ftable.insert(**office)
            assertTrue(office_id > 0)
            office.update(id=office_id)
            s3db.update_super(ftable, office)

            # Check records
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            assertNotEqual(row, None)
            assertEqual(row.approved_by, None)
            row = db(ftable.id==office_id).select(limitby=(0, 1)).first()
            assertNotEqual(row, None)
            assertEqual(row.approved_by, None)

            approved = auth.permission.approved
            unapproved = auth.permission.unapproved

            # Check approved/unapproved
            assertFalse(approved(otable, org_id))
            assertTrue(unapproved(otable, org_id))
            assertFalse(approved(ftable, office_id))
            assertTrue(unapproved(ftable, office_id))

            # Approve
            resource = s3db.resource("org_organisation", id=org_id, unapproved=True)
            assertTrue(resource.approve(components=["office"]))

            # Check record
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            assertNotEqual(row, None)
            assertEqual(row.approved_by, auth.user.id)
            row = db(ftable.id==office_id).select(limitby=(0, 1)).first()
            assertNotEqual(row, None)
            assertEqual(row.approved_by, auth.user.id)

            # Check approved/unapproved
            assertTrue(approved(otable, org_id))
            assertFalse(unapproved(otable, org_id))
            assertTrue(approved(ftable, office_id))
            assertFalse(unapproved(ftable, office_id))

            # Check hooks
            assertEqual(self.approved_org, org_id)
            assertEqual(self.approved_office, office_id)

        finally:
            current.db.rollback()
            settings.auth.record_approval = False
            auth.s3_impersonate(None)

            s3db.configure("org_organisation",
                           onapprove=org_onapprove,
                           requires_approval=otable_requires_approval)
            s3db.configure("org_office",
                           onapprove=office_onapprove,
                           requires_approval=ftable_requires_approval)

    # -------------------------------------------------------------------------
    def testRecordApprovalWithoutComponents(self):
        """ Test record approval without components"""

        db = current.db
        auth = current.auth
        s3db = current.s3db
        settings = current.deployment_settings

        # Set record approval on
        settings.auth.record_approval = True
        otable = s3db.org_organisation
        otable_requires_approval = s3db.get_config(otable, "requires_approval", None)
        s3db.configure(otable, requires_approval=True)
        ftable = s3db.org_office
        ftable_requires_approval = s3db.get_config(ftable, "requires_approval", None)
        s3db.configure(ftable, requires_approval=True)

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        try:
            # Impersonate as admin
            auth.s3_impersonate("admin@example.com")

            # Create test record
            otable = s3db.org_organisation
            otable.approved_by.default = None
            org = Storage(name="Test Approval Organisation")
            org_id = otable.insert(**org)
            assertTrue(org_id > 0)
            org.update(id=org_id)
            s3db.update_super(otable, org)

            # Create test component
            ftable = s3db.org_office
            ftable.approved_by.default = None
            office = Storage(name="Test Approval Office",
                             organisation_id=org_id)
            office_id = ftable.insert(**office)
            assertTrue(office_id > 0)
            office.update(id=office_id)
            s3db.update_super(ftable, office)

            # Check records
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            assertNotEqual(row, None)
            assertEqual(row.approved_by, None)
            row = db(ftable.id==office_id).select(limitby=(0, 1)).first()
            assertNotEqual(row, None)
            assertEqual(row.approved_by, None)

            approved = auth.permission.approved
            unapproved = auth.permission.unapproved

            # Check approved/unapproved
            assertFalse(approved(otable, org_id))
            assertTrue(unapproved(otable, org_id))
            assertFalse(approved(ftable, office_id))
            assertTrue(unapproved(ftable, office_id))

            # Approve
            resource = s3db.resource("org_organisation", id=org_id, unapproved=True)
            assertTrue(resource.approve(components=None))

            # Check record
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            assertNotEqual(row, None)
            assertEqual(row.approved_by, auth.user.id)
            row = db(ftable.id==office_id).select(limitby=(0, 1)).first()
            assertNotEqual(row, None)
            assertEqual(row.approved_by, None)

            # Check approved/unapproved
            assertTrue(approved(otable, org_id))
            assertFalse(unapproved(otable, org_id))
            assertFalse(approved(ftable, office_id))
            assertTrue(unapproved(ftable, office_id))

        finally:
            current.db.rollback()
            settings.auth.record_approval = False
            if otable_requires_approval is not None:
                s3db.configure("org_organisation",
                               requires_approval=otable_requires_approval)
            if ftable_requires_approval is not None:
                s3db.configure("org_office",
                               requires_approval=ftable_requires_approval)
            auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testRecordReject(self):

        db = current.db
        auth = current.auth
        s3db = current.s3db
        settings = current.deployment_settings

        self.rejected_org = None
        def org_onreject_test(record):
            self.rejected_org = record.id
        org_onreject = s3db.get_config("org_organisation", "onreject")
        s3db.configure("org_organisation", onreject=org_onreject_test)

        self.rejected_office = None
        def office_onreject_test(record):
            self.rejected_office = record.id
        office_onreject = s3db.get_config("org_office", "onreject")
        s3db.configure("org_office", onreject=office_onreject_test)

        # Set record approval on
        settings.auth.record_approval = True
        otable = s3db.org_organisation
        otable_requires_approval = s3db.get_config(otable, "requires_approval", None)
        otable.approved_by.default = None
        ftable = s3db.org_office
        ftable_requires_approval = s3db.get_config(ftable, "requires_approval", None)
        ftable.approved_by.default = None

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        try:

            # Impersonate as admin
            auth.s3_impersonate("admin@example.com")

            # Create test record
            org = Storage(name="Test Reject Organisation")
            org_id = otable.insert(**org)
            assertTrue(org_id > 0)
            org.update(id=org_id)
            s3db.update_super(otable, org)

            # Create test component
            office = Storage(name="Test Reject Office",
                             organisation_id=org_id)
            office_id = ftable.insert(**office)
            assertTrue(office_id > 0)
            office.update(id=office_id)
            s3db.update_super(ftable, office)

            # Check records
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            assertNotEqual(row, None)
            assertEqual(row.approved_by, None)
            row = db(ftable.id==office_id).select(limitby=(0, 1)).first()
            assertNotEqual(row, None)
            assertEqual(row.approved_by, None)

            # Activate approval for these tables
            s3db.configure(otable, requires_approval=True)
            s3db.configure(ftable, requires_approval=True)

            approved = auth.permission.approved
            unapproved = auth.permission.unapproved

            # Check approved/unapproved
            assertFalse(approved(otable, org_id))
            assertTrue(unapproved(otable, org_id))
            assertFalse(approved(ftable, office_id))
            assertTrue(unapproved(ftable, office_id))

            # Reject
            resource = s3db.resource("org_organisation", id=org_id, unapproved=True)
            assertTrue(resource.reject())

            # Check records
            row = db(otable.id==org_id).select(limitby=(0, 1)).first()
            assertNotEqual(row, None)
            assertEqual(row.approved_by, None)
            assertTrue(row.deleted)

            row = db(ftable.id==office_id).select(limitby=(0, 1)).first()
            assertNotEqual(row, None)
            assertEqual(row.approved_by, None)
            assertTrue(row.deleted)

            # Check hooks
            assertEqual(self.rejected_org, org_id)
            assertEqual(self.rejected_office, office_id)

        finally:
            current.db.rollback()
            settings.auth.record_approval = False
            auth.s3_impersonate(None)

            s3db.configure("org_organisation", onreject=org_onreject)
            if otable_requires_approval is not None:
                s3db.configure("org_organisation",
                               requires_approval=otable_requires_approval)
            s3db.configure("org_office", onreject=office_onreject)
            if ftable_requires_approval is not None:
                s3db.configure("org_office",
                               onreject=office_onreject,
                               requires_approval=ftable_requires_approval)

    # -------------------------------------------------------------------------
    def testHasPermissionWithRecordApproval(self):
        """ Test has_permission with record approval """

        db = current.db
        auth = current.auth
        acl = auth.permission
        s3db = current.s3db
        settings = current.deployment_settings

        has_permission = auth.s3_has_permission
        AUTHENTICATED = auth.get_system_roles().AUTHENTICATED

        # Store global settings
        approval = settings.get_auth_record_approval()
        approval_required = settings.get_auth_record_approval_required_for()

        # Record approval on, but for no tables
        settings.auth.record_approval = True
        settings.auth.record_approval_required_for = []

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        try:
            # Impersonate as admin
            auth.s3_impersonate("admin@example.com")

            # Create test record
            otable = s3db.org_organisation
            otable.approved_by.default = None
            org = Storage(name="Test Approval Organisation")
            org_id = otable.insert(**org)
            assertTrue(org_id > 0)
            org.update(id=org_id)
            s3db.update_super(otable, org)

            # Give AUTHENTICATED permissions to read all records and
            # update own records in this table (override any default rules):
            acl.update_acl(AUTHENTICATED,
                           c="org",
                           uacl=acl.READ,
                           oacl=acl.READ|acl.UPDATE)
            acl.update_acl(AUTHENTICATED,
                           c="org", f="organisation",
                           uacl=acl.READ,
                           oacl=acl.READ|acl.UPDATE)
            acl.update_acl(AUTHENTICATED,
                           t="org_organisation",
                           uacl=acl.READ,
                           oacl=acl.READ|acl.UPDATE)

            # Normal can see unapproved record if approval is not on for this table
            auth.s3_impersonate("normaluser@example.com")
            permitted = has_permission("read", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)
            permitted = has_permission("update", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)
            permitted = has_permission("delete", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)

            # They can not run any of the approval methods without permission, though
            permitted = has_permission("review", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)
            permitted = has_permission("approve", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)
            permitted = has_permission("reject", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)

            # Turn on approval for this table
            settings.auth.record_approval_required_for = ["org_organisation"]

            # Normal user must not see unapproved record
            auth.s3_impersonate("normaluser@example.com")
            permitted = has_permission("read", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)
            permitted = has_permission("update", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)
            permitted = has_permission("delete", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)

            # Normal user can not review/approve/reject the record
            permitted = has_permission(["read", "review"], otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)
            permitted = has_permission("review", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)
            permitted = has_permission("approve", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)
            permitted = has_permission("reject", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)

            # Normal user can see the unapproved record if he owns it
            db(otable.id==org_id).update(owned_by_user=auth.user.id)

            auth.s3_impersonate("normaluser@example.com")
            permitted = has_permission("read", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)
            permitted = has_permission("update", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)
            permitted = has_permission("delete", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted) # not permitted per default permission rules

            # Normal user can not review/approve/reject the record even if he owns it
            permitted = has_permission("review", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)
            permitted = has_permission("approve", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)
            permitted = has_permission("reject", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)

            db(otable.id==org_id).update(owned_by_user=None)

            # Give user review and approve permissions on this table
            acl.update_acl(AUTHENTICATED,
                           c="org",
                           uacl=acl.READ|acl.REVIEW|acl.APPROVE,
                           oacl=acl.READ|acl.UPDATE|acl.REVIEW|acl.APPROVE)
            acl.update_acl(AUTHENTICATED,
                           c="org", f="organisation",
                           uacl=acl.READ|acl.REVIEW|acl.APPROVE,
                           oacl=acl.READ|acl.UPDATE|acl.REVIEW|acl.APPROVE)
            acl.update_acl(AUTHENTICATED,
                           t="org_organisation",
                           uacl=acl.READ|acl.REVIEW|acl.APPROVE,
                           oacl=acl.READ|acl.UPDATE|acl.REVIEW|acl.APPROVE)

            # Normal user read/update unapproved records now that he has review-permission
            auth.s3_impersonate("normaluser@example.com")
            permitted = has_permission("read", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)
            permitted = has_permission("update", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)
            permitted = has_permission("delete", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted) # not permitted per default permission rules

            # Normal user can review/approve/reject according to permissions
            permitted = has_permission(["read", "review"], otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)
            permitted = has_permission("review", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)
            permitted = has_permission("approve", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)
            permitted = has_permission("reject", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)

            # Admin can always see the record
            auth.s3_impersonate("admin@example.com")
            permitted = has_permission("read", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)

            # Approve the record
            resource = s3db.resource(otable, id=org_id, unapproved=True)
            resource.approve()

            # Normal user can not review/approve/reject once the record is approved
            auth.s3_impersonate("normaluser@example.com")
            permitted = has_permission("review", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)
            permitted = has_permission("approve", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)
            permitted = has_permission("reject", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)

            # Withdraw review and approve permissions on this table for normal users
            acl.update_acl(AUTHENTICATED,
                           c="org",
                           uacl=acl.READ,
                           oacl=acl.READ|acl.UPDATE)
            acl.update_acl(AUTHENTICATED,
                           c="org", f="organisation",
                           uacl=acl.READ,
                           oacl=acl.READ|acl.UPDATE)
            acl.update_acl(AUTHENTICATED,
                           t="org_organisation",
                           uacl=acl.READ|acl.CREATE,
                           oacl=acl.READ|acl.UPDATE)

            # Normal user can now see the record without having review/approve permissions
            auth.s3_impersonate("normaluser@example.com")
            permitted = has_permission("read", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)
            permitted = has_permission("update", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)
            permitted = has_permission("delete", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted) # not allowed as per ACL!

        finally:
            # Restore global settings
            settings.auth.record_approval = approval
            settings.auth.record_approval_required_for = approval_required

            auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    def testAccessibleQueryWithRecordApproval(self):
        """ Test accessible_query with record approval """

        db = current.db
        auth = current.auth
        acl = auth.permission
        s3db = current.s3db
        settings = current.deployment_settings
        accessible_query = auth.s3_accessible_query
        session = current.session

        table = s3db.pr_person

        otable = s3db.org_organisation

        approval = settings.get_auth_record_approval()
        approval_required = settings.get_auth_record_approval_required_for()

        # Record approval on, but for no tables
        settings.auth.record_approval = True
        settings.auth.record_approval_required_for = []

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        try:
            AUTHENTICATED = auth.get_system_roles().AUTHENTICATED

            # Admin can always see all records
            auth.s3_impersonate("admin@example.com")
            query = accessible_query("read", table, c="pr", f="person")
            expected = (table.id > 0)
            assertEqual(str(query), str(expected))

            # User can only see their own records - approved_by not relevant
            auth.s3_impersonate("normaluser@example.com")
            query = accessible_query("read", table, c="pr", f="person")
            assertFalse("approved_by" in str(query))

            table = s3db.org_organisation

            # Approval not required by default
            auth.s3_impersonate("normaluser@example.com")
            query = accessible_query("read", table, c="org", f="organisation")
            expected = (table.id > 0)
            assertEqual(str(query), str(expected))

            settings.auth.record_approval_required_for = ["org_organisation"]

            # Admin can see all records
            auth.s3_impersonate("admin@example.com")

            # See only approved records in read
            query = accessible_query("read", table, c="org", f="organisation")
            expected = (table.approved_by != None) | \
                       (table.owned_by_user == auth.user.id)
            assertEqual(str(query), str(expected))
            # See only unapproved records in review
            query = accessible_query("review", table, c="org", f="organisation")
            expected = (table.approved_by == None)
            assertEqual(str(query), str(expected))
            # See all records with both
            query = accessible_query(["read", "review"], table, c="org", f="organisation")
            expected = (table.id > 0)
            assertEqual(str(query), str(expected))

            # User can only see approved records
            auth.s3_impersonate("normaluser@example.com")

            # See only approved and personally owned records in read
            query = accessible_query("read", table, c="org", f="organisation")
            expected = (table.approved_by != None) | \
                       (table.owned_by_user == auth.user.id)
            assertEqual(str(query), str(expected))
            # See no records in approve
            query = accessible_query("review", table, c="org", f="organisation")
            expected = (table.id == 0)
            assertEqual(str(query), str(expected))
            # See only approved and personally owned records with both
            query = accessible_query(["read", "review"], table, c="org", f="organisation")
            expected = (table.approved_by != None) | \
                       (table.owned_by_user == auth.user.id)
            assertEqual(str(query), str(expected))

            # Give user review and approve permissions on this table
            acl.update_acl(AUTHENTICATED,
                           c="org",
                           uacl=acl.READ|acl.REVIEW|acl.APPROVE,
                           oacl=acl.READ|acl.UPDATE|acl.REVIEW|acl.APPROVE)
            acl.update_acl(AUTHENTICATED,
                           c="org", f="organisation",
                           uacl=acl.READ|acl.REVIEW|acl.APPROVE,
                           oacl=acl.READ|acl.UPDATE|acl.REVIEW|acl.APPROVE)
            acl.update_acl(AUTHENTICATED,
                           t="org_organisation",
                           uacl=acl.READ|acl.CREATE|acl.REVIEW|acl.APPROVE,
                           oacl=acl.READ|acl.UPDATE|acl.REVIEW|acl.APPROVE)

            # User can now access unapproved records
            auth.s3_impersonate("normaluser@example.com")

            # See only approved records in read
            query = accessible_query("read", table, c="org", f="organisation")
            expected = (table.approved_by != None) | \
                       (table.owned_by_user == auth.user.id)
            assertTrue(str(expected) in str(query))
            # See only unapproved records in review
            query = accessible_query("review", table, c="org", f="organisation")
            expected = (table.approved_by != None)
            assertFalse(str(expected) in str(query))
            expected = (table.approved_by == None)
            assertTrue(str(expected) in str(query))
            # See all records with both
            query = accessible_query(["read", "approve"], table, c="org", f="organisation")
            expected = (table.approved_by != None) | \
                       (table.owned_by_user == auth.user.id)
            assertTrue(str(expected) in str(query))
            expected = (table.approved_by == None)
            assertTrue(str(expected) in str(query))

            # Turn off record approval and check the default query
            settings.auth.record_approval = False

            query = accessible_query("read", table, c="org", f="organisation")
            expected = (table.id > 0)
            assertEqual(str(query), str(expected))

        finally:
            settings.auth.record_approval = approval
            settings.auth.record_approval_required_for = approval_required
            auth.s3_impersonate(None)

# =============================================================================
class RealmEntityTests(unittest.TestCase):
    """ Test customization hooks for realm entity """

    # -------------------------------------------------------------------------
    def setUp(self):

        db = current.db
        s3db = current.s3db

        # Create a dummy record
        otable = s3db.org_organisation
        org = Storage(name="Ownership Test Organisation")
        org_id = otable.insert(**org)
        org.update(id=org_id)
        s3db.update_super(otable, org)

        self.org_id = org_id

        # Create a dummy record
        ftable = s3db.org_office
        office = Storage(organisation_id=self.org_id,
                         name="Ownership Test Office")
        office_id = ftable.insert(**office)
        office.update(id=office_id)
        s3db.update_super(ftable, office)

        self.office_id = office_id

        # Clear the hooks
        tname = "org_organisation"
        settings = current.deployment_settings
        self.ghook = settings.get_auth_realm_entity()
        self.shook = s3db.get_config(tname, "realm_entity")
        settings.auth.realm_entity = None
        s3db.clear_config(tname, "realm_entity")

        self.owned_record = None

    # -------------------------------------------------------------------------
    def testTableSpecificRealmEntity(self):
        """ Test table-specific realm_entity hook """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        otable = s3db.org_organisation
        record = otable[self.org_id]

        tname = "org_organisation"
        s3db.configure(tname, realm_entity = self.realm_entity)

        auth.s3_set_record_owner(otable, record, force_update=True)
        self.assertEqual(self.owned_record, (tname, record.id))

    # -------------------------------------------------------------------------
    def testGlobalRealmEntity(self):
        """ Test global realm_entity hook """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        otable = s3db.org_organisation
        record = otable[self.org_id]

        tname = "org_organisation"
        settings.auth.realm_entity = self.realm_entity

        auth.s3_set_record_owner(otable, record, force_update=True)
        self.assertEqual(self.owned_record, (tname, record.id))

    # -------------------------------------------------------------------------
    def testRealmEntityOverride(self):
        """ Check whether global realm_entity hook overrides any table-specific setting """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        otable = s3db.org_organisation
        record = otable[self.org_id]

        tname = "org_organisation"
        s3db.configure(tname, realm_entity = self.realm_entity)
        settings.auth.realm_entity = self.realm_entity_override

        auth.s3_set_record_owner(otable, record, force_update=True)
        self.assertEqual(self.owned_record, "checked")

    # -------------------------------------------------------------------------
    def testSetRealmEntityWithRecord(self):
        """ Test the realm entity can be set for a record """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        otable = s3db.org_organisation
        record = otable[self.org_id]

        tname = "org_organisation"
        settings.auth.realm_entity = self.realm_entity

        assertEqual = self.assertEqual

        auth.set_realm_entity(otable, record, force_update=True)
        assertEqual(self.owned_record, (tname, record.id))
        record = otable[self.org_id]
        assertEqual(record.realm_entity, 5)

    # -------------------------------------------------------------------------
    def testSetRealmEntityWithRealmComponent(self):
        """ Test whether the realm entity of the component updates automatically """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        realm_components = s3db.get_config("org_organisation",
                                           "realm_components", "none")
        s3db.configure("org_organisation",
                       realm_components = ["office"])

        assertEqual = self.assertEqual

        try:
            otable = s3db.org_organisation
            ftable = s3db.org_office

            settings.auth.realm_entity = self.realm_entity

            record = otable[self.org_id]
            record.update_record(realm_entity = None)
            record = ftable[self.office_id]
            record.update_record(realm_entity = None)

            record = otable[self.org_id]
            auth.set_realm_entity(otable, record, force_update=True)

            tname = "org_organisation"
            assertEqual(self.owned_record, (tname, record.id))

            record = otable[self.org_id]
            assertEqual(record.realm_entity, 5)

            record = ftable[self.office_id]
            assertEqual(record.realm_entity, 5)
        finally:
            if realm_components != "none":
                s3db.configure("org_organisation",
                               realm_components=realm_components)
            else:
                s3db.clear_config("org_organisation", "realm_components")

    # -------------------------------------------------------------------------
    def testSetRealmEntityWithRecordID(self):
        """ Test the realm entity can be set for a record ID """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        otable = s3db.org_organisation
        record = otable[self.org_id]

        tname = "org_organisation"
        settings.auth.realm_entity = self.realm_entity

        assertEqual = self.assertEqual

        auth.set_realm_entity(otable, self.org_id, force_update=True)
        assertEqual(self.owned_record, (tname, record.id))
        record = otable[self.org_id]
        assertEqual(record.realm_entity, 5)

    # -------------------------------------------------------------------------
    def testSetRealmEntityWithRecordIDList(self):
        """ Test the realm entity can be set for a list of record IDs """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        otable = s3db.org_organisation
        record = otable[self.org_id]

        tname = "org_organisation"
        settings.auth.realm_entity = self.realm_entity

        assertEqual = self.assertEqual

        auth.set_realm_entity(otable, [self.org_id], force_update=True)
        assertEqual(self.owned_record, (tname, record.id))
        record = otable[self.org_id]
        assertEqual(record.realm_entity, 5)

    # -------------------------------------------------------------------------
    def testSetRealmEntityWithQuery(self):
        """ Test the realm entity can be set for a query """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        otable = s3db.org_organisation
        record = otable[self.org_id]

        tname = "org_organisation"
        settings.auth.realm_entity = self.realm_entity

        assertEqual = self.assertEqual

        query = (otable.id == self.org_id)
        auth.set_realm_entity(otable, query, force_update=True)
        assertEqual(self.owned_record, (tname, record.id))
        record = otable[self.org_id]
        assertEqual(record.realm_entity, 5)

    # -------------------------------------------------------------------------
    def testSetRealmEntityWithQueryAndOverride(self):
        """ Test that realm entity can be overridden by call """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        otable = s3db.org_organisation

        tname = "org_organisation"
        settings.auth.realm_entity = self.realm_entity

        assertEqual = self.assertEqual

        query = (otable.id == self.org_id)
        auth.set_realm_entity(otable, query, entity=4, force_update=True)
        assertEqual(self.owned_record, None)

        record = otable[self.org_id]
        assertEqual(record.realm_entity, 4)

    # -------------------------------------------------------------------------
    def testSetRealmEntityWithQueryAndOverrideNone(self):
        """ Test that realm entity can be set to None """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        otable = s3db.org_organisation

        tname = "org_organisation"
        settings.auth.realm_entity = self.realm_entity

        assertEqual = self.assertEqual

        query = (otable.id == self.org_id)
        auth.set_realm_entity(otable, query, entity=None, force_update=True)
        assertEqual(self.owned_record, None)

        record = otable[self.org_id]
        assertEqual(record.realm_entity, None)

    # -------------------------------------------------------------------------
    def testUpdateSharedFields(self):
        """ Test that realm entity gets set in super-entity """

        s3db = current.s3db
        auth = current.auth
        settings = current.deployment_settings

        ftable = s3db.org_office
        stable = s3db.org_site

        assertEqual = self.assertEqual

        row = ftable[self.office_id]
        row.update_record(realm_entity=row["pe_id"])

        site_id = row["site_id"]

        auth.update_shared_fields(ftable, self.office_id, realm_entity=None)
        site = stable[site_id]
        assertEqual(site["realm_entity"], None)

        auth.update_shared_fields(ftable, self.office_id, realm_entity=row["realm_entity"])
        site = stable[site_id]
        assertEqual(site["realm_entity"], row["realm_entity"])

    # -------------------------------------------------------------------------
    def realm_entity(self, table, row):
        """ Dummy method for hook testing """

        self.owned_record = (table._tablename, row.id)
        return 5

    # -------------------------------------------------------------------------
    def realm_entity_override(self, table, row):
        """ Dummy method for hook testing """

        self.owned_record = "checked"
        return 6

    # -------------------------------------------------------------------------
    def tearDown(self):

        s3db = current.s3db
        settings = current.deployment_settings

        # Rollback DB
        current.db.rollback()

        # Restore the hooks
        settings.auth.realm_entity = self.ghook
        if self.shook is not None:
            s3db.configure("org_organisation", realm_entity=self.shook)

# =============================================================================
class LinkToPersonTests(unittest.TestCase):
    """ Test s3_link_to_person """

    # -------------------------------------------------------------------------
    def setUp(self):

        s3db = current.s3db

        assertTrue = self.assertTrue

        # Create organisation
        otable = s3db.org_organisation
        org = Storage(name="LTPRTestOrg")
        org_id = otable.insert(**org)
        assertTrue(org_id is not None)
        org["id"] = org_id
        s3db.update_super(otable, org)
        self.org_id = org_id
        self.org_pe_id = org.pe_id

        # Create person record
        ptable = s3db.pr_person
        person = Storage(first_name="TestLTPR",
                         last_name="User")
        person_id = ptable.insert(**person)
        assertTrue(person_id is not None)
        person["id"] = person_id
        s3db.update_super(ptable, person)
        self.person_id = person_id
        self.pe_id = person.pe_id

        # Add email contact
        ctable = s3db.pr_contact
        contact = Storage(pe_id=self.pe_id,
                          contact_method="EMAIL",
                          value="testltpr@example.com")
        contact_id = ctable.insert(**contact)
        assertTrue(contact_id is not None)

    # -------------------------------------------------------------------------
    def testLinkToNewPerson(self):
        """ Test linking a user account to a new person record """

        auth = current.auth
        s3db = current.s3db

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        # Create new user record
        utable = auth.settings.table_user
        user = Storage(first_name="TestLTPR2",
                       last_name="User",
                       email="testltpr2@example.com",
                       password="XYZ")
        user_id = utable.insert(**user)
        assertTrue(user_id is not None)
        user["id"] = user_id

        # Link to person
        person_id = auth.s3_link_to_person(user, self.org_id)

        # Check the person_id
        assertNotEqual(person_id, None)
        assertFalse(isinstance(person_id, list))
        assertNotEqual(person_id, self.person_id)

        # Get the person record
        ptable = s3db.pr_person
        person = ptable[person_id]
        assertNotEqual(person, None)

        # Check the owner
        assertEqual(person.realm_entity, self.org_pe_id)

        # Check the link
        ltable = s3db.pr_person_user
        query = (ltable.user_id == user_id) & \
                (ltable.pe_id == person.pe_id)
        links = current.db(query).select()
        assertEqual(len(links), 1)

    # -------------------------------------------------------------------------
    def testLinkToExistingPerson(self):
        """ Test linking a user account to a pre-existing person record """

        auth = current.auth
        s3db = current.s3db

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        # Create new user record
        utable = auth.settings.table_user
        user = Storage(first_name="TestLTPR",
                       last_name="User",
                       email="testltpr@example.com",
                       password="XYZ")
        user_id = utable.insert(**user)
        assertTrue(user_id is not None)
        user["id"] = user_id

        # Link to person record
        person_id = auth.s3_link_to_person(user, self.org_id)

        # Check the person_id
        assertNotEqual(person_id, None)
        assertFalse(isinstance(person_id, list))
        assertEqual(person_id, self.person_id)

        # Get the person record
        ptable = s3db.pr_person
        person = ptable[person_id]
        assertNotEqual(person, None)

        # Check the link
        ltable = s3db.pr_person_user
        query = (ltable.user_id == user_id) & \
                (ltable.pe_id == person.pe_id)
        links = current.db(query).select()
        assertEqual(len(links), 1)

    # -------------------------------------------------------------------------
    def testUpdateLinkedPerson(self):
        """ Test update of a pre-linked person record upon user account update """

        auth = current.auth
        s3db = current.s3db

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        # Create new user record
        utable = auth.settings.table_user
        user = Storage(first_name="TestLTPR",
                       last_name="User",
                       email="testltpr@example.com",
                       password="XYZ")
        user_id = utable.insert(**user)
        assertTrue(user_id is not None)
        user["id"] = user_id

        # Link to person
        person_id = auth.s3_link_to_person(user, self.org_id)

        # Check the person_id
        assertNotEqual(person_id, None)
        assertFalse(isinstance(person_id, list))
        assertEqual(person_id, self.person_id)

        # Update the user record
        update = Storage(first_name="TestLTPR2",
                         last_name="User",
                         email="testltpr2@example.com")
        current.db(utable.id == user_id).update(**update)
        update["id"] = user_id

        # Link to person record again
        update_id = auth.s3_link_to_person(user, self.org_id)

        # Check unchanged person_id
        assertEqual(update_id, person_id)

        # Check updated person record
        ptable = s3db.pr_person
        person = ptable[update_id]
        assertEqual(person.first_name, update["first_name"])
        assertEqual(person.last_name, update["last_name"])

        # Check updated contact record
        ctable = s3db.pr_contact
        query = (ctable.pe_id == self.pe_id) & \
                (ctable.contact_method == "EMAIL")
        contacts = current.db(query).select()
        assertEqual(len(contacts), 2)
        emails = [contact.value for contact in contacts]
        assertTrue(user.email in emails)
        assertTrue(update.email in emails)

    # -------------------------------------------------------------------------
    def testMultipleUserRecords(self):
        """ Test s3_link_to_person with multiple user accounts """

        auth = current.auth
        s3db = current.s3db

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue

        # Create new user records
        utable = auth.settings.table_user
        users = []
        user1 = Storage(first_name="TestLTPR1",
                       last_name="User",
                       email="testltpr1@example.com",
                       password="XYZ")
        user_id = utable.insert(**user1)
        assertTrue(user_id is not None)
        user1["id"] = user_id
        users.append(user1)

        user2 = Storage(first_name="TestLTPR2",
                       last_name="User",
                       email="testltpr2@example.com",
                       password="XYZ")
        user_id = utable.insert(**user2)
        assertTrue(user_id is not None)
        user2["id"] = user_id
        users.append(user2)

        user3 = Storage(first_name="TestLTPR3",
                       last_name="User",
                       email="testltpr3@example.com",
                       password="XYZ")
        user_id = utable.insert(**user3)
        assertTrue(user_id is not None)
        user3["id"] = user_id
        users.append(user3)

        person_ids = auth.s3_link_to_person(users, self.org_id)
        assertTrue(isinstance(person_ids, list))
        assertEqual(len(person_ids), 3)

        auth.s3_impersonate("testltpr2@example.com")
        pe_id = auth.user.pe_id
        ptable = s3db.pr_person
        query = (ptable.pe_id == pe_id)
        person2 = current.db(query).select().first()
        assertNotEqual(person2, None)
        assertTrue(person2.id in person_ids)

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.auth.s3_impersonate(None)
        current.db.rollback()

# =============================================================================
class EntityRoleManagerTests(unittest.TestCase):
    """ Test the entity role manager """

    # -------------------------------------------------------------------------
    def setUp(self):

        auth = current.auth

        # Test-login as system administrator
        auth.s3_impersonate("admin@example.com")

        self.rm = S3EntityRoleManager()

        self.user_id = auth.s3_get_user_id("normaluser@example.com")
        self.org_id = 1

        auth.s3_assign_role(self.user_id, "staff_reader", for_pe=self.org_id)
        auth.s3_assign_role(self.user_id, "project_editor", for_pe=self.org_id)

    # -------------------------------------------------------------------------
    def testGetAssignedRoles(self):
        """ Test get_assigned_roles """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        get_assigned_roles = self.rm.get_assigned_roles

        org_id = self.org_id
        user_id = self.user_id

        roles = get_assigned_roles(entity_id=org_id)
        assertTrue(user_id in roles)
        assigned_roles = roles[user_id]
        assertEqual(len(assigned_roles), 2)
        assertTrue("staff_reader" in assigned_roles)
        assertTrue("project_editor" in assigned_roles)

        roles = get_assigned_roles(entity_id=org_id, user_id=user_id)
        assertTrue(user_id in roles)
        assigned_roles = roles[user_id]
        assertEqual(len(assigned_roles), 2)
        assertTrue("staff_reader" in assigned_roles)
        assertTrue("project_editor" in assigned_roles)

        assigned_roles = get_assigned_roles(user_id=user_id)
        assertTrue(all([r in assigned_roles[org_id]
                        for r in ("staff_reader", "project_editor")]))
        assertEqual(len(assigned_roles[org_id]), 2)

        roles = get_assigned_roles(user_id=user_id)
        assertTrue(org_id in roles)
        assigned_roles = roles[org_id]
        assertEqual(len(assigned_roles), 2)
        assertTrue("staff_reader" in assigned_roles)
        assertTrue("project_editor" in assigned_roles)

        with self.assertRaises(RuntimeError):
            get_assigned_roles()

    # -------------------------------------------------------------------------
    def testUpdateRoles(self):
        """ Test that before/after works """

        before = ("staff_reader", "project_editor")
        after = ("survey_reader",)

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue

        rm = self.rm
        get_assigned_roles = rm.get_assigned_roles
        update_roles = rm.update_roles

        org_id = self.org_id
        user_id = self.user_id

        # Give the user a new set of roles
        update_roles(user_id, org_id, before, after)
        assigned_roles = get_assigned_roles(user_id=user_id)
        assertTrue(org_id in assigned_roles)
        assertTrue(all([r in assigned_roles[org_id]
                        for r in after]))
        assertEqual(len(assigned_roles[org_id]), len(after))

        # Reverse the changes
        update_roles(user_id, org_id, after, before)
        assigned_roles = get_assigned_roles(user_id=user_id)
        assertTrue(org_id in assigned_roles)
        assertTrue(all([r in assigned_roles[org_id]
                             for r in before]))
        assertEqual(len(assigned_roles[org_id]), len(before))

    # -------------------------------------------------------------------------
    def tearDown(self):

        auth = current.auth
        auth.s3_impersonate(None)
        auth.s3_withdraw_role(self.user_id, "staff_reader", for_pe=self.org_id)
        auth.s3_withdraw_role(self.user_id, "project_editor", for_pe=self.org_id)
        current.db.rollback()

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):
        pass

# =============================================================================
if __name__ == "__main__":

    run_suite(
        AuthUtilsTests,
        SetRolesTests,
        RoleAssignmentTests,
        RecordOwnershipTests,
        ACLManagementTests,
        HasPermissionTests,
        AccessibleQueryTests,
        DelegationTests,
        RecordApprovalTests,
        RealmEntityTests,
        LinkToPersonTests,
        EntityRoleManagerTests,
        )

# END ========================================================================
