# -*- coding: utf-8 -*-
#
# S3AAA Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/tests/unit_tests/modules/s3/s3aaa.py
#
import unittest

from gluon import current

# =============================================================================
class S3AuthTests(unittest.TestCase):
    """ S3Auth Tests """

    def setUp(self):
        pass

    # -------------------------------------------------------------------------
    # Role Management
    #
    def testSystemRoles(self):
        """ Test if system roles are present """

        sr = auth.get_system_roles()
        self.assertTrue("ADMIN" in sr)
        self.assertTrue(sr.ADMIN is not None)

    # -------------------------------------------------------------------------
    # Authentication
    #
    def testGetUserIDByEmail(self):

        user_id = auth.s3_get_user_id("normaluser@example.com")
        self.assertTrue(user_id is not None)

    def testImpersonate(self):
        """ Test s3_impersonate function """

        sr = auth.get_system_roles()
        ADMIN = sr.ADMIN
        ANONYMOUS = sr.ANONYMOUS

        # Test-login as system administrator
        auth.s3_impersonate("admin@example.com")
        self.assertTrue(auth.s3_logged_in())
        self.assertTrue(auth.user is not None)
        self.assertTrue(ADMIN in session.s3.roles)
        self.assertTrue(ANONYMOUS in session.s3.roles)
        self.assertTrue(ADMIN in auth.user.realms)

        # Test with nonexistent user
        self.assertRaises(ValueError, auth.s3_impersonate, "NonExistentUser")
        # => should still be logged in as ADMIN
        self.assertTrue(auth.s3_logged_in())
        self.assertTrue(ADMIN in session.s3.roles)

        # Test with None => should logout and reset the roles
        auth.s3_impersonate(None)
        self.assertFalse(auth.s3_logged_in())
        self.assertTrue(session.s3.roles == [] or
                        ANONYMOUS in session.s3.roles)

        # Logout
        auth.s3_impersonate(None)

    def testSetRolesPolicy3(self):

        deployment_settings.security.policy = 3
        auth.permission = s3base.S3Permission(auth)
        auth.s3_impersonate("normaluser@example.com")
        realms = auth.user.realms.keys()
        self.assertTrue(2 in realms)
        self.assertTrue(3 in realms)
        self.assertEqual(len(realms), 2)
        for r in auth.user.realms:
            self.assertEqual(auth.user.realms[r], None)
        auth.s3_impersonate(None)

    def testSetRolesPolicy4(self):

        deployment_settings.security.policy = 4
        auth.permission = s3base.S3Permission(auth)
        auth.s3_impersonate("normaluser@example.com")
        realms = auth.user.realms.keys()
        self.assertTrue(2 in realms)
        self.assertTrue(3 in realms)
        self.assertEqual(len(realms), 2)
        for r in auth.user.realms:
            self.assertEqual(auth.user.realms[r], None)
        auth.s3_impersonate(None)

    def testSetRolesPolicy5(self):

        deployment_settings.security.policy = 5
        auth.permission = s3base.S3Permission(auth)
        auth.s3_impersonate("normaluser@example.com")
        realms = auth.user.realms.keys()
        self.assertTrue(2 in realms)
        self.assertTrue(3 in realms)
        self.assertEqual(len(realms), 2)
        for r in auth.user.realms:
            self.assertEqual(auth.user.realms[r], None)
        auth.s3_impersonate(None)

    def testSetRolesPolicy6(self):

        try:
            org = s3db.pr_get_pe_id("org_organisation", 1)
            role = auth.s3_create_role("Example Role", uid="TESTROLE")
            user_id = auth.s3_get_user_id("normaluser@example.com")
            auth.s3_assign_role(user_id, role, for_pe=org)

            deployment_settings.security.policy = 6
            auth.permission = s3base.S3Permission(auth)
            auth.s3_impersonate("normaluser@example.com")
            realms = auth.user.realms.keys()
            self.assertTrue(2 in realms)
            self.assertTrue(3 in realms)
            self.assertTrue(role in realms)
            self.assertEqual(len(realms), 3)
            for r in auth.user.realms:
                if r == role:
                    self.assertEqual(auth.user.realms[r], [org])
                else:
                    self.assertEqual(auth.user.realms[r], None)
            auth.s3_impersonate(None)
        finally:
            auth.s3_delete_role("TESTROLE")

    def testSetRolesPolicy7(self):

        try:
            org1 = s3db.pr_get_pe_id("org_organisation", 1)
            org2 = s3db.pr_get_pe_id("org_organisation", 2)
            s3db.pr_add_affiliation(org1, org2, role="TestRole")

            role = auth.s3_create_role("Example Role", uid="TESTROLE")
            user_id = auth.s3_get_user_id("normaluser@example.com")
            auth.s3_assign_role(user_id, role, for_pe=org1)

            deployment_settings.security.policy = 7
            auth.permission = s3base.S3Permission(auth)
            auth.s3_impersonate("normaluser@example.com")
            realms = auth.user.realms.keys()
            self.assertTrue(2 in realms)
            self.assertTrue(3 in realms)
            self.assertTrue(role in realms)
            self.assertEqual(len(realms), 3)
            for r in auth.user.realms:
                if r == role:
                    self.assertTrue(org1 in auth.user.realms[r])
                    self.assertTrue(org2 in auth.user.realms[r])
                else:
                    self.assertEqual(auth.user.realms[r], None)
            auth.s3_impersonate(None)
        finally:
            auth.s3_delete_role("TESTROLE")
            db.rollback()

    def testSetRolesPolicy8(self):
        """ Test s3_set_roles for entity hierarchy plus delegations (policy8) """

        try:
            # Have two orgs, set org2 as OU descendant of org1
            org1 = s3db.pr_get_pe_id("org_organisation", 1)
            org2 = s3db.pr_get_pe_id("org_organisation", 2)
            s3db.pr_add_affiliation(org1, org2, role="TestOrgUnit")

            # Set org3 as non-OU (role_type=9) partner of org1
            org3 = s3db.pr_get_pe_id("org_organisation", 3)

            # Add the user as OU descendant of org3
            user = auth.s3_user_pe_id(auth.s3_get_user_id("normaluser@example.com"))
            self.assertNotEqual(user, None)
            s3db.pr_add_affiliation(org3, user, role="TestStaff")

            # Create a Test auth_group and delegate it to the TestPartners
            role = auth.s3_create_role("Test Group", uid="TESTGROUP")

            # We use delegations (policy 8)
            deployment_settings.security.policy = 8
            auth.permission = s3base.S3Permission(auth)

            auth.s3_delegate_role("TESTGROUP", org1, receiver=org3)

            # Impersonate as normal user
            auth.s3_impersonate("normaluser@example.com")

            # Check the realms
            realms = auth.user.realms.keys()
            self.assertTrue(2 in realms)
            self.assertTrue(3 in realms)
            self.assertEqual(len(realms), 2)

            for r in auth.user.realms:
                if r == role:
                    self.assertTrue(org3 in auth.user.realms[r])
                else:
                    self.assertEqual(auth.user.realms[r], None)

            # Check the delegations
            delegations = auth.user.delegations.keys()
            self.assertTrue(role in delegations)
            self.assertEqual(len(delegations), 1)

            realms = auth.user.delegations[role]
            self.assertTrue(org3 in realms)
            self.assertEqual(len(realms), 1)
            self.assertTrue(org1 in realms[org3])
            self.assertTrue(org2 in realms[org3])

            auth.s3_remove_delegation("TESTGROUP", org1, receiver=org3)

            # Check the delegations
            delegations = auth.user.delegations.keys()
            self.assertFalse(role in delegations)
            self.assertEqual(len(delegations), 0)

            # Logout
            auth.s3_impersonate(None)

        finally:
            s3db.pr_remove_affiliation(org1, org2, role="TestOrgUnit")
            s3db.pr_remove_affiliation(org1, org2, role="TestStaff")
            s3db.pr_remove_affiliation(org1, org3, role="TestPartners")
            auth.s3_delete_role("TESTGROUP")
            db.rollback()

    #def testPerformance(self):

        #MAX_RUNTIME = 18 # Maximum acceptable runtime per request in milliseconds
        ##MAX_RUNTIME = 3 # Maximum acceptable runtime per request in milliseconds (up to policy 7)

        #deployment_settings.security.policy = 8
        #auth.permission = s3base.S3Permission(auth)

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
            #db.rollback()

    def testAssignRole(self):

        UUID1 = "TESTAUTOCREATEDROLE1"
        UUID2 = "TESTAUTOCREATEDROLE2"

        uuids = [UUID1, UUID2]

        table = auth.settings.table_group
        query1 = (table.deleted != True) & (table.uuid == UUID1)
        query2 = (table.deleted != True) & (table.uuid == UUID2)

        auth.s3_impersonate("admin@example.com")
        user_id = auth.user.id

        row = db(query1).select(limitby=(0, 1)).first()
        self.assertEqual(row, None)
        row = db(query2).select(limitby=(0, 1)).first()
        self.assertEqual(row, None)

        auth.s3_assign_role(user_id, uuids, for_pe=0)
        row = db(query1).select(limitby=(0, 1)).first()
        self.assertNotEqual(row, None)
        self.assertTrue(row.id > 0)
        self.assertTrue(row.role == UUID1)
        self.assertTrue(row.uuid == UUID1)
        row = db(query2).select(limitby=(0, 1)).first()
        self.assertNotEqual(row, None)
        self.assertTrue(row.id > 0)
        self.assertTrue(row.role == UUID2)
        self.assertTrue(row.uuid == UUID2)

        auth.s3_delete_role(UUID1)
        row = db(query1).select(limitby=(0, 1)).first()
        self.assertEqual(row, None)
        row = db(query2).select(limitby=(0, 1)).first()
        self.assertNotEqual(row, None)
        self.assertTrue(row.id > 0)
        self.assertTrue(row.role == UUID2)
        self.assertTrue(row.uuid == UUID2)

        auth.s3_delete_role(UUID2)
        row = db(query1).select(limitby=(0, 1)).first()
        self.assertEqual(row, None)
        row = db(query2).select(limitby=(0, 1)).first()
        self.assertEqual(row, None)

    def testGetRoles(self):

        UUID = "TESTAUTOCREATEDROLE"
        role_id = auth.s3_create_role(UUID, uid=UUID)

        try:
            auth.s3_impersonate("normaluser@example.com")
            user_id = auth.user.id

            auth.s3_assign_role(user_id, role_id, for_pe=None)
            roles = auth.s3_get_roles(user_id)
            self.assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=None)
            self.assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=0)
            self.assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=1)
            self.assertFalse(role_id in roles)
            auth.s3_retract_role(user_id, role_id, for_pe=None)

            auth.s3_assign_role(user_id, role_id, for_pe=0)
            roles = auth.s3_get_roles(user_id)
            self.assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=None)
            self.assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=0)
            self.assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=1)
            self.assertFalse(role_id in roles)
            auth.s3_retract_role(user_id, role_id, for_pe=0)

            auth.s3_assign_role(user_id, role_id, for_pe=1)
            roles = auth.s3_get_roles(user_id)
            self.assertTrue(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=None)
            self.assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=0)
            self.assertFalse(role_id in roles)
            roles = auth.s3_get_roles(user_id, for_pe=1)
            self.assertTrue(role_id in roles)
            auth.s3_retract_role(user_id, role_id, for_pe=1)

        finally:

            auth.s3_delete_role(UUID)
            auth.s3_impersonate(None)

    # -------------------------------------------------------------------------
    # Record Ownership
    #
    def testOwnershipRequired(self):

        deployment_settings.security.policy = 1
        auth.permission = s3base.S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertFalse(o)

        deployment_settings.security.policy = 2
        auth.permission = s3base.S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertFalse(o)

        deployment_settings.security.policy = 3
        auth.permission = s3base.S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

        deployment_settings.security.policy = 4
        auth.permission = s3base.S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

        deployment_settings.security.policy = 5
        auth.permission = s3base.S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

        deployment_settings.security.policy = 6
        auth.permission = s3base.S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

        deployment_settings.security.policy = 7
        auth.permission = s3base.S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

        deployment_settings.security.policy = 8
        auth.permission = s3base.S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

        deployment_settings.security.policy = 0
        auth.permission = s3base.S3Permission(auth)
        ownership_required = auth.permission.ownership_required
        o = ownership_required("update", "dvi_body", c="dvi", f="body")
        self.assertTrue(o)

    def testSessionOwnership(self):

        table = s3db.pr_person
        table2 = "dvi_body"
        auth.s3_impersonate(None)
        auth.s3_clear_session_ownership()
        auth.s3_make_session_owner(table, 1)

        # No record ID should always return False
        self.assertFalse(auth.s3_session_owns(table, None))
        # Check for non-owned record
        self.assertFalse(auth.s3_session_owns(table, 2))
        # Check for owned record
        self.assertTrue(auth.s3_session_owns(table, 1))

        # If user is logged-in, session ownership is always False
        auth.s3_impersonate("normaluser@example.com")
        self.assertFalse(auth.s3_session_owns(table, 1))

        auth.s3_impersonate(None)
        auth.s3_make_session_owner(table, 1)
        auth.s3_make_session_owner(table, 2)
        self.assertTrue(auth.s3_session_owns(table, 1))
        self.assertTrue(auth.s3_session_owns(table, 2))
        auth.s3_clear_session_ownership(table, 1)
        self.assertFalse(auth.s3_session_owns(table, 1))
        self.assertTrue(auth.s3_session_owns(table, 2))

        auth.s3_make_session_owner(table, 1)
        auth.s3_make_session_owner(table, 2)
        auth.s3_make_session_owner(table2, 1)
        auth.s3_make_session_owner(table2, 2)
        self.assertTrue(auth.s3_session_owns(table, 1))
        self.assertTrue(auth.s3_session_owns(table, 2))
        self.assertTrue(auth.s3_session_owns(table2, 1))
        self.assertTrue(auth.s3_session_owns(table2, 2))
        auth.s3_clear_session_ownership(table)
        self.assertFalse(auth.s3_session_owns(table, 1))
        self.assertFalse(auth.s3_session_owns(table, 2))
        self.assertTrue(auth.s3_session_owns(table2, 1))
        self.assertTrue(auth.s3_session_owns(table2, 2))

        auth.s3_make_session_owner(table, 1)
        auth.s3_make_session_owner(table, 2)
        auth.s3_make_session_owner(table2, 1)
        auth.s3_make_session_owner(table2, 2)
        self.assertTrue(auth.s3_session_owns(table, 1))
        self.assertTrue(auth.s3_session_owns(table, 2))
        self.assertTrue(auth.s3_session_owns(table2, 1))
        self.assertTrue(auth.s3_session_owns(table2, 2))
        auth.s3_clear_session_ownership()
        self.assertFalse(auth.s3_session_owns(table, 1))
        self.assertFalse(auth.s3_session_owns(table, 2))
        self.assertFalse(auth.s3_session_owns(table2, 1))
        self.assertFalse(auth.s3_session_owns(table2, 2))

