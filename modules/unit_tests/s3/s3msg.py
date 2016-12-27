# -*- coding: utf-8 -*-
#
# Msg Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3msg.py
#
import unittest
import datetime
from lxml import etree
from gluon import *
from gluon.storage import Storage
from s3 import *

from unit_tests import run_suite

# =============================================================================
class S3OutboxTests(unittest.TestCase):
    """ Outbox processing tests """

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        current.auth.override = True

        xmlstr = """
<s3xml>
    <resource name="pr_person" uuid="MsgTestPerson1">
        <data field="first_name">MsgTest</data>
        <data field="last_name">Person1</data>
        <resource name="pr_contact">
            <data field="contact_method">EMAIL</data>
            <data field="value">test1@example.com</data>
        </resource>
    </resource>
    <resource name="pr_person" uuid="MsgTestPerson2">
        <data field="first_name">MsgTest</data>
        <data field="last_name">Person2</data>
        <resource name="pr_contact">
            <data field="contact_method">EMAIL</data>
            <data field="value">test2@example.com</data>
        </resource>
    </resource>
    <resource name="org_organisation" uuid="MsgTestOrg">
        <data field="name">MsgTestOrg</data>
        <resource name="hrm_human_resource">
            <reference field="person_id" resource="pr_person" uuid="MsgTestPerson1"/>
        </resource>
        <resource name="hrm_human_resource">
            <reference field="person_id" resource="pr_person" uuid="MsgTestPerson2"/>
        </resource>
    </resource>
    <resource name="pr_group" uuid="MsgTestGroup">
        <data field="name">MsgTestGroup</data>
        <resource name="pr_group_membership">
            <reference field="person_id" resource="pr_person" uuid="MsgTestPerson1"/>
        </resource>
        <resource name="pr_group_membership">
            <reference field="person_id" resource="pr_person" uuid="MsgTestPerson2"/>
        </resource>
    </resource>
</s3xml>"""
        xmltree = etree.ElementTree(etree.fromstring(xmlstr))

        s3db = current.s3db

        # Import the test entities
        resource = s3db.resource("pr_person")
        resource.import_xml(xmltree)
        if resource.error is not None:
            raise AssertionError("Test data import failed: %s" % resource.error)

        resource = s3db.resource("org_organisation")
        resource.import_xml(xmltree)
        if resource.error is not None:
            raise AssertionError("Test data import failed: %s" % resource.error)

        resource = s3db.resource("pr_group")
        resource.import_xml(xmltree)
        if resource.error is not None:
            raise AssertionError("Test data import failed: %s" % resource.error)

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        s3db = current.s3db

        resource = s3db.resource("pr_person", uid=["MsgTestPerson1", "MsgTestPerson2"])
        result = resource.delete()
        if result != 2:
            raise AssertionError("Test data deletion failed")

        resource = s3db.resource("org_organisation", uid="MsgTestOrg")
        result = resource.delete()
        if result != 1:
            raise AssertionError("Test data deletion failed")

        resource = s3db.resource("pr_group", uid="MsgTestGroup")
        result = resource.delete()
        if result != 1:
            raise AssertionError("Test data deletion failed")

        current.auth.override = False

    # -------------------------------------------------------------------------
    def setUp(self):

        db = current.db
        s3db = current.s3db

        # Backup normal method
        self.save_email = current.msg.send_email

        # Temporarily disable any pending messages, so they
        # don't interfere with this test
        outbox = s3db.msg_outbox
        db(outbox.status == 1).update(status=99)

        # Insert a test email
        mailbox = s3db.msg_email
        mail_id = mailbox.insert(subject="Test Email", body="Unit Test")
        record = db(mailbox.id == mail_id).select(mailbox.id,
                                                  mailbox.message_id,
                                                  limitby=(0, 1)).first()
        s3db.update_super(mailbox, record)
        self.message_id = record.message_id
        self.assertTrue(self.message_id > 0)

        self.sent = []

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()

        # Restore normal method
        current.msg.send_email = self.save_email

    # -------------------------------------------------------------------------
    def testProcessEmailToPerson(self):
        """ Test processing emails to individual persons """

        s3db = current.s3db
        resource = s3db.resource("pr_person", uid=["MsgTestPerson1",
                                                   "MsgTestPerson2"])
        rows = resource.select(["pe_id"], as_rows=True)

        self.sent = []

        outbox = s3db.msg_outbox
        for row in rows:
            outbox_id = outbox.insert(pe_id = row.pe_id,
                                      message_id = self.message_id)

        msg = current.msg
        msg.send_email = self.send_email
        msg.process_outbox()
        self.assertEqual(len(self.sent), 2)
        self.assertTrue("test1@example.com" in self.sent)
        self.assertTrue("test2@example.com" in self.sent)

    # -------------------------------------------------------------------------
    def testProcessEmailToGroup(self):
        """ Test processing emails to groups """

        s3db = current.s3db
        resource = s3db.resource("pr_group", uid=["MsgTestGroup"])
        rows = resource.select(["pe_id"], as_rows=True)

        self.sent = []

        outbox = s3db.msg_outbox
        for row in rows:
            outbox_id = outbox.insert(pe_id = row.pe_id,
                                      message_id = self.message_id)

        msg = current.msg
        msg.send_email = self.send_email
        msg.process_outbox()
        self.assertEqual(len(self.sent), 2)
        self.assertTrue("test1@example.com" in self.sent)
        self.assertTrue("test2@example.com" in self.sent)

    # -------------------------------------------------------------------------
    def testProcessEmailToOrganisation(self):
        """ Test processing emails to organisations """

        s3db = current.s3db
        resource = s3db.resource("org_organisation", uid=["MsgTestOrg"])
        rows = resource.select(["pe_id"], as_rows=True)

        self.sent = []

        outbox = s3db.msg_outbox
        for row in rows:
            outbox_id = outbox.insert(pe_id = row.pe_id,
                                      message_id = self.message_id)

        msg = current.msg
        msg.send_email = self.send_email
        msg.process_outbox()
        self.assertEqual(len(self.sent), 2)
        self.assertTrue("test1@example.com" in self.sent)
        self.assertTrue("test2@example.com" in self.sent)

    # -------------------------------------------------------------------------
    def testProcessingEmailToInvalidPerson(self):
        """ Test sending to a non-existent person """

        s3db = current.s3db
        resource = s3db.resource("pr_person", uid=["MsgTestPerson1"])
        row = resource.select(["pe_id"], as_rows=True).first()

        self.sent = []

        outbox = s3db.msg_outbox
        outbox_id = outbox.insert(pe_id = row.pe_id,
                                  message_id = self.message_id)
        outbox_id = outbox.insert(pe_id = None,
                                  message_id = self.message_id)

        msg = current.msg
        msg.send_email = self.send_email
        msg.process_outbox()
        self.assertEqual(len(self.sent), 1)
        self.assertTrue("test1@example.com" in self.sent)

    # -------------------------------------------------------------------------
    def testProcessingEmailToInvalidPersonInGroup(self):
        """ Test sending to a group that contains an invalid membership """

        db = current.db
        s3db = current.s3db

        ptable = s3db.pr_person
        gtable = s3db.pr_group
        mtable = s3db.pr_group_membership
        query = (gtable.uuid == "MsgTestGroup") & \
                (mtable.group_id == gtable.id) & \
                (ptable.id == mtable.person_id) & \
                (ptable.uuid == "MsgTestPerson1")
        membership = db(query).select(mtable.id).first()
        db(mtable.id==membership.id).update(person_id=None)

        s3db = current.s3db
        resource = s3db.resource("pr_group", uid=["MsgTestGroup"])
        rows = resource.select(["pe_id"], as_rows=True)

        self.sent = []

        outbox = s3db.msg_outbox
        for row in rows:
            outbox_id = outbox.insert(pe_id = row.pe_id,
                                      message_id = self.message_id)

        msg = current.msg
        msg.send_email = self.send_email
        msg.process_outbox()
        self.assertEqual(len(self.sent), 1)
        self.assertTrue("test2@example.com" in self.sent)

    # -------------------------------------------------------------------------
    def testProcessEmailToOrganisationSendError(self):
        """
            Test processing emails to an organisation with error
            during send
        """

        s3db = current.s3db
        resource = s3db.resource("org_organisation", uid=["MsgTestOrg"])
        rows = resource.select(["pe_id"], as_rows=True)

        self.sent = []

        outbox = s3db.msg_outbox
        for row in rows:
            outbox_id = outbox.insert(pe_id = row.pe_id,
                                      message_id = self.message_id)

        msg = current.msg
        msg.send_email = self.send_email_error
        msg.process_outbox()
        self.assertEqual(len(self.sent), 1)
        self.assertTrue("test2@example.com" in self.sent)

    # -------------------------------------------------------------------------
    def testProcessEmailToGroupSendException(self):
        """
            Test processing emails to an organisation with exception
            during send
        """

        s3db = current.s3db
        resource = s3db.resource("pr_group", uid=["MsgTestGroup"])
        rows = resource.select(["pe_id"], as_rows=True)

        self.sent = []

        outbox = s3db.msg_outbox
        for row in rows:
            outbox_id = outbox.insert(pe_id = row.pe_id,
                                      message_id = self.message_id)

        msg = current.msg
        msg.send_email = self.send_email_exception
        msg.process_outbox()
        self.assertEqual(len(self.sent), 1)
        self.assertTrue("test1@example.com" in self.sent)

    # -------------------------------------------------------------------------
    def testProcessEmailToPersonMaxRetries(self):
        """ Test inhibition of failing messages after max_send_retries """

        MAX_SEND_RETRIES = current.deployment_settings \
                                  .get_msg_max_send_retries()
        if MAX_SEND_RETRIES is None:
            return

        s3db = current.s3db
        resource = s3db.resource("pr_person", uid=["MsgTestPerson1"])
        row = resource.select(["pe_id"], as_rows=True).first()

        self.sent = []

        outbox = s3db.msg_outbox
        outbox_id = outbox.insert(pe_id = row.pe_id,
                                  message_id = self.message_id)

        msg = current.msg
        msg.send_email = self.send_email_error
        for i in range(MAX_SEND_RETRIES+1):
            out_msg = outbox[outbox_id]
            self.assertEqual(out_msg.status, 1) # Unsent
            msg.process_outbox()
        out_msg = outbox[outbox_id]
        self.assertEqual(out_msg.status, 5) # Failed

    # -------------------------------------------------------------------------
    def send_email(self, recipient, *args, **kwargs):
        """ Dummy send mechanism """

        if recipient in ("test1@example.com", "test2@example.com"):
            self.sent.append(recipient)
            return True
        else:
            return False

    # -------------------------------------------------------------------------
    def send_email_error(self, recipient, *args, **kwargs):
        """ Dummy send mechanism that fails for 1 recipient """

        if recipient == "test2@example.com":
            self.sent.append(recipient)
            return True
        else:
            return False

    # -------------------------------------------------------------------------
    def send_email_exception(self, recipient, *args, **kwargs):
        """ Dummy send mechanism that crashes for 1 recipient """

        if recipient == "test1@example.com":
            self.sent.append(recipient)
            return True
        elif recipient == "test2@example.com":
            raise RuntimeError
        else:
            return False

# =============================================================================
if __name__ == "__main__":

    run_suite(
        S3OutboxTests,
    )

# END ========================================================================
