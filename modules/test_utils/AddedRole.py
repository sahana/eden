
class AddedRole(object):
    """Adds a role and removes it at the end of a test no matter what happens.
    
    """
    def __init__(self, session, role):
        self.role = role
        self.session = session
    
    def __enter__(self):
        roles = self.session.s3.roles
        role = self.role
        if not role in roles:
            roles.append(role)

    def __exit__(self, type, value, traceback):
        session_s3_roles = self.session.s3.roles
        roles = list(session_s3_roles)
        for i in range(len(roles)):
            session_s3_roles.pop(0)
        add_role = session_s3_roles.append
        role = self.role
        for role in roles:
            if role is not role:
                add_role(role)
