# -*- coding: utf-8 -*-
#
# Unit tests for unit test utils
#
# To run this script use:
# python web2py.py -S eden -M -R applications/eden/modules/unit_tests/utils_tests.py
# This should be run on each DBMS supported by the db utils.

import unittest
utils_package = "applications.%s.modules.unit_tests" % (current.request.application)
utils_name = "utils"
utils = getattr(__import__(utils_package, fromlist=[utils_name]), utils_name)

#------------------------------------------------------------------------------
class DataHelperTests(unittest.TestCase):
    """ Test utils.insert_resource """

    def setUp(self):
        pass

    def testInsertResource(self):
        import uuid
        # Test inserting a record in a table that has a superentity.
        s3db = current.s3db
        otable = s3db.org_organisation
        otable_len_before = db(otable).count()
        ptable = s3db.pr_pentity
        ptable_len_before = db(ptable).count()

        # First, don't ask for a random suffix to be added. (Add said prefix
        # here, in case there happen to be records with this name.)
        prefix = "Insert Resource Test Org"
        name = "%s%s" % (prefix, uuid.uuid4())
        data = Storage(name=name)
        data_as_inserted = utils.insert_resource(s3db, otable, data)

        # Should have id and superentity id
        try:
            id = data_as_inserted["id"]
        except:
            self.fail("No id returned")
        try:
            pe_id = data_as_inserted["pe_id"]
        except:
            self.fail("No superentity id returned")

        # Should have new rows.
        otable_len_after = db(otable).count()
        self.assertEqual(otable_len_after, otable_len_before + 1)
        ptable_len_after = db(ptable).count()
        self.assertEqual(ptable_len_after, ptable_len_before + 1)

        # Read back the new record and verify the data.
        record = db(otable.id == id).select(otable.id, otable.pe_id, otable.name).first()
        try:
            self.assertEqual(record["id"], id)
            self.assertEqual(record["pe_id"], pe_id)
            self.assertEqual(record["name"], name)
        except:
            self.fail("Not all fields present")

        # Add another record with the same name prefix, but this time, let
        # insert_resource make it unique.
        data2 = Storage(name=prefix)
        data2_as_inserted = utils.insert_resource(s3db, otable, data2,
                                                  add_random_suffix_to="name")
        # Check for new rows.
        otable_len_after2 = db(otable).count()
        self.assertEqual(otable_len_after2, otable_len_after + 1)
        ptable_len_after2 = db(ptable).count()
        self.assertEqual(ptable_len_after2, ptable_len_after + 1)
        # Get the name and see if it has a suffix.
        id2 = data2_as_inserted["id"]
        self.assertNotEqual(id, id2)
        record2 = db(otable.id == id2).select(otable.name).first()
        name2 = record2["name"]
        self.assertTrue(name2.startswith(prefix))
        self.assertTrue(len(name2) > len(prefix))

    def tearDown(self):
        db.rollback()

