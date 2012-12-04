"""
    Tests for the report helper function in web2unittest.
"""

from gluon import current
from tests.web2unittest import SeleniumUnitTest

class ReportTestHelper(SeleniumUnitTest):
    # -------------------------------------------------------------------------
    def test_report_test_helper_normal(self):
        self.login(account="admin", nexturl="asset/asset/report")
        self.report("Item", "Category", False,
            ("Motorcyle - Yamaha - DT50MX", "Default > Vehicle", 5))

    # -------------------------------------------------------------------------
    def test_report_test_helper_invalid_report(self):
        self.login(account="admin", nexturl="asset/asset/report")
        with self.assertRaises(self.InvalidReportOrGroupException):
            self.report("Category", "Invalid Report", False,
                ("Default > Equipment", "Timor-Leste Red Cross Society (CVTL)",
                 16))

# END =========================================================================