from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.types import Float
import models
import schemas


# ---------- Managers ----------
def list_managers(db: Session):
    return db.execute(select(models.Manager)).scalars().all()

def get_manager(db: Session, id: str):
    return db.get(models.Manager, id)

def create_manager(db: Session, mgr: schemas.ManagerCreate):
    obj = models.Manager(id=mgr.id, name=mgr.name)
    db.add(obj); db.commit(); db.refresh(obj); return obj

def update_manager(db: Session, id: str, mgr: schemas.ManagerBase):
    obj = get_manager(db, id)
    if not obj:
        return None
    obj.name = mgr.name
    db.commit(); db.refresh(obj); return obj

def delete_manager(db: Session, id: str):
    obj = get_manager(db, id)
    if not obj:
        return False
    db.delete(obj); db.commit(); return True

# ---------- Accounts ----------
def list_accounts(db: Session):
    return db.execute(select(models.Account)).scalars().all()

def get_account(db: Session, id: str):
    return db.get(models.Account, id)

def create_account(db: Session, acc: schemas.AccountCreate):
    obj = models.Account(id=acc.id, key=acc.key, description=acc.description, manager_id=acc.manager_id)
    db.add(obj); db.commit(); db.refresh(obj); return obj

def update_account(db: Session, id: str, acc: schemas.AccountBase):
    obj = get_account(db, id)
    if not obj:
        return None
    obj.key = acc.key; obj.description = acc.description; obj.manager_id = acc.manager_id
    db.commit(); db.refresh(obj); return obj

def delete_account(db: Session, id: str):
    obj = get_account(db, id)
    if not obj:
        return False
    db.delete(obj); db.commit(); return True

# ---------- Budget Items ----------
def list_budget(db: Session):
    return db.execute(select(models.BudgetItem)).scalars().all()

def get_budget_item(db: Session, id: str):
    return db.get(models.BudgetItem, id)

def create_budget_item(db: Session, it: schemas.LineItemCreate):
    obj = models.BudgetItem(id=it.id, acct5=it.acct5, line=it.line, description=it.description, amount=it.amount)
    db.add(obj); db.commit(); db.refresh(obj); return obj

def update_budget_item(db: Session, id: str, it: schemas.LineItemBase):
    obj = get_budget_item(db, id)
    if not obj:
        return None
    obj.acct5 = it.acct5; obj.line = it.line; obj.description = it.description; obj.amount = it.amount
    db.commit(); db.refresh(obj); return obj

def delete_budget_item(db: Session, id: str):
    obj = get_budget_item(db, id)
    if not obj:
        return False
    db.delete(obj); db.commit(); return True

# ---------- Actual Items ----------
def list_actuals(db: Session):
    return db.execute(select(models.ActualItem)).scalars().all()

def get_actual_item(db: Session, id: str):
    return db.get(models.ActualItem, id)

def create_actual_item(db: Session, it: schemas.LineItemCreate):
    # calculate next seq number if not provided
    if it.seq is None:
        max_seq = db.execute(select(func.max(models.ActualItem.seq))).scalar()
        it.seq = float(max_seq + 5) if max_seq is not None else 1.0
    obj = models.ActualItem(id=it.id, acct5=it.acct5, line=it.line, description=it.description, amount=it.amount, tr_date=getattr(it, 'tr_date', None), seq=it.seq)
    db.add(obj); db.commit(); db.refresh(obj); return obj

def update_actual_item(db: Session, id: str, it: schemas.LineItemBase):
    obj = get_actual_item(db, id)
    if not obj:
        return None
    obj.acct5 = it.acct5
    obj.line = it.line
    obj.description = it.description
    obj.amount = it.amount
    obj.tr_date = getattr(it, 'tr_date', None)
    if it.seq is not None:
        obj.seq = it.seq
    db.commit(); db.refresh(obj); return obj

def delete_actual_item(db: Session, id: str):
    obj = get_actual_item(db, id)
    if not obj:
        return False
    db.delete(obj); db.commit(); return True

# ---------- Helpers ----------
def next_line_for_account(db: Session, table, acct5: str) -> str:
    # Ensure line is cast to integer safely for max calculation
    max_line = db.query(func.max(func.cast(table.line, Float))).filter(table.acct5 == acct5).scalar()
    n = int(max_line or 0) + 1
    return f"{n:02d}"
