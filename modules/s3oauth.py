# -*- coding: utf-8 -*-

""" Authentication via Facebook & Google

    @requires: U{B{I{gluon}} <http://web2py.com>}

    @copyright: (c) 2010-2012 Sahana Software Foundation
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

__all__ = ["FaceBookAccount",
           "GooglePlusAccount",
           ]

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

# =============================================================================
class FaceBookAccount(OAuthAccount):
    """ OAuth implementation for FaceBook """

    AUTH_URL = "https://graph.facebook.com/oauth/authorize"
    TOKEN_URL = "https://graph.facebook.com/oauth/access_token"

    # -------------------------------------------------------------------------
    def __init__(self):

        from facebook import GraphAPI, GraphAPIError

        self.GraphAPI = GraphAPI
        self.GraphAPIError = GraphAPIError
        g = dict(GraphAPI=GraphAPI,
                 GraphAPIError=GraphAPIError,
                 request=current.request,
                 response=current.response,
                 session=current.session,
                 HTTP=HTTP)
        client = current.auth.settings.facebook
        OAuthAccount.__init__(self, g, client["id"], client["secret"],
                              self.AUTH_URL, self.TOKEN_URL,
                              scope="email,user_about_me,user_location,user_photos,user_relationships,user_birthday,user_website,create_event,user_events,publish_stream")
        self.graph = None

    # -------------------------------------------------------------------------
    def login_url(self, next="/"):
        """ Overriding to produce a different redirect_uri """

        if not self.accessToken():
            request = current.request
            session = current.session
            if not request.vars.code:
                session.redirect_uri = "%s/%s/default/facebook/login" % \
                    (current.deployment_settings.get_base_public_url(),
                     request.application)
                data = dict(redirect_uri=session.redirect_uri,
                            response_type="code",
                            client_id=self.client_id)
                if self.args:
                    data.update(self.args)
                auth_request_url = "%s?%s" % (self.auth_url,
                                              urllib.urlencode(data))
                raise HTTP(307,
                           "You are not authenticated: you are being redirected to the <a href='%s'> authentication server</a>" % \
                                auth_request_url,
                           Location=auth_request_url)
            else:
                session.code = request.vars.code
                self.accessToken()
                #return session.code
        return next

    # -------------------------------------------------------------------------
    def get_user(self):
        """ Returns the user using the Graph API. """

        if not self.accessToken():
            return None

        if not self.graph:
            self.graph = self.GraphAPI((self.accessToken()))

        user = None
        try:
            user = self.graph.get_object_c("me")
        except self.GraphAPIError:
            current.session.token = None
            self.graph = None

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
                _user = dict(first_name = user.get("first_name", ""),
                             last_name = user.get("last_name", ""),
                             facebookid = user["id"],
                             facebook = user.get("username", user["id"]),
                             email = user["email"],
                             password = existent.password
                            )
                return _user
            else:
                # b = user["birthday"]
                # birthday = "%s-%s-%s" % (b[-4:], b[0:2], b[-7:-5])
                # if 'location' in user:
                #     session.flocation = user['location']
                #session["is_new_from"] = "facebook"
                auth.s3_send_welcome_email(user)
                # auth.initial_user_permission(user)  # Called on profile page
                _user = dict(first_name = user.get("first_name", ""),
                             last_name = user.get("last_name", ""),
                             facebookid = user["id"],
                             facebook = user.get("username", user["id"]),
                             nickname = IS_SLUG()(user.get("username", "%(first_name)s-%(last_name)s" % user) + "-" + user['id'][:5])[0],
                             email = user["email"],
                             # birthdate = birthday,
                             about = user.get("bio", ""),
                             website = user.get("website", ""),
                             # gender = user.get("gender", "Not specified").title(),
                             photo_source = 3,
                             tagline = user.get("link", ""),
                             registration_type = 2,
                            )
                return _user

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
    def __init__(self):

        request = current.request
        settings = current.deployment_settings

        g = dict(request=request,
                 response=current.response,
                 session=current.session,
                 HTTP=HTTP)

        client = current.auth.settings.google

        self.globals = g
        self.client = client
        self.client_id = client["id"]
        self.client_secret = client["secret"]
        self.auth_url = self.AUTH_URL
        self.args = dict(
                scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
                user_agent = "google-api-client-python-plus-cmdline/1.0",
                xoauth_displayname = settings.get_system_name(),
                response_type = "code",
                redirect_uri = "%s/%s/default/google/login" % \
                    (settings.get_base_public_url(),
                     request.application),
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

        if session.token and session.token.has_key("expires"):
            expires = session.token["expires"]
            # reuse token until expiration
            if expires == 0 or expires > time.time():
                return session.token["access_token"]
        if session.code:
            data = dict(client_id = self.client_id,
                        client_secret = self.client_secret,
                        redirect_uri = self.args["redirect_uri"],
                        code = session.code,
                        grant_type = "authorization_code",
                        scope = "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile")

            # if self.args:
            #     data.update(self.args)
            open_url = None
            opener = self.__build_url_opener(self.TOKEN_URL)
            try:
                open_url = opener.open(self.TOKEN_URL, urllib.urlencode(data))
            except urllib2.HTTPError, e:
                raise Exception(e.read())
            finally:
                del session.code # throw it away

            if open_url:
                try:
                    session.token = json.loads(open_url.read())
                    session.token["expires"] = int(session.token["expires_in"]) + \
                        time.time()
                finally:
                    opener.close()
                return session.token["access_token"]

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
                data = dict(redirect_uri=session.redirect_uri,
                            response_type="code",
                            client_id=self.client_id)
                if self.args:
                    data.update(self.args)
                auth_request_url = self.auth_url + "?" + urllib.urlencode(data)
                raise HTTP(307,
                           "You are not authenticated: you are being redirected to the <a href='" + auth_request_url + "'> authentication server</a>",
                           Location=auth_request_url)
            else:
                session.code = request.vars.code
                self.accessToken()
                #return session.code
        return next

    # -------------------------------------------------------------------------
    def get_user(self):
        """ Returns the user using the Graph API. """

        if not self.accessToken():
            return None

        session = current.session
        user = None
        try:
            user = self.call_api()
        except Exception, e:
            session.token = None

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
                _user = dict(
                            #first_name = user.get("given_name", user["name"]),
                            #last_name = user.get("family_name", user["name"]),
                            googleid = user["id"],
                            email = user["email"],
                            password = existent.password
                            )
                return _user
            else:
                # b = user["birthday"]
                # birthday = "%s-%s-%s" % (b[-4:], b[0:2], b[-7:-5])
                # if "location" in user:
                #     session.flocation = user["location"]
                #session["is_new_from"] = "google"
                auth.s3_send_welcome_email(user)
                _user = dict(
                            first_name = user.get("given_name",
                                                  user["name"].split()[0]),
                            last_name = user.get("family_name",
                                                 user["name"].split()[-1]),
                            googleid = user["id"],
                            nickname = "%(first_name)s-%(last_name)s-%(id)s" % \
                                dict(first_name=user["name"].split()[0].lower(),
                                     last_name=user["name"].split()[-1].lower(),
                                     id=user["id"][:5]),
                            email = user["email"],
                            # birthdate = birthday,
                            website = user.get("link", ""),
                            # gender = user.get("gender", "Not specified").title(),
                            photo_source = 6 if user.get("picture", None) else 2,
                            googlepicture = user.get("picture", ""),
                            registration_type = 3,
                            )
                return _user

    # -------------------------------------------------------------------------
    def call_api(self):
        """
        """

        api_return = urllib.urlopen("https://www.googleapis.com/oauth2/v1/userinfo?access_token=%s" % \
                                    self.accessToken())
        user = json.loads(api_return.read())
        if user:
            return user
        else:
            self.session.token = None
            return None

# END =========================================================================
