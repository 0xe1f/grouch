import bcrypt

class User:

    def __init__(self, source: dict={}):
        self._doc = source.copy()

    @property
    def id(self):
        return self._doc.get("id")

    @id.setter
    def id(self, val: str):
        self._doc["id"] = val

    @property
    def username(self):
        return self._doc.get("username")

    @username.setter
    def username(self, val: str):
        self._doc["username"] = val

    @property
    def hashed_password(self):
        return self._doc.get("hashed_password")

    @hashed_password.setter
    def hashed_password(self, val: str):
        self._doc["hashed_password"] = val

    @property
    def salt(self):
        return self._doc.get("salt")

    @salt.setter
    def salt(self, val: str):
        self._doc["salt"] = val

    @property
    def email_address(self):
        return self._doc.get("email_address")

    @email_address.setter
    def email_address(self, val: str):
        self._doc["email_address"] = val

    def set_hashed_password(self, plaintext: str, salt: bytes):
        self.hashed_password = bcrypt.hashpw(plaintext.encode(), salt).hex()
        self.salt = salt.hex()

    def doc(self):
        return self._doc
