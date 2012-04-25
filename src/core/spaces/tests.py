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

from django.test import TestCase
from django.core.urlresolvers import reverse

class Get_Test(TestCase):
    fixtures = ['temp1.json']
    
    def test_index(self):
    
        response = self.client.get('/spaces/')
        self.assertEqual(response.status_code, 200)
        
    def test_2(self):
    
        response = self.client.get('/spaces/')
        self.assertTrue('object_list' in response.context)
    
    def test_3(self):
    
        response = self.client.get('/spaces/')
        space_4 = response.context['object_list'][3]
        self.assertEqual(space_4.pk, 4)
        self.assertEqual(space_4.name, 'sk')
        self.assertEqual(space_4.url, 'sk')
    
    def test_3(self):    
        
        response = self.client.get('/spaces/sks/')
        self.assertEqual(response.status_code, 404)
        
        response = self.client.get('/spaces/sk/')
        self.assertEqual(response.status_code, 200)
        
        self.assertTrue('get_place' in response.context)
        self.assertTrue('entities' in response.context)
        self.assertTrue('documents' in response.context)
        self.assertTrue('proposals' in response.context)
        self.assertTrue('publication' in response.context)
        
        self.assertTrue(response.context['get_place'], 'sk')
        self.assertFalse(response.context['entities'], 'something')
        self.assertFalse(response.context['documents'], 'something')
        self.assertFalse(response.context['proposals'], 'something')
        self.assertFalse(response.context['publication'], 'something')

    def test_4(self):
    
        response = self.client.get('/spaces/sk/news')
        self.assertEqual(response.status_code, 301)
        print response.context
        
        

