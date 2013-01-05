# -*- coding: utf-8 -*-
#
# Helper functions for unit tests.
#
# Import utils as follows:
#
# utils_package = "applications.%s.modules.unit_tests" % (current.request.application)
# utils_name = "utils"
# utils = getattr(__import__(utils_package, fromlist=[utils_name]), utils_name)

#------------------------------------------------------------------------------
# Helpers for making test data.

def insert_resource(s3db, table, data, add_random_suffix_to=None):
    """ Insert one record, with its associated superentities.
        Usage example:
        table = s3db.org_organisation
        data = Storage(name="Some Org") # Can use dict as well.
        data_with_id_and_super_keys = utils.insert_resource(table, data, add_random_suffix_to="name")
    """

    if add_random_suffix_to and add_random_suffix_to in data:
        import uuid
        # Don't munge caller's argument.
        data = dict(data)
        new_val = "%s%s" % (data[add_random_suffix_to], uuid.uuid4())
        data[add_random_suffix_to] = new_val
    id = table.insert(**data)
    data.update(id=id)
    s3db.update_super(table, data)
    return data

#------------------------------------------------------------------------------
# Helpers for intercepting and mocking.

class InterceptCall:
    """ Allows intercepting a call to examine args or supply mock return values.

        Call interception refers to interposing a function before the original
        function being called. The intercept can log the call and arguments,
        provide desired mock return values, and / or allow the original function
        to run. Intercepts can be used for several purposes:
        1) Testing operations that would normally use external services (e.g.
        sending email or sms). The external service call can be intercepted to
        avoid performing the external action.
        2) Capturing arguments passed by the system under test to functions it
        uses, to directly check on the actions of the system under test, rather
        than doing only an end-to-end test. This makes it easier to see just
        where the system under test may be going wrong.
        3) Easy mocking, e.g. providing a desired return value from a function
        called by the system under test. The mock can supply desired test values
        directly, without the need to manipulate the environment to trick the
        original function into supplying the desired values.

        If custom record keeping isn't needed, the intercept can log the
        arguments on each call. If custom behavior isn't needed, the intercept
        can be told whether to call the original function, or what to return on
        each call.

        If data other than arguments needs to be captured on calls, or if other
        action needs to be taken, or if the mock return value has to be built
        from the arguments or environment, the user can supply a callback, which
        the intercept will call with the same arguments as the original
        function. The callback can take actions such as logging some of the
        arguments or recording other information for the test to examine, or
        determining whether to call the original function. The value returned by
        the callback will determine whether or not the original function is then
        run. If the original function is not run, the callback can instead
        provide a value to return to the caller. This allows the intercept to
        act as a mock, without the need to construct a full mock.

        The callback should return a tuple:
        (call_real_function, mock_return_value)
        If call_real_function is True, the original function will be called, and
        its return value will be returned to the caller.
        If call_real_function is False, the original function will not be
        called, and instead mock_return_value will be returned.
        If the return value from the callback doesn't have the right form,
        ValueError will be raised.

        Some notes on usage:

        One can hold a reference to the intercept explicitly, or just access it
        via the target object's original function attribute after the intercept
        is instantiated.

        The default callback captures arguments as *args, **kwargs. It does not
        know the signature of the original function. So if the call includes
        some kwargs in order *without their keywords*, i.e. they appear as
        positional arguments, they will be in args, not kwargs, in the log.

        The callback can be a method of the test case. It can then record the
        arguments it's called with. (It can use the "log" field of the
        intercept for this, or instance variables of the test case.)
        The test case can then check whether the arguments were as expected.
        Likewise, the test case can provide information to the callback via
        instance variables of the test case. This can allow one callback to be
        used in multiple tests where it has to act differently.

        An intercept is useful if you can't mock out the actual target object,
        or want to see how some service is being called, either without actually
        invoking the service, or without disturbing its operation. Note that the
        return value optionally supplied by the callback can depend on the
        arguments passed to the callback, and the callback has access to the
        Web2py environment. This allows using the intercept as a lightweight
        mock, without the bother of creating a full mock of some complex
        service.

        For example, an intercept could be used to catch email or sms on the way
        out to see what we're trying to send, without actually sending it. It
        could be used to deliver reproducible responses in place of some service
        where the responses aren't predictable -- that allows testing with all
        response values in a controlled manner.
    """

    def log_arguments_callback(self, *args, **kwargs):
        """ Default callback.
            Optionally log the arguments, and return the call_real_function and
            mock_return_value values.
        """
        if self.log_arguments:
            self.log.append((args, kwargs))
        return (self.call_real_function, self.mock_return_value)

    def __init__(self,
                 target,
                 real_function_name,
                 test_callback=None,
                 log_arguments=True,
                 call_real_function=True,
                 mock_return_value=None):
        """ Set up and enable the intercept.
            @param target: The object, class, or module whose function is being
                tested. If target is a string, it is taken to be a module name
                and the module is imported.
            @param real_function_name: The name of the function to intercept.
            @param test_callback: The function that should be called when the
                function call is intercepted.
            The following parameters are primarily relevant if a test_callback
            is not specified -- they are used by the default callback,
            log_arguments_callback. They can be changed after construction to
            alter the behavior of the intercept with the default callback.
            @param log_arguments: If true, the received arguments will be
                recorded on each call. The log will be a list of tuples of
                (args, kwargs), one for each call. Arguments are not copied, so
                it is possible that internal values in object arguments will be
                altered after the call.
            @param call_real_function: If True, the original function will be
                called, and its return value returned to the caller.
            @param mock_return_value:
        """
        self.target = target
        self.real_function_name = real_function_name
        self.real_function = getattr(target, real_function_name, None)
        if not self.real_function:
            raise ValueError("Function name %s not found in target." % real_function_name)
        if test_callback:
            self.test_callback = test_callback
        else:
            self.test_callback = self.log_arguments_callback
        self.log_arguments = log_arguments
        self.log = []
        self.call_real_function = call_real_function
        self.mock_return_value = mock_return_value
        self.enabled = True
        setattr(target, real_function_name, self)

    def __call__(self, *args, **kwargs):
        """ Call the callback and optionally the original function. """
        if self.enabled:
            try:
                (call_real_fn, mock_retval) = self.test_callback(*args, **kwargs)
            except (TypeError, ValueError):
                raise ValueError("Bad format for callback return value.")
        else:
            call_real_fn = True
        if call_real_fn:
            # @ToDo: Should this let the test have a look at the real function's
            # return value before returning it? Could have test supply another
            # callback for that.
            return self.real_function(*args, **kwargs)
        return mock_retval

    def disable(self):
        """ Disable the intercept, but preserve it so it can be re-enabled. """
        self.enabled = False

    def enable(self):
        """ (Re)enable the intercept. """
        self.enabled = True

    def remove(self):
        """ Remove the intercept from the target entirely.
            The intercept is not useful after this.
        """
        # Remove the target reference so that won't prevent garbage collecting
        # the target.
        target = self.target
        self.target = None
        setattr(target, self.real_function_name, self.real_function)

