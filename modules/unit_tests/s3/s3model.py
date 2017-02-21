# -*- coding: utf-8 -*-
#
# S3 Model Unit Tests
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/s3/s3model.py
#
import datetime
import unittest

from gluon import current, IS_EMPTY_OR, IS_FLOAT_IN_RANGE, IS_INT_IN_RANGE, IS_IN_SET, IS_NOT_EMPTY
from gluon.languages import lazyT
from gluon.storage import Storage

from s3.s3fields import s3_meta_fields
from s3.s3model import DYNAMIC_PREFIX, S3DynamicModel
from s3.s3validators import IS_NOT_ONE_OF, IS_ONE_OF, IS_UTC_DATE, IS_UTC_DATETIME

from unit_tests import run_suite

# =============================================================================
class S3ModelTests(unittest.TestCase):

    pass

# =============================================================================
class S3SuperEntityTests(unittest.TestCase):

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db

        # Create super-entity
        s3db.super_entity("setest_super",
                          "se_id",
                          {"setest_master": "SE Test Master"})

        # Add components to the SE
        s3db.add_components("setest_super",
                            setest_component_cascade="se_id",
                            setest_component_setnull="se_id",
                            setest_component_restrict="se_id",
                           )

        # Define master table
        s3db.define_table("setest_master",
                          s3db.super_link("se_id", "setest_super"),
                          *s3_meta_fields())

        # Make instance
        s3db.configure("setest_master",
                       super_entity = "setest_super")

        # Define component tables with constraints
        s3db.define_table("setest_component_cascade",
                          s3db.super_link("se_id", "setest_super",
                                          ondelete="CASCADE"),
                          *s3_meta_fields())

        s3db.define_table("setest_component_setnull",
                          s3db.super_link("se_id", "setest_super",
                                          ondelete="SET NULL"),
                          *s3_meta_fields())

        s3db.define_table("setest_component_restrict",
                          s3db.super_link("se_id", "setest_super",
                                          ondelete="RESTRICT"),
                          *s3_meta_fields())

        current.db.commit()

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        db = current.db

        # Drop all test tables
        db.setest_component_cascade.drop()
        db.setest_component_setnull.drop()
        db.setest_component_restrict.drop()
        db.setest_master.drop()
        db.setest_super.drop()

        current.db.commit()

    # -------------------------------------------------------------------------
    def setUp(self):

        s3db = current.s3db

        # Create the master record and link it to the SE
        master_table = s3db.setest_master
        master_id = master_table.insert()
        s3db.update_super(master_table, {"id": master_id})
        self.master_id = master_id

        current.auth.override = True

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.db.rollback()
        current.auth.override = False

    # -------------------------------------------------------------------------
    def testDeleteSuper(self):
        """ Test delete_super without constraints """

        s3db = current.s3db

        # Get the master record
        master_table = s3db.setest_master
        record = master_table[self.master_id]
        se_id = record.se_id

        # Try delete the super-record (returns True)
        success = s3db.delete_super(master_table, record)
        self.assertTrue(success)

        # Super-key is removed
        record = master_table[self.master_id]
        self.assertEqual(record.se_id, None)

        # Super-record is deleted
        super_table = s3db.setest_super
        super_record = super_table[se_id]
        self.assertTrue(super_record.deleted)

    # -------------------------------------------------------------------------
    def testDeleteSuperCascade(self):
        """ Test delete_super with CASCADE constraint """

        s3db = current.s3db

        # Get the master record
        master_table = s3db.setest_master
        record = master_table[self.master_id]
        se_id = record.se_id

        # Create a component record
        component_table = s3db.setest_component_cascade
        component_id = component_table.insert(se_id=se_id)
        component_record = component_table[component_id]
        self.assertNotEqual(component_record, None)

        # Try delete the super-record (returns True)
        success = s3db.delete_super(master_table, record)
        self.assertTrue(success)

        # Super-key is removed
        record = master_table[self.master_id]
        self.assertEqual(record.se_id, None)

        # Component record is deleted
        component_record = component_table[component_id]
        self.assertTrue(component_record.deleted)
        self.assertEqual(component_record.se_id, None)

        # Super-record is deleted
        super_table = s3db.setest_super
        super_record = super_table[se_id]
        self.assertTrue(super_record.deleted)

    # -------------------------------------------------------------------------
    def testDeleteSuperSetNull(self):
        """ Test delete_super with SET NULL constraint """

        s3db = current.s3db

        # Get the master record
        master_table = s3db.setest_master
        record = master_table[self.master_id]
        se_id = record.se_id

        # Create a component record
        component_table = s3db.setest_component_setnull
        component_id = component_table.insert(se_id=se_id)
        component_record = component_table[component_id]
        self.assertNotEqual(component_record, None)

        # Try delete the super-record (returns True)
        success = s3db.delete_super(master_table, record)
        self.assertTrue(success)

        # Super-key is removed
        record = master_table[self.master_id]
        self.assertEqual(record.se_id, None)

        # Component record is not deleted, but unlinked
        component_record = component_table[component_id]
        self.assertFalse(component_record.deleted)
        self.assertEqual(component_record.se_id, None)

        # Super-record is deleted
        super_table = s3db.setest_super
        super_record = super_table[se_id]
        self.assertTrue(super_record.deleted)

    # -------------------------------------------------------------------------
    def testDeleteSuperRestrict(self):
        """ Test delete_super with RESTRICT constraint """

        s3db = current.s3db

        # Get the master record
        master_table = s3db.setest_master
        record = master_table[self.master_id]
        se_id = record.se_id

        # Create a component record
        component_table = s3db.setest_component_restrict
        component_id = component_table.insert(se_id=se_id)
        component_record = component_table[component_id]
        self.assertNotEqual(component_record, None)

        # Try delete the super-record (must return False)
        success = s3db.delete_super(master_table, record)
        self.assertFalse(success)

        # Super-key is retained
        record = master_table[self.master_id]
        self.assertEqual(record.se_id, se_id)

        # Component record is not deleted and still linked
        component_record = component_table[component_id]
        self.assertFalse(component_record.deleted)
        self.assertEqual(component_record.se_id, se_id)

        # Super-record is not deleted
        super_table = s3db.setest_super
        super_record = super_table[se_id]
        self.assertFalse(super_record.deleted)

