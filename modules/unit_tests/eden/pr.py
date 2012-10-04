# -*- coding: utf-8 -*-
#
# PR Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/eden/pr.py
#
import unittest
import datetime

from gluon import *
from gluon.storage import Storage

from eden.pr import S3SavedSearch

# =============================================================================
class PRTests(unittest.TestCase):
    """ PR Tests """

    def setUp(self):
        """ Set up organisation records """

        auth = current.auth
        s3db = current.s3db

        auth.override = True

        otable = s3db.org_organisation

        org1 = Storage(name="Test PR Organisation 1",
                       acronym="TPO",
                       country="UK",
                       website="http://tpo.example.org")
        org1_id = otable.insert(**org1)
        org1.update(id=org1_id)
        s3db.update_super(otable, org1)

        org2 = Storage(name="Test PR Organisation 2",
                       acronym="PTO",
                       country="US",
                       website="http://pto.example.com")
        org2_id = otable.insert(**org2)
        org2.update(id=org2_id)
        s3db.update_super(otable, org2)

        self.org1 = s3db.pr_get_pe_id("org_organisation", org1_id)
        self.org2 = s3db.pr_get_pe_id("org_organisation", org2_id)

    def testGetRealmUsers(self):

        auth = current.auth
        s3db = current.s3db

        auth.s3_impersonate("admin@example.com")
        admin_id = auth.user.id
        admin_pe_id = auth.s3_user_pe_id(admin_id)
        auth.s3_impersonate("normaluser@example.com")
        user_id = auth.user.id
        user_pe_id = auth.s3_user_pe_id(user_id)
        auth.s3_impersonate(None)

        org1 = self.org1
        org2 = self.org2

        users = s3db.pr_realm_users(org1)
        self.assertEqual(users, Storage())

        users = s3db.pr_realm_users(org2)
        self.assertEqual(users, Storage())

        s3db.pr_add_affiliation(org1, admin_pe_id, role="Volunteer", role_type=9)
        s3db.pr_add_affiliation(org2, user_pe_id, role="Staff")

        users = s3db.pr_realm_users(org1)
        self.assertFalse(user_id in users)
        self.assertFalse(admin_id in users)

        users = s3db.pr_realm_users(org2)
        self.assertTrue(user_id in users)
        self.assertFalse(admin_id in users)

        users = s3db.pr_realm_users([org1, org2])
        self.assertTrue(user_id in users)
        self.assertFalse(admin_id in users)

        users = s3db.pr_realm_users(org1, roles="Volunteer")
        self.assertFalse(user_id in users)
        self.assertTrue(admin_id in users)

        users = s3db.pr_realm_users(org2, roles="Volunteer")
        self.assertFalse(user_id in users)
        self.assertFalse(admin_id in users)

        users = s3db.pr_realm_users([org1, org2], roles="Volunteer")
        self.assertFalse(user_id in users)
        self.assertTrue(admin_id in users)

        users = s3db.pr_realm_users(org1, roles="Staff")
        self.assertFalse(user_id in users)
        self.assertFalse(admin_id in users)

        users = s3db.pr_realm_users(org2, roles="Staff")
        self.assertTrue(user_id in users)
        self.assertFalse(admin_id in users)

        users = s3db.pr_realm_users([org1, org2], roles="Staff")
        self.assertTrue(user_id in users)
        self.assertFalse(admin_id in users)

        users = s3db.pr_realm_users([org1, org2], roles=["Staff", "Volunteer"])
        self.assertTrue(user_id in users)
        self.assertTrue(admin_id in users)

        users = s3db.pr_realm_users([org1, org2], role_types=1)
        self.assertTrue(user_id in users)
        self.assertFalse(admin_id in users)

        users = s3db.pr_realm_users([org1, org2], role_types=9)
        self.assertFalse(user_id in users)
        self.assertTrue(admin_id in users)

        users = s3db.pr_realm_users([org1, org2], role_types=None)
        self.assertTrue(user_id in users)
        self.assertTrue(admin_id in users)

        s3db.pr_remove_affiliation(org2, user_pe_id, role="Staff")
        users = s3db.pr_realm_users([org1, org2], role_types=None)
        self.assertFalse(user_id in users)
        self.assertTrue(admin_id in users)

        # None as realm should give a list of all current users
        table = auth.settings.table_user
        query = (table.deleted != True)
        rows = current.db(query).select(table.id)
        all_users = [row.id for row in rows]
        users = s3db.pr_realm_users(None)
        self.assertTrue(all([u in users for u in all_users]))

    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

