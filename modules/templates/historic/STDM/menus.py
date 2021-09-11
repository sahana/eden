# -*- coding: utf-8 -*-

from gluon import *
from s3 import *
from s3layouts import *
try:
    from .layouts import *
except ImportError:
    pass
import s3menus as default

# =============================================================================
class S3MainMenu(default.S3MainMenu):
    """
        Custom Application Main Menu:

        The main menu consists of several sub-menus, each of which can
        be customised separately as a method of this class. The overall
        composition of the menu is defined in the menu() method, which can
        be customised as well:

        Function        Sub-Menu                Access to (standard)

        menu_modules()  the modules menu        the Eden modules
        menu_gis()      the GIS menu            GIS configurations
        menu_admin()    the Admin menu          System/User Administration
        menu_lang()     the Language menu       Selection of the GUI locale
        menu_auth()     the User menu           Login, Logout, User Profile
        menu_help()     the Help menu           Contact page, About page

        The standard uses the MM layout class for main menu items - but you
        can of course use a custom layout class which you define in layouts.py.

        Additional sub-menus can simply be defined as additional functions in
        this class, and then be included in the menu() method.

        Each sub-menu function returns a list of menu items, only the menu()
        function must return a layout class instance.
    """

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        has_role = current.auth.s3_has_role
        if has_role("ADMIN"):

            return [homepage(),
                    M("Tenures", c="stdm", f="tenure"),
                    M("Gardens", c="stdm", f="garden"),
                    M("Parcels", c="stdm", f="parcel"),
                    M("Structures", c="stdm", f="structure"),
                    M("People", c="stdm", f="person"),
                    M("Groups", c="stdm", f="group"),
                    #homepage("gis"),
                    ]
            
        elif has_role("INFORMAL_SETTLEMENT"):
            locations = M("Structures", c="stdm", f="structure")

        elif has_role("RURAL_AGRICULTURE"):
            locations = M("Gardens", c="stdm", f="garden")

        elif has_role("LOCAL_GOVERNMENT"):
            locations = M("Parcels", c="stdm", f="parcel")

        else:
            # Unauthenticated
            locations = None

        return [homepage(),
                M("Tenures", c="stdm", f="tenure"),
                locations,
                M("People", c="stdm", f="person"),
                M("Groups", c="stdm", f="group"),
                #homepage("gis"),
                ]

# =============================================================================
class S3OptionsMenu(default.S3OptionsMenu):
    """
        Custom Controller Menus

        The options menu (left-hand options menu) is individual for each
        controller, so each controller has its own options menu function
        in this class.

        Each of these option menu functions can be customised separately,
        by simply overriding (re-defining) the default function. The
        options menu function must return an instance of the item layout.

        The standard menu uses the M item layout class, but you can of
        course also use any other layout class which you define in
        layouts.py (can also be mixed).

        Make sure additional helper functions in this class don't match
        any current or future controller prefix (e.g. by using an
        underscore prefix).
    """

    # -------------------------------------------------------------------------
    def gis(self):
        """ GIS Module """

        if current.request.function == "location":
            return super(S3OptionsMenu, self).stdm()
        else:
            return super(S3OptionsMenu, self).gis()

    # -------------------------------------------------------------------------
    @staticmethod
    def stdm():
        """ Social Tenure Domain Model """
        ADMIN = current.session.s3.system_roles.ADMIN
        has_role = current.auth.s3_has_role

        informal = lambda i: has_role("INFORMAL_SETTLEMENT")
        gov = lambda i: has_role("LOCAL_GOVERNMENT")
        rural = lambda i: has_role("RURAL_AGRICULTURE")

        return M(c="stdm")(
                    M("Administrative Units", c="gis", f="location",
                                              vars={"~.level__ne": None},
                      restrict=ADMIN)(
                        M("Create", m="create",
                                    vars={"~.level__ne": None}),
                    ),
                    #M("Spatial Units", c="gis", f="location",
                    #                   vars={"~.level": None})(
                    #    M("Create", m="create", vars={"~.level": None}),
                    #),
                    M("Gardens", f="garden",
                      check=rural)(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M("Parcels", f="parcel",
                      check=gov)(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M("Structures", f="structure",
                      check=informal)(
                        M("Create", m="create"),
                        M("Import", m="import"),
                    ),
                    M("Parties")(
                        M("People", f="person"),
                        M("Groups", f="group"),
                        M("Farmers", f="farmer", check=rural),
                        M("Planners", f="planner", check=gov),
                        M("Surveyors", f="surveyor", check=gov),
                    ),
                    M("Surveys", f="gov_survey", check=gov)(
                        M("Create", m="create"),
                    ),
                    M("Surveys", f="rural_survey", check=rural)(
                        M("Create", m="create"),
                    ),
                    M("Tenures", f="tenure")(
                        M("Create", m="create"),
                    ),
                    M("Lookup Lists", restrict=ADMIN)(
                        M("Disputes", f="dispute"),
                        M("Household Relations", f="group_member_role"),
                        M("Input Services", f="input_service"),
                        M("Land Uses", f="landuse"),
                        M("Officer Ranks", f="job_title"),
                        M("Ownership Types", f="ownership_type"),
                        M("Parcel Types", f="parcel_type"),
                        M("Socio-economic Impacts", f="socioeconomic_impact"),
                        M("Tenure Types", f="tenure_type"),
                    ),
                )

# END =========================================================================
