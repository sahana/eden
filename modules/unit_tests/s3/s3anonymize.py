# -*- coding: utf-8 -*-
#
# S3Anonymize Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3anonymize.py
#
import os
import unittest

from s3.s3anonymize import S3Anonymize
from s3compat import StringIO

from unit_tests import run_suite

# =============================================================================
class S3AnonymizeTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    def setUp(self):

        current.auth.override = True

        s3db = current.s3db

        ptable = s3db.pr_person
        ctable = s3db.pr_contact
        itable = s3db.pr_image

        # Create a person record
        person = {"pe_label": "KBT012",
                  "first_name": "Example",
                  "last_name": "Person",
                  #"date_of_birth": ...,
                  "comments": "This is a comment",
                  }

        person_id = ptable.insert(**person)
        person["id"] = person_id
        s3db.update_super(ptable, person)
        self.person_id = person_id

        # Add a contact record
        contact = {"pe_id": person["pe_id"],
                   "contact_method": "SMS",
                   "value": "+60738172623",
                   "comments": "This is a comment",
                   }
        self.contact_id = ctable.insert(**contact)

        # Add an image record
        stream = StringIO()
        stream.write("TEST")
        filename = itable.image.store(stream, "test.txt")
        filepath = os.path.join(current.request.folder, "uploads", filename)
        image = {"pe_id": person["pe_id"],
                 "image": filename,
                 "description": "Example description",
                 }
        self.image_id = itable.insert(**image)

        self.assertTrue(os.path.exists(filepath))
        self.image_path = filepath


    def tearDown(self):

        db = current.db
        s3db = current.s3db

        # Delete contact record
        ctable = s3db.pr_contact
        db(ctable.id == self.contact_id).delete()
        self.contact_id = None

        # Delete image record
        itable = s3db.pr_image
        db(itable.id == self.image_id).delete()
        self.image_path = None
        self.image_id = None

        # Delete the person record
        ptable = s3db.pr_person
        query = ptable.id == self.person_id
        row = db(query).select(ptable.id,
                               ptable.pe_id,
                               limitby = (0, 1),
                               ).first()

        if row:
            s3db.delete_super(ptable, row)
            db(query).delete()
        self.person_id = None

        current.auth.override = False

    # -------------------------------------------------------------------------
    def testApplyCascade(self):

        assertTrue = self.assertTrue
        assertFalse = self.assertFalse
        assertEqual = self.assertEqual

        s3db = current.s3db

        ptable = s3db.pr_person
        ctable = s3db.pr_contact
        itable = s3db.pr_image

        rules = {"fields": {#"pe_label": self.generate_label,
                            "first_name": ("set", "Anonymous"),
                            "last_name": "remove",
                            #"date_of_birth": self.obscure_dob,
                            "comments": "remove",
                            },
                 "cascade": [
                    ("pr_contact", {"key": "pe_id",
                                    "match": "pe_id",
                                    "fields": {"value": ("set", ""),
                                               "comments": "remove",
                                               },
                                    "delete": True,
                                    }),
                    ("pr_image", {"key": "pe_id",
                                  "match": "pe_id",
                                  "fields": {"image": "remove",
                                             "url": "remove",
                                             "description": "remove",
                                             },
                                  "delete": True,
                                  }),
                    ],
                 }

        S3Anonymize.cascade(ptable, (self.person_id,), rules)

        # Verify the person record
        query = (ptable.id == self.person_id)
        row = db(query).select(ptable.first_name,
                               ptable.last_name,
                               ptable.comments,
                               ptable.deleted,
                               limitby = (0, 1),
                               ).first()
        assertFalse(row.deleted)
        assertEqual(row.first_name, "Anonymous")
        assertEqual(row.last_name, None)
        assertEqual(row.comments, None)

        # Verify the contact record
        query = (ctable.id == self.contact_id)
        row = db(query).select(ctable.deleted,
                               ctable.value,
                               ctable.comments,
                               limitby = (0, 1),
                               ).first()
        assertTrue(row.deleted)
        assertEqual(row.value, "")
        assertEqual(row.comments, None)

        # Verify the image record
        query = (itable.id == self.image_id)
        row = db(query).select(itable.deleted,
                               itable.image,
                               itable.description,
                               limitby = (0, 1),
                               ).first()
        assertTrue(row.deleted)
        assertEqual(row.image, None)
        assertEqual(row.description, None)

        # Verify that the image file has been deleted
        assertFalse(os.path.exists(self.image_path))

    # -------------------------------------------------------------------------
    def testApplyFieldRules(self):
        """ Test correct application of field rules """

        # TODO: improve/extend

        table = current.s3db.pr_person

        rules = {"first_name": ("set", "Anonymous"),
                 "last_name": "remove",
                 "comments": "remove",
                 }

        S3Anonymize.apply_field_rules(table, (self.person_id,), rules)

        query = (table.id == self.person_id)
        row = current.db(query).select(table.first_name,
                                       table.last_name,
                                       table.comments,
                                       limitby = (0, 1),
                                       ).first()

        self.assertEqual(row.first_name, "Anonymous")
        self.assertEqual(row.last_name, None)
        self.assertEqual(row.comments, None)

# =============================================================================
if __name__ == "__main__":

    run_suite(
        S3AnonymizeTests,
    )

# END ========================================================================
