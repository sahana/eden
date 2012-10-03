# -*- coding: utf-8 -*-
#
# Project Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/eden/project.py
#
import unittest

from gluon import *
from gluon.storage import Storage
from gluon.dal import Row
from eden.project import S3ProjectActivityModel


# =============================================================================
class ProjectTests(unittest.TestCase):
    """ Project Module Tests """

    def setUp(self):
        """ Set up organisation records """

        # auth = current.auth
        s3db = current.s3db

        auth.override = True

        ptable = s3db.project_project
        atable = s3db.project_activity

        p1 = Row(name="Test Project 1", code="TP1")
        p1_id = ptable.insert(**p1)
        p1.update(id=p1_id)

        a1 = Row(name="Test Activity 1", project_id=p1_id)
        a1_id = atable.insert(**a1)
        a1.update(id=a1_id)

        # activity without a project
        a2 = Row(name="Test Activity 2")
        a2_id = atable.insert(**a2)
        a2.update(id=a2_id)

        self.p1 = p1
        self.a1 = a1
        self.a2 = a2

    def testActivityRepresent(self):
        rep = S3ProjectActivityModel.project_activity_represent

        self.assertEqual(
            rep(self.a1.id),
            "%s - %s" % (self.p1.code, self.a1.name),
        )

        self.assertEqual(
            rep(self.a2.id),
            "%s" % self.a2.name,
        )

        self.assertEqual(
            rep(None),
            current.messages.NONE,
        )

        self.assertEqual(
            rep(self.a1),
            "%s - %s" % (self.p1.code, self.a1.name),
        )

        self.assertEqual(
            rep(self.a1.id, self.a1),
            "%s - %s" % (self.p1.code, self.a1.name),
        )

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
        unittest.TextTestRunner().run(suite)
    return

if __name__ == "__main__":

    run_suite(
        ProjectTests,
    )

# END ========================================================================
