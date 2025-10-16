import base64
from fastapi import Request

class Auth:
    def __init__(self, request: Request):
        self.req = request
        self.session = ''
        self.username = self.decrypt_key(key='user')
        self.user_id = self.decrypt_key(key='uid')

    def decrypt_key(self, key:str)->str:
        keyval = self.req.cookies.get(key)
        keyresult = ''
        if keyval:
            keyresult = keyval.encode('ascii')
            keyresult = base64.b64decode(keyresult).decode('ascii')
        return keyresult

    def is_authenticated(self) -> bool:
        """Return True if the current session cookie corresponds to an admin user."""
        token = self.req.cookies.get("session")
        if not token:
            return False
        return True

    def is_admin(self) -> bool:
        """Return True if the current session cookie corresponds to an admin user."""
        if not self.is_authenticated():
            return False
        is_admin = self.req.cookies.get("isAdmin")
        return is_admin == "1"

    def is_manager(self) -> bool:
        """Return True if the current session cookie corresponds to a manager user."""
        if not self.is_authenticated():
            return False
        is_mgr = self.req.cookies.get("isMgr")
        return is_mgr == "1"

    def get_username(self) -> str:
        """Return the username from the session cookie."""
        return self.username

    def get_user_id(self) -> str:
        """Return the user ID from the session cookie."""
        return self.user_id

