# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2012 Cidadania S. Coop. Galega
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
This file contains functions to help with caching.
"""

# Django's cache module
from django.core.cache import cache

# Cached models
from core.spaces.models import Space

# Response types
from django.shortcuts import get_object_or_404

# Tries to get the object from cache
# Else queries the database
# Else returns a 404 error
def get_or_insert_in_cache(prefix, key, value, get_arg):
    return_object = cache.get(prefix+key)
    if not return_object:
        return_object = get_object_or_404(value, get_arg)
        cache.set(prefix+key, return_object)
    return return_object
