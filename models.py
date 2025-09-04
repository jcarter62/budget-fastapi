from sqlalchemy import Column, String, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from db import Base

class Manager(Base):
    __tablename__ = "managers"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)

    accounts = relationship("Account", back_populates="manager")

class Account(Base):
    __tablename__ = "accounts"
    id = Column(String, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)  # '52100-03-31-01-01'
    description = Column(String, nullable=False)
    manager_id = Column(String, ForeignKey("managers.id"), nullable=True)

    manager = relationship("Manager", back_populates="accounts")

class BudgetItem(Base):
    __tablename__ = "budget_items"
    id = Column(String, primary_key=True, index=True)
    acct5 = Column(String, nullable=False)  # references Account.key
    line = Column(String, nullable=False)   # '01'..'99'
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    datefrom = Column(String, nullable=True)  # e.g. '2023-01-01'
    dateto = Column(String, nullable=True)    # e.g. '2023-12-31'
    #
    __table_args__ = (UniqueConstraint('acct5', 'line', 'datefrom', name='uq_budget_acct5_line_from'),)

class ActualItem(Base):
    __tablename__ = "actual_items"
    id = Column(String, primary_key=True, index=True)
    acct5 = Column(String, nullable=False)  # references Account.key
    line = Column(String, nullable=False)   # '01'..'99'
    tr_date = Column(String, nullable=True)  # transaction date, e.g. '2023-03-15'
    description = Column(String, nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    seq = Column(Float, nullable=True)  # sequence number, increments by 5
    #__table_args__ = (UniqueConstraint('acct5', 'line', name='uq_actual_acct5_line'),)
