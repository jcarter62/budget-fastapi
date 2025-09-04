from pydantic import BaseModel, Field
from typing import Optional

class ManagerBase(BaseModel):
    name: str = Field(..., min_length=1)

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

class LineItemCreate(LineItemBase):
    id: str

class LineItem(LineItemBase):
    id: str
    class Config:
        from_attributes = True
