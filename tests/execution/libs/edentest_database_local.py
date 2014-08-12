# -*- coding: utf-8 -*-

from robot.api import logger
from gluon import current


class EdenTestQuery(object):
    """
        Query handles all the querying done with this library.
        It is imported by class edentest_database_local below
    """

    @staticmethod
    def query(statement):
        """
            Executes the query as it is without any processing done on it and
            returns the output
            Usage:
                ${output}=  Execute Query As It Is  db(s3db.auth_user.id > 0).select("email").first().as_dict()
                Log  ${output}
            -------
            {'_extra': {'email': 'admin@example.com'}}

        """

        db = current.db
        s3db = current.s3db

        logger.info("Executing %s" % statement)

        output = eval(statement)
        db.commit()
        return output

    @staticmethod
    def row_count(statement):
        """
            Returns the count of the number of the query given
            Usage:
                ${output} =  Row Count  s3db.org_site.id > 0
                Log to console  ${output}
            -------
            52
        """

        db = current.db
        s3db = current.s3db

        cmd = "db(%s).count()" % (statement)
        logger.info("Executing %s" % cmd)

        count_value = eval(cmd)
        return count_value

    @staticmethod
    def count_entries_of_table(table_name):
        """
            Returns the count of the number of entries of a table
            Usage:
                ${output} =  Count Entries Of Table  org_site
                Log to console  ${output}
            -------
            50
        """

        db = current.db
        s3db = current.s3db

        logger.info("Counting the entries in table %s" % (table_name))

        table = s3db[table_name]
        count_value = db(table.deleted != True).count()

        return count_value

    @staticmethod
    def truncate_table(table_name):
        """
            Truncates the table passed as argument
            If the database is in use, it will throw an OperationalError saying
            database is locked
            Usage:
                Truncate table  gis_layer_config
        """

        db = current.db
        s3db = current.s3db

        logger.info("Truncating table %s" % table_name)

        table = s3db[table_name]
        table.truncate()
        db.commit()

    @staticmethod
    def execute_sql_string(sql_string):
        """
            Executes the sqlString as SQL commands.
            SQL commands are expected to be delimited by a semi-colon (';').
            Usage:
                ${output}=  Execute sql string  select site_id from org_site where name = "Station 13";
                Log to console  ${output}
            ----------
            {'site_id': 50}]
        """

        db = current.db
        s3db = current.s3db

        logger.info("Executing query %s" % sql_string)

        output = db.executesql(sql_string, as_dict=True)
        db.commit()

        return output

    @staticmethod
    def query_and_return_the_first_row_where(statement):
        """
            It takes the where statement and returns the first row as a dict
            The various items present in the dict can then be used

            Usage:
                ${output}=  Query and return the first row as dict where  s3db.pr_address.id == 13
                Log to console  ${output}
            --------
            '{deleted_rb': None, 'mci': 2L, 'realm_entity': 44L, 'location_id': ... }
            <Shortened for brevity>
        """

        db = current.db
        s3db = current.s3db

        cmd = "db(%s).select(\
            limitby=(0,1) ).first()" % statement
        logger.info("Executing query %s" % cmd)

        output = eval(cmd)
        return output


class EdenTestAssertion(object):
    """"
        Assertion handles all the assertions done with this library.
        It is imported by class edentest_database_local below
    """

    def __init__(self):

        if not hasattr(self, "query_and_return_the_first_row_where") \
        or not hasattr(self, "row_count"):
            raise Exception("Attributes missing in class")

    def check_if_exists(self, statement):
        """
            Checks if a where statement given exists
            If there is no output, it will raise an assertion error
            Usage:
                Check if exists  s3db.auth_user.id > 100
            -----------
            False
            ========
                Check if exists  s3db.auth_user.id > 10
             ----------
             True
        """

        output = self.query_and_return_the_first_row_where(statement)

        if not output:
            raise AssertionError("Expected to have have at least one row from '%s' \
                but got 0 rows." % statement)

    def check_if_not_exists(self, statement):
        """
            Checks if a where statement given does not exist
            If there is no output, it will raise an assertion error
            Usage:
                Check if exists  s3db.auth_user.id < 100
            -----------
            True
            ========
                Check if exists  s3db.auth_user.id > 10
             ----------
             False
        """

        output = self.query_and_return_the_first_row_where(statement)

        if output:
            raise AssertionError("Expected to have no row from '%s' but got at \
                least one row." % statement)

    def row_count_is_zero(self, statement):
        """
            Check if any rows are returned from the submitted where statement.
            If there are, then this will throw an AssertionError.
            Usage:
                Row count is zero  (s3db.pr_contact.value == "af_editor@example.com")
                ... & (s3db.pr_contact.contact_method == "EMAIL")
            --------
            False
        """

        count = self.row_count(statement)

        if count != 0:
            raise AssertionError("Expected the count to be zero from %s but\
             it was %d instead" % (statement, count))

    def row_count_equals_x(self, statement, x):
        """
            Check if the number rows returned from the submitted where statement are x.
            If there are not, then this will throw an AssertionError.
            Usage:
                Row count is equals x  (s3db.asset_asset.id > 25)  16
            --------
            True
        """

        count = self.row_count(statement)

        if count != int(x):
            raise AssertionError("Expected the count to be %s from %s but\
             it was %d instead" % (x, statement, count))

    def row_count_greater_x(self, statement, x):
        """
            Check if the number rows returned from the submitted where statement
            are greater x. If there are not, then this will throw an AssertionError.
            Usage:
                Row count is greater x  (s3db.asset_asset.id > 25)  12
            --------
            False
        """

        count = self.row_count(statement)

        if count < int(x):
            raise AssertionError("Expected the count to be greater than \
                %s from %s but it was %d instead" % (x, statement, count))

    def row_count_less_x(self, statement, x):
        """
            Check if the number rows returned from the submitted where statement
            are less x. If there are not, then this will throw an AssertionError.
            Usage:
                Row count is greater x  (s3db.asset_asset.id > 25)  12
            --------
            False
        """

        count = self.row_count(statement)

        if count > int(x):
            raise AssertionError("Expected the count to be less than \
                %s from %s but it was %d instead" % (x, statement, count))

    def table_should_exist(self, table_name):
        """
            Checks if the table exits or not
            Usage:
                Table should exist  auth_user_options
            --------
            True
        """

        table = current.s3db[table_name]


class edentest_database_local(EdenTestQuery, EdenTestAssertion):
    """
        For DB inspection of local systems
    """
