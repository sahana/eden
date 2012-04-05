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
        
        

