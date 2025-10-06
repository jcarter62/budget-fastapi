import uuid

from fastapi import (APIRouter, Depends, HTTPException,
                     UploadFile, File, Request)
from fastapi import status
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import Table, MetaData
from db import get_db
from data.data import Data
import models
import schemas
import crud
import csv, io
from fastapi.responses import JSONResponse

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

@router.post("/actuals/delete00")
def actuals_delete_line00(db: Session = Depends(get_db)):
    # delete all actual_items with line='00';
    items = crud.list_actuals(db)
    delete_count = 0
    for it in items:
        if it.line == '00':
            crud.delete_actual_item(db, it.id)
            delete_count += 1
    return {"deleted": delete_count}

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

@router.post("/actuals/import")
def actuals_import(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint to import actuals. You can implement your import logic here.
    """
    # TODO: Implement import logic (e.g., parse uploaded file, insert records)
    data = Data()
    actual_items = data.load_actual_items()
    for item in actual_items:
        item['amount'] = float(item.get('amount') or 0)
        crud.create_actual_item(db, schemas.LineItemCreate(**item))
        print(f"Import: {item}")
    return {"status": "success", "message": "Import endpoint reached."}

# ---- Utility: Next line ----
@router.get("/next-line/{kind}/{acct5}")
def next_line(kind: str, acct5: str, db: Session = Depends(get_db)):
    if kind == "budget":
        return {"next": crud.next_line_for_account(db, models.BudgetItem, acct5)}
    elif kind == "actuals":
        return {"next": crud.next_line_for_account(db, models.ActualItem, acct5)}
    else:
        raise HTTPException(400, "Unknown kind")

@router.get("/actual-items")
def api_actual_items(request: Request, db: Session = Depends(get_db)):
    qp = request.query_params
    acct5_filter = qp.get('acct5') or None
    desc_filter = qp.get('description') or None
    vendor_filter = qp.get('vendor') or None
    manager_filter = qp.get('manager') or None
    accounts = crud.list_accounts(db)
    actuals = crud.list_actuals(db)
    acct_manager_map = {a.key: a.manager_id for a in accounts}
    items = []
    for a in actuals:
        if acct5_filter and a.acct5 != acct5_filter:
            continue
        if manager_filter and acct_manager_map.get(a.acct5) != manager_filter:
            continue
        if desc_filter and desc_filter.lower() not in (a.description or '').lower():
            continue
        if vendor_filter and vendor_filter.lower() not in (getattr(a, 'vendor_name', '') or '').lower():
            continue
        items.append({
            "acct5": a.acct5,
            "line": a.line,
            "amount": a.amount,
            "description": a.description,
            "tr_date": getattr(a, 'tr_date', None),
            "vendor_name": getattr(a, 'vendor_name', None),
            "vouchno": getattr(a, 'vouchno', None),
            "manager_id": acct_manager_map.get(a.acct5)
        })
    items.sort(key=lambda r: (r["acct5"], r["line"]))
    return JSONResponse(content=items)

@router.get("/line-items")
def api_line_items(request: Request, db: Session = Depends(get_db)):
    qp = request.query_params
    acct5_filter = qp.get('acct5') or None
    desc_filter = qp.get('description') or None
    manager_filter = qp.get('manager') or None
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    budget = crud.list_budget(db)
    actuals = crud.list_actuals(db)
    acct_manager_map = {a.key: a.manager_id for a in accounts}
    budget_lookup = {(b.acct5, b.line): b.description for b in budget}
    joined = {}
    for b in budget:
        if acct5_filter and b.acct5 != acct5_filter:
            continue
        if manager_filter and acct_manager_map.get(b.acct5) != manager_filter:
            continue
        if desc_filter and desc_filter.lower() not in (b.description or '').lower():
            continue
        k = (b.acct5, b.line)
        joined[k] = {"acct5": b.acct5, "line": b.line, "budget_desc": b.description, "budget": b.amount, "actual": 0.0, "actual_desc": None}
    for a in actuals:
        if acct5_filter and a.acct5 != acct5_filter:
            continue
        if manager_filter and acct_manager_map.get(a.acct5) != manager_filter:
            continue
        if desc_filter and desc_filter.lower() not in (a.description or '').lower():
            continue
        k = (a.acct5, a.line)
        if k not in joined:
            joined[k] = {
                "acct5": a.acct5,
                "line": a.line,
                "budget_desc": budget_lookup.get(k),
                "budget": 0.0,
                "actual": a.amount,
                "actual_desc": a.description
            }
        else:
            joined[k]["actual"] += a.amount
            joined[k]["actual_desc"] = a.description
    items = []
    for (acct5, line), row in joined.items():
        items.append({
            "acct5": acct5, "line": line,
            "budget": row["budget"],
            "actual": row["actual"],
            "variance": row["budget"] - row["actual"],
            "budget_desc": row["budget_desc"],
            "actual_desc": row["actual_desc"],
        })
    items.sort(key=lambda r: (r["acct5"], r["line"]))
    return JSONResponse(content=items)

@router.get("/budget-items")
def api_budget_items(request: Request, db: Session = Depends(get_db)):
    qp = request.query_params
    acct5_filter = qp.get('acct5') or None
    desc_filter = qp.get('description') or None
    manager_filter = qp.get('manager') or None
    accounts = crud.list_accounts(db)
    budget = crud.list_budget(db)
    acct_manager_map = {a.key: a.manager_id for a in accounts}
    items = []
    for b in budget:
        if acct5_filter and b.acct5 != acct5_filter:
            continue
        if manager_filter and acct_manager_map.get(b.acct5) != manager_filter:
            continue
        if desc_filter and desc_filter.lower() not in (b.description or '').lower():
            continue
        items.append({
            "acct5": b.acct5,
            "line": b.line,
            "budget": b.amount,
            "budget_desc": b.description,
            "manager_id": acct_manager_map.get(b.acct5)
        })
    items.sort(key=lambda r: (r["acct5"], r["line"]))
    return JSONResponse(content=items)


@router.post("/budgets/import", status_code=200)
def import_budgets(db: Session = Depends(get_db)):
    """
    Calls data.load_budget_import() and saves returned rows into `budget_items`.
    Expects load_budget_import() to return an iterable of dict-like records.
    """
    from db import engine
    metadata = MetaData()
    try:
        data = Data()
        rows: List[Dict] = data.load_budget_import()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    if not rows:
        return {"imported": 0}

    # Reflect the existing table
    try:
        budget_items = Table("budget_items", metadata, autoload_with=engine)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not reflect table: {exc}")

    # Bulk insert (SQLAlchemy Core)
    try:
        # If rows is a generator, convert to list
        row_list = list(rows)
        for r in row_list:
            amount = r.get('budgetamt', 0)
            desc = r.get('description', '')
            gl_acct = r.get('formattedglacctno', '')
            with engine.begin() as conn:
                conn.execute(budget_items.insert().values(
                    id=uuid.uuid4().hex.lower().replace('-', ''),
                    acct5=gl_acct,
                    line='00',
                    amount=float(amount) if amount is not None else 0.0,
                    description=desc if desc is not None else ''
                    )
                )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Insert failed: {exc}")

    return {"imported": len(row_list)}

@router.post("/budgets/delete_line00", status_code=200)
def delete_budgets00(db: Session = Depends(get_db)):
    """
    Delete all budget_items with line='00';
    """
    delete_count = 0
    try:
        items = crud.list_budget(db)
        for it in items:
            if it.line == '00':
                crud.delete_budget_item(db, it.id)
                delete_count += 1

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Delete failed: {exc}")

    return {"deleted": delete_count}