#------------------------------------------------------------------------------
# Helpers for manipulating and observing the database.
# (The simple helpers are provided just so people won't have to dig through
# gluon/dal.py.)

from gluon.dal import Row

def get_field_objects_from_names(table, field_names):
    """ Get Field objects in the given table for the given field names. """
    return [table[f] for f in field_names]

def fields_not_in_table(table, field_names):
    """ Determine which of the given fields are not in the given table. """
    return [f for f in field_names if f not in table.fields()]

# The following "remove_" helpers return a new list, and do not alter the
# supplied argument. That allows nesting the helpers if you want to remove
# both boilerplate fields and the id field, e.g.:
# ok_fields = remove_id_field(remove_meta_fields(table.fields()))

def remove_meta_fields(field_names):
    """ Remove fields defined in s3_meta_fields. """
    from s3.s3fields import s3_all_meta_field_names
    meta_names = s3_all_meta_field_names()
    return [name for name in field_names if name not in meta_names]

def remove_meta_fields_except_deleted(field_names):
    """ Remove fields defined in s3_meta_fields other than the deletion fields. """
    from s3.s3fields import s3_all_meta_field_names, s3_deletion_status
    meta_names = s3_all_meta_field_names()
    deleted_fields = s3_deletion_status()
    deleted_names = [field.name for field in deleted_fields]
    meta_names_except_deleted = [name for name in meta_names if name not in deleted_names]
    return [name for name in field_names if name not in meta_names_except_deleted]

