# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Cidadanía Coop.
# Written by: Oscar Carballal Prego <info@oscarcp.com>
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

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

class Space(models.Model):

    """
    Basic spaces model.
    """
    name = models.CharField(_('Name'), max_length=100, unique=True)
    description = models.TextField(_('Description'))
    date = models.DateTimeField(auto_now_add=True)

    logo = models.ImageField(verbose_name=_('Logotype'),
                             upload_to='spaces/logos')
    banner = models.ImageField(verbose_name=_('Banner'),
                               upload_to='spaces/banners')
    #theme = models.CharField(_('Theme'), m)
    
    # Modules
    mod_debate = models.BooleanField(_('Debate module'))
    mod_proposals = models.BooleanField(_('Proposals module'))
    mod_news = models.BooleanField(_('News module'))
    mod_cal = models.BooleanField(_('Calendar module'))
    mod_docs = models.BooleanField(_('Documents module'))

    def __unicode__(self):
        return self.name

class Entity(models.Model):

    """
    This models stores the name of the entities responsible
    for the creation of the space.
    """
    name = models.CharField(_('Name'), max_length=100, unique=True)
    space = models.ForeignKey(Space)
    
    def __unicode__(self):
        return self.name
