# -*- coding: utf-8 -*-
#
# S3Dashboard Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3dashboard.py
#
import unittest

from gluon import current
from gluon.storage import Storage

from s3.s3dashboard import S3DashboardContext

from unit_tests import run_suite

# =============================================================================
class S3DashboardContextTests(unittest.TestCase):
    """ Tests for S3DashboardContext """

    # -------------------------------------------------------------------------
    def setUp(self):

        request = current.request

        # Remember original request parameters
        self.http = request.env.request_method
        self.extension = request.extension
        self.args = request.args
        self._get_vars = request._get_vars

    # -------------------------------------------------------------------------
    def tearDown(self):

        request = current.request

        # Restore original request parameters
        request.env.request_method = self.http
        request.extension = self.extension
        request.args = self.args
        request._get_vars = self._get_vars

    # -------------------------------------------------------------------------
    def testWithoutCommand(self):
        """ Verify that no URL args give no context command """

        request = current.request
        request.args = []

        context = S3DashboardContext()
        self.assertEqual(context.command, None)

    # -------------------------------------------------------------------------
    def testWithCommand(self):
        """ Verify that first URL arg gives context command """

        request = current.request
        assertEqual = self.assertEqual

        request.args = ["test"]
        context = S3DashboardContext()
        assertEqual(context.command, "test")

        request.args = ["skip", "other"]
        context = S3DashboardContext()
        assertEqual(context.command, "skip")

    # -------------------------------------------------------------------------
    def testCommandWithFormatExtension(self):
        """ Verify that format extension is ignored for command """

        request = current.request
        assertEqual = self.assertEqual

        request.args = ["test.xml"]
        context = S3DashboardContext()
        assertEqual(context.command, "test")

    # -------------------------------------------------------------------------
    def testNoAgent(self):
        """ Verify there is no default agent """

        request = current.request
        assertEqual = self.assertEqual

        request._get_vars = Storage()
        context = S3DashboardContext()
        assertEqual(context.agent, None)
        assertEqual(context.bulk, False)

    # -------------------------------------------------------------------------
    def testSingleAgent(self):
        """ Verify single agent ID is recognized """

        request = current.request
        assertEqual = self.assertEqual

        request._get_vars = Storage({"agent": "widget-1"})
        context = S3DashboardContext()
        assertEqual(context.agent, "widget-1")
        assertEqual(context.bulk, False)

    # -------------------------------------------------------------------------
    def testSingleAgentBulk(self):
        """ Verify single agent ID can still be bulk """

        request = current.request
        assertEqual = self.assertEqual

        # Test with trailing comma
        request._get_vars = Storage({"agent": "widget-1,"})
        context = S3DashboardContext()
        assertEqual(context.agent, ["widget-1"])
        assertEqual(context.bulk, True)

        # Test with explicit "bulk" option
        request._get_vars = Storage({"agent": "widget-1", "bulk": "1"})
        context = S3DashboardContext()
        assertEqual(context.agent, ["widget-1"])
        assertEqual(context.bulk, True)

    # -------------------------------------------------------------------------
    def testMultiAgent(self):
        """ Verify multiple agent IDs are recognized """

        request = current.request

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertIn = self.assertIn

        agent_ids = ("widget-1", "widget-2", "widget-3")

        # Single "agent" var
        request._get_vars = Storage({"agent": "widget-1,widget-2,widget-3"})
        context = S3DashboardContext()
        assertTrue(type(context.agent) is list)
        for agent_id in agent_ids:
            assertIn(agent_id, context.agent)
        assertEqual(context.bulk, True)

        # Multiple "agent" vars
        request._get_vars = Storage({"agent": ["widget-1","widget-2,widget-3"]})
        context = S3DashboardContext()
        assertTrue(type(context.agent) is list)
        for agent_id in agent_ids:
            assertIn(agent_id, context.agent)
        assertEqual(context.bulk, True)

        # Can not deny "bulk" with multiple agent IDs
        request._get_vars = Storage({"agent": "widget-1,widget-2,widget-3", "bulk": "0"})
        context = S3DashboardContext()
        assertEqual(context.bulk, True)

    # -------------------------------------------------------------------------
    def testHTTP(self):
        """ Verify S3DashboardContext.http matches request method """

        request = current.request
        assertEqual = self.assertEqual

        for method in ("GET", "POST", "DELETE"):
            request.env.request_method = method
            context = S3DashboardContext()
            assertEqual(context.http, method)

    # -------------------------------------------------------------------------
    def testHTTPDefault(self):
        """ Verify S3DashboardContext.http defaults to GET """

        current.request.env.request_method = None
        context = S3DashboardContext()
        self.assertEqual(context.http, "GET")

    # -------------------------------------------------------------------------
    def testFormatExtension(self):
        """ Verify S3DashboardContext recognizes URL format extension """

        request = current.request
        request._get_vars = Storage()
        assertEqual = self.assertEqual

        request.extension = "json"
        request.args = ["command", "1"]
        context = S3DashboardContext()
        assertEqual(context.representation, "json")

        request.extension = "json"
        request.args = ["command.xml", "1"]
        context = S3DashboardContext()
        assertEqual(context.representation, "xml")

        request.extension = "json"
        request.args = ["command.xml", "1.pdf"]
        context = S3DashboardContext()
        assertEqual(context.representation, "pdf")

    # -------------------------------------------------------------------------
    def testFormatQuery(self):
        """ Verify S3DashboardContext recognizes URL format query """

        request = current.request
        request.extension = "html"
        request.args = ["command.json"]
        assertEqual = self.assertEqual

        request._get_vars = Storage()
        context = S3DashboardContext()
        assertEqual(context.representation, "json")

        request._get_vars = Storage({"format": "xml"})
        context = S3DashboardContext()
        assertEqual(context.representation, "xml")

    # -------------------------------------------------------------------------
    def testFormatDefault(self):
        """ Verify S3DashboardContext falls back to html format """

        # Remove all format hints
        request = current.request
        request.extension = None
        request.args = []
        request._get_vars = Storage()

        context = S3DashboardContext()
        self.assertEqual(context.representation, "html")

# =============================================================================
if __name__ == "__main__":

    run_suite(
        S3DashboardContextTests,
    )

# END ========================================================================