#------------------------------------------------------------------------------
class InterceptCallTests(unittest.TestCase):
    """ Test utils.InterceptCall """
    
    def setUp(self):
        self.callback_side_effect = None
    
    class Target:
        static_method_was_called = False
        class_method_was_called = False
        def __init__(self):
            self.instance_method_was_called = False
        def target_method(self, arg1, arg2, kwarg1="kwval1", kwarg2="kwval2"):
            self.instance_method_was_called = True
            return (kwarg2, kwarg1, arg2, arg1)
        @staticmethod
        def target_static_method(arg1, arg2, kwarg1="kwval1", kwarg2="kwval2"):
            InterceptCallTests.Target.static_method_was_called = True
            return (kwarg2, kwarg1, arg2, arg1, "static method")
        @classmethod
        def target_class_method(cls, arg1, arg2, kwarg1="kwval1", kwarg2="kwval2"):
            cls.class_method_was_called = True
            return (kwarg2, kwarg1, arg2, arg1, "class method")

    def callback_call_real_method(self, arg1, arg2, kwarg1=None, kwarg2=None):
        self.callback_side_effect = "Call %s %s %s %s" % (arg1, arg2, kwarg1, kwarg2)
        return (True, None)

    def callback_skip_real_method(self, arg1, arg2, kwarg1=None, kwarg2=None):
        self.callback_side_effect = "Skip %s %s %s %s" % (arg1, arg2, kwarg1, kwarg2)
        return (False, ("should be returned", arg1, arg2, kwarg1, kwarg2))
    
    def callback_bad_retval(self, arg1, arg2, kwarg1=None, kwarg2=None):
        self.callback_side_effect = "Bad %s %s %s %s" % (arg1, arg2, kwarg1, kwarg2)
        return "Anything but the proper form"

    def callback_call_real_module_function(self, text=None):
        self.callback_side_effect = "Call %s" % text
        return (True, None)

    # This will be swapped in place of Web2py's web2py_uuid. Return something
    # that is not a string so it can't be mistaken for a real web2py_uuid value.
    callback_skip_real_module_function_retval = ("Not a web2py_uuid",)
    def callback_skip_real_module_function(self, text=None):
        self.callback_side_effect = "Skip %s" % text
        return (False, InterceptCallTests.callback_skip_real_module_function_retval)

    def testInterceptCall(self):
        target = self.Target()

        # First test with a supplied callback.

        before_pattern = ".*Target.target_method.*"
        after_pattern = ".*InterceptCall.*"

        before_str = str(target.target_method)
        self.assertRegexpMatches(before_str, before_pattern)
        # This callback asks to call the original function.
        intercept = utils.InterceptCall(target, "target_method", self.callback_call_real_method)
        self.assertEqual(intercept, target.target_method)
        after_str = str(target.target_method)
        self.assertRegexpMatches(after_str, after_pattern)

        result = target.target_method(1, 2, kwarg1=3, kwarg2=4)
        # Callback should get called.
        self.assertEqual(self.callback_side_effect, "Call 1 2 3 4")
        # Target method should get called.
        self.assertTrue(target.instance_method_was_called)
        self.assertEqual(result, (4, 3, 2, 1))
        # Omit a keyword arg.
        result = target.target_method(1, 2, kwarg1=3)
        self.assertEqual(self.callback_side_effect, "Call 1 2 3 None")
        self.assertEqual(result, ("kwval2", 3, 2, 1))

        # Disable the intercept.
        target.target_method.disable()  # Or intercept.disable()
        self.callback_side_effect = None
        target.instance_method_was_called = False
        result = target.target_method(5, 6, kwarg1=7, kwarg2=8)
        # Callback should not get called.
        self.assertEqual(self.callback_side_effect, None)
        # Target method should get called.
        self.assertTrue(target.instance_method_was_called)
        self.assertEqual(result, (8, 7, 6, 5))
        # Intercept should still be installed.
        self.assertEqual(intercept, target.target_method)

        # Re-enable it.
        target.target_method.enable()
        self.callback_side_effect = None
        result = target.target_method(10, 20, kwarg1=30, kwarg2=40)
        # Callback should get called.
        self.assertEqual(self.callback_side_effect, "Call 10 20 30 40")
        # Target method should get called.
        self.assertEqual(result, (40, 30, 20, 10))

        # Remove it entirely.
        target.target_method.remove()
        remove_str = str(target.target_method)
        self.assertRegexpMatches(remove_str, before_pattern)
        self.callback_side_effect = None
        result = target.target_method(50, 60, kwarg1=70, kwarg2=80)
        # Callback should not get called.
        self.assertEqual(self.callback_side_effect, None)
        # Target method should get called.
        self.assertEqual(result, (80, 70, 60, 50))

        # This callback asks not to call the real function.
        utils.InterceptCall(target, "target_method", self.callback_skip_real_method)
        self.callback_side_effect = None
        result = target.target_method("able", "baker", kwarg1="charlie")
        # Callback should get called.
        self.assertEqual(self.callback_side_effect, "Skip able baker charlie None")
        # But not the target method.
        self.assertEqual(result, ("should be returned", "able", "baker", "charlie", None))
        # Check disabling again, as previous case called the real function in
        # all cases. Here, we can see that it reappears when the intercept is
        # disabled.
        target.target_method.disable()
        self.callback_side_effect = None
        target.instance_method_was_called = False
        result = target.target_method("dog", "easy", kwarg1="fox")
        # Real function should get called.
        self.assertEqual(result, ("kwval2", "fox", "easy", "dog"))
        self.assertTrue(target.instance_method_was_called)
        # Callback should not get called.
        self.assertEqual(self.callback_side_effect, None)
        target.target_method.remove()

        # Should raise ValueError if the callback doesn't return the right form.
        utils.InterceptCall(target, "target_method", self.callback_bad_retval)
        with self.assertRaises(ValueError):
            result = target.target_method(1, 2, kwarg1=3, kwarg2=4)
        target.target_method.remove()

        # For static and class methods, just be sure the target method gets
        # called properly.
        utils.InterceptCall(InterceptCallTests.Target,
                            "target_static_method",
                            self.callback_call_real_method)
        self.callback_side_effect = None
        result = InterceptCallTests.Target.target_static_method(1, 2, kwarg1=3, kwarg2=4)
        # Did the callback get called?
        self.assertEqual(self.callback_side_effect, "Call 1 2 3 4")
        # Did the target method get called?
        self.assertEqual(result, (4, 3, 2, 1, "static method"))
        InterceptCallTests.Target.target_static_method.remove()
        utils.InterceptCall(InterceptCallTests.Target,
                            "target_class_method",
                            self.callback_call_real_method)
        self.callback_side_effect = None
        result = InterceptCallTests.Target.target_class_method(1, 2, kwarg1=3, kwarg2=4)
        # Did the callback get called?
        self.assertEqual(self.callback_side_effect, "Call 1 2 3 4")
        # Did the target method get called?
        self.assertEqual(result, (4, 3, 2, 1, "class method"))
        InterceptCallTests.Target.target_class_method.remove()

        # Intercept a function at module scope.
        from gluon import utils as gluon_utils
        utils.InterceptCall(gluon_utils,
                            "web2py_uuid",
                            self.callback_call_real_module_function)
        self.callback_side_effect = None
        result = gluon_utils.web2py_uuid()
        # Did the callback get called?
        self.assertEqual(self.callback_side_effect, "Call None")
        # Can't test a specific value for the uuid.
        self.assertTrue(isinstance(result, str))
        gluon_utils.web2py_uuid.remove()
        # So here's what you'd do if you wanted web2py_uuid to reproducibly
        # return a specific string, e.g. for testing.
        utils.InterceptCall(gluon_utils,
                            "web2py_uuid",
                            self.callback_skip_real_module_function)
        self.callback_side_effect = None
        result = gluon_utils.web2py_uuid()
        # Did the callback get called?
        self.assertEqual(self.callback_side_effect, "Skip None")
        # Did we get the fake uuid we wanted?
        self.assertEqual(result,
                         InterceptCallTests.callback_skip_real_module_function_retval)
        gluon_utils.web2py_uuid.remove()
        # And is that gone now?
        result = gluon_utils.web2py_uuid()
        self.assertNotEqual(result,
                            InterceptCallTests.callback_skip_real_module_function_retval)

        # Next test the default callback.
        
        # Entirely default behavior -- log arguments, call real function, return
        # its return value.
        intercept = utils.InterceptCall(target, "target_method")
        result = target.target_method(1, 2, kwarg1=3, kwarg2=4)
        # Target method should get called.
        self.assertTrue(target.instance_method_was_called)
        self.assertEqual(result, (4, 3, 2, 1))
        # Arguments should be in the log.
        self.assertEqual(intercept.log, [((1, 2), {"kwarg1":3, "kwarg2":4})])
        # Another call.
        result = target.target_method(5, 6, kwarg1=7, kwarg2=8)
        self.assertEqual(result, (8, 7, 6, 5))
        # Arguments should be added to the log.
        self.assertEqual(intercept.log, [((1, 2), {"kwarg1":3, "kwarg2":4}),
                                         ((5, 6), {"kwarg1":7, "kwarg2":8})])
        # Caution!!! If caller includes kwargs as though they were positional
        # the default callback doesn't know they're kwargs, so they'll be
        # recorded as positional.
        result = target.target_method(10, 11, 12, 13)
        self.assertEqual(result, (13, 12, 11, 10))
        self.assertEqual(intercept.log, [((1, 2), {"kwarg1":3, "kwarg2":4}),
                                         ((5, 6), {"kwarg1":7, "kwarg2":8}),
                                         ((10, 11, 12, 13), {})])
        target.target_method.remove()
        target.instance_method_was_called = False

        # No argument logging, don't call the real function, return supplied
        # mock value.
        intercept = utils.InterceptCall(target, "target_method",
                                        test_callback=None,
                                        log_arguments=False,
                                        call_real_function=False,
                                        mock_return_value="Some value")
        result = target.target_method(1, 2, kwarg1=3, kwarg2=4)
        # Target method should not get called.
        self.assertFalse(target.instance_method_was_called)
        # Should get mock return value.
        self.assertEqual(result, "Some value")
        # Log should be empty.
        self.assertEqual(intercept.log, [])

        # Using the same default intercept, say we want logging and a
        # different return value.
        intercept.log_arguments = True
        intercept.mock_return_value = "Some other value"
        result = target.target_method(5, 6, kwarg1=7, kwarg2=8)
        # Target method should still not get called.
        self.assertFalse(target.instance_method_was_called)
        # Should get new mock return value.
        self.assertEqual(result, "Some other value")
        # Log should have only the call after logging was enabled.
        self.assertEqual(intercept.log, [((5, 6), {"kwarg1":7, "kwarg2":8})])

