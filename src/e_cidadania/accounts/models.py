# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 Cidadanía Coop.
# Contact: Oscar Carballal Prego <info@oscarcp.com>
#
# Distributed under terms of the GLPv3 license.

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

class UserProfile(models.Model):

    """
    Extends the default User profiles of Django.
    """
    user = models.ForeignKey(User, unique=True)
    
    # Maybe one day this will be replaced by a list of choices.
    province = models.CharField(_('Province'), max_length=50)
    municipality = models.CharField(_('Municipality'), max_length=50)
    localidad = models.CharField(_('Localidad'), max_length=50)
    
    # This could be replaces by an inline auxiliar data model.
    mobile = models.IntegerField(_('Mobile phone'), max_length=9, null=True,
                                 blank=True, help_text=_('9 digits maximum'))
    phone = models.IntegerField(_('Phone'), max_length=9, null=True, blank=True,
                                help_text=_('9 digits maximum'))
    
    website = models.URLField(_('Website'), verify_exists=True, max_length=200,
                              null=True, blank=True,
                              help_text=_('The URL will be checked'))
    
    # Not required since User module automatically sets the register time.
    #registered = models.DateTimeField('Registered', auto_now_add=True)
    
User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])