# =============================================================================
class PersonDeduplicateTests(unittest.TestCase):
    """ PR Tests """

    def setUp(self):

        s3db = current.s3db

        ptable = s3db.pr_person
        ctable = s3db.pr_contact

        person1 = Storage(first_name = "Test",
                          last_name = "UserDEDUP",
                          initials = "TU",
                          date_of_birth = datetime.date(1974, 4, 13))
        person1_id = ptable.insert(**person1)
        person1.update(id=person1_id)
        s3db.update_super(ptable, person1)

        self.person1_id = person1_id
        self.pe1_id = s3db.pr_get_pe_id(ptable, person1_id)

        person2 = Storage(first_name = "Test",
                          last_name = "UserDEDUP",
                          initials = "OU",
                          date_of_birth = datetime.date(1974, 4, 23))
        person2_id = ptable.insert(**person2)
        person2.update(id=person2_id)
        s3db.update_super(ptable, person2)

        self.person2_id = person2_id
        self.pe2_id = s3db.pr_get_pe_id(ptable, person2_id)

    def testHook(self):

        s3db = current.s3db

        deduplicate = s3db.get_config("pr_person", "deduplicate")
        self.assertNotEqual(deduplicate, None)
        self.assertTrue(callable(deduplicate))

    def testMatchNames(self):

        s3db = current.s3db
        from s3.s3import import S3ImportItem

        deduplicate = s3db.get_config("pr_person", "deduplicate")

        # Test Match:
        # Same first name and last name, no email in either record
        person = Storage(first_name = "Test",
                         last_name = "UserDEDUP")
        item = self.import_item(person)
        deduplicate(item)
        self.assertEqual(item.id, self.person1_id)
        self.assertEqual(item.method, S3ImportItem.METHOD.UPDATE)

        # Test Mismatch:
        # Different first name, same last name
        person = Storage(first_name = "Other",
                         last_name = "UserDEDUP")
        item = self.import_item(person)
        deduplicate(item)
        self.assertNotEqual(item.id, self.person1_id)
        self.assertNotEqual(item.id, self.person2_id)

    def testMatchEmail(self):

        s3db = current.s3db
        from s3.s3import import S3ImportItem

        deduplicate = s3db.get_config("pr_person", "deduplicate")

        # Test without contact records in the DB

        # Test Match:
        # Same first and last name,
        # no email in the DB but in the import item
        person = Storage(first_name = "Test",
                         last_name = "UserDEDUP")
        item = self.import_item(person, email="testuser@example.com")
        deduplicate(item)
        self.assertEqual(item.id, self.person1_id)
        self.assertEqual(item.method, S3ImportItem.METHOD.UPDATE)

        # Test Mismatch
        # Different first name, same last name,
        # no email in the DB but in the import item
        person = Storage(first_name = "Other",
                         last_name = "UserDEDUP")
        item = self.import_item(person, email="testuser@example.com")
        deduplicate(item)
        self.assertNotEqual(item.id, self.person1_id)
        self.assertNotEqual(item.id, self.person2_id)

        # Insert contact records into the DB
        ctable = s3db.pr_contact
        email = Storage(pe_id = self.pe1_id,
                        contact_method = "EMAIL",
                        value = "testuser@example.com")
        ctable.insert(**email)
        email = Storage(pe_id = self.pe2_id,
                        contact_method = "EMAIL",
                        value = "otheruser@example.org")
        ctable.insert(**email)

        # Test with contact records in the DB

        # Test Match - same names, same email
        person = Storage(first_name = "Test",
                         last_name = "UserDEDUP")
        item = self.import_item(person, email="testuser@example.com")
        deduplicate(item)
        self.assertEqual(item.id, self.person1_id)
        self.assertEqual(item.method, S3ImportItem.METHOD.UPDATE)

        # Test Mismatch - same names, no email in import item
        person = Storage(first_name = "Test",
                         last_name = "UserDEDUP")
        item = self.import_item(person)
        deduplicate(item)
        self.assertNotEqual(item.id, self.person1_id)
        self.assertNotEqual(item.id, self.person2_id)

        # Test Match - same names, no email in import item, but matching DOB
        person = Storage(first_name = "Test",
                         last_name = "UserDEDUP",
                         date_of_birth = datetime.date(1974, 4, 13))
        item = self.import_item(person)
        deduplicate(item)
        self.assertEqual(item.id, self.person1_id)
        self.assertEqual(item.method, S3ImportItem.METHOD.UPDATE)

        # Test Mismatch - same names, different email
        person = Storage(first_name = "Test",
                         last_name = "UserDEDUP")
        item = self.import_item(person, email="otheremail@example.com")
        deduplicate(item)
        self.assertNotEqual(item.id, self.person1_id)
        self.assertNotEqual(item.id, self.person2_id)

        # Test Match - same names, different email, but matching DOB
        person = Storage(first_name = "Test",
                         last_name = "UserDEDUP",
                         date_of_birth = datetime.date(1974, 4, 13))
        item = self.import_item(person, email="otheremail@example.com")
        deduplicate(item)
        self.assertEqual(item.id, self.person1_id)
        self.assertEqual(item.method, S3ImportItem.METHOD.UPDATE)

        # Test Match - same names, same email, but other record
        person = Storage(first_name = "Test",
                         last_name = "UserDEDUP")
        item = self.import_item(person, email="otheruser@example.org")
        deduplicate(item)
        self.assertEqual(item.id, self.person2_id)
        self.assertEqual(item.method, S3ImportItem.METHOD.UPDATE)

        # Test Mismatch - First names different
        person = Storage(first_name = "Other",
                         last_name = "UserDEDUP")
        item = self.import_item(person, email="testuser@example.com")
        deduplicate(item)
        self.assertNotEqual(item.id, self.person1_id)
        self.assertNotEqual(item.id, self.person2_id)

    def testMatchInitials(self):

        s3db = current.s3db
        from s3.s3import import S3ImportItem

        deduplicate = s3db.get_config("pr_person", "deduplicate")

        # Insert contact records into the DB
        ctable = s3db.pr_contact
        email = Storage(pe_id = self.pe1_id,
                        contact_method = "EMAIL",
                        value = "testuser@example.com")
        ctable.insert(**email)
        email = Storage(pe_id = self.pe2_id,
                        contact_method = "EMAIL",
                        value = "otheruser@example.org")
        ctable.insert(**email)

        # Test Match - same initials
        person = Storage(initials="TU")
        item = self.import_item(person)
        deduplicate(item)
        self.assertEqual(item.id, self.person1_id)
        self.assertEqual(item.method, S3ImportItem.METHOD.UPDATE)

        # Test Match - same names, different initials
        person = Storage(first_name="Test",
                         last_name="UserDEDUP",
                         initials="OU")
        item = self.import_item(person)
        deduplicate(item)
        self.assertEqual(item.id, self.person2_id)
        self.assertEqual(item.method, S3ImportItem.METHOD.UPDATE)

        # Test Match - same names, different initials, and email
        person = Storage(first_name="Test",
                         last_name="UserDEDUP",
                         initials="OU")
        item = self.import_item(person, email="testuser@example.org")
        deduplicate(item)
        self.assertEqual(item.id, self.person2_id)
        self.assertEqual(item.method, S3ImportItem.METHOD.UPDATE)

        # Test Match - same initials
        person = Storage(initials="OU")
        item = self.import_item(person)
        deduplicate(item)
        self.assertEqual(item.id, self.person2_id)
        self.assertEqual(item.method, S3ImportItem.METHOD.UPDATE)

        # Test Match - same initials, same email
        person = Storage(initials="TU")
        item = self.import_item(person, email="testuser@example.com")
        deduplicate(item)
        self.assertEqual(item.id, self.person1_id)
        self.assertEqual(item.method, S3ImportItem.METHOD.UPDATE)

    def testMatchDOB(self):

        s3db = current.s3db

        deduplicate = s3db.get_config("pr_person", "deduplicate")

        # Insert contact records into the DB
        ctable = s3db.pr_contact
        email = Storage(pe_id = self.pe1_id,
                        contact_method = "EMAIL",
                        value = "testuser@example.com")
        ctable.insert(**email)
        email = Storage(pe_id = self.pe2_id,
                        contact_method = "EMAIL",
                        value = "otheruser@example.org")
        ctable.insert(**email)

        # Test Match - same initials, different email, same DOB
        person = Storage(initials="TU",
                         date_of_birth=datetime.date(1974, 4, 13))
        item = self.import_item(person, email="otheremail@example.com")
        deduplicate(item)
        self.assertEqual(item.id, self.person1_id)

        # Test MisMatch - same initials, different email, different DOB
        person = Storage(initials="TU",
                         date_of_birth=datetime.date(1975, 6, 17))
        item = self.import_item(person, email="otheremail@example.com")
        deduplicate(item)
        self.assertNotEqual(item.id, self.person1_id)
        self.assertNotEqual(item.id, self.person2_id)

    def import_item(self, person, email=None, sms=None):
        """ Construct a fake import item """

        from s3.s3import import S3ImportItem
        def item(tablename, data):
            return Storage(id = None,
                           method = None,
                           tablename = tablename,
                           data = data,
                           components = [],
                           METHOD = S3ImportItem.METHOD)
        import_item = item("pr_person", person)
        if email:
            import_item.components.append(item("pr_contact",
                                Storage(contact_method = "EMAIL",
                                        value = email)))
        if sms:
            import_item.components.append(item("pr_contact",
                                Storage(contact_method = "SMS",
                                        value = sms)))
        return import_item

    def tearDown(self):

        current.db.rollback()
        self.pe_id = None
        self.person_id = None


