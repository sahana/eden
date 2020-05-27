# -*- coding: utf-8 -*-

from uuid import uuid4

from gluon import current

# -----------------------------------------------------------------------------
def rlp_obscure_dob(record_id, field, value):
    """
        Helper to obscure a date of birth; maps to the first day of
        the quarter, thus retaining the approximate age for statistics

        @param record_id: the pr_address record ID
        @param field: the location_id Field
        @param value: the location_id

        @return: the new date
    """

    if value:
        month = int((value.month - 1) / 3) * 3 + 1
        value = value.replace(month=month, day=1)

    return value

# -----------------------------------------------------------------------------
def rlp_decline_delegation(record_id, field, value):
    """
        Decline all requested deployments when anonymizing the volunteer

        @param record_id: the pr_address record ID
        @param field: the location_id Field
        @param value: the location_id

        @return: the new status
    """

    return "DECL" if value == "REQ" else value

# -----------------------------------------------------------------------------
def rlp_volunteer_anonymize():
    """ Rules to anonymize a volunteer """

    ANONYMOUS = "-"

    # Helper to produce an anonymous ID (pe_label)
    anonymous_id = lambda record_id, f, v: "NN%s" % uuid4().hex[-8:].upper()
    anonymous_code = lambda record_id, f, v: uuid4().hex

    # Rules for delegation messages
    notifications = ("hrm_delegation_message", {"key": "delegation_id",
                                                "match": "id",
                                                "fields": {"recipient": "remove",
                                                           "subject": "remove",
                                                           "message": "remove",
                                                           },
                                                "delete": True,
                                                })

    # Rules for delegation notes
    notes = ("hrm_delegation_note", {"key": "delegation_id",
                                     "match": "id",
                                     "fields": {"note": "remove",
                                                },
                                     "delete": True,
                                     })

    # Rules for user accounts
    auth = current.auth
    account = ("auth_user", {"key": "id",
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

    rules = [# Remove identity of volunteer
             {"name": "default",
              "title": "Names, IDs, Contact Information, Addresses",
              "fields": {"first_name": ("set", ANONYMOUS),
                         "last_name": ("set", ANONYMOUS),
                         "pe_label": anonymous_id,
                         "date_of_birth": rlp_obscure_dob,
                         "comments": "remove",
                         },
              "cascade": [("pr_contact", {"key": "pe_id",
                                          "match": "pe_id",
                                          "fields": {"contact_description": "remove",
                                                     "value": ("set", ""),
                                                     "comments": "remove",
                                                     },
                                          "delete": True,
                                          }),
                          ("pr_contact_emergency", {"key": "pe_id",
                                                    "match": "pe_id",
                                                    "fields": {"name": ("set", ANONYMOUS),
                                                               "relationship": "remove",
                                                               "phone": "remove",
                                                               "comments": "remove",
                                                               },
                                                    "delete": True,
                                                    }),
                          ("pr_address", {"key": "pe_id",
                                          "match": "pe_id",
                                          "fields": {"location_id": current.s3db.pr_address_anonymise,
                                                     "comments": "remove",
                                                     },
                                          }),
                          ("pr_person_details", {"key": "person_id",
                                                 "match": "id",
                                                 "fields": {"occupation": "remove",
                                                            "alias": ("set", "***"),
                                                            },
                                                 }),
                          ("hrm_human_resource", {"key": "person_id",
                                                  "match": "id",
                                                  "fields": {"status": ("set", 2),
                                                             "site_id": "remove",
                                                             "comments": "remove",
                                                             },
                                                  }),
                          ("hrm_competency", {"key": "person_id",
                                              "match": "id",
                                              "fields": {"comments": "remove",
                                                         },
                                              }),
                          ],
              },

             # Remove all free texts from delegations
             {"name": "delegations",
              "title": "Deployment Comments, Notifications and Notes",
              "cascade": [("hrm_delegation", {"key": "person_id",
                                              "match": "id",
                                              "fields": {"comments": "remove",
                                                         "status": rlp_decline_delegation,
                                                         },
                                              "cascade": [notifications,
                                                          notes,
                                                          ],
                                              }),
                          ],
              },

             # Remove user account
             {"name": "account",
              "title": "User Account",
              "cascade": [("pr_person_user", {"key": "pe_id",
                                              "match": "pe_id",
                                              "cascade": [account,
                                                          ],
                                              "delete": True,
                                              }),
                          ],
              },
             ]

    return rules

# END =========================================================================