# =============================================================================
class S3PermissionTests(unittest.TestCase):
    """ S3Permission Tests """

    def setUp(self):
        pass

    # -------------------------------------------------------------------------
    # Lambdas
    #
    def testRequiredACL(self):

        p = auth.permission
        self.assertEqual(p.required_acl(["read"]), p.READ)
        self.assertEqual(p.required_acl(["create"]), p.CREATE)
        self.assertEqual(p.required_acl(["update"]), p.UPDATE)
        self.assertEqual(p.required_acl(["delete"]), p.DELETE)
        self.assertEqual(p.required_acl(["create", "update"]), p.CREATE | p.UPDATE)
        self.assertEqual(p.required_acl([]), p.NONE)
        self.assertEqual(p.required_acl(["invalid"]), p.NONE)

    def testMostPermissive(self):

        p = auth.permission
        self.assertEqual(p.most_permissive([(p.NONE, p.READ),
                                            (p.READ, p.READ)]),
                                           (p.READ, p.READ))
        self.assertEqual(p.most_permissive([(p.NONE, p.ALL),
                                            (p.CREATE, p.ALL),
                                            (p.READ, p.ALL)]),
                                           (p.READ | p.CREATE, p.ALL))

    def testMostRestrictive(self):

        p = auth.permission
        self.assertEqual(p.most_restrictive([(p.NONE, p.READ),
                                             (p.READ, p.READ)]),
                                            (p.NONE, p.READ))
        self.assertEqual(p.most_restrictive([(p.CREATE, p.ALL),
                                             (p.READ, p.READ)]),
                                            (p.NONE, p.READ))

    # -------------------------------------------------------------------------
    # Record Ownership
    #
    def testOwnershipPublicRecord(self):

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            # Admin owns all records
            auth.s3_impersonate("admin@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Normal owns all public records
            auth.s3_impersonate("normaluser@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Unauthenticated users never own a record
            auth.s3_impersonate(None)
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ...unless the session owns the record
            auth.s3_make_session_owner(table, record_id)
            self.assertTrue(auth.permission.is_owner(table, record_id))

        finally:
            self.remove_test_record()

    def testOwnershipAdminOwnedRecord(self):

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            user_id = auth.s3_get_user_id("admin@example.com")
            db(table.id == record_id).update(owned_by_user=user_id)

            # Admin owns all records
            auth.s3_impersonate("admin@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Normal does not own this record
            auth.s3_impersonate("normaluser@example.com")
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # Unauthenticated does not own this record
            auth.s3_impersonate(None)
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ...unless the session owns the record
            auth.s3_make_session_owner(table, record_id)
            self.assertTrue(auth.permission.is_owner(table, record_id))

        finally:
            self.remove_test_record()

    def testOwnershipUserOwnedRecord(self):

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            # Change the record owner to admin
            user_id = auth.s3_get_user_id("normaluser@example.com")
            db(table.id == record_id).update(owned_by_user=user_id)

            # Admin owns all records
            auth.s3_impersonate("admin@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Normal owns this record
            auth.s3_impersonate("normaluser@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Unauthenticated does not own a record
            auth.s3_impersonate(None)
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ...unless the session owns the record
            auth.s3_make_session_owner(table, record_id)
            self.assertTrue(auth.permission.is_owner(table, record_id))

        finally:
            self.remove_test_record()

    def testOwnershipGroupOwnedRecord(self):

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            sr = auth.get_system_roles()
            user_id = auth.s3_get_user_id("admin@example.com")
            db(table.id == record_id).update(owned_by_user=user_id,
                                             owned_by_group=sr.AUTHENTICATED)

            # Admin owns all records
            auth.s3_impersonate("admin@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Normal owns this record as member of AUTHENTICATED
            auth.s3_impersonate("normaluser@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Unauthenticated does not own this record
            auth.s3_impersonate(None)
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ...unless the session owns the record
            auth.s3_make_session_owner(table, record_id)
            self.assertTrue(auth.permission.is_owner(table, record_id))

        finally:
            self.remove_test_record()

    def testOwnershipOrganisationOwnedRecord(self):

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            org = s3db.pr_get_pe_id("org_organisation", 1)
            role = auth.s3_create_role("Example Role", uid="TESTROLE")

            user_id = auth.s3_get_user_id("admin@example.com")
            db(table.id == record_id).update(owned_by_user=user_id,
                                             owned_by_group=role,
                                             owned_by_entity=org)
            auth.s3_clear_session_ownership()

            # Admin owns all records
            auth.s3_impersonate("admin@example.com")
            self.assertTrue(auth.permission.is_owner(table, record_id))

            # Normal user does not own the record
            auth.s3_impersonate("normaluser@example.com")
            user_id = auth.user.id
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ...unless they have the role for this org
            auth.s3_assign_role(user_id, role, for_pe=org)
            self.assertTrue(auth.permission.is_owner(table, record_id))
            auth.s3_retract_role(user_id, role, for_pe=org)
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ....or have the role without limitation (any org)
            auth.s3_assign_role(user_id, role, for_pe=0)
            self.assertTrue(auth.permission.is_owner(table, record_id))
            auth.s3_retract_role(user_id, role, for_pe=[])
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # Unauthenticated does not own this record
            auth.s3_impersonate(None)
            self.assertFalse(auth.permission.is_owner(table, record_id))

            # ...unless the session owns the record
            auth.s3_make_session_owner(table, record_id)
            self.assertTrue(auth.permission.is_owner(table, record_id))

        finally:
            self.remove_test_record()
            auth.s3_delete_role("TESTROLE")

    def testOwnershipOverride(self):

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            org = s3db.pr_get_pe_id("org_organisation", 1)
            role = auth.s3_create_role("Example Role", uid="TESTROLE")

            user_id = auth.s3_get_user_id("admin@example.com")
            db(table.id == record_id).update(owned_by_entity=org,
                                             owned_by_group=role,
                                             owned_by_user=user_id)

            owners_override = (None, None, None)

            # Normal user does not own the record
            auth.s3_impersonate("normaluser@example.com")
            self.assertFalse(auth.permission.is_owner(table, record_id))
            self.assertTrue(auth.permission.is_owner(table, record_id,
                                                     owners=owners_override))
        finally:
            self.remove_test_record()
            auth.s3_delete_role("TESTROLE")

    def testGetOwners(self):

        table, record_id = self.create_test_record()
        auth.s3_clear_session_ownership()

        try:
            user = auth.s3_get_user_id("admin@example.com")
            role = auth.s3_create_role("Example Role", uid="TESTROLE")
            org = s3db.pr_get_pe_id("org_organisation", 1)

            e, r, u = auth.permission.get_owners(table, None)
            self.assertEqual(e, None)
            self.assertEqual(r, None)
            self.assertEqual(u, None)

            e, r, u = auth.permission.get_owners(None, record_id)
            self.assertEqual(e, None)
            self.assertEqual(r, None)
            self.assertEqual(u, None)

            e, r, u = auth.permission.get_owners(None, None)
            self.assertEqual(e, None)
            self.assertEqual(r, None)
            self.assertEqual(u, None)

            e, r, u = auth.permission.get_owners(table, record_id)
            self.assertEqual(e, None)
            self.assertEqual(r, None)
            self.assertEqual(u, None)

            db(table.id == record_id).update(owned_by_user=user,
                                             owned_by_group=role,
                                             owned_by_entity=org)

            e, r, u = auth.permission.get_owners(table, record_id)
            self.assertEqual(e, org)
            self.assertEqual(r, role)
            self.assertEqual(u, user)

            e, r, u = auth.permission.get_owners(table._tablename, record_id)
            self.assertEqual(e, org)
            self.assertEqual(r, role)
            self.assertEqual(u, user)

        finally:
            self.remove_test_record()
            auth.s3_delete_role("TESTROLE")

    # -------------------------------------------------------------------------
    # ACL Management
    #
    def testUpdateControllerACL(self):

        table = auth.permission.table
        self.assertNotEqual(table, None)

        group_id = auth.s3_create_role("Test Role", uid="TEST")
        acl_id = None

        try:
            self.assertTrue(group_id is not None and group_id != 0)

            c = "pr"
            f = "person"
            uacl = auth.permission.NONE
            oacl = auth.permission.ALL


            acl_id = auth.permission.update_acl(group_id,
                                                c=c, f=f,
                                                uacl=uacl, oacl=oacl)
            self.assertNotEqual(acl_id, None)
            self.assertNotEqual(acl_id, 0)
            acl = table[acl_id]
            self.assertNotEqual(acl, None)
            self.assertEqual(acl.controller, c)
            self.assertEqual(acl.function, f)
            self.assertEqual(acl.tablename, None)
            self.assertEqual(acl.unrestricted, False)
            self.assertEqual(acl.entity, None)
            self.assertEqual(acl.uacl, uacl)
            self.assertEqual(acl.oacl, oacl)
            self.assertFalse(acl.deleted)

            success = auth.permission.delete_acl(group_id,
                                                 c=c, f=f)
            self.assertTrue(success is not None and success > 0)
            acl = table[acl_id]
            self.assertNotEqual(acl, None)
            self.assertTrue(acl.deleted)
            self.assertTrue(acl.deleted_fk, '{"group_id": %d}' % group_id)
        finally:
            if acl_id:
                del table[acl_id]
            auth.s3_delete_role(group_id)

    def testUpdateTableACL(self):

        table = auth.permission.table
        self.assertNotEqual(table, None)

        group_id = auth.s3_create_role("Test Role", uid="TEST")
        acl_id = None

        try:
            self.assertTrue(group_id is not None and group_id != 0)

            c = "pr"
            f = "person"
            t = "pr_person"
            uacl = auth.permission.NONE
            oacl = auth.permission.ALL


            acl_id = auth.permission.update_acl(group_id,
                                                c=c, f=f, t=t,
                                                uacl=uacl, oacl=oacl)
            self.assertNotEqual(acl_id, None)
            self.assertNotEqual(acl_id, 0)
            acl = table[acl_id]
            self.assertNotEqual(acl, None)
            self.assertEqual(acl.controller, None)
            self.assertEqual(acl.function, None)
            self.assertEqual(acl.tablename, t)
            self.assertEqual(acl.unrestricted, False)
            self.assertEqual(acl.entity, None)
            self.assertEqual(acl.uacl, uacl)
            self.assertEqual(acl.oacl, oacl)
            self.assertFalse(acl.deleted)

            success = auth.permission.delete_acl(group_id,
                                                 c=c, f=f, t=t)
            self.assertTrue(success is not None and success > 0)
            acl = table[acl_id]
            self.assertNotEqual(acl, None)
            self.assertTrue(acl.deleted)
            self.assertTrue(acl.deleted_fk, '{"group_id": %d}' % group_id)
        finally:
            if acl_id:
                del table[acl_id]
            auth.s3_delete_role(group_id)

    def testApplicableACLsPolicy8(self):

        try:
            # Have two orgs, set org2 as OU descendant of org1
            org1 = s3db.pr_get_pe_id("org_organisation", 1)
            org2 = s3db.pr_get_pe_id("org_organisation", 2)
            s3db.pr_add_affiliation(org1, org2, role="TestOrgUnit")

            # Set org3 as non-OU (role_type=9) partner of org1
            org3 = s3db.pr_get_pe_id("org_organisation", 3)
            partners = s3db.pr_add_affiliation(org1, org3, role="TestPartners", role_type=9)
            self.assertNotEqual(partners, None)

            # Add the user as OU descendant of org3
            user = auth.s3_user_pe_id(auth.s3_get_user_id("normaluser@example.com"))
            self.assertNotEqual(user, None)
            s3db.pr_add_affiliation(org3, user, role="TestStaff")

            # Create a TESTGROUP and assign a table ACL
            acl = auth.permission
            role = auth.s3_create_role("Test Group", None,
                                       dict(c="org", f="office", uacl=acl.ALL, oacl=acl.ALL),
                                       dict(t="org_office", uacl=acl.READ, oacl=acl.ALL),
                                       uid="TESTGROUP")

            # We use delegations (policy 8)
            deployment_settings.security.policy = 8
            auth.permission = s3base.S3Permission(auth)

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
            self.assertTrue(isinstance(acls, Storage))
            self.assertEqual(acls, Storage())

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

            self.assertTrue(isinstance(acls, Storage))
            self.assertTrue(org2 in acls)
            self.assertEqual(acls[org2], (acl.READ|acl.CREATE, acl.ALL))

        finally:
            s3db.pr_remove_affiliation(org1, org2, role="TestOrgUnit")
            s3db.pr_remove_affiliation(org1, org2, role="TestStaff")
            s3db.pr_remove_affiliation(org1, org3, role="TestPartners")
            auth.s3_delete_role("TESTGROUP")
            db.rollback()

    # -------------------------------------------------------------------------
    # Helpers
    #
    def create_test_record(self):

        # Create a record
        auth.override = True
        table = s3db.org_office
        record_id = table.insert(name="New Office")
        auth.override = False

        self.table = table
        self.record_id = record_id
        return table, record_id

    def remove_test_record(self):
        db(self.table.id == self.record_id).delete()
        db.commit()
        return

# =============================================================================
class S3HasPermissionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # Create test roles
        acl = auth.permission

        auth.s3_create_role("DVI Reader", None,
                            dict(c="dvi",
                                 uacl=acl.READ, oacl=acl.READ|acl.UPDATE),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE, oacl=acl.READ|acl.UPDATE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIREADER")

        auth.s3_create_role("DVI Editor", None,
                            dict(c="dvi",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIEDITOR")

        auth.s3_create_role("DVI Admin", None,
                            dict(c="dvi",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(c="dvi", f="body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(t="dvi_body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            uid="TESTDVIADMIN")
        db.commit()

    def setUp(self):

        # Get the role IDs
        gtable = auth.settings.table_group
        row = db(gtable.uuid=="TESTDVIREADER").select(limitby=(0, 1)).first()
        self.dvi_reader = row.id
        row = db(gtable.uuid=="TESTDVIEDITOR").select(limitby=(0, 1)).first()
        self.dvi_editor = row.id
        row = db(gtable.uuid=="TESTDVIADMIN").select(limitby=(0, 1)).first()
        self.dvi_admin = row.id

        auth.s3_impersonate("admin@example.com")

        # Create test organisations
        table = s3db.org_organisation
        record_id = table.insert(name="TestOrganisation1")
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.org1 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation2")
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.org2 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation3")
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.org3 = s3db.pr_get_pe_id(table, record_id)

        # Create test records
        table = s3db.dvi_body
        record_id = table.insert(pe_label="TestRecord1",
                                 owned_by_user=auth.user.id,
                                 owned_by_entity=self.org1)
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.record1 = record_id

        record_id = table.insert(pe_label="TestRecord2",
                                 owned_by_user=auth.user.id,
                                 owned_by_entity=self.org2)
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.record2 = record_id

        record_id = table.insert(pe_label="TestRecord3",
                                 owned_by_user=auth.user.id,
                                 owned_by_entity=self.org3)
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.record3 = record_id

        # Remove session ownership
        auth.s3_clear_session_ownership()
        auth.s3_impersonate(None)

    def testPolicy1(self):

        deployment_settings.security.policy = 1
        auth.permission = s3base.S3Permission(auth)

        has_permission = auth.s3_has_permission

        # Check anonymous
        permitted = has_permission("read", table="dvi_body")
        self.assertTrue(permitted)
        permitted = has_permission("update", table="dvi_body")
        self.assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", table="dvi_body")
        self.assertTrue(permitted)
        permitted = has_permission("update", table="dvi_body")
        self.assertTrue(permitted)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy3(self):

        deployment_settings.security.policy = 3
        auth.permission = s3base.S3Permission(auth)

        has_permission = auth.s3_has_permission

        # Check anonymous
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertTrue(permitted)
        permitted = auth.s3_has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertTrue(permitted)
        permitted = has_permission("create", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted) # Function ACL not applicable in policy 3
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy4(self):

        deployment_settings.security.policy = 4
        auth.permission = s3base.S3Permission(auth)

        has_permission = auth.s3_has_permission

        # Check anonymous
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertTrue(permitted)
        permitted = has_permission("create", c="dvi", f="body", table="dvi_body")
        self.assertTrue(permitted) # Function ACL overrides controller ACL
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy5(self):

        deployment_settings.security.policy = 5
        auth.permission = s3base.S3Permission(auth)

        has_permission = auth.s3_has_permission
        accessible_url = auth.permission.accessible_url

        # Check anonymous
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)
        url = accessible_url(c="dvi", f="body")
        self.assertEqual(url, False)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)
        url = accessible_url(c="dvi", f="body")
        self.assertEqual(url, False)

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertTrue(permitted)
        url = accessible_url(c="dvi", f="body")
        self.assertNotEqual(url, False)
        permitted = has_permission("create", c="dvi", f="body", table="dvi_body")
        self.assertTrue(permitted) # Function ACL overrides controller ACL
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted) # Page ACL blocks Table ACL

        # Toggle page ACL
        acl = auth.permission
        auth.permission.update_acl("TESTDVIREADER", c="dvi", f="body",
                                   uacl=acl.READ|acl.CREATE|acl.UPDATE,
                                   oacl=acl.READ|acl.CREATE|acl.UPDATE)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        auth.permission.update_acl("TESTDVIREADER", c="dvi", f="body",
                                   uacl=acl.READ|acl.CREATE,
                                   oacl=acl.READ|acl.CREATE|acl.UPDATE)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)

        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy6(self):

        deployment_settings.security.policy = 6
        auth.permission = s3base.S3Permission(auth)

        has_permission = auth.s3_has_permission

        # Check anonymous
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Test with TESTDVIEDITOR with universal realm
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=0)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertTrue(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted)
        auth.s3_retract_role(auth.user.id, self.dvi_editor, for_pe=[])

        # Test with TESTDVIEDITOR with limited realm
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted)
        permitted = has_permission("delete", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted)

        # Extend realm
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org2)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertTrue(permitted)

        # Retract dvi_editor role
        auth.s3_retract_role(auth.user.id, self.dvi_editor, for_pe=[])
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy7(self):

        deployment_settings.security.policy = 7
        auth.permission = s3base.S3Permission(auth)

        has_permission = auth.s3_has_permission

        # Check anonymous
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
        self.assertFalse(permitted)

        # Test with TESTDVIEDITOR with limited realm
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted)

        # Make org2 a sub-entity of org1
        s3db.pr_add_affiliation(self.org1, self.org2, role="TestOrgUnit")

        # Reload realms and test again
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertTrue(permitted) # Should now have access

        # Make org1 a sub-entity of org2
        s3db.pr_remove_affiliation(self.org1, self.org2, role="TestOrgUnit")
        s3db.pr_add_affiliation(self.org2, self.org1, role="TestOrgUnit")

        # Reload realms
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted) # Should no longer have access

        # Switch realm
        auth.s3_retract_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org2)

        # Reload realms
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertTrue(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertTrue(permitted) # Should have access again

        # Remove org1 from realm
        s3db.pr_remove_affiliation(self.org2, self.org1, role="TestOrgUnit")

        # Reload realms
        auth.s3_impersonate("normaluser@example.com")
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertTrue(permitted) # Should have access again

        # Retract dvi_editor role
        auth.s3_retract_role(auth.user.id, self.dvi_editor, for_pe=[])
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        self.assertFalse(permitted)
        permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
        self.assertFalse(permitted)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy8(self):

        deployment_settings.security.policy = 8
        auth.permission = s3base.S3Permission(auth)

        user = auth.s3_user_pe_id(auth.s3_get_user_id("normaluser@example.com"))

        try:

            has_permission = auth.s3_has_permission

            # Check anonymous
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
            self.assertFalse(permitted)

            # Check authenticated
            auth.s3_impersonate("normaluser@example.com")
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body")
            self.assertFalse(permitted)

            # Add the user as OU descendant of org3 and assign dvi_reader
            s3db.pr_add_affiliation(self.org3, user, role="TestStaff")
            auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org3)

            # User should not be able to read record1 or record2, but record3
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body", record_id=self.record1)
            self.assertFalse(permitted)
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body", record_id=self.record2)
            self.assertFalse(permitted)
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body", record_id=self.record3)
            self.assertTrue(permitted)

            permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
            self.assertFalse(permitted)
            permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
            self.assertFalse(permitted)
            permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record3)
            self.assertTrue(permitted)

            # Make org3 and OU of org2
            s3db.pr_add_affiliation(self.org2, self.org3, role="TestOrgUnit")

            # Delegate dvi_reader from org1 to org2
            auth.s3_delegate_role(self.dvi_reader, self.org1, receiver=self.org2)

            # Update realms
            auth.s3_impersonate("normaluser@example.com")

            # User should be able to read record2, but not record2
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body", record_id=self.record1)
            self.assertTrue(permitted)
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body", record_id=self.record2)
            self.assertFalse(permitted)
            permitted = has_permission("read", c="dvi", f="body", table="dvi_body", record_id=self.record3)
            self.assertTrue(permitted)

            permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
            self.assertFalse(permitted)
            permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record2)
            self.assertFalse(permitted)
            permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record3)
            self.assertTrue(permitted)

            auth.s3_remove_delegation(self.dvi_reader, self.org1, receiver=self.org2)

        finally:

            # Remove delegation, affiliation and role
            s3db.pr_remove_affiliation(self.org3, user, role="TestStaff")
            s3db.pr_remove_affiliation(self.org2, self.org3, role="TestOrgUnit")
            auth.s3_retract_role(user, self.dvi_reader, for_pe=self.org3)
            db.rollback()

            # Logout
            auth.s3_impersonate(None)

    #def testPerformance(self):

        #MAX_RUNTIME = 6 # Maximum acceptable runtime per request in milliseconds

        #deployment_settings.security.policy = 8
        #auth.permission = s3base.S3Permission(auth)

        #auth.s3_impersonate("normaluser@example.com")
        #has_permission = auth.s3_has_permission
        #auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        #def hasPermission():
            #permitted = has_permission("update", c="dvi", f="body", table="dvi_body", record_id=self.record1)
        #import timeit
        #runtime = timeit.Timer(hasPermission).timeit(number=100)
        #if runtime > (MAX_RUNTIME / 10.0):
            #raise AssertionError("has_permission: maximum acceptable run time exceeded (%sms > %sms)" % (int(runtime * 10), MAX_RUNTIME))
        #auth.s3_retract_role(auth.user.id, self.dvi_editor, for_pe=[])

    def tearDown(self):
        self.role = None
        db.rollback()

    @classmethod
    def tearDownClass(cls):
        auth.s3_delete_role("TESTDVIREADER")
        auth.s3_delete_role("TESTDVIEDITOR")
        auth.s3_delete_role("TESTDVIADMIN")

