from pydantic import BaseModel, Field
from typing import Optional

class ManagerBase(BaseModel):
    name: str = Field(..., min_length=1)
    isadmin: Optional[str] = Field('No', min_length=1)


class ManagerCreate(ManagerBase):
    id: str

class Manager(ManagerBase):
    id: str
    class Config:
        from_attributes = True

class AccountBase(BaseModel):
    key: str
    description: str
    manager_id: Optional[str] = None

class AccountCreate(AccountBase):
    id: str

class Account(AccountBase):
    id: str
    class Config:
        from_attributes = True

class LineItemBase(BaseModel):
    acct5: str
    line: str
    description: str
    amount: float
    seq: Optional[float] = None
    tr_date: Optional[str] = None
    vendor_name: Optional[str] = None
    vouchno: Optional[str] = None

class LineItemCreate(LineItemBase):
    id: str

class LineItem(LineItemBase):
    id: str
    class Config:
        from_attributes = True

class AcctMgrCreate(BaseModel):
    id: str
    key: str
    manager_id: str
