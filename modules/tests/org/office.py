from gluon import current

# Data for the Office resource
current.data["office"] = [
    [
        # 1st field used to check whether record already exists
        ("name",
         "Bucharest RFAAT Centre (Test)",
        ),
        ("code",
         "12345678",
        ),
        ("organisation_id",
         # @ToDo: Something less fragile
         current.data["organisation"][0][0][1],
         "autocomplete",
        ),
        ("type",
         "Headquarters",
         "option",
        ),
        ("comments",
         "This is a Test Office",
        ),
        ("L0",
         "Romania",
         "gis_location"
        ),
        ("street",
         "102 Diminescu St",
         "gis_location"
        ),
        ("L3",
         "Bucharest",
         "gis_location"
        ),
    ],
]

# END =========================================================================