# =============================================================================
class S3AccessibleQueryTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # Create test roles
        acl = auth.permission

        auth.s3_create_role("DVI Reader", None,
                            dict(c="dvi",
                                 uacl=acl.READ, oacl=acl.READ),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE, oacl=acl.READ|acl.UPDATE|acl.DELETE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIREADER")

        auth.s3_create_role("DVI Editor", None,
                            dict(c="dvi",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIEDITOR")

        auth.s3_create_role("DVI Admin", None,
                            dict(c="dvi",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(c="dvi", f="body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(t="dvi_body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            uid="TESTDVIADMIN")
        db.commit()

    def setUp(self):

        # Get the role IDs
        gtable = auth.settings.table_group
        row = db(gtable.uuid=="TESTDVIREADER").select(limitby=(0, 1)).first()
        self.dvi_reader = row.id
        row = db(gtable.uuid=="TESTDVIEDITOR").select(limitby=(0, 1)).first()
        self.dvi_editor = row.id
        row = db(gtable.uuid=="TESTDVIADMIN").select(limitby=(0, 1)).first()
        self.dvi_admin = row.id

        auth.s3_impersonate("admin@example.com")

        # Create test organisations
        table = s3db.org_organisation
        record_id = table.insert(name="TestOrganisation1")
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.org1 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation2")
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.org2 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation3")
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.org3 = s3db.pr_get_pe_id(table, record_id)

        # Create test records
        table = s3db.dvi_body
        record_id = table.insert(pe_label="TestRecord1",
                                 owned_by_user=auth.user.id,
                                 owned_by_entity=self.org1)
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.record1 = record_id

        record_id = table.insert(pe_label="TestRecord2",
                                 owned_by_user=auth.user.id,
                                 owned_by_entity=self.org2)
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.record2 = record_id

        record_id = table.insert(pe_label="TestRecord3",
                                 owned_by_user=auth.user.id,
                                 owned_by_entity=self.org3)
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.record3 = record_id

        # Remove session ownership
        auth.s3_clear_session_ownership()
        auth.s3_impersonate(None)

    def testPolicy3(self):

        deployment_settings.security.policy = 3
        auth.permission = s3base.S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy4(self):

        deployment_settings.security.policy = 4
        auth.permission = s3base.S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3,%s)))" %
                                     (auth.user.id, self.dvi_reader))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3,%s)))" %
                                     (auth.user.id, self.dvi_reader))
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy5(self):

        deployment_settings.security.policy = 5
        auth.permission = s3base.S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3,%s)))" %
                                     (auth.user.id, self.dvi_reader))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy6(self):

        deployment_settings.security.policy = 6
        auth.permission = s3base.S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader, for_pe=self.org1)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                     "(dvi_body.owned_by_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(((dvi_body.owned_by_group = %s) AND "
                                     "(dvi_body.owned_by_entity IN (%s))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" %
                                     (auth.user.id, self.dvi_reader, self.org1))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                     "(dvi_body.owned_by_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                     "(dvi_body.owned_by_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy7(self):

        deployment_settings.security.policy = 7
        auth.permission = s3base.S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader, for_pe=self.org1)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                     "(dvi_body.owned_by_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(((dvi_body.owned_by_group = %s) AND "
                                     "(dvi_body.owned_by_entity IN (%s))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" %
                                     (auth.user.id, self.dvi_reader, self.org1))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Make org2 a sub-entity of org1
        s3db.pr_add_affiliation(self.org1, self.org2, role="TestOrgUnit")
        # Reload realms and delegations
        auth.s3_impersonate("normaluser@example.com")

        # Re-check queries
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        qstr = ("(((dvi_body.owned_by_entity IN (%s,%s)) OR "
                "(dvi_body.owned_by_entity IS NULL)) OR "
                "(((dvi_body.owned_by_user = %s) OR "
                "(((dvi_body.owned_by_user IS NULL) AND "
                "(dvi_body.owned_by_group IS NULL)) AND "
                "(dvi_body.owned_by_entity IS NULL))) OR "
                "(dvi_body.owned_by_group IN (2,3))))")
        self.assertTrue(str(query) == qstr % (self.org1, self.org2, auth.user.id) or
                        str(query) == qstr % (self.org2, self.org1, auth.user.id))
        query = accessible_query("update",table,  c="dvi", f="body")
        qstr = ("(((dvi_body.owned_by_user = %s) OR "
                "(((dvi_body.owned_by_user IS NULL) AND "
                "(dvi_body.owned_by_group IS NULL)) AND "
                "(dvi_body.owned_by_entity IS NULL))) OR "
                "(((dvi_body.owned_by_group = %s) AND "
                "(dvi_body.owned_by_entity IN (%s,%s))) OR "
                "(dvi_body.owned_by_group IN (2,3))))")
        self.assertTrue(str(query) == qstr % (auth.user.id, self.dvi_reader, self.org1, self.org2) or
                        str(query) == qstr % (auth.user.id, self.dvi_reader, self.org2, self.org1))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        s3db.pr_remove_affiliation(self.org1, self.org2, role="TestOrgUnit")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                     "(dvi_body.owned_by_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                     "(dvi_body.owned_by_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Make org2 a sub-entity of org1
        s3db.pr_add_affiliation(self.org1, self.org2, role="TestOrgUnit")
        # Reload realms and delegations
        auth.s3_impersonate("normaluser@example.com")

        # Re-check queries
        qstr = ("(((dvi_body.owned_by_entity IN (%s,%s)) OR "
                "(dvi_body.owned_by_entity IS NULL)) OR "
                "(((dvi_body.owned_by_user = %s) OR "
                "(((dvi_body.owned_by_user IS NULL) AND "
                "(dvi_body.owned_by_group IS NULL)) AND "
                "(dvi_body.owned_by_entity IS NULL))) OR "
                "(dvi_body.owned_by_group IN (2,3))))")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertTrue(str(query) == qstr % (self.org1, self.org2, auth.user.id) or
                        str(query) == qstr % (self.org2, self.org1, auth.user.id))
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertTrue(str(query) == qstr % (self.org1, self.org2, auth.user.id) or
                        str(query) == qstr % (self.org2, self.org1, auth.user.id))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        s3db.pr_remove_affiliation(self.org1, self.org2, role="TestOrgUnit")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy8(self):

        deployment_settings.security.policy = 8
        auth.permission = s3base.S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        record = None
        try:

            # Add the user as OU descendant of org3 and assign dvi_editor
            user = auth.s3_user_pe_id(auth.s3_get_user_id("normaluser@example.com"))
            s3db.pr_add_affiliation(self.org3, user, role="TestStaff")
            auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org3)

            # User should only be able to access records of org3
            query = accessible_query("read", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                         "(dvi_body.owned_by_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.owned_by_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))
            query = accessible_query("update", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                         "(dvi_body.owned_by_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.owned_by_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))

            # Make org3 and OU of org2
            s3db.pr_add_affiliation(self.org2, self.org3, role="TestOrgUnit")

            auth.s3_delegate_role(self.dvi_reader, self.org1, receiver=self.org2)

            # Update realms
            auth.s3_impersonate("normaluser@example.com")

            # User should now be able to read records of org1 and org3, but update only org3
            query = accessible_query("read", table, c="dvi", f="body")
            qstr = ("(((dvi_body.owned_by_entity IN (%s,%s)) OR "
                    "(dvi_body.owned_by_entity IS NULL)) OR "
                    "(((dvi_body.owned_by_user = %s) OR "
                    "(((dvi_body.owned_by_user IS NULL) AND "
                    "(dvi_body.owned_by_group IS NULL)) AND "
                    "(dvi_body.owned_by_entity IS NULL))) OR "
                    "(dvi_body.owned_by_group IN (2,3))))")
            self.assertTrue(str(query) == qstr % (self.org1, self.org3, auth.user.id) or
                            str(query) == qstr % (self.org3, self.org1, auth.user.id))
            query = accessible_query("update", table, c="dvi", f="body")
            qstr = ("(((dvi_body.owned_by_entity = %s) OR "
                    "(dvi_body.owned_by_entity IS NULL)) OR "
                    "(((dvi_body.owned_by_user = %s) OR "
                    "(((dvi_body.owned_by_user IS NULL) AND "
                    "(dvi_body.owned_by_group IS NULL)) AND "
                    "(dvi_body.owned_by_entity IS NULL))) OR "
                    "(dvi_body.owned_by_group IN (2,3))))")
            self.assertEqual(str(query), qstr % (self.org3, auth.user.id))

            # Remove the affiliation with org2
            s3db.pr_remove_affiliation(self.org2, self.org3, role="TestOrgUnit")

            # Update realms
            auth.s3_impersonate("normaluser@example.com")

            # Check queries again
            query = accessible_query("read", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                         "(dvi_body.owned_by_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.owned_by_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))
            query = accessible_query("update", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                         "(dvi_body.owned_by_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.owned_by_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))
        finally:

            # Remove delegation, affiliation and role
            s3db.pr_remove_affiliation(self.org3, user, role="TestStaff")
            s3db.pr_remove_affiliation(self.org2, self.org3, role="TestOrgUnit")
            auth.s3_retract_role(user, self.dvi_reader, for_pe=self.org3)

    #def testPerformance(self):

        #MAX_RUNTIME = 5 # Maximum acceptable runtime per request in milliseconds

        #deployment_settings.security.policy = 8
        #auth.permission = s3base.S3Permission(auth)

        #auth.s3_impersonate("normaluser@example.com")
        #accessible_query = auth.s3_accessible_query
        #table = s3db.dvi_body

        #auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        #def accessibleQuery():
            #query = accessible_query("update", table, c="dvi", f="body")
        #import timeit
        #runtime = timeit.Timer(accessibleQuery).timeit(number=100)
        #if runtime > (MAX_RUNTIME / 10.0):
            #raise AssertionError("accessible_query: maximum acceptable run time exceeded (%sms > %sms)" % (int(runtime * 10), MAX_RUNTIME))
        #auth.s3_retract_role(auth.user.id, self.dvi_editor, for_pe=[])

    def tearDown(self):
        self.role = None
        db.rollback()

    @classmethod
    def tearDownClass(cls):
        auth.s3_delete_role("TESTDVIREADER")
        auth.s3_delete_role("TESTDVIEDITOR")
        auth.s3_delete_role("TESTDVIADMIN")

# =============================================================================
class S3DelegationTests(unittest.TestCase):


    @classmethod
    def setUpClass(cls):

        # Create test roles
        acl = auth.permission

        auth.s3_create_role("DVI Reader", None,
                            dict(c="dvi",
                                 uacl=acl.READ, oacl=acl.READ|acl.UPDATE),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE, oacl=acl.READ|acl.UPDATE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIREADER")

        auth.s3_create_role("DVI Editor", None,
                            dict(c="dvi",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIEDITOR")

        auth.s3_create_role("DVI Admin", None,
                            dict(c="dvi",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(c="dvi", f="body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(t="dvi_body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            uid="TESTDVIADMIN")
        db.commit()

    def setUp(self):

        # Get the role IDs
        gtable = auth.settings.table_group
        row = db(gtable.uuid=="TESTDVIREADER").select(limitby=(0, 1)).first()
        self.dvi_reader = row.id
        row = db(gtable.uuid=="TESTDVIEDITOR").select(limitby=(0, 1)).first()
        self.dvi_editor = row.id
        row = db(gtable.uuid=="TESTDVIADMIN").select(limitby=(0, 1)).first()
        self.dvi_admin = row.id

        auth.s3_impersonate("admin@example.com")

        # Create test organisations
        table = s3db.org_organisation
        record_id = table.insert(name="TestOrganisation1")
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.org1 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation2")
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.org2 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation3")
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.org3 = s3db.pr_get_pe_id(table, record_id)

        # Create test records
        table = s3db.dvi_body
        record_id = table.insert(pe_label="TestRecord1",
                                 owned_by_user=auth.user.id,
                                 owned_by_entity=self.org1)
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.record1 = record_id

        record_id = table.insert(pe_label="TestRecord2",
                                 owned_by_user=auth.user.id,
                                 owned_by_entity=self.org2)
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.record2 = record_id

        record_id = table.insert(pe_label="TestRecord3",
                                 owned_by_user=auth.user.id,
                                 owned_by_entity=self.org3)
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.record3 = record_id

        # Remove session ownership
        auth.s3_clear_session_ownership()
        auth.s3_impersonate(None)

    def testPolicy7(self):

        deployment_settings.security.policy = 7
        auth.permission = s3base.S3Permission(auth)

    def testPolicy8(self):

        deployment_settings.security.policy = 8
        auth.permission = s3base.S3Permission(auth)
        auth.s3_impersonate("normaluser@example.com")
        user = auth.user.id

        try:

            # Add the user as OU descendant of org3 and assign dvi_reader
            s3db.pr_add_affiliation(self.org3, user, role="TestStaff")
            auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org3)

            # Make org3 an OU descendant of org2
            s3db.pr_add_affiliation(self.org2, self.org3, role="TestOrgUnit")

            # Delegate the dvi_reader role for org1 to org2
            auth.s3_delegate_role(self.dvi_reader, self.org1, receiver=self.org2)

            # Check the delegations
            delegations = auth.user.delegations
            self.assertTrue(self.dvi_reader in delegations)
            self.assertTrue(self.org3 in delegations[self.dvi_reader])
            self.assertTrue(self.org1 in delegations[self.dvi_reader][self.org3])

            auth.s3_remove_delegation(self.dvi_reader, self.org1, receiver=self.org2)

            # Check the delegations
            delegations = auth.user.delegations
            self.assertEqual(delegations.keys(), [])

            # Delegate the dvi_reader role for org1 to org2
            auth.s3_delegate_role([self.dvi_reader, self.dvi_editor], self.org1, receiver=self.org2)

            delegations = auth.s3_get_delegations(self.org1)
            self.assertNotEqual(delegations, None)
            self.assertTrue(isinstance(delegations, Storage))
            self.assertTrue(self.org2 in delegations)
            self.assertTrue(isinstance(delegations[self.org2], list))
            self.assertEqual(len(delegations[self.org2]), 2)
            self.assertTrue(self.dvi_reader in delegations[self.org2])
            self.assertTrue(self.dvi_editor in delegations[self.org2])

            # Check the delegations
            delegations = auth.user.delegations
            self.assertTrue(self.dvi_reader in delegations)
            self.assertTrue(self.dvi_editor in delegations)
            self.assertTrue(self.org3 in delegations[self.dvi_reader])
            self.assertTrue(self.org1 in delegations[self.dvi_reader][self.org3])
            self.assertTrue(self.org3 in delegations[self.dvi_editor])
            self.assertTrue(self.org1 in delegations[self.dvi_editor][self.org3])

            auth.s3_remove_delegation(self.dvi_editor, self.org1, receiver=self.org2)

            delegations = auth.s3_get_delegations(self.org1)
            self.assertNotEqual(delegations, None)
            self.assertTrue(isinstance(delegations, Storage))
            self.assertTrue(self.org2 in delegations)
            self.assertTrue(isinstance(delegations[self.org2], list))
            self.assertEqual(len(delegations[self.org2]), 1)
            self.assertTrue(self.dvi_reader in delegations[self.org2])

            # Check the delegations
            delegations = auth.user.delegations
            self.assertTrue(self.dvi_reader in delegations)
            self.assertFalse(self.dvi_editor in delegations)
            self.assertTrue(self.org3 in delegations[self.dvi_reader])
            self.assertTrue(self.org1 in delegations[self.dvi_reader][self.org3])

            auth.s3_remove_delegation(self.dvi_reader, self.org1, receiver=self.org2)

            delegations = auth.s3_get_delegations(self.org1)
            self.assertNotEqual(delegations, None)
            self.assertTrue(isinstance(delegations, Storage))
            self.assertEqual(delegations.keys(), [])

            # Check the delegations
            delegations = auth.user.delegations
            self.assertEqual(delegations.keys(), [])

        finally:

            # Remove delegation, affiliation and role
            s3db.pr_remove_affiliation(self.org3, user, role="TestStaff")
            s3db.pr_remove_affiliation(self.org2, self.org3, role="TestOrgUnit")
            auth.s3_retract_role(user, self.dvi_reader, for_pe=self.org3)
            db.rollback()

            # Logout
            auth.s3_impersonate(None)

    def tearDown(self):
        self.role = None
        db.rollback()

    @classmethod
    def tearDownClass(cls):
        auth.s3_delete_role("TESTDVIREADER")
        auth.s3_delete_role("TESTDVIEDITOR")
        auth.s3_delete_role("TESTDVIADMIN")

# =============================================================================
class S3AccessibleQueryTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # Create test roles
        acl = auth.permission

        auth.s3_create_role("DVI Reader", None,
                            dict(c="dvi",
                                 uacl=acl.READ, oacl=acl.READ),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE, oacl=acl.READ|acl.UPDATE|acl.DELETE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIREADER")

        auth.s3_create_role("DVI Editor", None,
                            dict(c="dvi",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(c="dvi", f="body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            dict(t="dvi_body",
                                 uacl=acl.READ|acl.CREATE|acl.UPDATE, oacl=acl.READ|acl.UPDATE),
                            uid="TESTDVIEDITOR")

        auth.s3_create_role("DVI Admin", None,
                            dict(c="dvi",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(c="dvi", f="body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            dict(t="dvi_body",
                                 uacl=acl.ALL, oacl=acl.ALL),
                            uid="TESTDVIADMIN")
        db.commit()

    def setUp(self):

        # Get the role IDs
        gtable = auth.settings.table_group
        row = db(gtable.uuid=="TESTDVIREADER").select(limitby=(0, 1)).first()
        self.dvi_reader = row.id
        row = db(gtable.uuid=="TESTDVIEDITOR").select(limitby=(0, 1)).first()
        self.dvi_editor = row.id
        row = db(gtable.uuid=="TESTDVIADMIN").select(limitby=(0, 1)).first()
        self.dvi_admin = row.id

        auth.s3_impersonate("admin@example.com")

        # Create test organisations
        table = s3db.org_organisation
        record_id = table.insert(name="TestOrganisation1")
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.org1 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation2")
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.org2 = s3db.pr_get_pe_id(table, record_id)

        record_id = table.insert(name="TestOrganisation3")
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.org3 = s3db.pr_get_pe_id(table, record_id)

        # Create test records
        table = s3db.dvi_body
        record_id = table.insert(pe_label="TestRecord1",
                                 owned_by_user=auth.user.id,
                                 owned_by_entity=self.org1)
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.record1 = record_id

        record_id = table.insert(pe_label="TestRecord2",
                                 owned_by_user=auth.user.id,
                                 owned_by_entity=self.org2)
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.record2 = record_id

        record_id = table.insert(pe_label="TestRecord3",
                                 owned_by_user=auth.user.id,
                                 owned_by_entity=self.org3)
        s3mgr.model.update_super(table, Storage(id=record_id))
        self.record3 = record_id

        # Remove session ownership
        auth.s3_clear_session_ownership()
        auth.s3_impersonate(None)

    def testPolicy3(self):

        deployment_settings.security.policy = 3
        auth.permission = s3base.S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy4(self):

        deployment_settings.security.policy = 4
        auth.permission = s3base.S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3,%s)))" %
                                     (auth.user.id, self.dvi_reader))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3,%s)))" %
                                     (auth.user.id, self.dvi_reader))
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy5(self):

        deployment_settings.security.policy = 5
        auth.permission = s3base.S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3,%s)))" %
                                     (auth.user.id, self.dvi_reader))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id > 0)")
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy6(self):

        deployment_settings.security.policy = 6
        auth.permission = s3base.S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader, for_pe=self.org1)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                     "(dvi_body.owned_by_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(((dvi_body.owned_by_group = %s) AND "
                                     "(dvi_body.owned_by_entity IN (%s))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" %
                                     (auth.user.id, self.dvi_reader, self.org1))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                     "(dvi_body.owned_by_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                     "(dvi_body.owned_by_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy7(self):

        deployment_settings.security.policy = 7
        auth.permission = s3base.S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Test with TESTDVIREADER
        auth.s3_assign_role(auth.user.id, self.dvi_reader, for_pe=self.org1)
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                     "(dvi_body.owned_by_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update",table,  c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(((dvi_body.owned_by_group = %s) AND "
                                     "(dvi_body.owned_by_entity IN (%s))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" %
                                     (auth.user.id, self.dvi_reader, self.org1))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Make org2 a sub-entity of org1
        s3db.pr_add_affiliation(self.org1, self.org2, role="TestOrgUnit")
        # Reload realms and delegations
        auth.s3_impersonate("normaluser@example.com")

        # Re-check queries
        query = accessible_query("read", "dvi_body", c="dvi", f="body")
        qstr = ("(((dvi_body.owned_by_entity IN (%s,%s)) OR "
                "(dvi_body.owned_by_entity IS NULL)) OR "
                "(((dvi_body.owned_by_user = %s) OR "
                "(((dvi_body.owned_by_user IS NULL) AND "
                "(dvi_body.owned_by_group IS NULL)) AND "
                "(dvi_body.owned_by_entity IS NULL))) OR "
                "(dvi_body.owned_by_group IN (2,3))))")
        self.assertTrue(str(query) == qstr % (self.org1, self.org2, auth.user.id) or
                        str(query) == qstr % (self.org2, self.org1, auth.user.id))
        query = accessible_query("update",table,  c="dvi", f="body")
        qstr = ("(((dvi_body.owned_by_user = %s) OR "
                "(((dvi_body.owned_by_user IS NULL) AND "
                "(dvi_body.owned_by_group IS NULL)) AND "
                "(dvi_body.owned_by_entity IS NULL))) OR "
                "(((dvi_body.owned_by_group = %s) AND "
                "(dvi_body.owned_by_entity IN (%s,%s))) OR "
                "(dvi_body.owned_by_group IN (2,3))))")
        self.assertTrue(str(query) == qstr % (auth.user.id, self.dvi_reader, self.org1, self.org2) or
                        str(query) == qstr % (auth.user.id, self.dvi_reader, self.org2, self.org1))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        s3db.pr_remove_affiliation(self.org1, self.org2, role="TestOrgUnit")
        auth.s3_retract_role(auth.user.id, self.dvi_reader)

        # Test with TESTDVIEDITOR
        auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org1)
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                     "(dvi_body.owned_by_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                     "(dvi_body.owned_by_entity IS NULL)) OR "
                                     "(((dvi_body.owned_by_user = %s) OR "
                                     "(((dvi_body.owned_by_user IS NULL) AND "
                                     "(dvi_body.owned_by_group IS NULL)) AND "
                                     "(dvi_body.owned_by_entity IS NULL))) OR "
                                     "(dvi_body.owned_by_group IN (2,3))))" % (self.org1, auth.user.id))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Make org2 a sub-entity of org1
        s3db.pr_add_affiliation(self.org1, self.org2, role="TestOrgUnit")
        # Reload realms and delegations
        auth.s3_impersonate("normaluser@example.com")

        # Re-check queries
        qstr = ("(((dvi_body.owned_by_entity IN (%s,%s)) OR "
                "(dvi_body.owned_by_entity IS NULL)) OR "
                "(((dvi_body.owned_by_user = %s) OR "
                "(((dvi_body.owned_by_user IS NULL) AND "
                "(dvi_body.owned_by_group IS NULL)) AND "
                "(dvi_body.owned_by_entity IS NULL))) OR "
                "(dvi_body.owned_by_group IN (2,3))))")
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertTrue(str(query) == qstr % (self.org1, self.org2, auth.user.id) or
                        str(query) == qstr % (self.org2, self.org1, auth.user.id))
        query = accessible_query("update", table, c="dvi", f="body")
        self.assertTrue(str(query) == qstr % (self.org1, self.org2, auth.user.id) or
                        str(query) == qstr % (self.org2, self.org1, auth.user.id))
        query = accessible_query("delete", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        s3db.pr_remove_affiliation(self.org1, self.org2, role="TestOrgUnit")
        auth.s3_retract_role(auth.user.id, self.dvi_editor)

        # Logout
        auth.s3_impersonate(None)

    def testPolicy8(self):

        deployment_settings.security.policy = 8
        auth.permission = s3base.S3Permission(auth)

        accessible_query = auth.s3_accessible_query
        table = s3db.dvi_body

        # Check anonymous
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        # Check authenticated
        auth.s3_impersonate("normaluser@example.com")
        user = auth.user.id
        query = accessible_query("read", table, c="dvi", f="body")
        self.assertEqual(str(query), "(dvi_body.id = 0)")

        record = None
        try:

            # Add the user as OU descendant of org3 and assign dvi_editor
            user = auth.s3_user_pe_id(auth.s3_get_user_id("normaluser@example.com"))
            s3db.pr_add_affiliation(self.org3, user, role="TestStaff")
            auth.s3_assign_role(auth.user.id, self.dvi_editor, for_pe=self.org3)

            # User should only be able to access records of org3
            query = accessible_query("read", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                         "(dvi_body.owned_by_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.owned_by_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))
            query = accessible_query("update", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                         "(dvi_body.owned_by_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.owned_by_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))

            # Make org3 and OU of org2
            s3db.pr_add_affiliation(self.org2, self.org3, role="TestOrgUnit")

            auth.s3_delegate_role(self.dvi_reader, self.org1, receiver=self.org2)

            # Update realms
            auth.s3_impersonate("normaluser@example.com")

            # User should now be able to read records of org1 and org3, but update only org3
            query = accessible_query("read", table, c="dvi", f="body")
            qstr = ("(((dvi_body.owned_by_entity IN (%s,%s)) OR "
                    "(dvi_body.owned_by_entity IS NULL)) OR "
                    "(((dvi_body.owned_by_user = %s) OR "
                    "(((dvi_body.owned_by_user IS NULL) AND "
                    "(dvi_body.owned_by_group IS NULL)) AND "
                    "(dvi_body.owned_by_entity IS NULL))) OR "
                    "(dvi_body.owned_by_group IN (2,3))))")
            self.assertTrue(str(query) == qstr % (self.org1, self.org3, auth.user.id) or
                            str(query) == qstr % (self.org3, self.org1, auth.user.id))
            query = accessible_query("update", table, c="dvi", f="body")
            qstr = ("(((dvi_body.owned_by_entity = %s) OR "
                    "(dvi_body.owned_by_entity IS NULL)) OR "
                    "(((dvi_body.owned_by_user = %s) OR "
                    "(((dvi_body.owned_by_user IS NULL) AND "
                    "(dvi_body.owned_by_group IS NULL)) AND "
                    "(dvi_body.owned_by_entity IS NULL))) OR "
                    "(dvi_body.owned_by_group IN (2,3))))")
            self.assertEqual(str(query), qstr % (self.org3, auth.user.id))

            # Remove the affiliation with org2
            s3db.pr_remove_affiliation(self.org2, self.org3, role="TestOrgUnit")

            # Update realms
            auth.s3_impersonate("normaluser@example.com")

            # Check queries again
            query = accessible_query("read", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                         "(dvi_body.owned_by_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.owned_by_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))
            query = accessible_query("update", table, c="dvi", f="body")
            self.assertEqual(str(query), "(((dvi_body.owned_by_entity = %s) OR "
                                         "(dvi_body.owned_by_entity IS NULL)) OR "
                                         "(((dvi_body.owned_by_user = %s) OR "
                                         "(((dvi_body.owned_by_user IS NULL) AND "
                                         "(dvi_body.owned_by_group IS NULL)) AND "
                                         "(dvi_body.owned_by_entity IS NULL))) OR "
                                         "(dvi_body.owned_by_group IN (2,3))))" % (self.org3, auth.user.id))
        finally:

            # Remove delegation, affiliation and role
            s3db.pr_remove_affiliation(self.org3, user, role="TestStaff")
            s3db.pr_remove_affiliation(self.org2, self.org3, role="TestOrgUnit")
            auth.s3_retract_role(user, self.dvi_reader, for_pe=self.org3)

    def tearDown(self):
        self.role = None
        db.rollback()

    @classmethod
    def tearDownClass(cls):
        auth.s3_delete_role("TESTDVIREADER")
        auth.s3_delete_role("TESTDVIEDITOR")
        auth.s3_delete_role("TESTDVIADMIN")



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
        S3AuthTests,
        S3PermissionTests,
        S3HasPermissionTests,
        S3AccessibleQueryTests,
        S3DelegationTests
    )

# END ========================================================================
