#!/usr/bin/python
import os
import unittest
import translate_file_management


class TestTranslateFunctions(unittest.TestCase):
        
	""" Unit tests for the core Translate Functionality API """

        expectedModuleList = []
        expectedFileList = {}
	expectedStringList = {}

        def setUp(self):

	   """ Add all expected results here """

           # If a new module is added, it needs to appended to this list for the test to pass 
           self.expectedModuleList = [ 'admin',
                                       'appadmin',
                                       'assess',
                                       'asset',
                                       'auth',
                                       'budget',
                                       'building',
                                       'climate',
                                       'cms',
                                       'cr',
                                       'default',
                                       'delphi',
                                       'doc',
                                       'dvi',
                                       'dvr',
                                       'errors',
                                       'event',
                                       'fire',
                                       'flood',
                                       'gis',
                                       'hms',
                                       'hrm',
                                       'impact',
                                       'importer',
                                       'inv',
                                       'irs',
                                       'member',
                                       'mpr',
                                       'msg',
                                       'org',
                                       'patient',
                                       'pr',
                                       'project',
                                       'req',
                                       'scenario',
                                       'security',
                                       'supply',
                                       'survey',
                                       'sync',
                                       'vehicle',
                                       'xforms'
                                     ]
	   
	   base_dir = os.path.abspath('../')

           # Add all the expected files for a given module to this dictionary

           self.expectedFileList['inv'] = [os.path.join(base_dir,"controllers/inv.py"),
	                                   os.path.join(base_dir,"modules/eden/inv.py"),
					   os.path.join(base_dir,"modules/eden/inv.pyc"),
					   os.path.join(base_dir,"views/inv/index.html"),]
	   
           self.expectedFileList['supply'] = [os.path.join(base_dir,"controllers/supply.py"),
	                                   os.path.join(base_dir,"modules/eden/supply.py"),
	                                   os.path.join(base_dir,"models/supply.py"),
					   os.path.join(base_dir,"modules/eden/supply.pyc"),
					   os.path.join(base_dir,"views/supply/index.html"),]

           self.expectedFileList['assess'] = [os.path.join(base_dir,"controllers/assess.py"),
	                                   os.path.join(base_dir,"models/08_assess.py"),
					   os.path.join(base_dir,"views/assess/assess_create.html"),
					   os.path.join(base_dir,"views/assess/assess_list_create.html"),
					   os.path.join(base_dir,"views/assess/assess_list.html"),
					   os.path.join(base_dir,"views/assess/basic_assess.html"),
					   os.path.join(base_dir,"views/assess/mobile_basic_assess.html"),
					   os.path.join(base_dir,"views/assess/index.html"),]

           self.expectedFileList['survey'] = [os.path.join(base_dir,"controllers/survey.py"),
	                                   os.path.join(base_dir,"modules/eden/survey.py"),
					   os.path.join(base_dir,"modules/eden/survey.pyc"),
					   os.path.join(base_dir,"modules/s3/s3survey.pyc"),
					   os.path.join(base_dir,"modules/s3/s3survey.py"),
					   os.path.join(base_dir,"views/survey/section_create.html"),
					   os.path.join(base_dir,"views/survey/series_analysis.html"),
					   os.path.join(base_dir,"views/survey/series_map.html"),
					   os.path.join(base_dir,"views/survey/series_summary.html"),
					   os.path.join(base_dir,"views/survey/template_section_create"),
					   os.path.join(base_dir,"views/survey/template_section_list_create"),
					   os.path.join(base_dir,"views/survey/index.html"),]

	   for k in self.expectedFileList.keys():
		   self.expectedFileList[k].sort()


		   
           # Add all the expected strings for a given file to this dictionary
          
           self.expectedStringList[os.path.join(base_dir,"modules/eden/dvr.py")] = ['"Very High"',
	                                                                            '"High"',
										    '"Medium"',
										    '"Low"',
										    '"Open"',
										    '"Accepted"',
										    '"Rejected"',
										    '"Case Number"',
										    '"Home Address"',
										    '"Damage Assessment"',
										    '"Insurance"',
										    '"Status"',
										    '"Add Case"',
										    '"List Cases"',
										    '"Case Details"',
										    '"Edit Case"',
										    '"Search Cases"',
										    '"Add New Case"',
										    '"Cases"',
										    '"Delete Case"',
										    '"Case added"',
										    '"Case updated"',
										    '"Case deleted"',
										    '"No Cases found"'
										    ]
            
           self.expectedStringList[os.path.join(base_dir,"modules/s3cfg.py")] = ['"United States Dollars"',
	                                                                         '"Euros"',
	                                                                         '"Great British Pounds"',
	                                                                         '"Swiss Francs"',
	                                                                         '"Sahana Eden Humanitarian Management Platform"',
	                                                                         '"none"',
	                                                                         '"Christian"',
	                                                                         '"Muslim"',
	                                                                         '"Jewish"',
	                                                                         '"Buddhist"',
	                                                                         '"Hindu"',
	                                                                         '"Bahai"',
	                                                                         '"other"',
	                                                                         '"%Y-%m-%d"',
	                                                                         '"%H:%M:%S"',
	                                                                         '"%Y-%m-%d %H:%M:%S"',
	                                                                         '"Mobile Phone"',
	                                                                         '"Postcode"',
	                                                                         '"Warehouse Stock"',
	                                                                         '"People"',
	                                                                         '"Other Warehouse"',
	                                                                         '"Local Donation"',
	                                                                         '"Foreign Donation"',
	                                                                         '"Local Purchases"',
	                                                                         '"Lead Implementer"',
	                                                                         '"Partner"',
	                                                                         '"Donor"',
	                                                                         '"Customer"',
	                                                                         '"Supplier"']
                       
           self.expectedStringList[os.path.join(base_dir,"models/000_config.py")] = ['"Sahana Eden Humanitarian Management Platform"',
	                                                                             '"Sahana Eden"',
	                                                                             '"Home"',
	                                                                             '"Administration"',
	                                                                             '"Administration"',
	                                                                             '"Ticket Viewer"',
	                                                                             '"Synchronization"',
	                                                                             '"Map"',
	                                                                             '"Person Registry"',
	                                                                             '"Organizations"',
	                                                                             '"Staff & Volunteers"',
	                                                                             '"Content Management"',
	                                                                             '"Documents"',
	                                                                             '"Messaging"',
	                                                                             '"Supply Chain Management"',
	                                                                             '"Warehouse"',
	                                                                             '"Assets"',
	                                                                             '"Vehicles"',
	                                                                             '"Requests"',
	                                                                             '"Projects"',
	                                                                             '"Surveys"',
	                                                                             '"Shelters"',
	                                                                             '"Hospitals"',
	                                                                             '"Incidents"',
	                                                                             '"Scenarios"',
										     '"Events"',
										     '"Disaster Victim Identification"',
										     '"Missing Person Registry"',
										     '"Disaster Victim Registry"',
										     '"Members"',
										     '"Security"']
          

