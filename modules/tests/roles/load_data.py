from tests.roles.create_role_test_data import create_role_test_data

# Define Organisations
orgs = ["Org-A",
        "Org-B",
        "Org-C",
        ]
branches = [None,
            "Branch-A"
            ]

create_role_test_data(orgs, branches)
