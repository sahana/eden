# -*- coding: utf-8 -*-

"""
    Infection test result reporting for RLPPTM template

    @license: MIT
"""

import base64
import cbor2
import datetime
import hashlib
import json
import re
import requests
import secrets
import sys
import uuid

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import hashes

from gluon import current

ISSUER_PREFIX = "lsjvrlp"
EXPIRY_PERIOD = 48 # DCC expires 48h after probe

NONLATIN = re.compile(r"[^\u0020-\u0233\u1E02-\u1EF9]")
SEPARATORS = re.compile(r"[\u002C\u0020\u002D]")
DIACRITICS = {"A" : r"[\u00C0-\u00C3\u0100-\u0104\u01CD\u01DE\u01FA\u1EA0-\u1EB6]",
              "AE": r"[\u00C4\u00C6\u01FC]",
              "AA": r"[\u00C5]",
              "B" : r"[\u1E02]",
              "C" : r"[\u00C7\u0106-\u010C]",
              "D" : r"[\u00D0\u010E\u0110\u1E0A\u1E10]",
              "E" : r"[\u00C8-\u00CB\u0112-\u011A\u018F\u1EB8-\u1EC6]",
              "F" : r"[\u1E1E]",
              "G" : r"[\u011C-\u0122\u01E4\u01E6\u01F4\u1E20]",
              "H" : r"[\u0124\u0126\u021E\u1E24\u1E26]",
              "I" : r"[\u00CC-\u00CF\u0128-\u0131\u01CF\u1EC8\u1ECA]",
              "J" : r"[\u0134]",
              "IJ": r"[\u0132]",
              "K" : r"[\u0136\u01E8\u1E30]",
              "L" : r"[\u0139-\u0141]",
              "M" : r"[\u1E40]",
              "N" : r"[\u00D1\u0143-\u014A\u1E44]",
              "O" : r"[\u00D2-\u00D5\u014C-\u0150\u01A0\u01D1\u01EA\u01EC\u022A-\u0230\u1ECC-\u1EDC]",
              "OE": r"[\u00D6\u00D8\u0152\u01FE]",
              "P" : r"[\u1E56]",
              "R" : r"[\u0154-\u0158]",
              "S" : r"[\u015A-\u0160\u0218\u1E60\u1E62]",
              "SS": r"[\u00DF\u1E9E]",
              "T" : r"[\u0162-\u0166\u021A\u1E6A]",
              "TH": r"[\u00DE]",
              "U" : r"[\u00D9-\u00DB\u0168-\u0172\u01AF\u01D3\u1EE4-\u1EF0]",
              "UE": r"[\u00DC]",
              "W" : r"[\u0174\u1E80-\u1E84]",
              "X" : r"[\u1E8C]",
              "Y" : r"[\u00DD\u0176\u0178\u0232\u1E8E\u1EF2-\u1EF8]",
              "Z" : r"[\u0179-\u017D\u01B7\u01EE\u1E90\u1E92]",
              }

NUMERALS = {"1": "I",
            "2": "II",
            "3": "III",
            "4": "IV",
            "5": "V",
            "6": "VI",
            "7": "VII",
            "8": "VIII",
            "9": "IX",
            }

CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ<"

PEM_TEMPLATE = "-----BEGIN PUBLIC KEY-----\n%s\n-----END PUBLIC KEY-----"