def remove_meta_timestamp_fields(field_names):
    """ Remove just the timestamp fields defined in s3_meta_fields.
        These values are not under test control unless mocked, so won't match.
    """
    from s3.s3fields import s3_timestamp
    time_fields = s3_timestamp()
    time_names = [field.name for field in time_fields]
    return [name for name in field_names if name not in time_names]

def remove_id_field(field_names):
    """ Remove the "id" field.
        Included for completeness and so one can nest the calls to the remove
        helpers: remove_id_field(remove_meta_fields(table.fields()))
    """
    # Note use of comprehension avoids need for a try block around a remove
    # from a copy of the argument.
    return [name for name in field_names if name != "id"]

def read_table(table):
    """ Read contents of specified Table into a Rows.
        This is used to save the table contents, typically prior to truncating it.
        Caller is responsible for saving the returned contents.
        @param table: The DAL table object for the table to be read.
        @return: A Rows object holding the table contents.
    """
    return table._db().select(table.ALL)

def clear_table(table):
    """ Empty the table, leaving the table structure.
        This may be useful if the table contains unknown and unwanted stuff
        from prepop, and you'd rather put in just your test data, thanks very
        much...
        CAUTION!  Be sure to put back the original contents even if your test
        fails, in case the test harness continues, or in case the user wants
        their database in a usable state afterward.
        CAUTION!  Better run tests single-threaded if you're going to nuke
        tables, as other tests might want what was in the table...
    """
    table.truncate()

def load_table(table, rows):
    """ Put back the saved contents of a table.

        Caution: table will be truncated before the saved contents are inserted.
        The table contents should be a Rows object, or a list of dicts or Row
        objects. This should probably be run with constraint checks turned off.
        If you've installed a callback in insert, you probably want to take it
        out before calling this.
        (Note DAL insert and bulk_insert won't accept raw Row(s) objects, as
        they contain keys that aren't table fields, like update_record,
        delete_record. Row as_dict() takes those out.)
    """
    table.truncate()
    for row in rows:
        if isinstance(row, Row):
            row = row.as_dict()
        table.insert(**row)

