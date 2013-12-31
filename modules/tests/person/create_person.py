from tests.web2unittest import SeleniumUnitTest
class CreatePerson(SeleniumUnitTest):
	def test_pr001_create_person(self):
		self.login(account="admin",nexturl="pr/person/create")
		self.create("pr_person",
					[("first_name","Anurag"),
					 ("last_name","Sharma"),
					 ("gender","male"),
					 ("date_of_birth","2013-12-2"),
					 ("preferred_name","ans"),
					 ("comments","This is a test person added by the Selenium test PR001"),
					 # I suspect the data is created but the check fails in the Selenium test itself
					 ("sub_person_details_marital_status","single"),
					 ("sub_person_details_nationality","India"),
					 ("sub_person_details_religion","Hindu")
					 ],
					components = {"sub_person_details_marital_status":["pr_person_details", "person_id", "marital_status"],
								  "sub_person_details_nationality":["pr_person_details", "person_id", "nationality"],
								  "sub_person_details_religion":["pr_person_details", "person_id", "religion"]
								 }
					 )
