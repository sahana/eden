# -*- coding: utf-8 -*-

from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
import requests
import sqlite3
from base64 import b64encode
from subprocess import call
import subprocess


class edentest_robot(object):

    def __init__(self, server, appname, admin_email, admin_password):
        """
            Initialize the class variables
        """

        logger.debug("Arguments %s %s" % (server, appname), html=True)

        self.base_url = "http://%s/%s" % (server, appname)
        self.admin_email = admin_email
        self.admin_password = admin_password

    def get_deployment_settings(self, *asked):
        """
            Returns the deployment settings asked in a dict where key is the
            asked setting. It makes a get request to eden/default/edentest
            and uses s3cfg to get the settings.
            It uses env. proxy settings
        """

        logger.info("base_url %s" % (self.base_url))

        # Create the request_url for the get request
        request_url = "%s/default/get_settings/deployment_settings" % (self.base_url)

        for key in asked:
            request_url = "%s/%s" % (request_url, key)
        logger.info("request_url %s" % (request_url))

        # Create the headers
        b64_auth_string = b64encode("%s:%s" % (self.admin_email, self.admin_password))
        headers = {
            "content-type" : "application/json",
            "Authorization" : "Basic %s" % b64_auth_string
            }

        # Send the response and get the response
        response = requests.get(request_url, headers=headers)
        if response.status_code != requests.codes.ok:
            if response.status_code == 403:
                logger.warn("Could not login")
                m = "Check variable ADMIN_EMAIL and ADMIN_PASSWORD\
                 or allow_testing in config.py. request %s" % request_url

            elif response.status_code == 401:
                logger.warn("Insufficent priviledges")
                m = "You do not have admin rights. request %s" \
                % request_url

            elif response.status_code in (405, 500):
                logger.warn("Testing not allowed/Internal server error")
                m = "allow_testing set to False in 000_config.py. request %s" \
                % request_url

            else:
                logger.warn("Could not contact the Eden server")
                m = "Check 000_config.py/config.py/server/internet settings. request %s" \
                % request_url

            BuiltIn().fail(msg=m)

        output = response.json()

        for key in asked:
            if key not in output:
                logger.warn("Could not fetch the setting %s" % key)

        return output

    def switch_to_temp_database(self, db_type, is_repeatable):
        """
        The function creates a copy of the the current databsase,
        so that it can be restored at teardown.
        @param db_type: database type
        @param is_repeatable: True if repeatable, false otherwise
        """

        if is_repeatable:
            if db_type == "sqlite":
                # Create a copy of the database.
                call(['cp', 'applications/eden/databases/storage.db',
                    'applications/eden/databases/storage_temp.db'])

            elif db_type == "postgres":
                # Get the version of postgres
                pg_version = subprocess.check_output(['psql', '-V', '-q']).split()[2]
                # Query to terminate the connection with database.
                if (pg_version >= 9.2):
                    query = "SELECT pg_terminate_backend(pg_stat_activity.pid) \
                              FROM pg_stat_activity WHERE pg_stat_activity.datname = 'sahana' \
                              AND pid <> pg_backend_pid();"
                else:
                    query = "SELECT pg_terminate_backend(pg_stat_activity.procpid) \
                              FROM pg_stat_activity WHERE pg_stat_activity.datname = 'sahana' \
                              AND procpid <> pg_backend_pid();"

                # Terminate the connection.
                call(['psql', '-q', '-c', query,'-U','postgres'])

                # Creates a copy of the database.
                call(['createdb', '-U', 'postgres', '-T', 'sahana', 'sahana_temp'])

    def switch_to_original_database(self, db_type, is_repeatable):
        """
        The function removes the modified database
        and restore it back to the original.
        @param db_type: database type
        @param is_repeatable: True if repeatable, false otherwise
        """
        if is_repeatable:
            if db_type == "sqlite":
                # Removes the modified database.
                call(['rm', 'applications/eden/databases/storage.db'])
                # Restore the original database.
                call(['mv','applications/eden/databases/storage_temp.db',
                    'applications/eden/databases/storage.db'])

            elif db_type == "postgres":
                pg_version = subprocess.check_output(['psql', '-V', '-q']).split()[2]

                if (pg_version >= 9.2):
                    query = "SELECT pg_terminate_backend(pg_stat_activity.pid) \
                              FROM pg_stat_activity WHERE pg_stat_activity.datname = 'sahana' \
                              AND pid <> pg_backend_pid();"
                else:
                    query = "SELECT pg_terminate_backend(pg_stat_activity.procpid) \
                              FROM pg_stat_activity WHERE pg_stat_activity.datname = 'sahana' \
                              AND procpid <> pg_backend_pid();"
                # Terminate the connection.
                call(['psql', '-q', '-c', query,'-U','postgres'])
                # Drops the modified database.
                call(['dropdb', 'sahana', '-U', 'postgres'])
                # Restores the original database.
                call(['createdb', '-U', 'postgres', '-T', 'sahana_temp', 'sahana'])
                # Drops the database copy.
                call(['dropdb', 'sahana_temp', '-U', 'postgres'])