# =============================================================================
class DCC(object):
    """ Helper class to handle Digital Covid Certificates (DCCs) """

    def __init__(self, instance_id):
        """
            Constructor

            @param instance_id: the instance ID
        """

        self.instance_id = instance_id

        self.status = None
        self.data = None

        self.issuer_id = None

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
                                       ftable.site_id,
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

        # Make sure the test facility is valid
        facility = row.org_facility
        issuer_id = cls.get_issuer_id(facility.site_id)
        if not issuer_id:
            raise ValueError(error("invalid test facility"))

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
        instance.status = "PENDING"
        instance.issuer_id = issuer_id
        instance.data = {"fn": first_name,
                         "ln": last_name,
                         "dob": dob.isoformat() if isinstance(dob, datetime.date) else dob,
                         "disease": result.disease_id,
                         "site": facility.site_id,
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
                               table.issuer_id,
                               table.payload,
                               table.vhash,
                               table.status,
                               table.valid_until,
                               table.certified_on,
                               limitby = (0, 1),
                               ).first()
        if not row:
            raise ValueError("Certificate data not found")
        issuer_id = row.issuer_id
        if not issuer_id:
            raise ValueError("Certificate data lacking issuer ID")

        data = row.payload

        # Create the instance and fill it with data
        instance = cls(instance_id)
        instance.issuer_id = issuer_id
        instance.status = row.status
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
    def save(self, errors=None):
        """
            Store/update this instance as HCERT data record

            @param errors: error messages to store in the record
        """

        db = current.db
        s3db = current.s3db

        table = s3db.disease_hcert_data

        now = datetime.datetime.utcnow()
        instance_id = self.instance_id

        # Check if record already exists
        query = (table.instance_id == instance_id)
        record = db(query).select(table.id,
                                  table.errors,
                                  table.certified_on,
                                  limitby = (0, 1),
                                  ).first()
        if record:
            # Status update
            status = self.status
            data = {"status": status,
                    }
            if status == "ISSUED" and not record.certified_on:
                data["certified_on"] = now
            if errors:
                data["errors"] = errors
            record.update_record(**data)
            s3db.onaccept(table, record, method="update")
        else:
            # New record
            data = {"disease_id": self.data.get("disease"),
                    "type": "TEST",
                    "instance_id": instance_id,
                    "issuer_id": self.issuer_id,
                    "payload": self.data,
                    "status": "PENDING",
                    "vhash": self.vhash(),
                    "valid_until": now + datetime.timedelta(hours=48),
                    }
            if errors:
                data["errors"] = errors

            # Insert and post-process the record
            data["id"] = table.insert(**data)
            current.auth.s3_set_record_owner(table, data)
            s3db.onaccept(table, data, method="create")

    # -------------------------------------------------------------------------
    def upload(self, dcci, public_key):
        """
            Send the encrypted DCC to the server

            @param dcci: the DCC ID
            @param public_key: public key to encrypt the AES key

            @returns: error message on error, else None
        """

        # Check status
        if self.status != "PENDING":
            return "DCC upload failed, invalid status"

        settings = current.deployment_settings

        dcc_json = self.encode(dcci, public_key)
        if not dcc_json:
            return "DCC upload failed, no data"
        key, cert, verify = self.get_dcc_credentials()

        # The server endpoint to send to
        dcc_base_url = settings.get_custom("dcc_base_url")
        endpoint = "%s/version/v1/test/%s/dcc" % (dcc_base_url.rstrip("/"), self.instance_id)

        errors = None
        try:
            sr = requests.post(endpoint,
                               json = dcc_json,
                               cert = (cert, key),
                               verify = verify,
                               )
        except Exception:
            # Local errors
            errors = "DCC upload failed (local error: %s)" % sys.exc_info()[1]
        else:
            # Check return code (should be 204, but 202/200 would also be good news)
            status_code = sr.status_code
            if status_code not in (204, 202, 200, 409):
                errors = "DCC upload failed, status code %s" % status_code
                if status_code in (403, 404):
                    # Either test result was not found, or we're not
                    # authorized to certify this test result => don't try again
                    self.status = "INVALID"
            else:
                self.status = "ISSUED"

        # Update record status
        self.save(errors=errors)

        return errors

    # -------------------------------------------------------------------------
    def anonymize(self):
        """
            Anonymize the HCERT data record of this instance (=drop the payload)
        """

        table = current.s3db.disease_hcert_data
        query = (table.instance_id == self.instance_id)

        row = current.db(query).select(table.id,
                                       table.status,
                                       limitby = (0, 1),
                                       ).first()
        if not row:
            return
        data = {"payload": None,
                }
        if row.status == "PENDING":
            # Once anonymized, DCC can no longer be produced
            self.status = data["status"] = "INVALID"

        row.update_record(**data)

        self.data = None

    # -------------------------------------------------------------------------
    # Instance helpers
    # -------------------------------------------------------------------------
    def vhash(self):
        """
            Generate a verification hash from instance ID and data

            @returns: the verification hash
        """

        data = self.data

        instance_id = self.instance_id
        issuer_id = self.issuer_id

        fields = ("fn", "ln", "dob", "disease", "site", "device", "timestamp", "result", "expires")
        hashable = "%s#%s#%s" % (instance_id,
                                 issuer_id,
                                 "#".join(str(data[k]) for k in fields),
                                 )

        return hashlib.sha512(hashable.encode("utf-8")).hexdigest().lower()

    # -------------------------------------------------------------------------
    def encode(self, dcci, public_key):
        """
            Encode and encrypt this instance for transmission to the DCC server

            @param dcci: the certificate ID from the DCC request,
                         e.g. "URN:UVCI:V1:DE:DMN3L94E7PBDYYLAPNNSS5T218"
            @param public_key: the base64-encoded public RSA key from the
                               DCC request

            @returns: dict {
                        "dataEncryptionKey": the encrypted AES-key (base64-encoded),
                        "encryptedDcc":      the encrypted DCC (base64-encoded),
                        "dccHash":           hash of the DCC (hex),
                        }
        """

        data = self.data
        if not data:
            return None

        # Convert timestamp into datetime
        timestamp = data.get("timestamp")
        expires = data.get("expires")
        sc = "%sZ" % datetime.datetime.fromtimestamp(timestamp).isoformat()

        # Convert test result to code
        result_codes = {"NEG": "260415000",
                        "POS": "260373001",
                        }
        result = data.get("result")
        tr = result_codes.get(result)

        # Look up site name from site
        ftable = current.s3db.org_facility
        query = (ftable.site_id == data.get("site"))
        facility = current.db(query).select(ftable.name, limitby=(0, 1)).first()
        tc = facility.name if facility else None

        # Device code
        ma = data.get("device")

        # Names
        fn = data.get("ln")
        gn = data.get("fn")
        # TODO catch ValueError
        gnt = self.format_name(gn)
        fnt = self.format_name(fn)

        # Date of birth
        dob = data.get("dob")

        # Encoded DCC payload
        data = {"t": [{"ci": dcci,
                       "co": "DE",
                       "is": "Robert Koch-Institut",
                       "tg": "840539006",
                       "tt": "LP217198-3",
                       "sc": sc,
                       "tr": tr,
                       "tc": tc,
                       "ma": ma,
                       },
                      ],
                "dob": dob,
                "nam": {"fn": fn,
                        "gn": gn,
                        "fnt": fnt,
                        "gnt": gnt,
                        },
                "ver": "1.3.0",
                }

        # HCERT container
        hcert = {1: "DE",
                 4: expires,
                 6: timestamp,
                 -260: { 1: data },
                 }

        return self.encrypt(cbor2.dumps(hcert), public_key)

    # -------------------------------------------------------------------------
    @staticmethod
    def encrypt(hcert, public_key):
        """
            Encrypt the HCERT

            @param hcert: the HCERT as CBOR-bytestring
            @param public_key: base64-encoded public key to encrypt the AES key with

            @returns: dict {
                        "dataEncryptionKey": the encrypted AES-key (base64-encoded),
                        "encryptedDcc":      the encrypted DCC (base64-encoded),
                        "dccHash":           hash of the DCC (hex),
                        }
        """

        # Generate AES symmetric key (32 bytes)
        key = secrets.token_bytes(32)

        # Pad the hcert data to 128bit blocksize for AES encryption
        padder = padding.PKCS7(128).padder()
        padded = padder.update(hcert) + padder.finalize()

        # Encrypt the padded hcert
        iv = b"\x00" * 16
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded) + encryptor.finalize()

        # Convert base64-encoded public key to PEM and load it
        pem = (PEM_TEMPLATE % public_key).encode("utf-8")
        pkey = load_pem_public_key(pem, default_backend())

        # Encrypt the AES key with the public key
        sha256 = hashes.SHA256()
        mgf = asym_padding.MGF1(algorithm=sha256)
        padder = asym_padding.OAEP(mgf=mgf, algorithm=sha256, label=None)
        key_enc = pkey.encrypt(key, padder)

        # Build COSE for signature, and generate hash
        es256 = cbor2.dumps({1:-7}) # COSE algorithm ECDSA w/ SHA256
        cose = cbor2.dumps(["Signature1", es256, b"", hcert])
        dcchash = hashlib.sha256(cose).hexdigest().lower()

        b64encode = base64.b64encode
        return {"encryptedDcc": b64encode(encrypted).decode('utf-8'),
                "dataEncryptionKey": b64encode(key_enc).decode('utf-8'),
                "dccHash": dcchash,
                }

    # -------------------------------------------------------------------------
    # Background tasks
    # -------------------------------------------------------------------------
    @classmethod
    def poll(cls):
        """
            Poll the server for DCC requests, and issue any requested DCCs
        """

        db = current.db
        s3db = current.s3db

        settings = current.deployment_settings

        # Get the issuer IDs for all pending DCCs
        now = datetime.datetime.utcnow()
        table = s3db.disease_hcert_data
        query = (table.status == "PENDING") & \
                ((table.valid_until == None) | (table.valid_until > now)) & \
                (table.issuer_id != None) & \
                (table.deleted == False)
        rows = db(query).select(table.issuer_id,
                                groupby = table.issuer_id,
                                )

        # The client credentials to access the server
        cert, key, verify = cls.get_dcc_credentials()

        # The server endpoint to poll
        dcc_base_url = settings.get_custom("dcc_base_url")
        endpoint = "%s/version/v1/publicKey/search" % (dcc_base_url.rstrip("/"))

        for row in rows:
            # Search URL is per-issuer
            search_url = "%s/%s" % (endpoint, row.issuer_id)
            try:
                sr = requests.get(search_url,
                                  cert = (cert, key),
                                  verify = verify,
                                  )
            except Exception:
                # Local error
                error = sys.exc_info()[1]
                current.log.error("DCC requests: polling failed (local error: %s)" % error)
                continue

            # Check return code
            if sr.status_code != 200:
                # Remote error
                current.log.error("DCC requests: polling failed, status code %s" % sr.status_code)
                continue

            # Decode the results
            try:
                requested_dccs = sr.json()
            except json.JSONDecodeError:
                error = sys.exc_info()[1]
                current.log.error("DCC results: server response parse error: %s" % error)
                continue

            # If there are any requests, issue the DCCs
            cls.issue(requested_dccs)

    # -------------------------------------------------------------------------
    @classmethod
    def issue(cls, dcc_request_list):
        """
            Encode, encrypt and upload the requested DCCs, and anonymize the
            respective HCERT data records when done

            @param dcc_request_list: a list of dicts:
                        {"testId":    DCC instance ID,
                         "dcci":      certificate ID,
                         "publicKey": public RSA key to encrypt the AES key
                         }
        """

        if not isinstance(dcc_request_list, list):
            return

        for item in dcc_request_list:
            if not isinstance(item, dict):
                continue

            instance_id = item.get("testId")
            if not instance_id:
                continue
            try:
                inst = cls.load(instance_id)
            except ValueError:
                continue

            dcci = item.get("dcci")
            public_key = item.get("publicKey")
            if not dcci or not public_key:
                continue

            inst.upload(dcci, public_key)

            if inst.status != "PENDING":
                inst.anonymize()

    # -------------------------------------------------------------------------
    # Tools
    # -------------------------------------------------------------------------
    @staticmethod
    def get_issuer_id(site_id):
        """
            Get the Point-of-Care ID for a site
            - a string consisting of a common prefix and the site UUID

            @returns: the ID as string, or None if site not found
        """

        s3db = current.s3db

        stable = s3db.org_site
        query = (stable.site_id == site_id)
        row = current.db(query).select(stable.uuid,
                                       cache = s3db.cache,
                                       limitby = (0, 1),
                                       ).first()
        if row:
            uid = uuid.UUID(row.uuid).hex
            issuer_id = ("%s%s" % (ISSUER_PREFIX, uid)).lower()
        else:
            issuer_id = None

        return issuer_id

    # -------------------------------------------------------------------------
    @classmethod
    def register_issuer(cls, issuer_id):
        """
            Register an issuer ID (labID) with the DCC server

            @param issuer_id: the issuer ID as string

            @returns: success True|False
        """

        settings = current.deployment_settings

        # The client credentials to access the server
        cert, key, verify = cls.get_dcc_credentials()

        # The server endpoint to register
        dcc_base_url = settings.get_custom("dcc_base_url")
        endpoint = "%s/version/v1/labId" % dcc_base_url

        # POST to server
        try:
            sr = requests.post(endpoint,
                               json = {"labId": issuer_id},
                               cert = (cert, key),
                               verify = verify,
                               )
        except Exception:
            # Local error
            error = sys.exc_info()[1]
            current.log.error("DCC issuer registration: transmission failed (local error: %s)" % error)
            return False

        # Check return code (should be 204, but 202/200 would also be good news)
        if sr.status_code not in (204, 202, 200):
            # Remote error
            current.log.error("DCC issuer registration: registration failed, status code %s" % sr.status_code)
            return False

        # Success
        return True

    # -------------------------------------------------------------------------
    @staticmethod
    def get_dcc_credentials():
        """
            Get the credentials for access to the DCC server

            @returns: tuple (cert, key, verify)
                      - cert   = absolute pathname of the SSL client certificate
                      - key    = absolute pathname of the key for the client
                                 certificate
                      - verify = absolute pathname to the CA certificate chain
                                 for the server certificate, or True to use
                                 python-certifi
        """

        settings = current.deployment_settings
        folder = current.request.folder

        # The client credentials to access the server
        cert = settings.get_custom("cwa_client_certificate")
        key = settings.get_custom("cwa_certificate_key")
        if not cert or not key:
            raise RuntimeError("No CWA client credentials configured")
        cert = "%s/%s" % (folder, cert)
        key = "%s/%s" % (folder, key)

        # The certificate chain to verify the server identity
        verify = settings.get_custom("dcc_server_ca")
        if verify:
            # Use the specified CA Certificate to verify server identity
            verify = "%s/%s" % (current.request.folder, verify)
        else:
            # Use python-certifi (=> make sure the latest version is installed)
            verify = True

        return cert, key, verify

    # -------------------------------------------------------------------------
    @staticmethod
    def format_name(name):
        """
            Transliterate+format a name according to ICAO conventions

            @param name: the name

            @returns: the transliterated/formatted name as string
        """

        # Remove any non-latin characters
        string = NONLATIN.sub("", name).strip()
        if not string:
            raise ValueError

        # Replace separators by <
        string = SEPARATORS.sub("<", string.upper()).strip("<")
        while("<<" in string):
            string = string.replace("<<", "<")

        # Map diacritics
        for s, o in DIACRITICS.items():
            string = re.sub(o, s, string)

        # Map numerals
        for o, s in NUMERALS.items():
            string = string.replace(o, s)

        # Remove all remaining invalid characters
        string = "".join(c for c in string if c in CHARSET)
        if not string:
            raise ValueError

        return string

# END =========================================================================
