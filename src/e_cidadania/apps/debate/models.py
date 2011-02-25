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
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from tagging.fields import TagField
from tagging.models import Tag

class Debate(models.Model):

    """
    Very basic outline of a debate, or group of sections.
    """
    title = models.CharField(_('Title'), max_length=200)
    objectives = models.CharField(_('Objectives'), max_length=100)
    description = models.TextField(_('Description'))
    
    pub_date = models.DateTimeField(auto_now_add=True)
    pub_author = models.ForeignKey(User)
    
    def __unicode__(self):
        return self.title
    
class Phases(models.Model):

    """
    Basic outline of sections, or phases of the debate.
    """
    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'))
    tags = TagField()

    debate = models.ForeignKey(Debate)
    
    def __unicode__(self):
        return self.debate.name + ' / ' + self.title

class Message(models.Model):

    """
    The important unit, the message.
    """
    message = models.CharField(_('Message'), max_length=100)
    explanation = models.CharField(_('Explanation'), max_length=100,
                                   null=True, blank=True)

    section = models.ForeignKey(Phases)
    pub_date = models.DateTimeField(auto_now_add=True)
    pub_author = models.ForeignKey(User)
    
    def __unicode__(self):
        return self.message
        
#class Matrix(modes.Model)
