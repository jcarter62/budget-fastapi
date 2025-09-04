from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from sqlalchemy.orm import Session
from db import get_db
from models import Manager
import schemas
import crud
import csv, io

router = APIRouter(prefix="/api")

# ---- Manager routes (single-record writes) ----
@router.get("/managers", response_model=List[schemas.Manager])
def managers_list(db: Session = Depends(get_db)):
    return crud.list_managers(db)

@router.post("/managers", response_model=schemas.Manager)
def managers_create(m: schemas.ManagerCreate, db: Session = Depends(get_db)):
    return crud.create_manager(db, m)

@router.put("/managers/{id}", response_model=schemas.Manager)
def managers_update(id: str, m: schemas.ManagerBase, db: Session = Depends(get_db)):
    obj = crud.update_manager(db, id, m)
    if not obj: raise HTTPException(404, "Not found")
    return obj

@router.delete("/managers/{id}")
def managers_delete(id: str, db: Session = Depends(get_db)):
    ok = crud.delete_manager(db, id)
    if not ok: raise HTTPException(404, "Not found")
    return {"ok": True}

# ---- Account routes ----
@router.get("/accounts", response_model=List[schemas.Account])
def accounts_list(db: Session = Depends(get_db)):
    return crud.list_accounts(db)

@router.post("/accounts", response_model=schemas.Account)
def accounts_create(a: schemas.AccountCreate, db: Session = Depends(get_db)):
    return crud.create_account(db, a)

@router.put("/accounts/{id}", response_model=schemas.Account)
def accounts_update(id: str, a: schemas.AccountBase, db: Session = Depends(get_db)):
    obj = crud.update_account(db, id, a)
    if not obj: raise HTTPException(404, "Not found")
    return obj

@router.delete("/accounts/{id}")
def accounts_delete(id: str, db: Session = Depends(get_db)):
    ok = crud.delete_account(db, id)
    if not ok: raise HTTPException(404, "Not found")
    return {"ok": True}

# ---- Budget items ----
@router.get("/budget", response_model=List[schemas.LineItem])
def budget_list(db: Session = Depends(get_db)):
    return crud.list_budget(db)

@router.post("/budget", response_model=schemas.LineItem)
def budget_create(it: schemas.LineItemCreate, db: Session = Depends(get_db)):
    return crud.create_budget_item(db, it)

@router.put("/budget/{id}", response_model=schemas.LineItem)
def budget_update(id: str, it: schemas.LineItemBase, db: Session = Depends(get_db)):
    obj = crud.update_budget_item(db, id, it)
    if not obj: raise HTTPException(404, "Not found")
    return obj

@router.delete("/budget/{id}")
def budget_delete(id: str, db: Session = Depends(get_db)):
    ok = crud.delete_budget_item(db, id)
    if not ok: raise HTTPException(404, "Not found")
    return {"ok": True}

# ---- Actuals items ----
@router.get("/actuals", response_model=List[schemas.LineItem])
def actuals_list(db: Session = Depends(get_db)):
    return crud.list_actuals(db)

@router.post("/actuals", response_model=schemas.LineItem)
def actuals_create(it: schemas.LineItemCreate, db: Session = Depends(get_db)):
    return crud.create_actual_item(db, it)

@router.put("/actuals/{id}", response_model=schemas.LineItem)
def actuals_update(id: str, it: schemas.LineItemBase, db: Session = Depends(get_db)):
    obj = crud.update_actual_item(db, id, it)
    if not obj: raise HTTPException(404, "Not found")
    return obj

@router.delete("/actuals/{id}")
def actuals_delete(id: str, db: Session = Depends(get_db)):
    ok = crud.delete_actual_item(db, id)
    if not ok: raise HTTPException(404, "Not found")
    return {"ok": True}

# ---- CSV import/export ----

@router.post("/import/{kind}")
def import_csv(kind: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = file.file.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))
    count = 0
    if kind == "managers":
        for row in reader:
            crud.create_manager(db, schemas.ManagerCreate(**row))
            count += 1
    elif kind == "accounts":
        for row in reader:
            crud.create_account(db, schemas.AccountCreate(**row))
            count += 1
    elif kind == "budget":
        for row in reader:
            row['amount'] = float(row.get('amount') or 0)
            crud.create_budget_item(db, schemas.LineItemCreate(**row))
            count += 1
    elif kind == "actuals":
        for row in reader:
            row['amount'] = float(row.get('amount') or 0)
            crud.create_actual_item(db, schemas.LineItemCreate(**row))
            count += 1
    else:
        raise HTTPException(400, "Unknown kind")
    return {"ok": True, "count": count}

# ---- Utility: Next line ----
@router.get("/next-line/{kind}/{acct5}")
def next_line(kind: str, acct5: str, db: Session = Depends(get_db)):
    if kind == "budget":
        return {"next": crud.next_line_for_account(db, models.BudgetItem, acct5)}
    elif kind == "actuals":
        return {"next": crud.next_line_for_account(db, models.ActualItem, acct5)}
    else:
        raise HTTPException(400, "Unknown kind")
