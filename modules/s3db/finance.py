__all__ = ["FinanceDonations",
           
           ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *
from s3layouts import S3AddResourceLink


class FinanceDonations(S3Model):
	names = ["finance_donations",
             "finance_donations_id",
			 
			 ]
			 
	def model(self):

        # You will most likely need (at least) these:
			db = current.db
			T = current.T

        # This one may be useful:
			settings = current.deployment_settings
	

			tablename = "finance_donations"
			table=self.define_table(tablename,
							Field("donar", label=T("Donar"),),
							Field("amount", "double", label=T("Amount"),
									default=0.00, 
									requires = IS_FLOAT_AMOUNT(),
									),
							s3_currency(required=True),
							)
			
			self.configure(tablename,
						   listadd=True)
						   
			finance_donations_id = S3ReusableField("finance_donations_id", table,
                                               label = T("Finance Donations"),
                                               requires = IS_NULL_OR(IS_ONE_OF(db,
                                                                     "finance_donations.id")))

        # Pass names back to global scope (s3.*)
			return dict(
				finance_donations_id=finance_donations_id,
			)
			
			
			self.set_method("finance", "donations", method="total", action=donations_total)
			
	