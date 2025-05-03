# used to store database model
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id = None, email = None, password = None, firstName = None):
        self.id = id
        self.email = {'email': email}
        self.password = {'password': password}
        self.firstName = {'firstName': firstName}

    def create_document(self):
        newDoc = {}
        newDoc |= self.email
        newDoc |= self.password
        newDoc |= self.firstName
        return newDoc

    def documentToUserInst(userDocument):
        if userDocument:
            return User(
                id = userDocument.get('_id'),
                email = userDocument.get('email'),
                password = userDocument.get('password'),
                firstName = userDocument.get('firstName')
            )
        return None

    def get_id(self):
        return str(self.id)

class Place:
    def __init__(self, id = None, name = None, website = None, phone = None, address = None, hasFundraising = None):
        self.id = id
        self.name = {'name' : name}
        self.website = {'website' : website}
        self.phone = {'phone' : phone}
        self.address = {'address' : address}
        self.hasFundraising = {'hasFundraising' : hasFundraising}