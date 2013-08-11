from gluon import current

def get_org_branches():	
	"""
		Defines the Organisations and branches for which the role test data is to be created.
	"""

	# Define Organisations
	orgs = ["Org-A",
	        "Org-B",
	        "Org-C",
	        ]
	if(current.deployment_settings.get_org_branches()):
	    branches = [None,
	                "Branch-A"]
	else:
	    branches = [None]

	return (orgs, branches)