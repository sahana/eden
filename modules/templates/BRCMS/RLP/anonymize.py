# -*- coding: utf-8 -*-

from uuid import uuid4

from gluon import current

def rlpcm_person_anonymize():
    """ Rules to anonymize a case file """

    auth = current.auth
    s3db = current.s3db

    ANONYMOUS = "-"

    # Helper to produce an anonymous ID (pe_label)
    anonymous_id = lambda record_id, f, v: "NN%s" % uuid4().hex[-8:].upper()
    anonymous_code = lambda record_id, f, v: uuid4().hex

    # Case Activity Default Closure
    activity_closed = s3db.br_case_activity_default_status(closing=True)

    anonymous_address = s3db.br_anonymous_address

    # General rule for attachments
    documents = ("doc_document", {
                        "key": "doc_id",
                        "match": "doc_id",
                        "fields": {"name": ("set", ANONYMOUS),
                                   "file": "remove",
                                   "url": "remove",
                                   "comments": "remove",
                                   },
                        "delete": True,
                        })

    # Rule for direct offers (from the offerer perspective)
    direct_offers = ("br_direct_offer", {
                        "key": "offer_id",
                        "match": "id",
                        "delete": True,
                        })

    # Rules for user accounts
    account = ("auth_user", {
                        "key": "id",
                        "match": "user_id",
                        "fields": {"id": auth.s3_anonymise_roles,
                                   "first_name": ("set", "-"),
                                   "last_name": "remove",
                                   "email": anonymous_code,
                                   "organisation_id": "remove",
                                   "password": auth.s3_anonymise_password,
                                   "deleted": ("set", True),
                                   },
                        })

    # Rules
    rules = [
        # Rules to remove PID from person record and case file
        {"name": "default",
         "title": "Names, IDs, Reference Numbers, Contact Information, Addresses",

         "fields": {"first_name": ("set", ANONYMOUS),
                    "last_name": ("set", ANONYMOUS),
                    "pe_label": anonymous_id,
                    "date_of_birth": s3db.br_obscure_dob,
                    "comments": "remove",
                    },

         "cascade": [("br_case", {
                        "key": "person_id",
                        "match": "id",
                        "fields": {"comments": "remove",
                                   },
                        "cascade": [documents,
                                    ],
                        }),
                     ("pr_contact", {
                        "key": "pe_id",
                        "match": "pe_id",
                        "fields": {"contact_description": "remove",
                                   "value": ("set", ""),
                                   "comments": "remove",
                                   },
                        "delete": True,
                        }),
                     ("pr_contact_emergency", {
                        "key": "pe_id",
                        "match": "pe_id",
                        "fields": {"name": ("set", ANONYMOUS),
                                   "relationship": "remove",
                                   "phone": "remove",
                                   "comments": "remove",
                                   },
                        "delete": True,
                        }),
                    ("pr_address", {
                        "key": "pe_id",
                        "match": "pe_id",
                        "fields": {"location_id": anonymous_address,
                                   "comments": "remove",
                                   },
                        }),
                    ("pr_person_details", {
                        "key": "person_id",
                        "match": "id",
                        "fields": {"education": "remove",
                                   "occupation": "remove",
                                   },
                        }),
                    ("pr_image", {
                        "key": "pe_id",
                        "match": "pe_id",
                        "fields": {"image": "remove",
                                   "url": "remove",
                                   "description": "remove",
                                   },
                        "delete": True,
                        }),
                    ("hrm_human_resource", {
                        "key": "person_id",
                        "match": "id",
                        "fields": {"status": ("set", 2),
                                   "site_id": "remove",
                                   "comments": "remove",
                                   },
                        }),
                     ],
         },

        # Rules to remove PID from activities and offers
        {"name": "activities",
         "title": "Needs Reports and Offers of Assistance",
         "cascade": [("br_case_activity", {
                        "key": "person_id",
                        "match": "id",
                        "fields": {"location_id": anonymous_address,
                                   "subject": ("set", ANONYMOUS),
                                   "need_details": "remove",
                                   "activity_details": "remove",
                                   "outcome": "remove",
                                   "comments": "remove",
                                   "status_id": ("set", activity_closed),
                                   },
                        "cascade": [documents,
                                    ],
                        }),
                     ("br_assistance_offer", {
                        "key": "pe_id",
                        "match": "pe_id",
                        "fields": {"name": ("set", ANONYMOUS),
                                   "description": "remove",
                                   "capacity": "remove",
                                   "location_id": anonymous_address,
                                   "contact_name": "remove",
                                   "contact_phone": "remove",
                                   "contact_email": "remove",
                                   "availability": ("set", "RTD"),
                                   "comments": "remove",
                                   },
                        "cascade": [direct_offers,
                                    ],
                        }),
                     ],
         },

        # Rules to unlink and remove user account
        {"name": "account",
         "title": "User Account",
         "cascade": [("pr_person_user", {
                        "key": "pe_id",
                        "match": "pe_id",
                        "cascade": [account,
                                    ],
                        "delete": True,
                        }),
                     ],
         },
        ]

    return rules
