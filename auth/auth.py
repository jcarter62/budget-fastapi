import base64
from fastapi import Request
import os
import db
from sqlalchemy.orm import Session
import crud

class Auth:
    def __init__(self, request: Request):
        self.req = request
        self.session = ''
        self.username = self.decrypt_key(key='user')
        self.user_id = self.decrypt_key(key='uid')
        self.dbpath = os.environ.get("DB_PATH", "app.db")
        self.is_admin = self.get_admin_status()

    # get user info from sqlite database managers table
    def get_user_info(self, userid: str):
        result = None
        try:
            db_session: Session = next(db.get_db())
            user_info = crud.get_manager(db_session, userid)
            result = {
                "id": user_info.id,
                "name": user_info.name,
                "is_admin": user_info.isadmin,
                "is_default": user_info.isdefault,
            }
        except Exception as e:
            print(f"Err:auth.get_user_info: {e}")
        return result

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

    def get_admin_status(self) -> bool:
        """Return True if the current session cookie corresponds to an admin user."""
        result = False

        if self.is_authenticated():
            # determine if current user is admin
            try:
                user_info = self.get_user_info(self.user_id)
                if user_info and (user_info['is_admin'] == 'on'):
                    result = True
            except Exception as e:
                print(f"Err:auth.is_admin: {e}")

        print(f"user: {self.username} - Admin: {result}")
        return result


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

