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
from django.contrib.auth.models import User

class MailMessage(models.Model):

    """
    E-Mail storage model. This class will store all the mails sent to the
    users.
    
    .. versionadded:: 0.1.5
    """
    subject = models.CharField(_('Subject'), max_length=250,
                               help_text=_('Max: 250 characters'))
    message = models.TextField(_('Message'))
    date = models.DateTimeField(_('Created on'), auto_now_add=True)
    author = models.ForeignKey(User, blank=True, null=True,
                               verbose_name=_('Message creator'))
    last_mod = models.DateTimeField(_('Last modification time'), auto_now=True)

    def __unicode__(self):
        return self.subject
