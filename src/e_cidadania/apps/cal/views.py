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

from django.shortcuts import render_to_response
from django.utils.safestring import mark_safe

from e_cidadania.apps.spaces.models import Meeting

def calendar(request, year, month):
    meetings = Meeting.objects.order_by('meeting_date')
                              .filter(meeting_date__year = year,
                                      meeting_date__month = month)
    
    cal = EventCalendar(meetings).formatmonth(year, month)
    return render_to_response('cal/calendar.html', {'calendar': mark_safe(cal),})
