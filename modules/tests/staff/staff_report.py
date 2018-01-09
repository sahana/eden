# -*- coding: utf-8 -*-

""" Sahana Eden Staff Module Automated Tests

    @copyright: 2011-2018 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

from gluon import current
from tests.web2unittest import SeleniumUnitTest


class StaffReport(SeleniumUnitTest):
    """
    @case: hrm008
    @description: Staff Report
    """
    def setUp(self):
        super(StaffReport, self).setUp()
        print "\n"
        self.login(account="admin", nexturl="hrm/staff/report")
        self.settings = current.deployment_settings

    def test_staff_report_simple(self):
        self.report(None,
                self.settings.get_hrm_organisation_label(),
                "County / District",
                self.settings.get_hrm_organisation_label() + " (Count)",
                ("Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste) (CVTL)", "Ainaro", 1),
                ("Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste) (CVTL)", "Kuala Lumpur", 0),
            )

    def test_staff_report_filter(self):
        self.report(
            ({
                "name": "human_resource_search_select_organisation_id",
                "label": "Timor-Leste Red Cross Society (CVTL)",
                "value": True
            },), self.settings.get_hrm_organisation_label(),
                "County / District",
                 self.settings.get_hrm_organisation_label() + " (Count)",
            row_count=1)

    def test_staff_report_filter_L0_L1(self):
        self.report(
            ({
                "name": "human_resource_search_select_location_id$L0",
                "label": "Timor-Leste",
                "value": True
            },
            {
                "name": "human_resource_search_select_location_id$L2",
                "label": "Ainaro",
                "value": True
            }),
            "County / District",
            self.settings.get_hrm_organisation_label(),
            self.settings.get_hrm_organisation_label() + " (Count)",
            row_count=1)

    def test_staff_report_person(self):
        self.report(None,
            self.settings.get_hrm_organisation_label(),
            "State / Province",
            "Person (List)",
            ("Timor-Leste Red Cross Society (Cruz Vermelha de Timor-Leste) (CVTL)", "Dili",
                ("Duarte Botelheiro",
                "Adriana Macedo",
                "Quito Cromos",
                "Guilherme Soares",
                "Xanana Chilro",
                u"José Saboga",
                "Elly Marques",
                "Nilton Moniz",
                "Herculano Ximenes",
                "Goku Gohan")
            ))
