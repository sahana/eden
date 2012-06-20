from gluon import current

# Data for the Organisation resource
current.data["organisation"] = [
    [
        # 1st field used to check whether record already exists
        # & for organisation_id lookups
        ("name", "Romanian Food Assistance Association (Test)"),
        ("acronym", "RFAAT"),
        ("organisation_type_id", "Institution", "option"),
        ("region", "Europe"),
        # Whilst the short  form is accepted by the DB, our validation routine needs the full form
        ("website", "http://www.rfaat.com"),
        ("comments", "This is a Test Organization"),
    ],
]

# END =========================================================================