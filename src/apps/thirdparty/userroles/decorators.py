from django.contrib.auth.decorators import user_passes_test
from apps.thirdparty.userroles.models import set_user_role
import pdb

def role_required(*roles):
    """
    The decortor will check if the logged in user has the specified role.
    
    """

    c_roles = []

    def check_role(user):
        try:    
            for i in range(len(roles)):
                c_roles.append(roles[i].name)
            u_role = getattr(user,'role').all()
            if u_role[0] in c_roles:
                role_exist = True
            else:
                role_exist = False
        except IndexError:
            role_exist = False

        return role_exist
        
    return user_passes_test(check_role)
    