#-----------------------------------------------------------------------------------------------------------------------------

        def testGetModules(self):

		""" Single test method to test the get_module_list() function """
                A = translate_file_management.TranslateAPI()
		mod = A.get_modules()
	        mod.sort()
	        self.assertEqual(mod,self.expectedModuleList)

#-------------------------------------------------------------------------------------------------------------------------------

	def testGetFilesbyModule(self):

	      """ Test method to test the get_files_by_module() function 
	          for each module added to the dictionary in setUp method """
              A = translate_file_management.TranslateAPI()
              for k in self.expectedFileList.keys(): 
		files = A.get_files_by_module(k)
		files.sort()
		self.assertEqual(files,self.expectedFileList[k])

#-------------------------------------------------------------------------------------------------------------------------------

        def testGetStringsbyFile(self):

	        """ Test method to test the get_strings_by_file() function 
	          for each file added to the dictionary in setUp method """
                A = translate_file_management.TranslateAPI()
		for k in self.expectedStringList.keys():
		    string_tuple = A.get_strings_by_file(k)
		    strings=[]
                    for s in string_tuple:
	                  strings.append(s[1])
		    self.assertEqual(strings,self.expectedStringList[k])

#-------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTranslateFunctions)
    unittest.TextTestRunner(verbosity=2).run(suite)

#END==============================================================================================================================
