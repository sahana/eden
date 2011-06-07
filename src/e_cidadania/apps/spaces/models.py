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
from django.contrib.auth.models import User, Group

class Space(models.Model):

    """     
    Spaces model. This model stores a "space" or "place". Every place has
    a minimum set of settings for customization.
    """
    name = models.CharField(_('Name'), max_length=100, unique=True)
    url = models.CharField(_('URL'), max_length=100, unique=True,
                            help_text=_('All lowercase. Obligatory. \
                                        Take in mind that this will be the\
                                        accesible URL'))
    description = models.TextField(_('Description'))
    date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, blank=True, null=True, verbose_name=_('Author'))

    logo = models.ImageField(upload_to='spaces/logos',
                             verbose_name=_('Logotype'),
                             help_text=_('100px width, 75px height'))
    banner = models.ImageField(upload_to='spaces/banners',
                               verbose_name=_('Banner'),
                               help_text=_('75px height'))
    authorized_groups = models.ManyToManyField(Group,
                                            verbose_name=_('Authorized groups'))
    public = models.BooleanField(_('Public space'))
    #theme = models.CharField(_('Theme'), m)
    
    # Modules
    mod_debate = models.BooleanField(_('Debate module'))
    mod_proposals = models.BooleanField(_('Proposals module'))
    mod_news = models.BooleanField(_('News module'))
    mod_cal = models.BooleanField(_('Calendar module'))
    mod_docs = models.BooleanField(_('Documents module'))

    class Meta:
        ordering = ['name']
        verbose_name = _('Space')
        verbose_name_plural = _('Spaces')
        get_latest_by = 'date'

    def __unicode__(self):
        return self.name

class Entity(models.Model):

    """
    This models stores the name of the entities responsible
    for the creation of the space.
    """
    name = models.CharField(_('Name'), max_length=100, unique=True)
    website = models.CharField(_('Website'), max_length=100, null=True, blank=True)
    logo = models.ImageField(upload_to='spaces/logos', verbose_name=_('Logo'),
                             blank = True, null = True)
    space = models.ForeignKey(Space, blank=True, null=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = _('Entity')
        verbose_name_plural = _('Entities')

    def __unicode__(self):
        return self.name
        
class Document(models.Model):

    """
    Document model
    """
    title = models.CharField(_('Document title'), max_length=100)
    space = models.ForeignKey(Space, blank=True, null=True)
    docfile = models.FileField(upload_to='spaces/documents/%Y/%m/%d')
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, verbose_name=_('Author'), blank=True,
                               null=True)
    
    class Meta:
        ordering = ['pub_date']
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        get_latest_by = 'pub_date'

class MeetingType(models.Model):

    """
    Meeting type model. This will give enough flexibility to add any type of
    meeting in any space.
    """
    title = models.CharField(_('Name'), max_length=100)

    class Meta:
        verbose_name = _('Meeting Type')
        verbose_name_plural = _('Meeting Types')

    def __unicode__(self):
        return self.title

class Meeting(models.Model):

    """
    Meeting data model. Every space (process) has N meetings. This will
    keep record of the assistants, meeting name, etc.
    """
    title = models.CharField(_('Meeting title'), max_length=100)
    space = models.ForeignKey(Space, blank=True, null=True)
    user = models.ManyToManyField(User, verbose_name=_('Users'))
    pub_date = models.DateTimeField(auto_now_add=True)
    meeting_author = models.ForeignKey(User, verbose_name=_('Author'),
                                     blank=True, null=True,
                                     related_name='meeting_author')
    meeting_date = models.DateField(verbose_name=_('Meeting Date'))
    meeting_type = models.ForeignKey(MeetingType, blank=True, null=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    location = models.TextField(_('Location'), blank=True, null=True)
    
    class Meta:
        ordering = ['meeting_date']
        verbose_name = _('Meeting')
        verbose_name_plural = _('Meetings')
        get_latest_by = 'meeting_date'

    def __unicode__(self):
        return self.title

