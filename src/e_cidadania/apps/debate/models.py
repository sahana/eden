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

class Column(models.Model):
    """
    Debate column object. The debate table is done mixing columns and rows. The column
    object is linked to the debate, but with no preferrable order.
    
    .. versionadded:: 0.1b
    """
    criteria = models.CharField(_('Criteria'), max_length=100, blank=True, null=True)
    debate = models.ForeignKey(Debate)
    date = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.criteria + "(" + str(self.debate) + ")"
    
class Row(models.Model):
    """
    Row object for the debate system.  Thw row object works exactly like the
    column. It's associated to the debate in no preferred order.
    
    .. versionadded:: 0.1b
    """
    criteria = models.CharField(_('Criteria'), max_length=100, blank=True, null=True)
    debate = models.ForeignKey(Debate)
    date = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.criteria + "(" + str(self.debate) + ")"
           
    
class Note(models.Model):

    """
    The most important object in every debate, the message. It has a coordinates
    value to determine the position of the note in its debate.
    
    .. versionadded:: 0.1b
    """
    column = models.ForeignKey(Column)
    row = models.ForeignKey(Row)
    debate = models.ForeignKey(Debate)
    title = models.CharField(_('Title'), max_length=60, blank=True, null=True)
    message = models.TextField(_('Message'), max_length=100, null=True, blank=True)

    pub_date = models.DateTimeField(auto_now_add=True)
    pub_author = models.ForeignKey(User, null=True, blank=True)
    
    def __unicode__(self):
        return self.message