# =============================================================================
class S3DynamicModelTests(unittest.TestCase):
    """ Dynamic Model Tests """

    TABLENAME = "%s_test" % DYNAMIC_PREFIX

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db

        ttable = s3db.s3_table
        ftable = s3db.s3_field

        # Create dynamic table
        table_id = ttable.insert(name = cls.TABLENAME,
                                 )

        # The dynamic data model
        model = (
            # String field
            {"name": "name",
             "field_type": "string",
             "label": "My Name",
             "comments": "Explanation of the field",
             },
            # Numeric field
            {"name": "some_number",
             "field_type": "integer",
             },
            )

        for field_def in model:

            # Add field definition
            record = Storage(field_def)
            record["table_id"] = table_id
            record_id = ftable.insert(**record)

            # Run onaccept
            record["id"] = record_id
            s3db.onaccept(ftable, record)

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        # Remove the dynamic table
        s3db = current.s3db

        ttable = s3db.s3_table
        query = (ttable.name == cls.TABLENAME)
        current.db(query).delete()

    # -------------------------------------------------------------------------
    def testDynamicTableInstantiationFailure(self):
        """ Test attempted instantiation of nonexistent dynamic table """

        # Attribute/Key access raises attribute error
        with self.assertRaises(AttributeError):
            current.s3db.s3dt_nonexistent
        with self.assertRaises(AttributeError):
            current.s3db["s3dt_nonexistent"]

        # table() function returns None
        table = current.s3db.table("s3dt_nonexistent")
        self.assertEqual(table, None)

    # -------------------------------------------------------------------------
    def testDynamicTableInstantiation(self):
        """ Test instantiation of dynamic tables with S3Model """

        assertEqual = self.assertEqual
        assertNotEqual = self.assertNotEqual
        assertIn = self.assertIn
        assertTrue = self.assertTrue

        s3db = current.s3db

        # Check if s3db.table can instantiate the table
        table = s3db.table(self.TABLENAME)
        assertNotEqual(table, None)
        assertTrue(self.TABLENAME in current.db)

        # Verify that it contains the right fields of the right type
        fields = table.fields

        assertIn("name", fields)
        field = table.name
        assertEqual(field.type, "string")
        # Internationalised custom label
        assertTrue(type(field.label) is lazyT)
        assertEqual(field.label.m, "My Name")
        # Internationalised comment
        assertTrue(type(field.comment) is lazyT)
        assertEqual(field.comment.m, "Explanation of the field")

        assertIn("some_number", fields)
        field = table.some_number
        assertEqual(field.type, "integer")
        # Internationalised default label
        assertTrue(type(field.label) is lazyT)
        assertEqual(field.label.m, "Some Number")
        # No comment
        assertEqual(field.comment, None)

        # Verify that meta-fields have automatically been added
        assertIn("uuid", fields)

    # -------------------------------------------------------------------------
    def testStringFieldConstruction(self):
        """
            Test construction of string field
        """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        dm = S3DynamicModel(self.TABLENAME)
        define_field = dm._field

        # String-field, not unique and empty allowed
        params = Storage(name = "name",
                         field_type = "string",
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "name")
        assertEqual(field.type, "string")
        assertFalse(field.requires)

        # String-field, not unique but empty not allowed
        params = Storage(name = "name",
                         field_type = "string",
                         require_not_empty = True,
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "name")
        assertEqual(field.type, "string")
        assertTrue(isinstance(field.requires, IS_NOT_EMPTY))

        # String-field, unique and empty not allowed
        params = Storage(name = "name",
                         field_type = "string",
                         require_unique = True,
                         require_not_empty = True,
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "name")
        assertEqual(field.type, "string")
        assertTrue(isinstance(field.requires, IS_NOT_ONE_OF))

        # String-field, unique or empty
        params = Storage(name = "name",
                         field_type = "string",
                         require_unique = True,
                         require_not_empty = False,
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "name")
        assertEqual(field.type, "string")
        assertEqual(field.default, None)
        requires = field.requires
        assertTrue(isinstance(requires, IS_EMPTY_OR))
        requires = requires.other
        assertTrue(isinstance(requires, IS_NOT_ONE_OF))

        # String-field, with default value
        params = Storage(name = "name",
                         field_type = "string",
                         default_value = "Default Name"
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "name")
        assertEqual(field.type, "string")
        assertEqual(field.default, "Default Name")

    # -------------------------------------------------------------------------
    def testReferenceFieldConstruction(self):
        """
            Test construction of reference field
        """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        dm = S3DynamicModel(self.TABLENAME)
        define_field = dm._field

        # Reference-field, empty allowed
        params = Storage(name = "organisation_id",
                         field_type = "reference org_organisation",
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "organisation_id")
        assertEqual(field.type, "reference org_organisation")
        requires = field.requires
        assertTrue(isinstance(requires, IS_EMPTY_OR))
        requires = requires.other
        assertTrue(isinstance(requires, IS_ONE_OF))
        assertEqual(requires.ktable, "org_organisation")

        # Reference-field, must not be empty
        params = Storage(name = "organisation_id",
                         field_type = "reference org_organisation",
                         require_not_empty = True,
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "organisation_id")
        assertEqual(field.type, "reference org_organisation")
        requires = field.requires
        assertTrue(isinstance(requires, IS_ONE_OF))
        assertEqual(requires.ktable, "org_organisation")

        # Reference-field, nonexistent table
        params = Storage(name = "organisation_id",
                         field_type = "reference nonexistent_table",
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field, None)

    # -------------------------------------------------------------------------
    def testBooleanFieldConstruction(self):
        """
            Test construction of boolean field
        """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        dm = S3DynamicModel(self.TABLENAME)
        define_field = dm._field

        from s3 import s3_yes_no_represent

        # Boolean field
        params = Storage(name = "flag",
                         field_type = "boolean",
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "flag")
        assertEqual(field.type, "boolean")
        assertFalse(field.requires)
        assertEqual(field.default, False)
        assertEqual(field.represent, s3_yes_no_represent)

        # Boolean field, with default value
        params = Storage(name = "flag",
                         field_type = "boolean",
                         default_value = "true",
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "flag")
        assertEqual(field.type, "boolean")
        assertFalse(field.requires)
        assertEqual(field.default, True)
        assertEqual(field.represent, s3_yes_no_represent)

    # -------------------------------------------------------------------------
    def testIntegerFieldConstruction(self):
        """
            Test construction of integer field
        """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        dm = S3DynamicModel(self.TABLENAME)
        define_field = dm._field

        # Integer-field
        params = Storage(name = "number",
                         field_type = "integer",
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "number")
        assertEqual(field.type, "integer")
        requires = field.requires
        assertTrue(isinstance(requires, IS_EMPTY_OR))
        requires = requires.other
        assertTrue(isinstance(requires, IS_INT_IN_RANGE))

        # Integer-field, empty not allowed, no range limits
        params = Storage(name = "number",
                         field_type = "integer",
                         require_not_empty = True,
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "number")
        assertEqual(field.type, "integer")
        requires = field.requires
        assertTrue(isinstance(requires, IS_INT_IN_RANGE))
        assertEqual(requires.minimum, None)
        assertEqual(requires.maximum, None)

        # Integer-field, with range limits
        params = Storage(name = "number",
                         field_type = "integer",
                         settings = {"min": 2,
                                     "max": 5,
                                     },
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "number")
        assertEqual(field.type, "integer")
        requires = field.requires
        assertTrue(isinstance(requires, IS_EMPTY_OR))
        requires = requires.other
        assertTrue(isinstance(requires, IS_INT_IN_RANGE))
        assertEqual(requires.minimum, 2)
        assertEqual(requires.maximum, 5)

        # Integer field, with default value
        params = Storage(name = "number",
                         field_type = "integer",
                         default_value = "14"
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "number")
        assertEqual(field.type, "integer")
        assertEqual(field.default, 14)

        # Integer field, with invalid default value
        params = Storage(name = "number",
                         field_type = "integer",
                         default_value = "not_an_integer"
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "number")
        assertEqual(field.type, "integer")
        assertEqual(field.default, None)

    # -------------------------------------------------------------------------
    def testDoubleFieldConstruction(self):
        """
            Test construction of double field
        """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        dm = S3DynamicModel(self.TABLENAME)
        define_field = dm._field

        # Double-field
        params = Storage(name = "number",
                         field_type = "double",
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "number")
        assertEqual(field.type, "double")
        requires = field.requires
        assertTrue(isinstance(requires, IS_EMPTY_OR))
        requires = requires.other
        assertTrue(isinstance(requires, IS_FLOAT_IN_RANGE))

        # Double-field, empty not allowed, no range limits
        params = Storage(name = "number",
                         field_type = "double",
                         require_not_empty = True,
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "number")
        assertEqual(field.type, "double")
        requires = field.requires
        assertTrue(isinstance(requires, IS_FLOAT_IN_RANGE))
        assertEqual(requires.minimum, None)
        assertEqual(requires.maximum, None)

        # Double-field, with range limits
        params = Storage(name = "number",
                         field_type = "double",
                         settings = {"min": 2.7,
                                     "max": 8.3,
                                     },
                         )
        field = define_field(self.TABLENAME, params)
        assertEqual(field.name, "number")
        assertEqual(field.type, "double")
        requires = field.requires
        assertTrue(isinstance(requires, IS_EMPTY_OR))
        requires = requires.other
        assertTrue(isinstance(requires, IS_FLOAT_IN_RANGE))
        assertEqual(requires.minimum, 2.7)
        assertEqual(requires.maximum, 8.3)

    # -------------------------------------------------------------------------
    def testDateFieldConstruction(self):
        """
            Test construction of date field
        """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        dm = S3DynamicModel(self.TABLENAME)
        define_field = dm._field

        # Date-field
        params = Storage(name = "start_date",
                         field_type = "date",
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "start_date")
        assertEqual(field.type, "date")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_EMPTY_OR))
        requires = requires.other
        assertTrue(isinstance(requires, IS_UTC_DATE))

        # => verify (no) range limits
        assertEqual(requires.minimum, None)
        assertEqual(requires.maximum, None)

        # Date-field with range limits
        params = Storage(name = "start_date",
                         field_type = "date",
                         require_not_empty = True,
                         settings = {"past": 10,
                                     "future": 8,
                                     },
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "start_date")
        assertEqual(field.type, "date")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_UTC_DATE))

        # => verify range limits
        now = current.request.utcnow.date()
        from dateutil.relativedelta import relativedelta
        assertEqual(requires.minimum, now - relativedelta(months = 10))
        assertEqual(requires.maximum, now + relativedelta(months = 8))

        # Date-field with default (keyword "now")
        params = Storage(name = "start_date",
                         field_type = "date",
                         default_value = "now",
                         require_not_empty = True,
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "start_date")
        assertEqual(field.type, "date")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_UTC_DATE))

        # => verify default value
        assertEqual(field.default, now)

        # Date-field with default (particular date)
        params = Storage(name = "start_date",
                         field_type = "date",
                         default_value = "2016-08-14",
                         require_not_empty = True,
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "start_date")
        assertEqual(field.type, "date")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_UTC_DATE))

        # => verify default value
        assertEqual(field.default, datetime.date(2016, 8, 14))

        # Date-field with invalid default
        params = Storage(name = "start_date",
                         field_type = "date",
                         default_value = "invalid_default",
                         require_not_empty = True,
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "start_date")
        assertEqual(field.type, "date")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_UTC_DATE))

        # => verify default value
        assertEqual(field.default, None)

    # -------------------------------------------------------------------------
    def testDateTimeFieldConstruction(self):
        """
            Test construction of date field
        """

        import dateutil.tz
        from dateutil.relativedelta import relativedelta

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse

        dm = S3DynamicModel(self.TABLENAME)
        define_field = dm._field

        # Datetime-field
        params = Storage(name = "start_date",
                         field_type = "datetime",
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "start_date")
        assertEqual(field.type, "datetime")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_EMPTY_OR))
        requires = requires.other
        assertTrue(isinstance(requires, IS_UTC_DATETIME))

        # => verify (no) range limits
        assertEqual(requires.minimum, None)
        assertEqual(requires.maximum, None)

        # Datetime-field with range limits
        params = Storage(name = "start_date",
                         field_type = "datetime",
                         require_not_empty = True,
                         settings = {"past": 0,
                                     "future": 720,
                                     },
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "start_date")
        assertEqual(field.type, "datetime")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_UTC_DATETIME))

        # => verify range limits
        # NB s3_datetime computes range limits against current.request.utcnow,
        #    which is slightly offset against datetime.datetime.utcnow due to
        #    processing time
        # NB current.request.utcnow is tz-unaware, and so should be the range
        #    limits (otherwise raises TypeError here)
        now = current.request.utcnow
        assertEqual(requires.minimum, now)
        assertEqual(requires.maximum, now + relativedelta(hours = 720))

        # Datetime-field with default (keyword "now")
        params = Storage(name = "start_date",
                         field_type = "datetime",
                         default_value = "now",
                         require_not_empty = True,
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "start_date")
        assertEqual(field.type, "datetime")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_UTC_DATETIME))

        # => verify default value
        assertEqual(field.default, now)

        # Datetime-field with default (particular date)
        params = Storage(name = "start_date",
                         field_type = "datetime",
                         default_value = "2016-08-14T20:00:00Z",
                         require_not_empty = True,
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "start_date")
        assertEqual(field.type, "datetime")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_UTC_DATETIME))

        # => verify default value
        expected = datetime.datetime(2016, 8, 14, 20, 0, 0,
                                     tzinfo=dateutil.tz.tzutc(),
                                     )
        assertEqual(field.default, expected)

        # Date-field with invalid default
        params = Storage(name = "start_date",
                         field_type = "datetime",
                         default_value = "invalid_default",
                         require_not_empty = True,
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "start_date")
        assertEqual(field.type, "datetime")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_UTC_DATETIME))

        # => verify default value
        assertEqual(field.default, None)

    # -------------------------------------------------------------------------
    def testOptionFieldConstruction(self):
        """
            Test construction of options-field
        """

        assertEqual = self.assertEqual
        assertTrue = self.assertTrue
        assertFalse = self.assertFalse
        assertIn = self.assertIn

        T = current.T
        T.force("en") # Options sort order depends on language

        dm = S3DynamicModel(self.TABLENAME)
        define_field = dm._field

        # Options-field
        params = Storage(name = "status",
                         field_type = "integer",
                         # Options as list of tuples (from JSON)
                         options = [[1, "new"],
                                    [2, "in progress"],
                                    [3, "done"],
                                    ],
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "status")
        assertEqual(field.type, "integer")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_EMPTY_OR))
        requires = requires.other
        assertTrue(isinstance(requires, IS_IN_SET))

        # Options retain list order
        options = requires.options()
        assertEqual(options, [('', ''),
                              ('1', 'new'),
                              ('2', 'in progress'),
                              ('3', 'done'),
                              ])

        # Options-field, must not be empty
        params = Storage(name = "status",
                         field_type = "integer",
                         # Options as dict (from JSON)
                         options = {"1": "new",
                                    "2": "in progress",
                                    "0": "done",
                                    },
                         require_not_empty = True
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "status")
        assertEqual(field.type, "integer")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_IN_SET))

        # Options are sorted
        options = requires.options()
        assertEqual(options, [('', ''),
                              ('0', 'done'),
                              ('2', 'in progress'),
                              ('1', 'new'),
                              ])

        # Options-field, must not be empty, sorted, default value
        params = Storage(name = "status",
                         field_type = "string",
                         # Options as list of tuples (from JSON)
                         options = [["A", "new"],
                                    ["B", "in progress"],
                                    ["C", "done"],
                                    ],
                         default_value = "A",
                         require_not_empty = True,
                         # Enforce sorting of options
                         settings = {"sort_options": True,
                                     },
                         )
        field = define_field(self.TABLENAME, params)

        # => verify field name and type
        assertEqual(field.name, "status")
        assertEqual(field.type, "string")

        # => verify validators
        requires = field.requires
        assertTrue(isinstance(requires, IS_IN_SET))

        options = requires.options()
        # Options are sorted, no zero-option
        assertEqual(options, [('C', 'done'),
                              ('B', 'in progress'),
                              ('A', 'new'),
                              ])

