# -*- coding: utf-8 -*-
#
# CMS Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3db/cms.py
#
import unittest

from gluon import *
from unit_tests import run_suite

# =============================================================================
class CMSPostBodyRepresentTests(unittest.TestCase):
    """ Tests for the represent method on the cms_post.body field """

    # -------------------------------------------------------------------------
    def setUp(self):
        self.represent = current.s3db.cms_post.body.represent

    # -------------------------------------------------------------------------
    def testNoURLs(self):
        """ Test that no hrefs are added if there are no URLs """

        self.assertEqual(
            self.represent("no urls in here, just unicode ßñö chars"),
            "no urls in here, just unicode ßñö chars"
            )


    # -------------------------------------------------------------------------
    def testURLsWithoutHref(self):
        """ Test that href elements are added for all URLs if there are no hrefs """

        self.assertEqual(
            self.represent(
                "unicode ßñö chars, urls for https://sahanafoundation.org/ and "
                "www.github.com/sahana/eden"
            ),
            "unicode ßñö chars, urls for "
            "<a href=\"https://sahanafoundation.org/\" target=\"_blank\">"
            "https://sahanafoundation.org/</a> and "
            "<a href=\"www.github.com/sahana/eden\" target=\"_blank\">"
            "www.github.com/sahana/eden</a>"
        )

    # -------------------------------------------------------------------------
    def testURLsWithHrefs(self):
        """ Test that if there is already at least one href, then no hrefs are added """

        self.assertEqual(
            self.represent(
                "unicode ßñö chars and urls for "
                "<a href=\"https://sahanafoundation.org/\" target=\"_blank\">"
                "https://sahanafoundation.org/ and www.github.com/sahana/eden"
            ),
            "unicode ßñö chars and urls for "
            "<a href=\"https://sahanafoundation.org/\" target=\"_blank\">"
            "https://sahanafoundation.org/ and www.github.com/sahana/eden"
        )

# =============================================================================
if __name__ == "__main__":

    run_suite(
        CMSPostBodyRepresentTests,
    )

# END ========================================================================