#------------------------------------------------------------------------------
def recordsWithRef():
    """ Make test records with a foreign key reference between them. """
    # Note this was written before insert_resource had an option to add a random
    # suffix to a chosen field. Preserved as an example of doing it another way.
    # Note also that the rollback in TearDown does not protect against having
    # these test records persist -- that can happen if the tests fail in a way
    # that rollback does not get called.
    s3db = current.s3db
    org_table = s3db.org_organisation
    ofc_table = s3db.org_office
    while True:
        try:
            org = Storage(name="Test DB Utils Org %d" % recordsWithRef.num)
            org = utils.insert_resource(s3db, org_table, org)
            ofc = Storage(name="Test DB Utils Office %d" % recordsWithRef.num,
                          organisation_id=org["id"])
            ofc = utils.insert_resource(s3db, ofc_table, ofc)
            return (org, ofc)
        except Exception, e:
            # DAL will throw any of several exceptions if a required-unique
            # field exists, that have IntegrityError in their names. Don't want
            # to hang on some other exception so only retry on IntegrityError.
            if str(e.__class__).find("IntegrityError") == -1:
                raise e
            recordsWithRef.num += 1  # Make unique names.
recordsWithRef.num = 1

class DBUtilsTests(unittest.TestCase):
    """ Test db helpers from utils """

    def setUp(self):
        db.rollback()

    def testDisableEnableFKConstraints(self):
        s3db = current.s3db
        # We don't know whether constraints are currently enabled. Try deleting
        # the target of an fk ref, and see if there's an error. We have to use
        # raw SQL to try the delete, as the DAL will enforce foreign key
        # constraints regardless of the DBMS setting.
        (org, ofc) = recordsWithRef()
        query = "DELETE FROM org_organisation WHERE id = %s" % org.id
        try:
            db.executesql(query)
        except:
            # Currently enabled.
            enabled = True
        else:
            # Currently not enabled.
            enabled = False
        db.rollback()
        # Turn them off -- call this regardless of above result, to check the
        # return value of set_foreign_key_constraints(db, constraint_setting)
        old_setting = utils.set_foreign_key_constraints(db, False)
        self.assertEqual(old_setting, enabled)
        # Make sure there is no error on deleting the target of a foreign key
        # reference.
        (org, ofc) = recordsWithRef()
        query = "DELETE FROM org_organisation WHERE id = %s" % org.id
        try:
            db.executesql(query)
        except Exception, e:
            self.fail("set_foreign_key_constraints did not turn off constraints")
        db.rollback()
        # Now turn them on and check that there is an error on that same delete.
        old_setting = utils.set_foreign_key_constraints(db, True)
        self.assertEqual(old_setting, False)
        (org, ofc) = recordsWithRef()
        query = "DELETE FROM org_organisation WHERE id = %s" % org.id
        try:
            db.executesql(query)
            self.fail("set_foreign_key_constraints did not turn on constraints")
        except Exception, e:
            pass
        db.rollback()
        # Turn them off again -- we haven't checked turning them off when we're
        # sure they were on.
        old_setting = utils.set_foreign_key_constraints(db, False)
        self.assertEqual(old_setting, True)
        # Make sure there is no error on deleting the target of a foreign key
        # reference.
        (org, ofc) = recordsWithRef()
        query = "DELETE FROM org_organisation WHERE id = %s" % org.id
        try:
            db.executesql(query)
        except Exception, e:
            self.fail("set_foreign_key_constraints did not turn off constraints (2nd test)")
        db.rollback()
        # Finally, them back the way they were originally.
        old_setting = utils.set_foreign_key_constraints(db, enabled)
        self.assertEqual(old_setting, False)

    def testFieldHelpers(self):
        s3db = current.s3db
        # Use a table that has few fields, and is not in imminent danger of
        # having said fields changed.
        table = s3db.gis_poi_feed
        field_names = table.fields()
        non_meta_field_names = ["location_id", "tablename", "last_update"]
        non_meta_field_names_with_id = non_meta_field_names + ["id"]
        deleted_field_names = ["deleted", "deleted_fk", "deleted_rb"]
        timestamp_field_names = ["created_on", "modified_on"]
        # Test fields_not_in_table
        field_names_plus = list(field_names)
        field_names_plus.insert(1, "extra_field_1")
        field_names_plus.append("extra_field_2")
        result = utils.fields_not_in_table(table, field_names_plus)
        # Order doesn't matter, so compare as sets.
        self.assertEqual(set(result), set(["extra_field_1", "extra_field_2"]))
        # Test remove_meta_fields
        result = utils.remove_meta_fields(field_names)
        self.assertEqual(set(result), set(non_meta_field_names_with_id))
        # Test remove_meta_fields_except_deleted
        result = utils.remove_meta_fields_except_deleted(field_names)
        self.assertEqual(set(result), set(non_meta_field_names_with_id + deleted_field_names))
        # Test remove_meta_timestamp_fields -- avoid a test that does exactly
        # what the test subject does...
        result = utils.remove_meta_timestamp_fields(field_names)
        self.assertEqual(len(result), len(field_names) - len(timestamp_field_names))
        for name in timestamp_field_names:
            self.assertTrue(name not in result)
        # Test the combination of nested calls shown in comments.
        result = utils.remove_id_field(utils.remove_meta_fields(table.fields()))
        self.assertEqual(set(result), set(non_meta_field_names))
    
    def testReadClearLoadDB(self):
        # This test reads / saves the contents of a table, truncates it,
        # then reloads the original contents.
        #
        # It's not much use testing the read helper by reading the table here
        # and comparing against the result of read_table(), as the same DAL
        # operations would be used to do the save and to test it.
        #
        # Use a table that has prepopulate data in every template, is usually
        # small, and has foreign key references to it: gis_projection. It
        # generally has one record, as gis_config references it, and there must
        # be one gis_config record, else the map won't work, and the gis module
        # is always enabled.
        s3db = current.s3db
        gp_table = s3db.gis_projection
        gc_table = s3db.gis_config
        # Some checks independent of just repeating what read_table does:
        # Get the initial length and values from a record joined to the a
        # gis_config record.
        gp_len = db(gp_table).count()
        gc_joined_record = db((gc_table.projection_id == gp_table.id)).select(
                               gc_table.id, gc_table.name, gp_table.id, gp_table.name).first()
        # Read out the gis_symbology table.
        try:
            gp_contents = utils.read_table(gp_table)
        except Exception, e:
            self.fail("read_table threw exception %s" % e)
        # Turn off foreign key constraints.
        constraint_setting = utils.set_foreign_key_constraints(db, False)
        # Truncate it.
        try:
            utils.clear_table(gp_table)
        except Exception, e:
            self.fail("clear_table threw exception %s" % e)
        self.assertEqual(db(gp_table).count(), 0)
        # Put it back.
        try:
            utils.load_table(gp_table, gp_contents)
        except Exception, e:
            self.fail("load_table threw exception %s" % e)
        self.assertEqual(db(gp_table).count(), gp_len)
        gc_joined_record_after = db((gc_table.projection_id == gp_table.id)).select(
                                     gc_table.id, gc_table.name, gp_table.id, gp_table.name).first()
        # Compare the query results before and after truncating and restoring.
        self.assertDictEqual(gc_joined_record.as_dict(), gc_joined_record_after.as_dict())
        # Put back constraints.
        utils.set_foreign_key_constraints(db, constraint_setting)
        del constraint_setting

    def testCompareTable(self):
        # Use a table that has multiple records from prepop data -- gis_config.
        # Construct tests that exercise the compare_table options.
        s3db = current.s3db
        table = s3db.gis_config
        # The S3Resource delete call below is going to do a commit, so get rid
        # of any junk this test has put in so far.
        db.rollback()
        # Although the test data contains no deleted records to begin with, they
        # may creep in if a fresh database is not instantiated for each test
        # run. Get rid of those first.
        db(table.deleted==True).delete()
        table_rows = utils.read_table(table)
        table_field_names = table.fields()

        # First, a simple smoke test -- compare the table against itself.
        # We don't need to exclude timestamp fields here since this we're
        # comparing the table to itself.
        # Supply values as Row objects in a Rows object.
        # Note in this first test, the literal return value from compare_table
        # is checked. Subsequent tests show more realistic usage.
        compare_result = utils.compare_table(table, table_field_names, table_rows)
        self.assertEqual(compare_result, (True, ""), compare_result[1])
        # Repeat the comparison, this time supplying values as a "spreadsheet"
        # (list of lists of values in the same order as a list of field names.)
        table_lists = []
        for row in table_rows:
            row_list = [row[f] for f in table_field_names]
            table_lists.append(row_list)
        compare_result = utils.compare_table(table, table_field_names, table_lists)
        self.assertTrue(compare_result[0], compare_result[1])
        # Repeat, supplying values as dicts in a list.
        table_dicts = []
        for row in table_rows:
            table_dicts.append(row.as_dict())
        compare_result = utils.compare_table(table, table_field_names, table_dicts)
        self.assertTrue(compare_result[0], compare_result[1])
        # Mix up the three forms. Web2py Rows doesn't support extended slicing.
        # @ToDo: Send in a fix for that? On the other hand, why would anyone
        # want strides in a database table (except for constructing tests)??
        # Probably a waste of time on the critical path to support it.
        #table_mixed = table_rows[0::3]
        table_mixed = [table_rows[i] for i in range(0, len(table_rows), 3)]
        table_mixed.extend(table_lists[1::3])
        table_mixed.extend(table_dicts[2::3])
        compare_result = utils.compare_table(table, table_field_names, table_mixed)
        self.assertTrue(compare_result[0], compare_result[1])

        # Test extra_ok. No id field included in field_names. This will also,
        # perforce, test multiple_matches_ok.
        # First test extra_ok = False. Since the fields in field_names won't be
        # the same as those in the values, we use the dict form for the values.
        # Leave all fields in the field_values, but only match on a subset.
        # First use a subset that yields a unique match per pattern.
        field_names = ["name", "lat", "lon"]
        compare_result = utils.compare_table(table, field_names, table_dicts)
        self.assertTrue(compare_result[0], compare_result[1])
        # A set of patterns that match all rows with duplication. This is
        # somewhat artificial, but if the set of patterns is constructed
        # programmatically, it may be simpler to allow it to match duplicates.
        # Note multiple_matches_ok is True, as we expect multiple rows to match.
        field_names = ["symbology_id", "projection_id"]
        compare_result = utils.compare_table(table, field_names, table_dicts,
                                             multiple_matches_ok=True)
        self.assertTrue(compare_result[0], compare_result[1])
        # Repeat above with extra_ok set to True, though there are no extras.
        compare_result = utils.compare_table(table, field_names, table_dicts,
                                             extra_ok=True, multiple_matches_ok=True)
        self.assertTrue(compare_result[0], compare_result[1])
        # Patterns that match only a subset. Check for success with extra_ok
        # = True, failure with extra_ok = False.
        field_names = ["min_lat", "min_lon"]
        field_values = [{"min_lat":-90, "min_lon":-180}]
        compare_result = utils.compare_table(table, field_names, field_values,
                                             extra_ok=True, multiple_matches_ok=True)
        self.assertTrue(compare_result[0], compare_result[1])
        compare_result = utils.compare_table(table, field_names, field_values,
                                             multiple_matches_ok=True)
        self.assertFalse(compare_result[0], "Extra rows with extra_ok=False did not fail")

        # Test missing_ok -- include a query that matches nothing.
        field_names = ["symbology_id", "projection_id"]
        field_values = [{"symbology_id":1, "projection_id":100}]
        compare_result = utils.compare_table(table, field_names, field_values,
                                             missing_ok=True, extra_ok=True, multiple_matches_ok=True)
        self.assertTrue(compare_result[0], compare_result[1])
        compare_result = utils.compare_table(table, field_names, field_values,
                                             extra_ok=True, multiple_matches_ok=True)
        self.assertFalse(compare_result[0], "Unmatched pattern with missing_ok=False did not fail")
        
        # Test include_deleted. Create a record to delete, so there won't be
        # references to it. Act as a user who has permission to delete.
        current.auth.s3_impersonate("admin@example.com")
        new_row = {"name": "Test config"}
        new_row_inserted = utils.insert_resource(s3db, table, new_row,
                                                 add_random_suffix_to="name")
        new_row_id = new_row_inserted["id"]
        # Delete the record using S3Resource delete not DAL delete, so the
        # deletion status fields are correctly updated.
        from s3.s3resource import S3Resource
        new_row_resource = S3Resource(table, id=new_row_id)
        new_row_resource.delete()
        new_row_after_delete = db(table.id==new_row_id).select().first()
        # This is not a test of compare_table, it's a test of this test.
        deleted_val = new_row_after_delete["deleted"]
        self.assertTrue(deleted_val)
        current.auth.s3_impersonate(None)
        # Ok, *now* test compare_table with include_deleted. If we leave
        # include_deleted at its default False, then the table contents should
        # match what they did originally.
        compare_result = utils.compare_table(table, table_field_names, table_dicts)
        self.assertTrue(compare_result[0], compare_result[1])
        # Whereas, if we include deleted records, the comparison should fail...
        compare_result = utils.compare_table(table, table_field_names, table_dicts,
                                             include_deleted=True)
        self.assertFalse(compare_result[0],
                         "Deleted row with include_deleted True did not cause match of undeleted contents to fail.")
        # ...unless we say extra_ok.
        compare_result = utils.compare_table(table, table_field_names, table_dicts,
                                             include_deleted=True, extra_ok=True)
        self.assertTrue(compare_result[0], compare_result[1])
        # Include the deleted row in the comparison data, and it should match
        # with include_deleted True.
        table_dicts_with_deleted = list(table_dicts)
        table_dicts_with_deleted.append(new_row_after_delete.as_dict())
        compare_result = utils.compare_table(table, table_field_names, table_dicts_with_deleted,
                                             include_deleted=True)
        self.assertTrue(compare_result[0], compare_result[1])
        # Clean up after the commit -- really delete the deleted row, in case a
        # further test needs a clean table.
        db(table.id == new_row_id).delete()

    def tearDown(self):
        # If we have a constraint setting that wasn't restored, put it back.
        try:
            utils.set_foreign_key_constraints(db, constraint_setting)
        except:
            pass
        db.rollback()

#------------------------------------------------------------------------------
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
        DataHelperTests,
        InterceptCallTests,
        DBUtilsTests,
    )