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

from s3.s3dashboard import S3DashboardAgent, \
                           S3DashboardContext, \
                           S3DashboardWidget, \
                           delegated

from unit_tests import run_suite

# =============================================================================
class S3DashboardAgentTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    class DummyWidget(S3DashboardWidget):
        """ Dummy subclass for testing """

        @delegated
        def command(agent, context):
            """ An agent command implemented by the widget """

            config = agent.config

            # Build return value from config and context
            return {"param": "%s,%s" % (config.get("param"),
                                        context.get("param"),
                                        ),
                    }

        def not_delegated():
            """ Some other internal method of the widget """

            # Agent should never execute this
            raise RuntimeError

    # -------------------------------------------------------------------------
    def setUp(self):

        self.widget = self.DummyWidget(defaults = {"param": "default"})

    # -------------------------------------------------------------------------
    def testDelegation(self):
        """ Verify execution of delegated widget method """

        # The widget
        widget = self.widget

        # Create an agent for the widget
        agent = widget.create_agent("agent",
                                    config = {"param": "live",
                                              },
                                    )

        # Dummy context
        context = {"param": "test"}

        # Verify execution of delegated method
        output = agent.do("command", context)
        self.assertIn("param", output)
        self.assertEqual(output["param"], "live,test")

    # -------------------------------------------------------------------------
    def testDelegationMultipleAgents(self):
        """ Verify execution of delegated widget method with multiple agents """

        assertIn = self.assertIn
        assertEqual = self.assertEqual

        num_agents = 4

        # The widget
        widget = self.widget
        create_agent = widget.create_agent

        # Create an array of agents for the widget
        agents = []
        append = agents.append
        for i in range(num_agents):
            agent = create_agent("agent%s" % i,
                                 config = {"param": "live%s" % i},
                                 )
            append(agent)
        assertEqual(len(widget.agents), num_agents)

        # Dummy context
        context = {"param": "test"}

        # Verify execution of delegated method
        for i, agent in enumerate(agents):
            output = agent.do("command", context)
            assertIn("param", output)
            assertEqual(output["param"], "live%s,test" % i)

    # -------------------------------------------------------------------------
    def testInvalidDelegation(self):
        """ Verify error handling for delegated widget methods """

        # The widget
        widget = self.widget

        # Create an agent for the widget
        agent = widget.create_agent("agent")

        # Attempt to execute a nonexistent widget method should raise exception
        with self.assertRaises(NotImplementedError):
            agent.do("nonexistent", {})

        # Attempt to execute a non-delegated widget method should raise exception
        with self.assertRaises(NotImplementedError):
            agent.do("not_delegated", {})

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
        request._get_vars = Storage({"agent": ["widget-1", "widget-2,widget-3"]})
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

    # -------------------------------------------------------------------------
    def testSharedWrite(self):
        """ Verify item pattern to write shared context dict """

        context = S3DashboardContext()

        context["test"] = "ABC"
        self.assertTrue("test" in context.shared)
        self.assertEqual(context.shared["test"], "ABC")

    # -------------------------------------------------------------------------
    def testSharedRead(self):
        """ Verify item pattern to read shared context dict """

        context = S3DashboardContext()

        context.shared["test"] = "XYZ"
        self.assertEqual(context["test"], "XYZ")

        # Verify KeyError raised when attempting to access nonexistent item
        with self.assertRaises(KeyError):
            context["nonexistent"]

    # -------------------------------------------------------------------------
    def testSharedGet(self):
        """ Verify get() method to read shared context dict """

        assertEqual = self.assertEqual

        context = S3DashboardContext()

        context.shared["test"] = "XYZ"

        assertEqual(context.get("test"), "XYZ")
        assertEqual(context.get("nonexistent"), None)

        default = lambda: None
        self.assertTrue(context.get("nonexistent", default) is default)

    # -------------------------------------------------------------------------
    def testSharedDelete(self):
        """ Verify deletion of shared context items """

        context = S3DashboardContext()

        context.shared["test"] = "XYZ"

        # Verify deletion of item
        del context["test"]
        self.assertNotIn("test", context.shared)

        # Verify KeyError raised when attempting to delete nonexistent item
        with self.assertRaises(KeyError):
            del context["test"]

    # -------------------------------------------------------------------------
    def testAttributeFallback(self):
        """ Verify attribute access falls back to current request """

        request = current.request

        assertIn = self.assertIn
        assertNotIn = self.assertNotIn
        assertTrue = self.assertTrue

        fallback = request.args
        override = ["override"]

        context = S3DashboardContext(request)

        # Check fallback
        assertNotIn("args", context.__dict__)
        assertTrue(context.args is fallback)

        # Check override
        context.args = override
        assertIn("args", context.__dict__)
        assertTrue(request.args is fallback)
        assertTrue(context.args is override)

# =============================================================================
if __name__ == "__main__":

    run_suite(
        S3DashboardContextTests,
        S3DashboardAgentTests,
    )

# END ========================================================================
