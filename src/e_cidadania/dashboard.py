# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2012 Cidadania S. Coop. Galega
#
# This file is part of e-cidadania.
#
# e-cidadania is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# e-cidadania is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with e-cidadania. If not, see <http://www.gnu.org/licenses/>.

"""
This file was generated with the customdashboard management command and
contains the class for the main dashboard.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'e_cidadania.dashboard.CustomIndexDashboard'
"""

from django.utils.translation import ugettext_lazy as _

from grappelli.dashboard import modules, Dashboard
from grappelli.dashboard.utils import get_admin_site_name


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """
    
    def init_with_context(self, context):
        
        # append a group for "Administration" & "Applications"
        #self.children.append(modules.Group(
        #    _('Users & Groups'),
        #    column=1,
        #    collapsible=True,
        #    children = [
        #        modules.ModelList(
        #            _('Users'),
        #            column=1,
        #            css_classes=('collapse closed',),
        #            models=('django.contrib.auth.models.User',
        #                    'django.contrib.auth.models.Group',
        #                    'e_cidadania.apps.accounts.models.UserProfile',)
        #        ),
        #       modules.AppList(
        #            _('Applications'),
        #            column=1,
        #            css_classes=('collapse closed',),
        #            exclude=('django.contrib.*',),
        #        ),
        #    ]
        #))
        
        
        
        # append an app list module for "Applications"
        self.children.append(modules.ModelList(
            _('Users'),
            column=1,
            collapsible=False,
            models=('django.contrib.auth.models.User',
                    'e_cidadania.apps.accounts.models.UserProfile',
                    'django.contrib.auth.models.Group',
                    'django.contrib.sites.*',)
        ))
        
        self.children.append(modules.AppList(
            _('Applications'),
            collapsible=False,
            column=1,
            exclude=('django.contrib.*',
                     'e_cidadania.apps.accounts.*',),
        ))
        
        # append a feed module
        self.children.append(modules.Feed(
            _('Latest News'),
            column=2,
            feed_url='http://www.djangoproject.com/rss/weblog/',
            limit=5
        ))
        
        # append another link list module for "media".
        self.children.append(modules.LinkList(
            _('Media Management'),
            column=2,
            children=[
                {
                    'title': _('FileBrowser'),
                    'url': '/admin/filebrowser/browse/',
                    'external': False,
                },
            ]
        ))
        
        # append another link list module for "support".
        self.children.append(modules.LinkList(
            _('e-cidadania Support'),
            column=2,
            children=[
                {
                    'title': _('Documentation'),
                    'url': 'http://docs.ecidadania.org',
                    'external': True,
                },
                {
                    'title': _('Wiki'),
                    'url': 'http://dev.ecidadania.org',
                    'external': True,
                },
                {
                    'title': _('Translations'),
                    'url': '../rosetta',
                    'external': True,
                },
            ]
        ))
        
        self.children.append(modules.LinkList(
            _('Thirdparty Support'),
            column=2,
            children=[
                {
                    'title': _('Django Documentation'),
                    'url': 'http://docs.djangoproject.com/',
                    'external': True,
                },
                {
                    'title': _('Grappelli Documentation'),
                    'url': 'http://packages.python.org/django-grappelli/',
                    'external': True,
                },
                {
                    'title': _('python-dateutil Documentation'),
                    'url': 'http://labix.org/python-dateutil',
                    'external': True,
                },
            ]
        ))
        
        # append another link list module for "support".
        self.children.append(modules.LinkList(
            _('e-cidadania source code'),
            column=2,
            children=[
                {
                    'title': _('GitHub'),
                    'url': 'http://github.com/oscarcp/e-cidadania',
                    'external': True,
                },
                {
                    'title': _('Gitorious'),
                    'url': 'http://gitorious.org/e-cidadania',
                    'external': True,
                },
                {
                    'title': _('Repo.or.vz (Mirror)'),
                    'url': 'http://repo.or.cz/w/e_cidadania.git',
                    'external': True,
                },
            ]
        ))
        
        # append a recent actions module
        self.children.append(modules.RecentActions(
            _('Recent Actions'),
            limit=5,
            collapsible=False,
            column=3,
        ))


