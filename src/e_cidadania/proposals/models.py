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

import datetime

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

CLOSE_REASONS = (
    ('1', _('Out of money')),
    ('2', _('Not accepted')),
    ('3', _('Not estimated')),
    ('4', _('Not viable')),
)

class Proposal(models.Model):
    title = models.CharField(_('Title'), max_length=100, unique=True)
    message = models.TextField(_('Message'), max_length=200)
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User)
    latitude = models.DecimalField(_('Latitude'), max_digits=8,
                                                  decimal_places=6)
    longitude = models.DecimalField(_('Longitude'), max_digits=8,
                                                    decimal_places=6)
    closed = models.BooleanField(default=False)
    closed_by = models.ForeignKey(User, blank=True, null=True)
