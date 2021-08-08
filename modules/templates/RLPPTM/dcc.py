# -*- coding: utf-8 -*-

"""
    Infection test result reporting for RLPPTM template

    @license: MIT
"""

import datetime
import hashlib

from gluon import current

EXPIRY_PERIOD = 48 # DCC expires 48h after probe

# =============================================================================
class DCC(object):
    """ Helper class to handle Digital Covid Certificates (DCCs) """

    def __init__(self, instance_id):
        """
            Constructor

            @param instance_id: the instance ID
        """

        self.instance_id = instance_id
        self.data = None

    # -------------------------------------------------------------------------
    @classmethod
    def from_result(cls, test_id, result_id, first_name, last_name, dob):
        """
            Create a DCC instance from a test result

            @param test_id: the identifier under which the result has been
                            reported to CWA (report to CWA is mandatory for DCC)
            @param result_id: case diagnostics record ID
            @param first_name: the first name to use in the DCC
            @param last_name: the last name to use in the DCC
            @param dob: the date of birth to use in the DCC (date instance or ISO-formatted)

            @returns: DCC instance

            @raises: ValueError if the data are invalid
        """

        # Generate instance ID (=hash of the test ID)
        if not isinstance(test_id, str) or not test_id:
            raise ValueError("Test ID is required")
        instance_id = hashlib.sha256(test_id.encode("utf-8")).hexdigest().lower()

        # Template for error messages
        error = lambda msg: current.T("Cannot certify result [%(reason)s]") % {"reason": msg}

        # Check person data are complete
        if not all((first_name, last_name, dob)):
            raise ValueError(error("incomplete person data"))

        # Lookup probe date, result, name of test station, and device code
        s3db = current.s3db
        rtable = s3db.disease_case_diagnostics
        dtable = s3db.disease_testing_device
        ftable = s3db.org_facility

        left = [ftable.on((ftable.site_id == rtable.site_id) & \
                          (ftable.deleted == False)),
                dtable.on((dtable.id == rtable.device_id) & \
                          (dtable.deleted == False)),
                ]

        query = (rtable.id == result_id) & \
                (rtable.deleted == False)

        row = current.db(query).select(rtable.id,
                                       rtable.disease_id,
                                       rtable.result,
                                       rtable.probe_date,
                                       ftable.id,
                                       ftable.name,
                                       dtable.id,
                                       dtable.code,
                                       left = left,
                                       limitby = (0, 1),
                                       ).first()
        if not row:
            raise ValueError(error("result record not found"))

        # Make sure result is conclusive
        result = row.disease_case_diagnostics
        if result.result not in ("POS", "NEG"):
            raise ValueError(error("inconclusive result"))

        # Make sure the test facility is known
        facility = row.org_facility
        if not facility.id or not facility.name:
            raise ValueError(error("test facility unknown"))

        # Make sure the test device is known
        device = row.disease_testing_device
        if not device.id or not device.code:
            raise ValueError(error("testing device unknown"))

        # Determine probe data and thence, expiry date
        probe_date = result.probe_date
        expires = probe_date + datetime.timedelta(hours=48)
        #if expires < datetime.datetime.utcnow():
        #    raise ValueError(error("result has expired"))

        # Create the instance and fill with data
        instance = cls(instance_id)
        instance.data = {"fn": first_name,
                         "ln": last_name,
                         "dob": dob.isoformat() if isinstance(dob, datetime.date) else dob,
                         "disease": result.disease_id,
                         "site": facility.name,
                         "device": device.code,
                         "timestamp": int(probe_date.replace(microsecond=0).timestamp()),
                         "expires": int(expires.replace(microsecond=0).timestamp()),
                         "result": result.result,
                         }

        return instance

    # -------------------------------------------------------------------------
    @classmethod
    def load(cls, instance_id):
        """
            Instantiate a DCC from stored HCERT data record

            @param instance_id: the instance ID

            @returns: DCC instance

            @raises: ValueError for invalid data
                     TODO make sure these errors appear in the scheduler logs
        """

        db = current.db
        s3db = current.s3db

        table = s3db.disease_hcert_data
        query = (table.instance_id == instance_id) & \
                (table.type == "TEST") & \
                (table.deleted == False)
        row = db(query).select(table.disease_id,
                               table.payload,
                               table.vhash,
                               table.status,
                               table.valid_until,
                               table.certified_on,
                               limitby = (0, 1),
                               ).first()
        if not row:
            raise ValueError("Certificate data not found")
        data = row.payload

        # Create the instance and fill it with data
        instance = cls(instance_id)
        instance.data = {"fn": data.get("fn"),
                         "ln": data.get("ln"),
                         "dob": data.get("dob"),
                         "disease": row.disease_id,
                         "site": data.get("site"),
                         "device": data.get("device"),
                         "timestamp": data.get("timestamp"),
                         "expires": data.get("expires"),
                         "result": data.get("result")
                         }

        # Verify record integrity
        vhash = instance.vhash()
        if vhash != row.vhash:
            raise ValueError("Certificate data have been tempered with")

        return instance

    # -------------------------------------------------------------------------
    def vhash(self):
        """
            Generate a verification hash from instance ID and data

            @returns: the verification hash
        """

        data = self.data
        instance_id = self.instance_id

        fields = ("fn", "ln", "dob", "disease", "site", "device", "timestamp", "result", "expires")
        hashable = "%s#%s" % (instance_id, "#".join(str(data[k]) for k in fields))

        return hashlib.sha512(hashable.encode("utf-8")).hexdigest().lower()

    # -------------------------------------------------------------------------
    def save(self):
        """
            Store this instance as HCERT data record

            @returns: HCERT data record ID
        """

        db = current.db
        s3db = current.s3db

        table = s3db.disease_hcert_data

        instance_id = self.instance_id

        # Check if record already exists (must not override)
        query = (table.instance_id == instance_id)
        if db(query).select(table.id, limitby=(0, 1)).first():
            return

        # Generate record
        now = datetime.datetime.utcnow()
        data = {"disease_id": self.data.get("disease"),
                "type": "TEST",
                "instance_id": instance_id,
                "payload": self.data,
                "status": "PENDING",
                "vhash": self.vhash(),
                "valid_until": now + datetime.timedelta(hours=48),
                }

        # Insert and post-process the record
        data["id"] = table.insert(**data)
        current.auth.s3_set_record_owner(table, data)
        s3db.onaccept(table, data, method="create")

    # -------------------------------------------------------------------------
    def send(self):
        """
            Send the encrypted DCC to the server
        """
        # TODO implement

        pass

    # -------------------------------------------------------------------------
    def anonymize(self):
        """
            Anonymize the HCERT data record
        """
        # TODO implement

        pass

    # -------------------------------------------------------------------------
    @classmethod
    def poll(cls):
        """
            Poll the server for DCC requests
        """
        # TODO implement

        pass

    # -------------------------------------------------------------------------
    @classmethod
    def issue(cls, dcc_request_list):
        """
            Issue the requested DCCs and send them to the server
        """
        # TODO implement

        pass

# END =========================================================================
