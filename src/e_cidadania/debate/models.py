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

class Debate(models.Model):

    """
    Very basic outline of a debate, or group of sections.
    """
    name = models.CharField('Nombre: ', max_length=200)
    pub_date = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.name
    
class Section(models.Model):

    """
    basic outline of sections, or gropus of messages.
    """
    name = models.CharField('Nombre: ', max_length=200)
    debate = models.ForeignKey(Debate)
    
    def __unicode__(self):
        return self.debate.name + ' / ' + self.name

class Message(models.Model):

    """
    The important unit, the message.
    """
    name = models.CharField('Nombre: ', max_length=200)
    description = models.TextField()
    section = models.ForeignKey(Section)
    pub_date = models.DateTimeField(auto_now_add=True)
    pub_author = models.ForeignKey(User)
    
    def __unicode__(self):
        return self.name
