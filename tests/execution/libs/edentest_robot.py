# -*- coding: utf-8 -*-

from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
import requests
import sqlite3
from base64 import b64encode
import subprocess
import os
import re

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
            "content-type": "application/json",
            "Authorization": "Basic %s" % b64_auth_string
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

    def copy_database(self, db_info, is_repeatable):
        """
        The function creates a copy of the the current databsase,
        so that it can be restored at teardown.
        @param db_info: Information regarding the databse like
                        database type, database name, hostname & port number.
        @param is_repeatable: True if repeatable, false otherwise
        """
        db = db_info[0].split(":")
        db_type = db[0]

        if is_repeatable:
            if db_type == "sqlite":
                source = os.path.join("applications", "eden",
                                      "databases", "storage.db")
                destination = os.path.join("applications", "eden",
                                           "databases", "storage_temp.db")

                # Create a copy of the database.
                subprocess.call(["cp", source, destination])

            elif db_type == "postgres":

                db_username = re.sub("/", "", db[1])
                db_password = db[2].split("@")[0]
                db_host = db[2].split("@")[1]
                db_port = db[3].split("/")[0]
                db_name = db[3].split("/")[1]
                os.environ["PGPASSWORD"] = db_password

                # Get the version of postgres
                version_command = subprocess.check_output(["psql", "-V", "-q"])
                temp1 = version_command.split()[2].split(".")[0]
                temp2 = version_command.split()[2].split(".")[1]
                pg_version = float(("%s%s%s") % (temp1, ".", temp2))

                # Query to terminate the connection with database.
                if (pg_version >= 9.2):
                    process = "pid"

                else:
                    process = "procpid"

                killconn_query = ("SELECT pg_terminate_backend(pg_stat_activity.%s) \
                                   FROM pg_stat_activity \
                                   WHERE pg_stat_activity.datname = '%s' \
                                   AND %s <> pg_backend_pid();"
                                  ) % (process, db_name, process)

                # Terminate the connection.
                subprocess.call(["psql", "-h", db_host, "-p", db_port,
                                 "-c", killconn_query, "-U", db_username])

                temp_db = "sahana_temp"
                copydb_query = ("CREATE DATABASE %s \
                                 TEMPLATE %s;") % (temp_db, db_name)

                # Creates a copy of the database.
                subprocess.call(["psql", "-h", db_host, "-p", db_port,
                                 "-c", copydb_query, "-U", db_username])

    def restore_original_database(self, db_info, is_repeatable):
        """
        The function creates a copy of the the current databsase,
        so that it can be restored at teardown.
        @param db_info: Information regarding the databse like
                        database type, database name, hostname & port number.
        @param is_repeatable: True if repeatable, false otherwise
        """

        db = db_info[0].split(":")
        db_type = db[0]

        if is_repeatable:

            if db_type == "sqlite":

                # Removes the modified database.
                db_path = os.path.join("applications", "eden",
                                       "databases", "storage.db")
                subprocess.call(["rm", db_path])

                # Restore the original database.
                tempdb_path = os.path.join("applications", "eden",
                                           "databases", "storage_temp.db")
                orgndb_path = os.path.join("applications", "eden",
                                           "databases", "storage.db")
                subprocess.call(["mv", tempdb_path, orgndb_path])

            elif db_type == "postgres":
                print "check1"
                db_username = re.sub("/", "", db[1])
                db_password = db[2].split("@")[0]
                db_host = db[2].split("@")[1]
                db_port = db[3].split("/")[0]
                db_name = db[3].split("/")[1]
                os.environ["PGPASSWORD"] = db_password

                # Get the version of postgres
                version_command = subprocess.check_output(["psql", "-V", "-q"])
                temp1 = version_command.split()[2].split(".")[0]
                temp2 = version_command.split()[2].split(".")[1]
                pg_version = float(("%s%s%s") % (temp1, ".", temp2))

                # Query to terminate the connection with database.
                if (pg_version >= 9.2):
                    process = "pid"

                else:
                    process = "procpid"

                killconn_query = ("SELECT pg_terminate_backend(pg_stat_activity.%s) \
                                   FROM pg_stat_activity \
                                   WHERE pg_stat_activity.datname = '%s' \
                                   AND %s <> pg_backend_pid();"
                                  ) % (process, db_name, process)

                # Terminate the connection.
                subprocess.call(["psql", "-h", db_host, "-p", db_port,
                                 "-c", killconn_query, "-U", db_username])

                # Drops the modified database.
                dropdb_query = ("DROP DATABASE %s;") % db_name
                subprocess.call(["psql", "-h", db_host, "-p", db_port,
                                 "-c", dropdb_query, "-U", db_username])

                # Restores the original database.
                temp_db = "sahana_temp"
                createdb_query = ("CREATE DATABASE %s \
                                   TEMPLATE %s;") % (db_name, temp_db)
                subprocess.call(["psql", "-h", db_host, "-p", db_port,
                                 "-c", createdb_query, "-U", db_username])

                # Drops the database copy.
                dropdb_final = ("DROP DATABASE %s;") % temp_db
                subprocess.call(["psql", "-h", db_host, "-p", db_port,
                                 "-c", dropdb_final, "-U", db_username])