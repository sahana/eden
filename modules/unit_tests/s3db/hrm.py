# -*- coding: utf-8 -*-
#
# HRM Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3db/hrm.py
#
import unittest

from gluon import *
from gluon.storage import Storage

# =============================================================================
class LocationSettingTests(unittest.TestCase):
    """ Test setting/updating of the location_id field in hrm_human_resource """

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

    # -------------------------------------------------------------------------
    def _testStaffWithExistingLocations(self, site, address):
        """
            Test a New Staff with existing Site &/or Home Address
        """

        db = current.db
        s3db = current.s3db
        gtable = s3db.gis_location

        if site:
            # Create a Site Location
            record = Storage(name = "Test Site Location",
                             )
            site_location_id = gtable.insert(**record)
            self.assertNotEqual(site_location_id, None)
            record["id"] = site_location_id
            #s3db.update_super(gtable, record)
            s3db.onaccept(gtable, record, method="create")

            # Create a Site with that Location
            otable = s3db.org_office
            record = Storage(name = "Test Office",
                             location_id = site_location_id,
                             )
            office_id = otable.insert(**record)
            self.assertNotEqual(office_id, None)
            record["id"] = office_id
            s3db.update_super(otable, record)
            s3db.onaccept(otable, record, method="create")
            site_id = record["site_id"]
        else:
            site_id = site_location_id = None

        # Create a Person
        ptable = s3db.pr_person
        record = Storage(first_name = "Test",
                         last_name = "Person",
                         )
        person_id = ptable.insert(**record)
        self.assertNotEqual(person_id, None)
        record["id"] = person_id
        s3db.update_super(ptable, record)
        s3db.onaccept(ptable, record, method="create")

        if address:
            pe_id = record["pe_id"]
            # Create an Address Location
            record = Storage(name = "Test Address Location",
                             )
            address_location_id = gtable.insert(**record)
            self.assertNotEqual(address_location_id, None)
            record["id"] = address_location_id
            #s3db.update_super(gtable, record)
            s3db.onaccept(gtable, record, method="create")

            # Give them a Home Address with that Location
            atable = s3db.pr_address
            record = Storage(pe_id = pe_id,
                             type = 1,
                             location_id = address_location_id,
                             )
            address_id = atable.insert(**record)
            self.assertNotEqual(address_id, None)
            record["id"] = address_id
            #s3db.update_super(atable, record)
            s3db.onaccept(atable, record, method="create")

        else:
            address_location_id = None

        # Make them a Staff
        htable = s3db.hrm_human_resource
        record = Storage(person_id = person_id,
                         type = 1,
                         site_id = site_id,
                         )
        human_resource_id = htable.insert(**record)
        self.assertNotEqual(human_resource_id, None)
        record["id"] = human_resource_id
        s3db.update_super(htable, record)
        s3db.onaccept(htable, record, method="create")

        # Test that the HR location is set correctly
        row = db(htable.id == human_resource_id).select(htable.location_id,
                                                        limitby=(0, 1)).first()

        self.assertNotEqual(row, None)
        return row, address_location_id, site_location_id

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations1(self):

        current.deployment_settings.hrm.location_staff = "site_id"

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=True, address=False)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations2(self):

        current.deployment_settings.hrm.location_staff = "site_id"

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=False, address=False)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations3(self):

        current.deployment_settings.hrm.location_staff = "site_id"

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=True, address=True)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations4(self):

        current.deployment_settings.hrm.location_staff = "site_id"

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=False, address=True)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations5(self):

        current.deployment_settings.hrm.location_staff = ("site_id", "person_id")

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=True, address=False)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations6(self):

        current.deployment_settings.hrm.location_staff = ("site_id", "person_id")

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=False, address=False)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations7(self):

        current.deployment_settings.hrm.location_staff = ("site_id", "person_id")

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=True, address=True)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations8(self):

        current.deployment_settings.hrm.location_staff = ("site_id", "person_id")

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=False, address=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations9(self):

        current.deployment_settings.hrm.location_staff = ("person_id", "site_id")

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=True, address=False)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations10(self):

        current.deployment_settings.hrm.location_staff = ("person_id", "site_id")

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=False, address=False)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations11(self):

        current.deployment_settings.hrm.location_staff = ("person_id", "site_id")

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=True, address=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations12(self):

        current.deployment_settings.hrm.location_staff = ("person_id", "site_id")

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=False, address=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations13(self):

        current.deployment_settings.hrm.location_staff = "person_id"

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=True, address=False)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations14(self):

        current.deployment_settings.hrm.location_staff = "person_id"

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=False, address=False)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations15(self):

        current.deployment_settings.hrm.location_staff = "person_id"

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=True, address=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testStaffWithExistingLocations16(self):

        current.deployment_settings.hrm.location_staff = "person_id"

        row, address_location_id, site_location_id = self._testStaffWithExistingLocations(site=False, address=True)
        self.assertEqual(row.location_id, address_location_id)

        # -------------------------------------------------------------------------
    def _testStaffUpdateFromSite(self, address):
        """
            Test a Staff which has a Site assigned after creation
        """

        db = current.db
        s3db = current.s3db
        gtable = s3db.gis_location

        # Create a Site Location
        record = Storage(name = "Test Site Location",
                         )
        site_location_id = gtable.insert(**record)
        self.assertNotEqual(site_location_id, None)
        record["id"] = site_location_id
        #s3db.update_super(gtable, record)
        s3db.onaccept(gtable, record, method="create")

        # Create a Site with that Location
        otable = s3db.org_office
        record = Storage(name = "Test Office",
                         location_id = site_location_id,
                         )
        office_id = otable.insert(**record)
        self.assertNotEqual(office_id, None)
        record["id"] = office_id
        s3db.update_super(otable, record)
        s3db.onaccept(otable, record, method="create")
        site_id = record["site_id"]

        # Create a Person
        ptable = s3db.pr_person
        record = Storage(first_name = "Test",
                         last_name = "Person",
                         )
        person_id = ptable.insert(**record)
        self.assertNotEqual(person_id, None)
        record["id"] = person_id
        s3db.update_super(ptable, record)
        s3db.onaccept(ptable, record, method="create")

        if address:
            pe_id = record["pe_id"]
            # Create an Address Location
            record = Storage(name = "Test Address Location",
                             )
            address_location_id = gtable.insert(**record)
            self.assertNotEqual(address_location_id, None)
            record["id"] = address_location_id
            #s3db.update_super(gtable, record)
            s3db.onaccept(gtable, record, method="create")

            # Give them a Home Address with that Location
            atable = s3db.pr_address
            record = Storage(pe_id = pe_id,
                             type = 1,
                             location_id = address_location_id,
                             )
            address_id = atable.insert(**record)
            self.assertNotEqual(address_id, None)
            record["id"] = address_id
            #s3db.update_super(atable, record)
            s3db.onaccept(atable, record, method="create")

        else:
            address_location_id = None

        # Make them a Staff
        htable = s3db.hrm_human_resource
        record = Storage(person_id = person_id,
                         type = 1,
                         #site_id = site_id,
                         )
        human_resource_id = htable.insert(**record)
        self.assertNotEqual(human_resource_id, None)
        record["id"] = human_resource_id
        s3db.update_super(htable, record)
        s3db.onaccept(htable, record, method="create")

        # Assign the Staff to a Site
        ltable = s3db.hrm_human_resource_site
        record = Storage(human_resource_id = human_resource_id,
                         site_id = site_id,
                         )
        link_id = ltable.insert(**record)
        self.assertNotEqual(link_id, None)
        record["id"] = link_id
        #s3db.update_super(ltable, record)
        s3db.onaccept(ltable, record, method="create")


        # Test that the HR location is set correctly
        row = db(htable.id == human_resource_id).select(htable.location_id,
                                                        limitby=(0, 1)).first()

        self.assertNotEqual(row, None)
        return row, address_location_id, site_location_id

    # -------------------------------------------------------------------------
    def testStaffUpdateFromSite1(self):

        current.deployment_settings.hrm.location_staff = "site_id"

        row, address_location_id, site_location_id = self._testStaffUpdateFromSite(address=False)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testStaffUpdateFromSite2(self):

        current.deployment_settings.hrm.location_staff = "site_id"

        row, address_location_id, site_location_id = self._testStaffUpdateFromSite(address=True)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testStaffUpdateFromSite3(self):

        current.deployment_settings.hrm.location_staff = ("site_id", "person_id")

        row, address_location_id, site_location_id = self._testStaffUpdateFromSite(address=False)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testStaffUpdateFromSite4(self):

        current.deployment_settings.hrm.location_staff = ("site_id", "person_id")

        row, address_location_id, site_location_id = self._testStaffUpdateFromSite(address=True)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testStaffUpdateFromSite5(self):

        current.deployment_settings.hrm.location_staff = ("person_id", "site_id")

        row, address_location_id, site_location_id = self._testStaffUpdateFromSite(address=False)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testStaffUpdateFromSite6(self):

        current.deployment_settings.hrm.location_staff = ("person_id", "site_id")

        row, address_location_id, site_location_id = self._testStaffUpdateFromSite(address=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testStaffUpdateFromSite7(self):

        current.deployment_settings.hrm.location_staff = "person_id"

        row, address_location_id, site_location_id = self._testStaffUpdateFromSite(address=False)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testStaffUpdateFromSite8(self):

        current.deployment_settings.hrm.location_staff = "person_id"

        row, address_location_id, site_location_id = self._testStaffUpdateFromSite(address=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def _testVolWithExistingLocations(self, site, address):
        """
            Test a New Volunteer with existing Site &/or Home Address
        """

        db = current.db
        s3db = current.s3db
        gtable = s3db.gis_location

        # Create a Person
        ptable = s3db.pr_person
        record = Storage(first_name = "Test",
                         last_name = "Person",
                         )
        person_id = ptable.insert(**record)
        self.assertNotEqual(person_id, None)
        record["id"] = person_id
        s3db.update_super(ptable, record)
        s3db.onaccept(ptable, record, method="create")
        pe_id = record["pe_id"]

        if address:
            # Create an Address Location
            record = Storage(name = "Test Address Location",
                             )
            address_location_id = gtable.insert(**record)
            self.assertNotEqual(address_location_id, None)
            record["id"] = address_location_id
            #s3db.update_super(gtable, record)
            s3db.onaccept(gtable, record, method="create")

            # Give them a Home Address with that Location
            atable = s3db.pr_address
            record = Storage(pe_id = pe_id,
                             type = 1,
                             location_id = address_location_id,
                             )
            address_id = atable.insert(**record)
            self.assertNotEqual(address_id, None)
            record["id"] = address_id
            #s3db.update_super(atable, record)
            s3db.onaccept(atable, record, method="create")
        else:
            address_location_id = None

        if site:
            # Create a Site Location
            record = Storage(name = "Test Site Location",
                             )
            site_location_id = gtable.insert(**record)
            self.assertNotEqual(site_location_id, None)
            record["id"] = site_location_id
            #s3db.update_super(gtable, record)
            s3db.onaccept(gtable, record, method="create")

            # Create a Site with that Location
            otable = s3db.org_office
            record = Storage(name = "Test Office",
                             location_id = site_location_id,
                             )
            office_id = otable.insert(**record)
            self.assertNotEqual(office_id, None)
            record["id"] = office_id
            s3db.update_super(otable, record)
            s3db.onaccept(otable, record, method="create")
            site_id = record["site_id"]
        else:
            site_location_id = site_id = None

        # Make them a Volunteer
        htable = s3db.hrm_human_resource
        record = Storage(person_id = person_id,
                         type = 2,
                         site_id = site_id
                         )
        human_resource_id = htable.insert(**record)
        self.assertNotEqual(human_resource_id, None)
        record["id"] = human_resource_id
        s3db.update_super(htable, record)
        s3db.onaccept(htable, record, method="create")

        # Test that the HR location is set correctly
        row = db(htable.id == human_resource_id).select(htable.location_id,
                                                        limitby=(0, 1)).first()

        self.assertNotEqual(row, None)
        return row, address_location_id, site_location_id

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations1(self):

        current.deployment_settings.hrm.location_vol = "person_id"

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=False, address=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations2(self):

        current.deployment_settings.hrm.location_vol = "person_id"

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=False, address=False)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations3(self):

        current.deployment_settings.hrm.location_vol = "person_id"

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=True, address=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations4(self):

        current.deployment_settings.hrm.location_vol = "person_id"

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=True, address=False)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations5(self):

        current.deployment_settings.hrm.location_vol = ("person_id", "site_id")

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=False, address=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations6(self):

        current.deployment_settings.hrm.location_vol = ("person_id", "site_id")

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=False, address=False)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations7(self):

        current.deployment_settings.hrm.location_vol = ("person_id", "site_id")

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=True, address=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations8(self):

        current.deployment_settings.hrm.location_vol = ("person_id", "site_id")

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=True, address=False)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations9(self):

        current.deployment_settings.hrm.location_vol = ("site_id", "person_id")

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=False, address=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations10(self):

        current.deployment_settings.hrm.location_vol = ("site_id", "person_id")

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=False, address=False)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations11(self):

        current.deployment_settings.hrm.location_vol = ("site_id", "person_id")

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=True, address=True)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations12(self):

        current.deployment_settings.hrm.location_vol = ("site_id", "person_id")

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=True, address=False)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations13(self):

        current.deployment_settings.hrm.location_vol = "site_id"

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=False, address=True)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations14(self):

        current.deployment_settings.hrm.location_vol = "site_id"

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=False, address=False)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations15(self):

        current.deployment_settings.hrm.location_vol = "site_id"

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=True, address=True)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testVolWithExistingLocations16(self):

        current.deployment_settings.hrm.location_vol = "site_id"

        row, address_location_id, site_location_id = self._testVolWithExistingLocations(site=True, address=False)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def _testVolUpdateFromPersonAddress(self, site):
        """
            Test a Volunteer which has a Home Address added after creation
        """

        db = current.db
        s3db = current.s3db
        gtable = s3db.gis_location

        if site:
            # Create a Site Location
            record = Storage(name = "Test Site Location",
                             )
            site_location_id = gtable.insert(**record)
            self.assertNotEqual(site_location_id, None)
            record["id"] = site_location_id
            #s3db.update_super(gtable, record)
            s3db.onaccept(gtable, record, method="create")

            # Create a Site with that Location
            otable = s3db.org_office
            record = Storage(name = "Test Office",
                             location_id = site_location_id,
                             )
            office_id = otable.insert(**record)
            self.assertNotEqual(office_id, None)
            record["id"] = office_id
            s3db.update_super(otable, record)
            s3db.onaccept(otable, record, method="create")
            site_id = record["site_id"]
        else:
            site_location_id = site_id = None

        # Create a Person
        ptable = s3db.pr_person
        record = Storage(first_name = "Test",
                         last_name = "Person",
                         )
        person_id = ptable.insert(**record)
        self.assertNotEqual(person_id, None)
        record["id"] = person_id
        s3db.update_super(ptable, record)
        s3db.onaccept(ptable, record, method="create")
        pe_id = record["pe_id"]

        # Make them a Volunteer
        htable = s3db.hrm_human_resource
        record = Storage(person_id = person_id,
                         type = 2,
                         site_id = site_id,
                         )
        human_resource_id = htable.insert(**record)
        self.assertNotEqual(human_resource_id, None)
        record["id"] = human_resource_id
        s3db.update_super(htable, record)
        s3db.onaccept(htable, record, method="create")

        # Create a Location
        #gtable = s3db.gis_location
        record = Storage(name = "Test Location",
                         )
        address_location_id = gtable.insert(**record)
        self.assertNotEqual(address_location_id, None)
        record["id"] = address_location_id
        #s3db.update_super(gtable, record)
        s3db.onaccept(gtable, record, method="create")

        # Give them a Home Address with that Location
        atable = s3db.pr_address
        record = Storage(pe_id = pe_id,
                         type = 1,
                         location_id = address_location_id,
                         )
        address = atable.insert(**record)
        self.assertNotEqual(address, None)
        record["id"] = address
        #s3db.update_super(atable, record)
        s3db.onaccept(atable, record, method="create")

        # Test that the HR location is set correctly
        row = db(htable.id == human_resource_id).select(htable.location_id,
                                                        limitby=(0, 1)).first()

        self.assertNotEqual(row, None)
        return row, address_location_id, site_location_id

    # -------------------------------------------------------------------------
    def testVolUpdateFromPersonAddress1(self):
        """
            Test that a Volunteer can get their location_id updated from a
            New Home Address: with just "person_id"
        """

        current.deployment_settings.hrm.location_vol = "person_id"

        row, address_location_id, site_location_id = self._testVolUpdateFromPersonAddress(site=False)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testVolUpdateFromPersonAddress2(self):
        """
            Test that a Volunteer can get their location_id updated from a
            New Home Address: with just "person_id"
        """

        current.deployment_settings.hrm.location_vol = "person_id"

        row, address_location_id, site_location_id = self._testVolUpdateFromPersonAddress(site=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testVolUpdateFromPersonAddress3(self):
        """
            Test that a Volunteer can get their location_id updated from a
            New Home Address: with "person_id" 1st
        """

        current.deployment_settings.hrm.location_vol = ("person_id", "site_id")

        row, address_location_id, site_location_id = self._testVolUpdateFromPersonAddress(site=False)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testVolUpdateFromPersonAddress4(self):
        """
            Test that a Volunteer can get their location_id updated from a
            New Home Address: with "person_id" 1st
        """

        current.deployment_settings.hrm.location_vol = ("person_id", "site_id")

        row, address_location_id, site_location_id = self._testVolUpdateFromPersonAddress(site=True)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testVolUpdateFromPersonAddress5(self):
        """
            Test that a Volunteer can get their location_id updated from a
            New Home Address: with "person_id" 2nd
        """

        current.deployment_settings.hrm.location_vol = ("site_id", "person_id")

        row, address_location_id, site_location_id = self._testVolUpdateFromPersonAddress(site=False)
        self.assertEqual(row.location_id, address_location_id)

    # -------------------------------------------------------------------------
    def testVolUpdateFromPersonAddress6(self):
        """
            Test that a Volunteer can get their location_id updated from a
            New Home Address: with "person_id" 2nd
        """

        current.deployment_settings.hrm.location_vol = ("site_id", "person_id")

        row, address_location_id, site_location_id = self._testVolUpdateFromPersonAddress(site=True)
        self.assertEqual(row.location_id, site_location_id)

    # -------------------------------------------------------------------------
    def testVolUpdateFromPersonAddress7(self):
        """
            Test that a Volunteer can get their location_id updated from a
            New Home Address: with no "person_id"
        """

        current.deployment_settings.hrm.location_vol = "site_id"

        row, address_location_id, site_location_id = self._testVolUpdateFromPersonAddress(site=False)
        self.assertEqual(row.location_id, None)

    # -------------------------------------------------------------------------
    def testVolUpdateFromPersonAddress8(self):
        """
            Test that a Volunteer can get their location_id updated from a
            New Home Address: with no "person_id"
        """

        current.deployment_settings.hrm.location_vol = "site_id"

        row, address_location_id, site_location_id = self._testVolUpdateFromPersonAddress(site=True)
        self.assertEqual(row.location_id, site_location_id)

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
        LocationSettingTests,
    )

# END ========================================================================
