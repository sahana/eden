# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.utils.translation import ugettext_lazy as _
from rosetta.conf import settings as rosetta_settings
import datetime, os, shutil, hashlib


class RosettaTestCase(TestCase):
    urls = 'rosetta.tests.urls'
    
    
    def __init__(self, *args,**kwargs):
        super(RosettaTestCase,self).__init__(*args,**kwargs)
        self.curdir = os.path.dirname(__file__)
        self.dest_file = os.path.normpath(os.path.join(self.curdir, '../locale/xx/LC_MESSAGES/django.po'))


    def setUp(self):
        user    = User.objects.create_user('test_admin', 'test@test.com', 'test_password')
        user2   = User.objects.create_user('test_admin2', 'test@test2.com', 'test_password')
        
        user.is_superuser, user2.is_superuser = True,True
        user.save()
        user2.save()
        
        self.client2 = Client()
        
        self.client.login(username='test_admin',password='test_password')
        self.client2.login(username='test_admin2',password='test_password')
        
        settings.LANGUAGES = (('xx','dummy language'),)
        
        

    def test_1_ListLoading(self):
        r = self.client.get(reverse('rosetta-pick-file') +'?rosetta')
        self.assertTrue(os.path.normpath('rosetta/locale/xx/LC_MESSAGES/django.po') in r.content)
        
        
    def test_2_PickFile(self):
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) +'?rosetta')
        r = self.client.get(reverse('rosetta-home'))
        
        self.assertTrue('dummy language' in r.content)
        
    def test_3_DownloadZIP(self):
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) +'?rosetta')
        r = self.client.get(reverse('rosetta-home'))
        r = self.client.get(reverse('rosetta-download-file' ) +'?rosetta')
        self.assertTrue ('content-type' in r._headers.keys() )
        self.assertTrue ('application/x-zip' in r._headers.get('content-type'))
    
    def test_4_DoChanges(self):
        
        # copy the template file
        shutil.copy(self.dest_file, self.dest_file + '.orig')
        shutil.copy(os.path.normpath(os.path.join(self.curdir,'./django.po.template')), self.dest_file)

        # Load the template file
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) +'?rosetta')
        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))
        
        # make sure both strings are untranslated
        self.assertTrue('dummy language' in r.content)
        self.assertTrue('String 1' in r.content)
        self.assertTrue('String 2' in r.content)
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content)
        
        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))
        
        # reload all untranslated strings
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) +'?rosetta')
        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))
        
        # the translated string no longer is up for translation
        self.assertTrue('String 1'  in r.content)
        self.assertTrue('String 2' not in r.content)
        
        # display only translated strings
        r = self.client.get(reverse('rosetta-home') + '?filter=translated')
        r = self.client.get(reverse('rosetta-home'))
        
        # The tranlsation was persisted
        self.assertTrue('String 1' not  in r.content)
        self.assertTrue('String 2' in r.content)
        self.assertTrue('Hello, world' in r.content)
        
        # reset the original file
        shutil.move(self.dest_file+'.orig', self.dest_file)
        

    def test_5_TestIssue67(self):
        # testcase for issue 67: http://code.google.com/p/django-rosetta/issues/detail?id=67
        # copy the template file
        shutil.copy(self.dest_file, self.dest_file + '.orig')
        shutil.copy(os.path.normpath(os.path.join(self.curdir,'./django.po.issue67.template')), self.dest_file)
        
        # Make sure the plurals string is valid
        f_ = open(self.dest_file,'rb')
        content = f_.read()
        f_.close()
        self.assertTrue(u'Hello, world' not in content)
        self.assertTrue(u'|| n%100>=20) ? 1 : 2)' in content)
        del(content)
        
        # Load the template file
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) +'?rosetta')
        r = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r = self.client.get(reverse('rosetta-home'))
        
        # make sure all strings are untranslated
        self.assertTrue('dummy language' in r.content)
        self.assertTrue('String 1' in r.content)
        self.assertTrue('String 2' in r.content)
        self.assertTrue('m_e48f149a8b2e8baa81b816c0edf93890' in r.content)
        
        # post a translation
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world', _next='_next'))
        
        # Make sure the plurals string is still valid
        f_ = open(self.dest_file,'rb')
        content = f_.read()
        f_.close()
        self.assertTrue(u'Hello, world' in content)
        self.assertTrue(u'|| n%100>=20) ? 1 : 2)' in content)
        self.assertTrue(u'or n%100>=20) ? 1 : 2)' not in content)
        del(content)

        shutil.move(self.dest_file + '.orig', self.dest_file)
        

    def test_6_ExcludedApps(self):
        
        rosetta_settings.EXCLUDED_APPLICATIONS = ('rosetta',)
        
        r = self.client.get(reverse('rosetta-pick-file') +'?rosetta')
        self.assertTrue('rosetta/locale/xx/LC_MESSAGES/django.po' not in r.content)
        
        rosetta_settings.EXCLUDED_APPLICATIONS = ()
        
        r = self.client.get(reverse('rosetta-pick-file') +'?rosetta')
        self.assertTrue('rosetta/locale/xx/LC_MESSAGES/django.po' in r.content)
        
    def test_7_selfInApplist(self):    
        r = self.client.get(reverse('rosetta-pick-file') +'?rosetta')
        self.assertTrue('rosetta/locale/xx/LC_MESSAGES/django.po' in r.content)

        r = self.client.get(reverse('rosetta-pick-file'))
        self.assertTrue('rosetta/locale/xx/LC_MESSAGES/django.po' not in r.content)


    def test_8_hideObsoletes(self):
        r = self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) +'?rosetta')
        
        # not in listing
        for p in range(1,5):
            r = self.client.get(reverse('rosetta-home') + '?page=%d'%p)
            self.assertTrue('dummy language' in r.content)
            self.assertTrue('Les deux' not in r.content)
        
        r = self.client.get(reverse('rosetta-home') + '?query=Les%20Deux')
        self.assertTrue('dummy language' in r.content)
        self.assertTrue('Les deux' not in r.content)


    def test_9_concurrency(self):
        shutil.copy(self.dest_file, self.dest_file + '.orig')
        shutil.copy(os.path.normpath(os.path.join(self.curdir,'./django.po.template')), self.dest_file)
        
        
        self.client.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) +'?rosetta')
        self.client2.get(reverse('rosetta-language-selection', args=('xx',0,), kwargs=dict() ) +'?rosetta')

        # Load the template file
        r   = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r   = self.client.get(reverse('rosetta-home'))
        r2  = self.client2.get(reverse('rosetta-home') + '?filter=untranslated')
        r2  = self.client2.get(reverse('rosetta-home'))
        
        self.assertTrue('String 1' in r.content)
        self.assertTrue('String 1' in r2.content)
        self.assertTrue('m_08e4e11e2243d764fc45a5a4fba5d0f2' in r.content)
        
        
        r = self.client.post(reverse('rosetta-home'), dict(m_08e4e11e2243d764fc45a5a4fba5d0f2='Hello, world', _next='_next'))
        r2  = self.client2.get(reverse('rosetta-home'))
        
        # Client 2 reloads the home, forces a reload of the catalog, 
        # the untranslated string1 is now translated
        self.assertTrue('String 1' not in r2.content)
        self.assertTrue('String 2' in r2.content)


        r   = self.client.get(reverse('rosetta-home') + '?filter=untranslated')
        r   = self.client.get(reverse('rosetta-home'))
        r2  = self.client2.get(reverse('rosetta-home') + '?filter=untranslated')
        r2  = self.client2.get(reverse('rosetta-home'))


        self.assertTrue('String 2' in r2.content and 'm_e48f149a8b2e8baa81b816c0edf93890' in r2.content)
        self.assertTrue('String 2' in r.content and 'm_e48f149a8b2e8baa81b816c0edf93890' in r.content)
        
        # client 2 posts!
        r2 = self.client2.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world, from client two!', _next='_next'))
        self.assertTrue('save-conflict' not in r2.content)
        
        
        # uh-oh here comes client 1
        r = self.client.post(reverse('rosetta-home'), dict(m_e48f149a8b2e8baa81b816c0edf93890='Hello, world, from client one!', _next='_next'))
        # An error message is displayed
        self.assertTrue('save-conflict' in r.content)
        
        # Both clients show all strings, error messages are gone
        r  = self.client.get(reverse('rosetta-home') +'?filter=translated')
        self.assertTrue('save-conflict' not in r.content)
        r2  = self.client2.get(reverse('rosetta-home') +'?filter=translated')
        self.assertTrue('save-conflict' not in r2.content)
        r  = self.client.get(reverse('rosetta-home'))
        self.assertTrue('save-conflict' not in r.content)
        r2  = self.client2.get(reverse('rosetta-home'))
        self.assertTrue('save-conflict' not in r2.content)
        
        # Both have client's two version
        self.assertTrue('Hello, world, from client two!' in r.content)
        self.assertTrue('Hello, world, from client two!' in r2.content)
        self.assertTrue('save-conflict' not in r2.content)
        self.assertTrue('save-conflict' not in r.content)
        
        
        
        # reset the original file
        shutil.move(self.dest_file+'.orig', self.dest_file)

        