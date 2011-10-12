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

from django.shortcuts import render_to_response, get_object_or_404
from django.utils.safestring import mark_safe
from django.template import RequestContext
from django.utils import translation

from e_cidadania.apps.spaces.models import Meeting, Space
from e_cidadania.apps.cal.models import EventCalendar
from e_cidadania import settings

def calendar(request, space_name, year, month):
    
    # Avoid people writing wrong numbers or any program errors.
    if int(month) not in range(1, 13):
        return render_to_response('cal/error.html',
                                  context_instance=RequestContext(request))

    place = get_object_or_404(Space, url=space_name)
    next_month = int(month) + 1
    prev_month = int(month) - 1
                              
    meetings = Meeting.objects.order_by('meeting_date') \
                              .filter(space = place,
                                      meeting_date__year = year,
                                      meeting_date__month = month)

    cur_lang = translation.get_language()
    cur_locale = translation.to_locale(cur_lang) + '.UTF-8' #default encoding with django
    cal = EventCalendar(meetings, settings.FIRST_WEEK_DAY, cur_locale).formatmonth(int(year), int(month))

    # cal = EventCalendar(meetings).formatmonth(int(year), int(month))

    return render_to_response('cal/calendar.html',
                              {'calendar': mark_safe(cal),
                               'nextmonth': '%02d' % next_month,
                               'prevmonth': '%02d' % prev_month,
                               'get_place': place},
                               context_instance = RequestContext(request))
