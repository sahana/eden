from tests.roles.create_role_test_data import create_role_test_data

# Define Organisations
orgs = ["Org-A",
        "Org-B",
        "Org-C",
        "Org-D",
        "Org-E",
        ]
branches = [None,
            "Branch-A",
            "Branch-B",
            "Branch-C",
            "Branch-D",
            "Branch-E",
            ]

create_role_test_data(orgs, branches)
