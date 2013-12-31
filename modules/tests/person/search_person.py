
"""
		Sahana Eden Person Search Module Automated Tests

"""
from tests.web2unittest import SeleniumUnitTest
class SearchPerson(SeleniumUnitTest):

	def test_pr003_search_person(self):
		"""
			simple search for person by id
			This search can be done by either using the name or the id .
		"""
		self.login(account="admin", nexturl="pr/index")
		self.search(self.search.simple_form,
			True,
			({
				"name": "person_search_simple",
				"value" : "Number"
				},),row_count = 1)

	def test_pr004_search_person(self):
		"""
			simple search for person by name
			This search can be done by either using the name or the id .
		"""
		self.login(account="admin", nexturl="pr/index")
		self.search(self.search.simple_form,
			True,
			({
				"name": "person_search_simple",
				"value" : "Admin"
				},),row_count = 2)