def compare_table(table, field_names, field_values,
                  missing_ok=False,
                  extra_ok=False,
                  multiple_matches_ok=False,
                  include_deleted=False):
    """ Compare specified fields of table to supplied values.

        @param table: The table to check.
        @param field_names: List of names of fields to compare. Recommend
            excluding fields with indeterminate values like created or modified
            times or the id field, and fields irrelevant to the test. Names
            should be supplied as strings not Field instances, and should not
            include the table name.
        @param field_values: List or Rows object of data to compare against.
            Each element in the list or Rows holds the values for one record to
            be compared against the table. An element can either be:
            -- a list of values (which must be in the same order as the fields
            in field_names)
            -- a dict or Row with field names as keys
            The dict or Row forms may be more convenient in cases where the
            records to test are obtained programmatically. The list form may be
            simpler if a static set of records is hard-coded in the test. (Even
            with the dict or Row form, the caller must provide field_names, as
            the main purpose of field_names is to restrict which table fields
            are compared.) If a record represented as a dict omits a field in
            field_names, that field won't be included in the query to look up
            matching records. In general, it is possible for multiple table
            records to match one entry in field_values.
        @param extra_ok: If this is True, there can be other rows in the table
            besides those specified.
        @param missing_ok: If this is True, it is ok if not all supplied rows
            are found.
        @param multiple_matches_ok: If True, it is ok if multiple database rows
            match one supplied row.
        @param include_deleted: Normally, deleted records are not included in
            matching, i.e. a supplied pattern will not match deleted records.
            If include_deleted is True, then deleted records are not excluded
            from matching. This might be used to test operations that involve
            deletion. Note this does not alter either the field_names or
            field_values submitted for comparison -- the caller can still match
            on the values of the deletion status fields. This only affects
            whether queries to find matching records include a term to require
            non-deleted records only.

        @raise ValueError: if the number of primary key rows and data rows are
            not the same, or if the number of values in a row isn't the same as
            the number of specified fields, or if the specified fields are
            not in the table.

        @return: (True, "") if the supplied fields match their counterparts in
            the table, taking into account the missing_ok and extra_ok options,
            or (False, <reason text>) if the check failed. Only the first
            mismatch, extra, missing or duplicate row that caused the failure
            is reported.

        Usage:
        compare_result = utils.compare_table(table, field_names, records_to_check)
        self.assertTrue(compare_result[0], compare_result[1])  # 2nd arg is error message.
    """
    # @ToDo: Will anyone ever want missing_ok?
    # @ToDo: What should we do about deleted? Can that just be one of the fields
    # to match? Might need to test whether a row gets deleted. What will the
    # behavior be if we don't do anything explicit about deleted?
    # @ToDo: Want option to report *all* mismatches, other, missing, duplicates?
    # @ToDo: Does anyone want matching on joins? Could just CREATE VIEW...

    def err_msg(field_names, vals):
        """ Form string with field = value list. """
        if isinstance(vals, list):
            pairs = zip(field_names, vals)
        elif isinstance(vals, dict):
            pairs = vals.items()
        else:
            return str(vals)
        msg = ",".join(["%s=%s" % pair for pair in pairs])
        return msg

    db = table._db

    num_fields = len(field_names)
    if num_fields == 0:
        raise ValueError("Must supply fields.")
    bad_fields = fields_not_in_table(table, field_names)
    if bad_fields:
        raise ValueError("Fields %s are not in table %s" %
                         (" ".join(bad_fields), table._tablename))

    # Get Field objects for the field names, to use in select.
    # If "id" is not in field_names, we'll need to add it to the select --
    # id is needed as the same record may be matched by multiple patterns in
    # field_values.
    if "id" in field_names:
        select_names = field_names
    else:
        select_names = list(field_names)
        select_names.append("id")
    select_fields = get_field_objects_from_names(table, select_names)

    # Ids matched by the patterns in field_values. A record may be matched by
    # multiple patterns -- need to avoid counting it multiple times.
    all_matched_ids = []

    # Check each row.
    for vals in field_values:
        if isinstance(vals, list):
            if len(vals) != num_fields:
                raise ValueError("# values doesn't match # fields for %s" %
                                 err_msg(field_names, vals))
            fields_vals = zip(field_names, vals)
        else:
            if isinstance(vals, Row):
                vals = vals.as_dict()
            if isinstance(vals, dict):
                # Only match on fields in field_names.
                fields_vals = [(field, val) for (field, val) in vals.items() if field in field_names]
            else:
                raise ValueError(
                    "field_values entries must be lists, dicts, or Row objects: %s" %
                    err_msg(field_names, vals))
            if len(fields_vals) == 0:
                raise ValueError("field_values entries must not be empty.")

        # Construct the query. Note dal Query does not have a simple True form,
        # which is why one frequently sees table.id > 0 queries. (If one gives
        # DAL.__call__ a Table as its query argument, that is converted to
        # query._id != None.) Here, we use the first field value pair to start
        # the query.
        query = table[fields_vals[0][0]] == fields_vals[0][1]
        for field_val in fields_vals[1:]:
            query = query & (table[field_val[0]] == field_val[1])
        if not include_deleted:
            query = query & (table["deleted"] == False)
        # Perform the query.
        matches = db(query).select(*select_fields)
        num_matches = len(matches)
        # Was there a matching row?
        if num_matches == 0:
            if not missing_ok:
                return (False, "Missing row with %s" % err_msg(field_names, vals))
            continue
        # Was the result not unique?
        if num_matches > 1:
            if not multiple_matches_ok:
                return (False, "Multiple rows with %s" % err_msg(field_names, vals))
        # For total matches across all patterns in field_values, only count
        # unique matches -- exclude ids we've matched before.
        new_ids = [match.id for match in matches if match.id not in all_matched_ids]
        all_matched_ids.extend(new_ids)

    # Check for leftover rows.
    if not extra_ok:
        if include_deleted:
            query = table
        else:
            query = table.deleted == False
        total_rows = db(query).count()
        if len(all_matched_ids) != total_rows:
            return (False, "Records other than those matched found in table.")

    return (True, "")