class SavedSearchTests(unittest.TestCase):
    """
        Test the saved search validation and save functions
    """
    def setUp(self):
        s3db = current.s3db

        ptable = s3db.pr_person
        stable = s3db.pr_saved_search

        person = Storage(
            first_name = "Test",
            last_name = "SavedSearch",
        )
        person_id = ptable.insert(**person)
        person.update(id=person_id)
        s3db.update_super(ptable, person)

        self.person_id = person_id
        self.pe_id = s3db.pr_get_pe_id(ptable, person_id)

    def testOnValidation(self):
        f = S3SavedSearch.pr_saved_search_onvalidation

    def testFriendlyQuery(self):
        app = current.request.application
        f = S3SavedSearch.friendly_string_from_field_query

        result = f(
            "org",
            "organisation",
            "/%s/org/organisation/search?organisation.country__belongs=NZ" % app,
        )
        self.assertEqual(
            "Home Country=New Zealand",
            result,
        )

        result = f(
            "org",
            "organisation",
            "/%s/org/organisation/search?parent.acronym%%7Cparent.name%%7Cacronym%%7Cname__like=%%2Atest%%2A" % app,
        )
        self.assertEqual(
            "Acronym|Name|Acronym|Name=*test*",
            result,
        )

    def tearDown(self):
        current.db.rollback()
        self.pe_id = None
        self.person_id = None


# =============================================================================
def run_suite(*test_classes):
    """ Run the test suite """

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    if suite is not None:
        unittest.TextTestRunner().run(suite)
    return

if __name__ == "__main__":

    run_suite(
        PRTests,
        PersonDeduplicateTests,
        SavedSearchTests,
    )

# END ========================================================================
