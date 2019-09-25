# -*- coding: utf-8 -*-

from robot.api import logger
from robot.libraries.BuiltIn import BuiltIn
import requests
from base64 import b64encode

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
        auth_string = "%s:%s" % (self.admin_email, self.admin_password)
        headers = {
            "content-type" : "application/json",
            "Authorization" : "Basic %s" % b64encode(auth_string.encode("utf-8")).decode("utf-8")
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
