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
    """ Custom Application Main Menu """

    # -------------------------------------------------------------------------
    @classmethod
    def menu(cls):

        image = "/%s/static/themes/CRMT/img/logos/sahana-sunflower.png" % \
            current.request.application
        title_area = H1(A(IMG(_width="42",
                           _height="40",
                           _alt="Sahana Foundation",
                           _src=image,
                           ),
                          "Sahana",
                          _href=URL(c="default", f="index"),
                          ))

        main_menu = MM(title_area=title_area)(

            # Modules-menu, align-left
            cls.menu_modules(),

            # Service menus, align-right
            # Note: always define right-hand items in reverse order!
            cls.menu_lang(right=True),
            cls.menu_register(right=True),
            cls.menu_auth(right=True),
        )
        return main_menu

    # -------------------------------------------------------------------------
    @classmethod
    def menu_modules(cls):
        """ Custom Modules Menu """

        return [
            # In title_area
            #MM("Sahana"),
            MM("Find", link=False)(
                MM("People", c="pr", f="person", m="summary", always_display=True),
                MM("Organizations", c="org", f="organisation", m="summary"),
                MM("Activities", c="project", f="activity", m="summary",
                   always_display=True),
                MM("Points", c="gis", f="poi", m="summary",
                   vars={"~.location_id$gis_feature_type": 1},
                   always_display=True),
                MM("Routes", c="gis", f="poi", m="summary",
                   vars={"~.location_id$gis_feature_type": 2},
                   always_display=True),
                MM("Areas", c="gis", f="poi", m="summary",
                   vars={"~.location_id$gis_feature_type": 3},
                   always_display=True),
            ),
            MM("Add", link=False)(
                MM("Person", c="pr", f="person", args="create",
                   always_display=True),
                MM("Organization", c="org", f="organisation", args="create"),
                MM("Activity", c="project", f="activity", args="create",
                   always_display=True),
                MM("Point", c="gis", f="poi", args="create",
                   vars={"~.location_id$gis_feature_type": 1},
                   always_display=True),
                MM("Route", c="gis", f="poi", args="create",
                   vars={"~.location_id$gis_feature_type": 2},
                   always_display=True),
                MM("Area", c="gis", f="poi", args="create",
                   vars={"~.location_id$gis_feature_type": 3},
                   always_display=True),
            ),
            MM("Share", link=False)(
                MM("Maps", c="gis", f="config", args="datalist", always_display=True),
                MM("Stories", c="cms", f="post", args="datalist", always_display=True),
            ),
            MM("Map", c="gis", f="index", always_display=True),
        ]

    # -------------------------------------------------------------------------
    @classmethod
    def menu_auth(cls, **attr):
        """ Auth Menu """

        auth = current.auth

        if not auth.is_logged_in():
            request = current.request
            login_next = URL(args=request.args, vars=request.get_vars)
            if request.controller == "default" and \
               request.function == "user" and \
               "_next" in request.get_vars:
                login_next = request.get_vars["_next"]

            menu_auth = MM("Log in", c="default", f="user", m="login",
                           _id="auth_menu_login",
                           vars=dict(_next=login_next), **attr)
        else:
            # Logged-in
            user = auth.user

            greeting = "Welcome, %s!" % user.first_name
            if user.org_group_id:
                menu_auth = MM(greeting, c="org", f="group",
                               args=[user.org_group_id, "dashboard"],
                               translate=False,
                               _id="auth_menu_email",
                               **attr)
            else:
                # User is not associated with a coalition
                menu_auth = MM(greeting,
                               link=False,
                               translate=False,
                               _id="auth_menu_email",
                               **attr)

            menu_auth(MM("Your Maps", c="gis", f="config",
                          args="datalist",
                          vars={"~.pe_id__belongs": user.pe_id}),
                      MM("Admin Users", c="admin", f="user"),
                      MM("Edit Profile", c="default", f="user", m="profile"),
                      MM("Change Password", c="default", f="user", m="change_password"),
                      MM("Logout", c="default", f="user", m="logout", _id="auth_menu_logout"),
                      )

        return menu_auth

    # -------------------------------------------------------------------------
    @classmethod
    def menu_register(cls, **attr):
        """ Registration Menu """

        if current.auth.is_logged_in():
            return None

        #self_registration = current.deployment_settings.get_security_registration_visible()

        request = current.request
        login_next = URL(args=request.args, vars=request.vars)
        if request.controller == "default" and \
           request.function == "user" and \
           "_next" in request.get_vars:
            login_next = request.get_vars["_next"]

        menu_auth = MM("Register", c="default", f="user", m="register",
                       vars=dict(_next=login_next),
                       #check=self_registration
                       **attr)

        return menu_auth

    # -------------------------------------------------------------------------
    @classmethod
    def menu_lang(cls, **attr):
        """ Language menu """

        if current.auth.is_logged_in():
            return None

        #settings = current.deployment_settings
        #if not settings.get_L10n_display_toolbar():
        #    return None

        request = current.request
        s3 = current.response.s3
        languages = s3.l10n_languages
        current_language = s3.language

        menu_lang = MM("Language", **attr)
        for language in languages:
            if language == current_language:
                _class = "active"
            else:
                _class = ""
            menu_lang.append(MM(languages[language], r=request,
                                translate=False,
                                selectable=False,
                                vars={"_language":language},
                                ltr=True,
                                # @ToDo: Fix this getting passed inside
                                # 'active' class gets applied to item.selected
                                _class=_class,
                                ))
        return menu_lang

# END =========================================================================
