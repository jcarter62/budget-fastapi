from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from sqlalchemy.types import Float
import models
import schemas


# ---------- Managers ----------
def list_managers(db: Session):
    mgrs = db.execute(select(models.Manager))
    mgrs = mgrs.scalars()
    mgrs = mgrs.all()
    return mgrs

def get_manager(db: Session, id: str):
    mgr = db.get(models.Manager, id)
    return mgr

def get_manager_id_by_name(db: Session, name: str) -> str | None:
    obj = db.execute(select(models.Manager).where(models.Manager.name == name)).scalars().first()
    return obj.id if obj else None

def create_manager(db: Session, mgr: schemas.ManagerCreate):
    obj = models.Manager(id=mgr.id, name=mgr.name, isdefault='No', isadmin='No')
    db.add(obj); db.commit(); db.refresh(obj); return obj

def update_manager(db: Session, id: str, mgr: schemas.ManagerBase, isdefault: str = 'off', isadmin: str = 'off'):
    obj = get_manager(db, id)
    if not obj:
        return None
    obj.name = mgr.name
    obj.isadmin = isadmin
    obj.isdefault = isdefault
    if isdefault == 'on':
        # Reset other managers' isdefault to 'off'
        db.execute(
            models.Manager.__table__.update().where(models.Manager.id != id).values(isdefault='off')
        )
    db.commit(); db.refresh(obj); return obj

def delete_manager(db: Session, id: str):
    obj = get_manager(db, id)
    if not obj:
        return False
    db.delete(obj); db.commit(); return True

# ---------- Account-Managers ----------

def list_acct_mgrs(db: Session):
    result = db.execute(select(models.AcctMgr)).scalars().all()
    return result

def get_acct_mgr(db: Session, id: str):
    return db.get(models.AcctMgr, id)

def get_acct_mgr_by_key_mgr(db: Session, key: str, manager_id: str):
    result = None
    try:
        result = (db.execute(
                select(models.AcctMgr)
                .where(models.AcctMgr.key == key, models.AcctMgr.manager_id == manager_id))
                .scalars().first()
              )
    except Exception:
        result = None

    return result

def create_acct_mgr(db: Session, am: schemas.AcctMgrCreate):
    obj = models.AcctMgr(id=am.id, key=am.key, manager_id=am.manager_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return

def delete_acct_mgr(db: Session, record_id: str):
    obj = get_acct_mgr(db, record_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# ---------- Accounts ----------
def list_accounts(db: Session):
    return db.execute(select(models.Account)).scalars().all()

def account_list(db: Session, filter_acct: str | None = None,
                 filter_desc: str | None = None, filter_manager: str | None = None) -> []:
    results = []
    if filter_manager:
        query = select(models.Account).join(models.AcctMgr, models.Account.key == models.AcctMgr.key)
        query = query.where(models.AcctMgr.manager_id == filter_manager)
    else:
        query = select(models.Account)
    if filter_acct:
        query = query.where(models.Account.key.like(f"%{filter_acct}%"))
    if filter_desc:
        query = query.where(models.Account.description.like(f"%{filter_desc}%"))

    accounts = db.execute(query).scalars().all()
    # return only account keys
    for acc in accounts:
        if (acc.key):
            if (acc.key.strip() != ""):
                results.append(acc.key)

    return results

def get_account(db: Session, id: str):
    return db.get(models.Account, id)

def get_account_glkey(db: Session, id: str):
    obj = get_account(db, id)
    return obj.key if obj else None

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

def get_all_accounts(db: Session):
    accounts = db.execute(select(models.Account)).scalars().all()
    return accounts

def get_account_by_key(db: Session, key: str):
    search_result = db.execute(select(models.Account).where(models.Account.key == key)).scalars().first()
    return search_result

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


def get_budget_total_for_account(db, a:str) -> float | None:
    result = db.execute(
        select(models.BudgetItem.amount).where(models.BudgetItem.acct5 == a)
    ).scalar()
    if result is None:
        result = 0.0
    return result


def get_actual_total_for_account(db, a:str) -> float | None:
    # calculate the sum of actual_items.amount where acct5 == a
    result = db.execute(
        select(func.sum(models.ActualItem.amount)).where(models.ActualItem.acct5 == a)
    ).scalar_one_or_none()
    return float(result) if result is not None else 0.0

def get_account_description_for_account(db, a:str) -> str | None:
    result = db.execute(
        select(models.Account.description).where(models.Account.key == a)
    ).scalar()
    if result is None:
        result = ""
    return result


def actuals_get_by_account_vendor(db, account, filter_vendor):
    stmt = select(models.ActualItem)
    conds = []
    # If filtering by manager, join Account and add condition on manager_id
    if account:
        conds.append(models.ActualItem.acct5 == account)
    if filter_vendor:
        pat = f"%{filter_vendor.lower()}%"
        conds.append(func.lower(func.coalesce(models.ActualItem.vendor_name, '')).like(pat))

    if conds:
        stmt = stmt.where(and_(*conds))
    return db.execute(stmt).scalars().all()


def get_managers_for_account(db, a):
    results = []
    acct_mgrs = db.execute(
        select(models.AcctMgr).where(models.AcctMgr.key == a)
    ).scalars().all()
    for am in acct_mgrs:
        mgr_id = get_manager(db, am.manager_id)
        mgr_name = mgr_id.name if mgr_id else ""
        mgr = {
            "id": am.manager_id,
            "name": mgr_name
        }
        if mgr:
            results.append(mgr)
    return results
