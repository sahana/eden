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

"""
This file contains all the data models for the debate module.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from e_cidadania.apps.tagging.fields import TagField
from e_cidadania.apps.tagging.models import Tag
from e_cidadania.apps.spaces.models import Space

class Debate(models.Model):

    """
    Debate object. In every space there can be unlimited debates, each one of
    them holds all the related notes. Debates are filtered by space. Start/End
    dates are gathered adding the phases dates.
    
    .. versionadded:: 0.1b
    """
    title = models.CharField(_('Title'), max_length=200, unique=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    scope = models.CharField(_('Scope'), blank=True, null=True, max_length=100)
    columns = models.CharField(_('X Values'), max_length=300, blank=True, null=True)
    
    space = models.ForeignKey(Space, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    date_mod = models.DateTimeField(_('Last update'), auto_now=True)
    author = models.ForeignKey(User, blank=True, null=True)
    
    def __unicode__(self):
        return self.title
        
    @models.permalink
    def get_absolute_url(self):
        return ('view-debate', (), {
            'space_name': self.space.url,
            'debate_id': str(self.id)})


class Row(models.Model):
    """
    """
    criteria = models.CharField(_('Criteria'), max_length=100, blank=True, null=True)
    debate = models.ForeignKey(Debate)
    date = models.DateTimeField(auto_now_add=True)
    sortables = models.CharField(_('Sortables'), max_length=100, blank=True, null=True)
    
    def __unicode__(self):
        return self.criteria + "(" + str(self.debate) + ")"
           
    
class Note(models.Model):

    """
    The most important object in every debate, the message. It has a coordinates
    value to determine the position of the note in its debate.
    
    .. versionadded:: 0.1b
    """
    debate = models.IntegerField('Debate', blank=True, null=True)
    noteid = models.CharField(_('Note div ID'), max_length=100, blank=True, null=True)
    title = models.CharField(_('Title'), max_length=60, blank=True, null=True)
    message = models.TextField(_('Message'), max_length=100, null=True, blank=True)
    parent = models.CharField(_('Parent TD or DIV'), max_length=200, blank=True, null=True)

    pub_date = models.DateTimeField(auto_now_add=True)
    pub_author = models.ForeignKey(User, null=True, blank=True)
    
    def __unicode__(self):
        return self.message
        
#class Matrix(modes.Model)
