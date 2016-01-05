# -*- coding: utf-8 -*-

""" Authentication via Facebook & Google

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: (c) 2010-2016 Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("FaceBookAccount",
           "GooglePlusAccount",
           "HumanitarianIDAccount",
           )

import time
import urllib
import urllib2

try:
    import json # try stdlib (Python 2.6)
except ImportError:
    try:
        import simplejson as json # try external module
    except:
        import gluon.contrib.simplejson as json # fallback to pure-Python module

from gluon import current, HTTP, IS_SLUG
from gluon.contrib.login_methods.oauth20_account import OAuthAccount

REDIRECT_MSG = "You are not authenticated: you are being redirected " \
               "to the <a href='%s'> authentication server</a>"

# =============================================================================
class FaceBookAccount(OAuthAccount):
    """ OAuth implementation for FaceBook """

    AUTH_URL = "https://graph.facebook.com/oauth/authorize"
    TOKEN_URL = "https://graph.facebook.com/oauth/access_token"

    # -------------------------------------------------------------------------
    def __init__(self, channel):
        """
            Constructor

            @param channel: Facebook channel (Row) with API credentials:
                            {app_id=clientID, app_secret=clientSecret}
        """

        from facebook import GraphAPI, GraphAPIError

        self.GraphAPI = GraphAPI
        self.GraphAPIError = GraphAPIError

        scope = "email,user_about_me," \
                "user_location,user_photos," \
                "user_relationships,user_birthday,user_website," \
                "create_event,user_events,publish_stream"

        # Set the redirect URI to the default/facebook controller
        redirect_uri = "%s/%s/default/facebook/login" % \
                       (settings.get_base_public_url(), request.application)

        OAuthAccount.__init__(self,
                              client_id = channel.app_id,
                              client_secret = channel.app_secret,
                              auth_url = self.AUTH_URL,
                              token_url = self.TOKEN_URL,
                              scope = scope,
                              redirect_uri = redirect_uri,
                              )
        self.graph = None

    # -------------------------------------------------------------------------
    def login_url(self, next="/"):
        """ Overriding to produce a different redirect_uri """

        if not self.accessToken():

            request = current.request
            session = current.session

            if not request.vars.code:

                session.redirect_uri = self.args["redirect_uri"]

                data = {"redirect_uri": session.redirect_uri,
                        "response_type": "code",
                        "client_id": self.client_id,
                        }

                if self.args:
                    data.update(self.args)

                auth_request_url = "%s?%s" % (self.auth_url,
                                              urllib.urlencode(data),
                                              )
                raise HTTP(307,
                           REDIRECT_MSG % auth_request_url,
                           Location = auth_request_url,
                           )
            else:
                session.code = request.vars.code
                self.accessToken()

        return next

    # -------------------------------------------------------------------------
    def get_user(self):
        """ Returns the user using the Graph API. """

        token = self.accessToken()

        if not token:
            return None

        if not self.graph:
            self.graph = self.GraphAPI(token)

        user = None
        try:
            user = self.graph.get_object_c("me")
        except self.GraphAPIError:
            current.session.token = None
            self.graph = None

        user_dict = None

        if user:
            # Check if a user with this email has already registered
            #session = current.session
            #session.facebooklogin = True

            auth = current.auth
            table = auth.settings.table_user

            query = (table.email == user["email"])
            existent = current.db(query).select(table.id,
                                                table.password,
                                                limitby=(0, 1)).first()
            if existent:
                #session["%s_setpassword" % existent.id] = existent.password

                user_dict = {"first_name": user.get("first_name", ""),
                             "last_name": user.get("last_name", ""),
                             "facebookid": user["id"],
                             "facebook": user.get("username", user["id"]),
                             "email": user["email"],
                             "password": existent.password,
                             }

            else:
                # b = user["birthday"]
                # birthday = "%s-%s-%s" % (b[-4:], b[0:2], b[-7:-5])
                # if 'location' in user:
                #     session.flocation = user['location']
                #session["is_new_from"] = "facebook"

                auth.s3_send_welcome_email(user)

                user_dict = {"first_name": user.get("first_name", ""),
                             "last_name": user.get("last_name", ""),
                             "facebookid": user["id"],
                             "facebook": user.get("username", user["id"]),
                             "nickname": IS_SLUG()(user.get("username", "%(first_name)s-%(last_name)s" % user) + "-" + user['id'][:5])[0],
                             "email": user["email"],
                             #"birthdate": birthday,
                             "about": user.get("bio", ""),
                             "website": user.get("website", ""),
                             #"gender": user.get("gender", "Not specified").title(),
                             "photo_source": 3,
                             "tagline": user.get("link", ""),
                             "registration_type": 2,
                             }
        return user_dict

# =============================================================================
class GooglePlusAccount(OAuthAccount):
    """
        OAuth implementation for Google
        https://code.google.com/apis/console/
    """

    AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    TOKEN_URL = "https://accounts.google.com/o/oauth2/token"
    API_URL = "https://www.googleapis.com/oauth2/v1/userinfo"

    # -------------------------------------------------------------------------
    def __init__(self, channel):
        """
            Constructor

            @param channel: dict with Google API credentials:
                            {id=clientID, secret=clientSecret}
        """

        request = current.request
        settings = current.deployment_settings

        scope = "https://www.googleapis.com/auth/userinfo.email " \
                "https://www.googleapis.com/auth/userinfo.profile"
        user_agent = "google-api-client-python-plus-cmdline/1.0"

        # Set the redirect URI to the default/google controller
        redirect_uri = "%s/%s/default/google/login" % \
                       (settings.get_base_public_url(), request.application)

        OAuthAccount.__init__(self,
                              client_id = channel["id"],
                              client_secret = channel["secret"],
                              auth_url = self.AUTH_URL,
                              token_url = self.TOKEN_URL,
                              scope = scope,
                              user_agent = user_agent,
                              xoauth_displayname = settings.get_system_name(),
                              response_type = "code",
                              redirect_uri = redirect_uri,
                              approval_prompt = "force",
                              state = "google"
                              )
        self.graph = None

    # -------------------------------------------------------------------------
    def __build_url_opener(self, uri):
        """
            Build the url opener for managing HTTP Basic Authentication
        """

        # Create an OpenerDirector with support
        # for Basic HTTP Authentication...
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(None,
                                  uri,
                                  self.client_id,
                                  self.client_secret)
        opener = urllib2.build_opener(auth_handler)
        return opener

    # -------------------------------------------------------------------------
    def accessToken(self):
        """
            Return the access token generated by the authenticating server.

            If token is already in the session that one will be used.
            Otherwise the token is fetched from the auth server.
        """

        session = current.session

        token = session.token
        if token and "expires" in token:
            expires = token["expires"]
            # reuse token until expiration
            if expires == 0 or expires > time.time():
                return token["access_token"]

        code = session.code
        if code:
            data = {"client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.args["redirect_uri"],
                    "code": code,
                    "grant_type": "authorization_code",
                    "scope": self.args["scope"],
                    }

            open_url = None
            opener = self.__build_url_opener(self.token_url)
            try:
                open_url = opener.open(self.token_url, urllib.urlencode(data))
            except urllib2.HTTPError, e:
                raise Exception(e.read())
            finally:
                del session.code # throw it away

            if open_url:
                try:
                    token = json.loads(open_url.read())
                    token["expires"] = int(token["expires_in"]) + time.time()
                finally:
                    opener.close()
                session.token = token
                return token["access_token"]

        session.token = None
        return None

    # -------------------------------------------------------------------------
    def login_url(self, next="/"):
        """ Overriding to produce a different redirect_uri """

        if not self.accessToken():

            request = current.request
            session = current.session
            if not request.vars.code:

                session.redirect_uri = self.args["redirect_uri"]

                data = {"redirect_uri": session.redirect_uri,
                        "response_type": "code",
                        "client_id": self.client_id,
                        }

                if self.args:
                    data.update(self.args)

                auth_request_url = "%s?%s" % (self.auth_url,
                                              urllib.urlencode(data),
                                              )
                raise HTTP(307,
                           REDIRECT_MSG % auth_request_url,
                           Location = auth_request_url,
                           )
            else:
                session.code = request.vars.code
                self.accessToken()

        return next

    # -------------------------------------------------------------------------
    def get_user(self):
        """ Returns the user using the Graph API. """

        token = self.accessToken()
        if not token:
            return None

        session = current.session
        user = None
        try:
            user = self.call_api(token)
        except Exception, e:
            session.token = None

        user_dict = None
        if user:
            # Check if a user with this email has already registered
            #session.googlelogin = True

            auth = current.auth
            table = auth.settings.table_user
            query = (table.email == user["email"])
            existent = current.db(query).select(table.id,
                                                table.password,
                                                limitby=(0, 1)).first()
            if existent:
                #session["%s_setpassword" % existent.id] = existent.password

                user_dict = {#"first_name": user.get("given_name", user["name"]),
                             #"last_name": user.get("family_name", user["name"]),
                             "googleid": user["id"],
                             "email": user["email"],
                             "password": existent.password
                             }
            else:
                # b = user["birthday"]
                # birthday = "%s-%s-%s" % (b[-4:], b[0:2], b[-7:-5])
                # if "location" in user:
                #     session.flocation = user["location"]
                #session["is_new_from"] = "google"

                auth.s3_send_welcome_email(user)

                names = user.get("name", "").split()
                first = names[0] if len(names) > 0 else ""
                last = names[-1] if len(names) > 1 else ""

                user_dict = {"first_name": user.get("given_name", first),
                             "last_name": user.get("family_name", last),
                             "googleid": user["id"],
                             "nickname": "%(first_name)s-%(last_name)s-%(id)s" % \
                                                {"first_name": first.lower(),
                                                 "last_name": last.lower(),
                                                 "id": user["id"][:5],
                                                 },
                             "email": user["email"],
                             #"birthdate": birthday,
                             "website": user.get("link", ""),
                             #"gender": user.get("gender", "Not specified").title(),
                             "photo_source": 6 if user.get("picture", None) else 2,
                             "googlepicture": user.get("picture", ""),
                             "registration_type": 3,
                             }

        return user_dict

    # -------------------------------------------------------------------------
    @classmethod
    def call_api(cls, token):
        """
            Get the user info from the API

            @param token: the current access token
            @return: user info (dict)
        """

        api_response = urllib.urlopen("%s?access_token=%s" % (cls.API_URL, token))

        user = json.loads(api_response.read())
        if not user:
            user = None
            current.session.token = None

        return user

# =============================================================================
class HumanitarianIDAccount(OAuthAccount):
    """
        OAuth implementation for Humanitarian.ID
        https://docs.google.com/document/d/1-FGDOo2BkhuclxqHcBjCprywZKE_wA6IFTbrs8W26i0
    """

    AUTH_URL = "https://auth.humanitarian.id/oauth/authorize"
    TOKEN_URL = "https://auth.humanitarian.id/oauth/access_token"
    API_URL = "https://auth.humanitarian.id/account.json"

    # -------------------------------------------------------------------------
    def __init__(self, channel):
        """
            Constructor

            @param channel: dict with Humanitarian.ID API credentials:
                            {id=clientID, secret=clientSecret}
        """

        request = current.request
        settings = current.deployment_settings

        scope = "profile"

        # Set the redirect URI to the default/humanitarian_id controller
        redirect_uri = "%s/%s/default/humanitarian_id/login" % \
                       (settings.get_base_public_url(), request.application)

        OAuthAccount.__init__(self,
                              client_id = channel["id"],
                              client_secret = channel["secret"],
                              auth_url = self.AUTH_URL,
                              token_url = self.TOKEN_URL,
                              scope = scope,
                              response_type = "code",
                              redirect_uri = redirect_uri,
                              state = "humanitarian_id"
                              )
        self.graph = None

    # -------------------------------------------------------------------------
    def __build_url_opener(self, uri):
        """
            Build the url opener for managing HTTP Basic Authentication
        """

        # Create an OpenerDirector with support
        # for Basic HTTP Authentication...
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(None,
                                  uri,
                                  self.client_id,
                                  self.client_secret)
        opener = urllib2.build_opener(auth_handler)
        return opener

    # -------------------------------------------------------------------------
    def accessToken(self):
        """
            Return the access token generated by the authenticating server.

            If token is already in the session that one will be used.
            Otherwise the token is fetched from the auth server.
        """

        session = current.session

        token = session.token
        if token and "expires" in token:
            expires = token["expires"]
            # reuse token until expiration
            if expires == 0 or expires > time.time():
                return token["access_token"]

        code = session.code
        if code:
            data = {"client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.args["redirect_uri"],
                    "code": code,
                    "grant_type": "authorization_code",
                    "scope": self.args["scope"],
                    }

            open_url = None
            opener = self.__build_url_opener(self.token_url)
            try:
                open_url = opener.open(self.token_url, urllib.urlencode(data))
            except urllib2.HTTPError, e:
                raise Exception(e.read())
            finally:
                del session.code # throw it away

            if open_url:
                try:
                    token = json.loads(open_url.read())
                    token["expires"] = int(token["expires_in"]) + time.time()
                finally:
                    opener.close()
                session.token = token
                return token["access_token"]

        session.token = None
        return None

    # -------------------------------------------------------------------------
    def login_url(self, next="/"):
        """ Overriding to produce a different redirect_uri """

        if not self.accessToken():

            request = current.request
            session = current.session
            if not request.vars.code:

                session.redirect_uri = self.args["redirect_uri"]

                data = {"redirect_uri": session.redirect_uri,
                        "response_type": "code",
                        "client_id": self.client_id,
                        }

                if self.args:
                    data.update(self.args)

                auth_request_url = "%s?%s" % (self.auth_url,
                                              urllib.urlencode(data),
                                              )
                raise HTTP(307,
                           REDIRECT_MSG % auth_request_url,
                           Location = auth_request_url,
                           )
            else:
                session.code = request.vars.code
                self.accessToken()

        return next

    # -------------------------------------------------------------------------
    def get_user(self):
        """ Returns the user using the Graph API. """

        token = self.accessToken()
        if not token:
            return None

        session = current.session
        user = None
        try:
            user = self.call_api(token)
        except Exception, e:
            session.token = None

        user_dict = None
        if user:
            # Check if a user with this email has already registered
            #session.humanitarian_id_login = True

            auth = current.auth
            table = auth.settings.table_user
            query = (table.email == user["email"])
            existent = current.db(query).select(table.id,
                                                table.password,
                                                limitby=(0, 1)).first()
            if existent:
                #session["%s_setpassword" % existent.id] = existent.password

                user_dict = {#"first_name": user.get("name_given", ""),
                             #"last_name": user.get("name_family", ""),
                             "humanitarian_id": user["user_id"],
                             "email": user["email"],
                             "password": existent.password
                             }
            else:
                #session["is_new_from"] = "humanitarian_id"

                auth.s3_send_welcome_email(user)

                user_dict = {"first_name": user.get("name_given", ""),
                             "last_name": user.get("name_family", ""),
                             "humanitarian_id": user["user_id"],
                             "email": user["email"],
                             "registration_type": 3,
                             }

        return user_dict

    # -------------------------------------------------------------------------
    @classmethod
    def call_api(cls, token):
        """
            Get the user info from the API

            @param token: the current access token
            @return: user info (dict)
        """

        api_response = urllib.urlopen("%s?access_token=%s" % (cls.API_URL, token))

        user = json.loads(api_response.read())
        if not user:
            user = None
            current.session.token = None

        return user

# END =========================================================================