def set_db_callbacks(db, insert=None, update=None, delete=None):
    """ Insert supplied callbacks in the db adapter insert, update, delete calls.

        The supplied functions are called prior to calling the real DAL
        insert, update, and delete.  The functions should take the same
        parameters as the corresponding DAL calls.  This allows tests to see
        what args are being passed to the DAL.  If the callback returns true,
        then the real call is executed.  If the callback returns false, then
        the real call is skipped.
        (Q: Should this allow passing hint objects to the test_callbacks?)
        (Q: Should this just take arbitrary keyword args, so it can install
        callbacks in whatever adapter functions the user wants?)
    """
    if insert:
        InterceptCall(db._adapter, insert, "insert")
    if update:
        InterceptCall(db._adapter, update, "update")
    if delete:
        InterceptCall(db._adapter, delete, "delete")

def remove_db_callbacks(db):
    """ Remove any inserted callbacks from insert, update, delete calls. """
    if isinstance(db._adapter.insert, InterceptCall):
        db._adapter.insert.remove()
    if isinstance(db._adapter.update, InterceptCall):
        db._adapter.update.remove()
    if isinstance(db._adapter.delete, InterceptCall):
        db._adapter.delete.remove()

def set_foreign_key_constraints(db, constraint_setting):
    """ Set foreign key constraints to supplied value.
        @param constraint_setting:  If False turn off constraints.  If True,
        turn them on.
        @return:  The original state of the foreign key constraints, True for
        on, False for off.  Caller is responsible for saving this and supplying
        it to set_foreign_key_constraints(new_value).
        Use this prior to truncating tables that may have references to them
        from other tables.  This permits truncating a table and inserting test
        data even if other tables contain records that point to the original
        contents of the table.  Currently supports SQLite, MySQL, POstgreSQL.
    """
    from gluon import dal

    current_constraint_setting = True

    if isinstance(db._adapter, dal.SQLiteAdapter) or \
       isinstance(db._adapter, dal.SpatiaLiteAdapter) or \
       isinstance(db._adapter, dal.JDBCSQLiteAdapter):
        raw_constraint_setting = db.executesql("PRAGMA foreign_keys;")
        # Response looks like [(0,)] if off, or [(1,)] if on.
        current_constraint_setting = raw_constraint_setting[0][0] == 1
        # Note Sqlite sets pragma values per connection, so you won't be able
        # to see it change from some other connection (e.g. sqlite command line
        # or Sqlite Manager) when the following command is executed.
        setting_argument = "ON" if constraint_setting else "OFF"
        db.executesql("PRAGMA foreign_keys = %s;" % setting_argument)

    elif isinstance(db._adapter, dal.MySQLAdapter):
        raw_constraint_setting = db.executesql("SHOW VARIABLES LIKE 'FOREIGN_KEY_CHECKS';")
        # Response looks like:
        # ((u'foreign_key_checks', u'ON'),)
        current_constraint_setting = raw_constraint_setting[0][1] == "ON"
        setting_argument = "1" if constraint_setting else "0"
        db.executesql("PRAGMA foreign_keys = %s;" % setting_argument)

    # @ToDo: Verify this PostgreSQL code.
    elif isinstance(db._adapter, dal.PostgreSQLAdapter) or \
         isinstance(db._adapter, dal.NewPostgreSQLAdapter) or \
         isinstance(db._adapter, dal.JDBCPostgreSQLAdapter):
        # PostgreSQL does not have a global option for turning constraints on
        # and off. Instead, one can drop and re-add the constraints or disable
        # and re-enable the triggers that enforce the constraints. The latter
        # is simpler as it's done per table not per constraint. There's no
        # sign of Web2py (or us) adding triggers for other purposes.
        # Unfortunately there is no single answer for the current setting, so
        # sample one table that is always defined.
        raw_constraint_setting = db.executesql("""
            SELECT pg_trigger.tgenabled
            FROM pg_trigger,pg_class,pg_namespace
            WHERE pg_trigger.tgrelid=pg_class.oid
            AND pg_class.relname='auth_user';""")
        current_constraint_setting = raw_constraint_setting[0][1] == "D"
        setting_argument = "ENABLE" if constraint_setting else "DISABLE"
        command = "ALTER TABLE %%s %s TRIGGERS ALL" % setting_argument
        for table in db.tables():
            db.executesql(command % table._tablename)

    return current_constraint_setting