# =============================================================================
class S3DynamicComponentTests(unittest.TestCase):
    """ Dynamic Component Tests """

    TABLENAME = "%s_test_component" % DYNAMIC_PREFIX

    # -------------------------------------------------------------------------
    @classmethod
    def setUpClass(cls):

        s3db = current.s3db

        ttable = s3db.s3_table
        ftable = s3db.s3_field

        # Create dynamic table
        table_id = ttable.insert(name = cls.TABLENAME,
                                 )

        # The dynamic data model
        model = (
            # Component key
            {"name": "organisation_id",
             "field_type": "reference org_organisation",
             "component_key": True,
             "component_alias": "test_rating",
             "label": "Organisation",
             },
             # Other field
             {"name": "value",
              "field_type": "integer",
              "options": {1: "very good",
                          2: "good",
                          3: "average",
                          4: "acceptable",
                          5: "poor",
                          },
              },
             )

        for field_def in model:

            # Add field definition
            record = Storage(field_def)
            record["table_id"] = table_id
            record_id = ftable.insert(**record)

            # Run onaccept
            record["id"] = record_id
            s3db.onaccept(ftable, record)

    # -------------------------------------------------------------------------
    @classmethod
    def tearDownClass(cls):

        # Remove the dynamic table
        s3db = current.s3db

        ttable = s3db.s3_table
        query = (ttable.name == cls.TABLENAME)
        current.db(query).delete()

    # -------------------------------------------------------------------------
    def setUp(self):

        s3db = current.s3db

        self.dynamic_components = s3db.get_config("org_organisation",
                                                  "dynamic_components",
                                                  )

        s3db.configure("org_organisation",
                       dynamic_components = True,
                       )

    # -------------------------------------------------------------------------
    def tearDown(self):

        current.s3db.configure("org_organisation",
                               dynamic_components = self.dynamic_components,
                               )

    # -------------------------------------------------------------------------
    def testComponentAccess(self):
        """ Test access to dynamic components """

        s3db = current.s3db

        assertTrue = self.assertTrue
        assertEqual = self.assertEqual

        resource = s3db.resource("org_organisation")

        # Verify that the component is present
        assertTrue("test_rating" in resource.components)
        component = resource.components["test_rating"]

        # Verify table name of the component
        assertEqual(component.tablename, self.TABLENAME)

        # Verify fields in the component table
        assertTrue("organisation_id" in component.fields)
        assertTrue("value" in component.fields)

    # -------------------------------------------------------------------------
    def testFieldSelectorResolution(self):
        """ Test field selector resolution for dynamic components """

        s3db = current.s3db

        assertEqual = self.assertEqual

        resource = s3db.resource("org_organisation")
        rfield = resource.resolve_selector("test_rating.value")

        assertEqual(rfield.tname, self.TABLENAME)
        assertEqual(rfield.fname, "value")
        assertEqual(rfield.ftype, "integer")

# =============================================================================
if __name__ == "__main__":

    run_suite(
        #S3ModelTests,
        S3SuperEntityTests,
        S3DynamicModelTests,
        S3DynamicComponentTests,
    )

# END ========================================================================
