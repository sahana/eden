# Eden Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/core/aaa/auth.py
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

# =============================================================================
class RoleAssignmentTests(unittest.TestCase):
    """ Test role assignments """

    def tearDown(self):

        current.db.rollback()

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
            auth.s3_remove_role(user_id, role_id, for_pe=None)

            auth.s3_assign_role(user_id, role_id, for_pe=0)
            roles = auth.s3_get_roles(user_id)
            assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=None)
            assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=0)
            assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=1)
            assertFalse(role_id in roles)
            auth.s3_remove_role(user_id, role_id, for_pe=0)

            auth.s3_assign_role(user_id, role_id, for_pe=1)
            roles = auth.s3_get_roles(user_id)
            assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=None)
            assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=0)
            assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=1)
            assertTrue(role_id in roles)
            auth.s3_remove_role(user_id, role_id, for_pe=1)

        finally:
            auth.s3_delete_role(UUID)
            auth.s3_impersonate(None)

# =============================================================================
class RecordOwnershipTests(unittest.TestCase):
    """ Test record ownership """

    @classmethod
    def setUpClass(cls):

        tablename = "ownership_test_table"
        current.db.define_table(tablename,
                                Field("name"),
                                *MetaFields())

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
        auth.s3_remove_role(user_id, role, for_pe=[])
        assertFalse(is_owner(table, record_id))

        # ....or have the role without limitation (any org)
        auth.s3_assign_role(user_id, role, for_pe=0)
        assertTrue(is_owner(table, record_id))
        auth.s3_remove_role(user_id, role, for_pe=[])
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
class RecordApprovalTests(unittest.TestCase):
    """ Tests for the record approval framework """

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
            assertFalse(permitted)
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

            # Normal user read unapproved records now that he has review-permission
            auth.s3_impersonate("normaluser@example.com")
            permitted = has_permission("read", otable, record_id=org_id, c="org", f="organisation")
            assertTrue(permitted)
            permitted = has_permission("update", otable, record_id=org_id, c="org", f="organisation")
            assertFalse(permitted)
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
            assertFalse(permitted)
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

        auth = current.auth
        acl = auth.permission
        s3db = current.s3db
        settings = current.deployment_settings
        accessible_query = auth.s3_accessible_query

        table = s3db.pr_person

        approval = settings.get_auth_record_approval()
        approval_required = settings.get_auth_record_approval_required_for()

        # Record approval on, but for no tables
        settings.auth.record_approval = True
        settings.auth.record_approval_required_for = []

        assertEqual = self.assertEqual
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

    def setUp(self):

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

    def tearDown(self):

        s3db = current.s3db
        settings = current.deployment_settings

        # Rollback DB
        current.db.rollback()

        # Restore the hooks
        settings.auth.realm_entity = self.ghook
        if self.shook is not None:
            s3db.configure("org_organisation", realm_entity=self.shook)

    # -------------------------------------------------------------------------
    def testTableSpecificRealmEntity(self):
        """ Test table-specific realm_entity hook """

        s3db = current.s3db
        auth = current.auth

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

# =============================================================================
class LinkToPersonTests(unittest.TestCase):
    """ Test s3_link_to_person """

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

    def tearDown(self):

        current.auth.s3_impersonate(None)
        current.db.rollback()

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

# =============================================================================
if __name__ == "__main__":

    run_suite(
        AuthUtilsTests,
        SetRolesTests,
        RoleAssignmentTests,
        RecordOwnershipTests,
        RecordApprovalTests,
        RealmEntityTests,
        LinkToPersonTests,
        )

# END ========================================================================
