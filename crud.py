from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from sqlalchemy.types import Float
import models
import schemas


# ---------- Managers ----------
def list_managers(db: Session):
    return db.execute(select(models.Manager)).scalars().all()

def get_manager(db: Session, id: str):
    return db.get(models.Manager, id)

def create_manager(db: Session, mgr: schemas.ManagerCreate):
    obj = models.Manager(id=mgr.id, name=mgr.name, isdefault='N')
    db.add(obj); db.commit(); db.refresh(obj); return obj

def update_manager(db: Session, id: str, mgr: schemas.ManagerBase, isdefault: str = 'N'):
    obj = get_manager(db, id)
    if not obj:
        return None
    obj.name = mgr.name
    obj.isdefault = isdefault
    if isdefault == 'on':
        # Reset other managers' isdefault to 'N'
        db.execute(
            models.Manager.__table__.update().where(models.Manager.id != id).values(isdefault='off')
        )
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

def delete_all_accounts(db: Session):
    db.query(models.Account).delete()
    db.commit()

def get_account_by_key(db: Session, key: str):
    return db.execute(select(models.Account).where(models.Account.key == key)).scalars().first()

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

def get_budget_item_by_acct_line(db: Session, acct5: str, line: str):
    return db.execute(select(models.BudgetItem).where(models.BudgetItem.acct5 == acct5, models.BudgetItem.line == line)).scalars().first()

def upsert_budget_item(db: Session, acct5: str, line: str, description: str, amount: float):
    obj = get_budget_item_by_acct_line(db, acct5, line)
    if obj:
        obj.description = description
        obj.amount = amount
        db.commit(); db.refresh(obj)
        return obj, False
    else:
        new = models.BudgetItem(id=str(__import__('uuid').uuid4()), acct5=acct5, line=line, description=description, amount=amount)
        db.add(new); db.commit(); db.refresh(new)
        return new, True

# ---------- Actual Items ----------
def list_actuals(db: Session):
    return db.execute(select(models.ActualItem)).scalars().all()

def list_actuals_filtered(db: Session, acct5: str | None = None, description: str | None = None, vendor: str | None = None, manager: str | None = None):
    """Return actual items optionally filtered by acct5 (exact), description (contains, case-insensitive),
    vendor_name (contains, case-insensitive), and manager (by joining accounts -> manager_id).
    Uses lower() + COALESCE to be portable across DBs.
    """
    stmt = select(models.ActualItem)
    conds = []
    # If filtering by manager, join Account and add condition on manager_id
    if manager:
        stmt = stmt.join(models.Account, models.Account.key == models.ActualItem.acct5)
        conds.append(models.Account.manager_id == manager)
    if acct5:
        conds.append(models.ActualItem.acct5 == acct5)
    if description:
        pat = f"%{description.lower()}%"
        conds.append(func.lower(func.coalesce(models.ActualItem.description, '')).like(pat))
    if vendor:
        patv = f"%{vendor.lower()}%"
        conds.append(func.lower(func.coalesce(models.ActualItem.vendor_name, '')).like(patv))
    if conds:
        stmt = stmt.where(and_(*conds))
    return db.execute(stmt).scalars().all()

def get_actual_item(db: Session, id: str):
    return db.get(models.ActualItem, id)

def create_actual_item(db: Session, it: schemas.LineItemCreate):
    # calculate next seq number if not provided
    if it.seq is None:
        max_seq = db.execute(select(func.max(models.ActualItem.seq))).scalar()
        it.seq = float(max_seq + 5) if max_seq is not None else 1.0
    obj = models.ActualItem(
        id=it.id,
        acct5=it.acct5,
        line=it.line,
        description=it.description,
        amount=it.amount,
        tr_date=getattr(it, 'tr_date', None),
        seq=it.seq,
        vendor_name=getattr(it, 'vendor_name', None),
        vouchno=getattr(it, 'vouchno', None)
    )
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
    obj.vendor_name = getattr(it, 'vendor_name', None)
    obj.vouchno = getattr(it, 'vouchno', None)
    db.commit(); db.refresh(obj); return obj

def delete_actual_item(db: Session, id: str):
    obj = get_actual_item(db, id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

def actual_exists_ignore_line(db: Session, acct5: str, description: str, amount: float, tr_date: str | None, vendor_name: str | None) -> bool:
    eps = 0.005  # 1/2 cent tolerance
    stmt = select(models.ActualItem).where(
        and_(
            models.ActualItem.acct5 == acct5,
            models.ActualItem.description == description,
            func.abs(models.ActualItem.amount - amount) <= eps,
            (models.ActualItem.tr_date == tr_date if tr_date is not None else models.ActualItem.tr_date.is_(None)),
            (models.ActualItem.vendor_name == vendor_name if vendor_name is not None else models.ActualItem.vendor_name.is_(None)),
        )
    ).limit(1)
    return db.execute(stmt).scalars().first() is not None

# ---------- Helpers ----------
def next_line_for_account(db: Session, table, acct5: str) -> str:
    # Ensure line is cast to integer safely for max calculation
    max_line = db.query(func.max(func.cast(table.line, Float))).filter(table.acct5 == acct5).scalar()
    n = int(max_line or 0) + 1
    return f"{n:02d}"
