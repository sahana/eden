# S3Filter Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3filter.py

import unittest

from gluon import *
from gluon.storage import Storage
from s3.s3forms import *

from unit_tests import run_suite

# =============================================================================
class InlineLinkTests(unittest.TestCase):

    def testInlineLinkValidation(self):

        # Default error message
        widget = S3SQLInlineLink("component",
                                 field = "test",
                                 required = True,
                                 )
        widget.alias = "default"

        form = Storage(vars = Storage(link_defaultcomponent=[1,2]),
                       errors=Storage(),
                       )

        widget.validate(form)
        errors = form.errors
        self.assertNotIn("link_defaultcomponent", errors)

        form = Storage(vars = Storage(),
                       errors=Storage(),
                       )

        widget.validate(form)
        errors = form.errors
        self.assertIn("link_defaultcomponent", errors)

        # Custom error message
        msg = "Custom Error Message"
        widget = S3SQLInlineLink("component",
                                 field = "test",
                                 required = msg,
                                 )
        widget.alias = "default"

        form = Storage(vars = Storage(link_defaultcomponent=[1,2]),
                       errors=Storage(),
                       )

        widget.validate(form)
        errors = form.errors
        self.assertNotIn("link_defaultcomponent", errors)

        form = Storage(vars = Storage(),
                       errors=Storage(),
                       )

        widget.validate(form)
        errors = form.errors
        self.assertIn("link_defaultcomponent", errors)
        self.assertEqual(errors.link_defaultcomponent, msg)

# =============================================================================
if __name__ == "__main__":

    run_suite(
        InlineLinkTests,
    )

# END ========================================================================
