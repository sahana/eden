# -*- coding: utf-8 -*-

"""
    This file specifies the tests which are to be run on the default template.

    modules/tests/suite.py runs this file to get the test_list which is to be loaded.
    To add more tests which are to run on this template, simply add the class name
    to the list below.
"""

from gluon import current

current.selenium_tests = ["CreateOrganisation",
                          "CreateOffice",
                          "CreateStaff",
                          "CreateStaffJobTitle",
                          "CreateStaffCertificate",
                          "SearchStaff",
                          "StaffReport",
                          "CreateVolunteer",
                          "CreateVolunteerJobTitle",
                          "CreateVolunteerProgramme",
                          "CreateVolunteerSkill",
                          "CreateVolunteerCertificate",
                          "VolunteerSearch",
                          "CreateStaffTraining",
                          "CreateVolunteerTraining",
                          "SendItem",
                          "ReceiveItem",
                          "SendReceiveItem",
                          "CreateProject",
                          "CreateAsset",
                          "AssetSearch",
                          "AssetReport",
                          "AddStaffParticipants",
                          "AddStaffToOrganisation",
                          "AddStaffToOffice",
                          "AddStaffToWarehouse",
                          "CreateWarehouse",
                          "SearchWarehouse",
                          "CreateItem",
                          "CreateCatalog",
                          "CreateCategory",
                          "ReportTestHelper",
                          "CreateFacility",
                          "CreateEvent",
                          "CreateIncidentReport",
                          "ImportStaff"
                          ]
