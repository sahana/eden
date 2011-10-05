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
Proposal data models are the ones to store the data inside the DB.
"""

import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from e_cidadania.apps.tagging.fields import TagField
from e_cidadania.apps.tagging.models import Tag
from e_cidadania.apps.spaces.models import Space

CLOSE_REASONS = (
    (1, _('Economically not viable')),
    (2, _('Legally not viable')),
    (3, _('Technically not viable')),
    (4, _('Offtopic'))
)

class BaseClass(models.Model):

    """
    Abstract base class for titles and descriptions (dummy models)
    """
    title = models.CharField(_('Title'), max_length=200)

    class Meta:
        abstract = True


class Category(BaseClass):

    """
    Dummy class for proposal categories. Inherits directly from :class:`BaseClass`
    without adding any fields.
    """
    pass

class Proposal(models.Model):

    """
    Proposal data model. This will store the user proposal in a similar
    way that Stackoverflow does. Take in mind that this data model is very
    exhaustive because it covers the administrator and the user.

    :automatically filled fields: Space, Author, Pub_date, mod_date.
    :user filled fields: Title, Description, Tags, Latitude, Longitude.
    :admin fields (manual): Code, Closed, Close_reason, Anon_allowed,
                            Refurbished, Budget.
    :admin fields (auto): Closed_by
    :extra permissions: proposal_view

    :const:`CLOSE_REASONS` for :class:Proposal data model is hardcoded with four
    values, which will fit most of the requirements.
    """
    code = models.CharField(_('Code'), max_length=50, unique=True, blank=True,
                            null=True)
    title = models.CharField(_('Title'), max_length=100, unique=True)
    description = models.TextField(_('Description'), max_length=300)
    space = models.ForeignKey(Space, blank=True, null=True)
    author = models.ForeignKey(User, related_name='proposal_authors',
                               blank=True, null=True)
    #debatelink = models.ForeignKey()
    tags = TagField()
    latitude = models.DecimalField(_('Latitude'), blank=True, null=True,
                                   max_digits=8, decimal_places=6)
    longitude = models.DecimalField(_('Longitude'), blank=True, null=True,
                                    max_digits=8, decimal_places=6)
    closed = models.NullBooleanField(default=False, blank=True)
    closed_by = models.ForeignKey(User, blank=True, null=True,
                                  related_name='proposal_closed_by')
    close_reason = models.SmallIntegerField(choices=CLOSE_REASONS, null=True,
                                            blank=True)
    anon_allowed = models.NullBooleanField(default=False, blank=True)
    support_votes = models.IntegerField(blank=True, null=True)
    refurbished = models.NullBooleanField(default=False, blank=True)
    budget = models.IntegerField(blank=True, null=True)

    pub_date = models.DateTimeField(auto_now_add=True)
    mod_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.title

    def set_tags(self, tags):
        Tag.objects.update_tags(self, tags)

    def get_tags(self, tags):
        return Tag.objects.get_for_object(self)

    class Meta:
        verbose_name = _('Proposal')
        verbose_name_plural = _('Proposals')
        get_latest_by = 'pub_date'
        permissions = (
            ('view', 'Can view the object'),
        )

    @models.permalink
    def get_absolute_url(self):
        return ('view-proposal', (), {
            'space_name': self.space.url,
            'prop_id': str(self.id)})
