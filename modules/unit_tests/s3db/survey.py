# -*- coding: utf-8 -*-
#
# Survey Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3db/survey.py
#
import unittest

from gluon import *
from gluon.storage import Storage

from s3.s3rest import S3Request
from s3db.survey import series_ExportFormatted
from s3survey import DataMatrix

# =============================================================================
class ExportFormattedTests(unittest.TestCase):
    """ Test series_ExportFormatted """

    # -------------------------------------------------------------------------
    def setUp(self):
        """
            Implements setUp method of TestCase class
        """

        current.auth.override = True
        db = current.db
        s3db = current.s3db
        ttable = s3db.survey_template
        stable = s3db.survey_series

        # Insert a test record for survey_template
        record = dict(name = "Test template",
                      competion_qstn = "Name of assessment team leader",
                      date_qstn = "Date of Assessment",
                      time_qstn = "Time of Assessment",
                      location_detail = "['L0', 'L1', 'L2', 'L3', 'Lat', 'Lon']",
                      priority_qstn = "24H-8")
        self.template_id = ttable.insert(**record)
        self.t = str(self.template_id)
        self.assertNotEqual(self.template_id, None)

        # Insert a test record for survey_series
        record = dict(name = "Test series",
                      description = "Test Description",
                      template_id = self.template_id,
                      )
        self.series_id = stable.insert(**record)
        self.s = str(self.series_id)
        self.assertNotEqual(self.series_id, None)

        self.S = series_ExportFormatted()


    # -------------------------------------------------------------------------
    def tearDown(self):
        """
            Implements tearDown method of TestCase class
        """

        current.db.rollback()
        current.auth.override = False

    # -------------------------------------------------------------------------
    def testExportSpreadsheet(self):
        """
            Test export formatted spreadsheet
        """

        r = S3Request(prefix = "survey",
                      name = "series",
                      args = [self.s, "export_formatted_spreadsheet"],
                      )

        logo = None
        (matrix, matrixAnswers) = self.S.series_prepare_matrix(self.series_id,
                                                               r.record,
                                                               logo,                                 
                                                               dict(),
                                                               justified = True)

        self.assertTrue(isinstance(matrix, DataMatrix))
        self.assertTrue(isinstance(matrixAnswers, DataMatrix))

        
        output = self.S.series_export_spreadsheet(matrix,
                                                  matrixAnswers,
                                                  logo)
        self.assertNotEqual(output, None)
        
    # -------------------------------------------------------------------------
    def testGetStyleList(self):
        """
            Test get_style_list()
        """
        style_list = self.S._get_style_list()
        self.assertTrue(isinstance(style_list, dict))

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
        ExportFormattedTests,
    )

# END ========================================================================
