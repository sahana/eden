# -*- coding: utf-8 -*-
#
# PR Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3db/pr.py
#
import unittest
import datetime

from gluon import *
from gluon.storage import Storage

from lxml import etree

# =============================================================================
class PRTests(unittest.TestCase):
    """ PR Tests """

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

# =============================================================================
class PersonDeduplicateTests(unittest.TestCase):
    """ PR Tests """

    # -------------------------------------------------------------------------
    def setUp(self):

        s3db = current.s3db

        ptable = s3db.pr_person
        ctable = s3db.pr_contact

        # Make sure the first record is the older record
        created_on = current.request.utcnow - datetime.timedelta(hours=1)

        person1 = Storage(first_name = "Test",
                          last_name = "UserDEDUP",
                          initials = "TU",
                          date_of_birth = datetime.date(1974, 4, 13),
                          created_on = created_on)
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

    # -------------------------------------------------------------------------
    def testHook(self):

        s3db = current.s3db

        deduplicate = s3db.get_config("pr_person", "deduplicate")
        self.assertNotEqual(deduplicate, None)
        self.assertTrue(callable(deduplicate))

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        self.pe_id = None
        self.person_id = None

# =============================================================================
class ContactValidationTests(unittest.TestCase):
    """ Test validation of mobile phone numbers in pr_contact_onvalidation """

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

        self.current_setting = current.deployment_settings \
                                      .get_msg_require_international_phone_numbers()

    # -------------------------------------------------------------------------
    def tearDown(self):

        settings = current.deployment_settings
        current.deployment_settings \
               .msg.require_international_phone_numbers = self.current_setting

        current.db.rollback()
        current.auth.override = False

    # -------------------------------------------------------------------------
    def testMobilePhoneNumberValidationStandard(self):
        """ Test that validator for mobile phone number is applied """

        current.deployment_settings \
               .msg.require_international_phone_numbers = False

        from s3db.pr import S3ContactModel
        onvalidation = S3ContactModel.pr_contact_onvalidation

        form = Storage(
            vars = Storage(
                contact_method = "SMS",
            )
        )

        # valid
        form.errors = Storage()
        form.vars.value = "0368172634"
        onvalidation(form)
        self.assertEqual(form.vars.value, "0368172634")
        self.assertFalse("value" in form.errors)

        # invalid
        form.errors = Storage()
        form.vars.value = "036-ASBKD"
        onvalidation(form)
        self.assertEqual(form.vars.value, "036-ASBKD")
        self.assertTrue("value" in form.errors)

    # -------------------------------------------------------------------------
    def testMobilePhoneNumberValidationInternational(self):
        """ Test that validator for mobile phone number is applied """

        current.deployment_settings \
               .msg.require_international_phone_numbers = True

        from s3db.pr import S3ContactModel
        onvalidation = S3ContactModel.pr_contact_onvalidation

        form = Storage(
            vars = Storage(
                contact_method = "SMS",
            )
        )

        # valid
        form.errors = Storage()
        form.vars.value = "+46-73-3847589"
        onvalidation(form)
        self.assertEqual(form.vars.value, "+46733847589")
        self.assertFalse("value" in form.errors)

        # invalid
        form.errors = Storage()
        form.vars.value = "0368172634"
        onvalidation(form)
        self.assertEqual(form.vars.value, "0368172634")
        self.assertTrue("value" in form.errors)

    # -------------------------------------------------------------------------
    def testMobilePhoneNumberImportValidationStandard(self):
        """ Test that validator for mobile phone number is applied during import """

        s3db = current.s3db
        current.deployment_settings \
               .msg.require_international_phone_numbers = False

        xmlstr = """
<s3xml>
    <resource name="pr_person" uuid="CONTACTVALIDATORTESTPERSON1">
        <data field="first_name">ContactValidatorTestPerson1</data>
        <resource name="pr_contact" uuid="VALIDATORTESTCONTACT1">
            <data field="contact_method">SMS</data>
            <data field="value">0368172634</data>
        </resource>
        <resource name="pr_contact" uuid="VALIDATORTESTCONTACT2">
            <data field="contact_method">SMS</data>
            <data field="value">036-ASBKD</data>
        </resource>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = s3db.resource("pr_person")
        result = resource.import_xml(xmltree, ignore_errors=True)

        resource = s3db.resource("pr_contact", uid="VALIDATORTESTCONTACT1")
        self.assertEqual(resource.count(), 1)
        row = resource.select(["value"], as_rows=True).first()
        self.assertNotEqual(row, None)
        self.assertEqual(row.value, "0368172634")

        resource = s3db.resource("pr_contact", uid="VALIDATORTESTCONTACT2")
        self.assertEqual(resource.count(), 0)
        row = resource.select(["value"], as_rows=True).first()
        self.assertEqual(row, None)

    # -------------------------------------------------------------------------
    def testMobilePhoneNumberImportValidationInternational(self):
        """ Test that validator for mobile phone number is applied during import """

        s3db = current.s3db
        current.deployment_settings \
               .msg.require_international_phone_numbers = True

        xmlstr = """
<s3xml>
    <resource name="pr_person" uuid="CONTACTVALIDATORTESTPERSON2">
        <data field="first_name">ContactValidatorTestPerson2</data>
        <resource name="pr_contact" uuid="VALIDATORTESTCONTACT1">
            <data field="contact_method">SMS</data>
            <data field="value">0368172634</data>
        </resource>
        <resource name="pr_contact" uuid="VALIDATORTESTCONTACT2">
            <data field="contact_method">SMS</data>
            <data field="value">+46-73-3847589</data>
        </resource>
    </resource>
</s3xml>"""

        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        resource = s3db.resource("pr_person")
        result = resource.import_xml(xmltree, ignore_errors=True)

        resource = s3db.resource("pr_contact", uid="VALIDATORTESTCONTACT1")
        self.assertEqual(resource.count(), 0)
        row = resource.select(["value"], as_rows=True).first()
        self.assertEqual(row, None)

        resource = s3db.resource("pr_contact", uid="VALIDATORTESTCONTACT2")
        self.assertEqual(resource.count(), 1)
        row = resource.select(["value"], as_rows=True).first()
        self.assertNotEqual(row, None)
        self.assertEqual(row.value, "+46733847589")

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
        PRTests,
        PersonDeduplicateTests,
        ContactValidationTests,
    )

# END ========================================================================
