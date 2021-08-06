# -*- coding: utf-8 -*-

"""
    RAT (Rapid Antigen Test) device list updater for RLPPTM template

    @license: MIT
"""

import json
import requests
import sys

from gluon import current

from s3compat import urllib_quote

VSETURL = "https://distribution.dcc-rules.de/valuesets"
VSETID = "covid-19-lab-test-manufacturer-and-name"

# =============================================================================
class RATList(object):
    """
        Helper class to update the local testing device database
        with the the list of currently EU-approved COVID-19 RAT testing
        devices

        See https://github.com/corona-warn-app/cwa-quicktest-onboarding/blob/master/api/dcc-rules-openAPI.json
    """

    # -------------------------------------------------------------------------
    @classmethod
    def sync(cls):
        """
            Synchronize the local RAT device registry with upstream data

            @returns: success True|False
        """

        settings = current.deployment_settings
        vseturl = settings.get_custom("dcc_rules_url", VSETURL)
        vsetid = settings.get_custom("dcc_rules_id", VSETID)

        # Retrieve the value set list
        valuesets = cls.get(vseturl)
        if valuesets is None:
            return False

        # Get the current hash of the target value set
        vsethash = None
        for item in valuesets:
            if item.get("id") == vsetid:
                vsethash = item.get("hash")
                break
        if not vsethash:
            return False

        # Construct the source URI
        source = "/".join((vseturl, urllib_quote(vsethash)))

        # Retrieve the value set and update the device registry
        valueset = cls.get(source)
        if valueset:
            return cls.update_device_registry(source, valueset)

        return True

    # -------------------------------------------------------------------------
    @classmethod
    def update_device_registry(cls, source, vset):
        """
            Update the RAT device registry from the value set

            @param source: the source URI
            @param vset: the value set retrieved from the source

            @returns: success True|False
        """

        if not isinstance(vset, dict):
            return False

        devices = vset.get("valueSetValues")
        if not isinstance(devices, dict):
            return False

        db = current.db
        s3db = current.s3db

        table = s3db.disease_testing_device

        set_record_owner = current.auth.s3_set_record_owner
        s3db_onaccept = s3db.onaccept

        defaults = cls.defaults()

        updated = 0
        for device_code, device_data in devices.items():
            data = {"code": device_code,
                    "name": device_data.get("display"),
                    "approved": device_data.get("active", False),
                    "source": source,
                    }

            # Check for existing entry
            query = (table.code == device_code) & \
                    (table.disease_id == defaults.get("disease_id")) & \
                    (table.device_class == defaults.get("device_class")) & \
                    (table.deleted == False)
            row = db(query).select(table.id, limitby=(0, 1)).first()
            if row:
                # Entry exists => update it
                row.update_record(**data)
                data["id"] = row.id
                s3db_onaccept(table, data, method="update")
            else:
                # Add new entry
                data.update(defaults)
                data["available"] = data["approved"]
                data["id"] = table.insert(**data)
                set_record_owner(table, data)
                s3db_onaccept(table, data, method="create")

            updated += 1

        # Disable all other entries
        query = (table.disease_id == defaults.get("disease_id")) & \
                (table.device_class == defaults.get("device_class")) & \
                ((table.source == None) | (table.source != source)) & \
                (table.deleted == False)
        disabled = db(query).update(approved = False,
                                    available = False,
                                    )

        current.log.info("RATList: update complete (%s added/updated, %s disabled)" % (updated, disabled))

        return True

    # -------------------------------------------------------------------------
    @staticmethod
    def defaults():
        """
            Get the defaults for new testing device entries

            @returns: the defaults as dict
        """

        defaults = {"device_class": "RAT",
                    }

        # Lookup disease ID
        table = current.s3db.disease_disease
        query = (table.name == "COVID-19") & \
                (table.deleted == False)
        row = current.db(query).select(table.id,
                                       limitby = (0, 1),
                                       ).first()
        if row:
            defaults["disease_id"] = row.id

        return defaults

    # -------------------------------------------------------------------------
    @staticmethod
    def get(url):
        """
            Read JSON data from URL

            @param url: the URL to read from

            @returns: the decoded data, or None on error
        """

        try:
            sr = requests.get(url)
        except requests.exceptions.RequestException:
            # Local or network error
            error = sys.exc_info()[1]
            current.log.error("RATList: request to server failed (local error: %s)" % error)
            return None

        if sr.status_code != 200:
            # Remote error
            current.log.error("RATList: request to server failed, status code %s" % sr.status_code)
            return None

        try:
            data = sr.json()
        except json.JSONDecodeError:
            error = sys.exc_info()[1]
            current.log.error("RATList: server response parse error: %s" % error)
            return None

        return data

# END =========================================================================
