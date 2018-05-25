# -*- coding: utf-8 -*-
#
# S3DataTable Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3datatable.py
#
import unittest
import datetime
from gluon import *
from gluon.storage import Storage

from s3.s3data import S3DataTable

from unit_tests import run_suite

# =============================================================================
class S3DataTableTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    def setUp(self):
        """
            Set up the list of fields each time since the call to S3DataTables
            could change it.
        """

        current.auth.override = True

        resource = current.s3db.resource("org_office")
        list_fields = ["id",
                       "organisation_id$name",
                       "name",
                       "office_type_id",
                       "location_id$L0",
                       "location_id$L1",
                       "location_id$L2",
                       "location_id$L3",
                       "phone1",
                       "email"
                       ]

        self.resource = resource
        self.list_fields = list_fields

        data = resource.select(list_fields)

        self.data = data["rows"]
        self.rfields = data["rfields"]

    # -------------------------------------------------------------------------
    def testDataTableInitialOrderby(self):
        """ Test the initial orderby for different types of input. """

        table = self.resource.table

        dt = S3DataTable(self.rfields, self.data)
        expected = [[1, "asc"]]
        actual = dt.orderby
        self.assertEqual(expected, actual)

        dt = S3DataTable(self.rfields, self.data,
                         orderby=table.name)
        expected = [[2, "asc"]]
        actual = dt.orderby
        self.assertEqual(expected, actual)

        dt = S3DataTable(self.rfields, self.data,
                         orderby=~table.name)
        expected = [[2, "desc"]]
        actual = dt.orderby
        self.assertEqual(expected, actual)

        dt = S3DataTable(self.rfields, self.data,
                         orderby=table.office_type_id | table.name)
        expected = [[3, "asc"], [2, "asc"]]
        actual = dt.orderby
        self.assertEqual(expected, actual)

        dt = S3DataTable(self.rfields, self.data,
                         orderby=~table.office_type_id | table.name)
        expected = [[3, "desc"], [2, "asc"]]
        actual = dt.orderby
        self.assertEqual(expected, actual)

        otable = current.s3db.org_organisation
        dt = S3DataTable(self.rfields, self.data,
                         orderby=otable.name | ~table.office_type_id | table.name)
        expected = [[1, "asc"], [3, "desc"], [2, "asc"]]
        actual = dt.orderby
        self.assertEqual(expected, actual)

    # -------------------------------------------------------------------------
    def tearDown(cls):

        current.auth.override = False

# =============================================================================
if __name__ == "__main__":

    run_suite(
        S3DataTableTests,
    )

# END ========================================================================
