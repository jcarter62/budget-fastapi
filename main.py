from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import Base, engine, get_db
import schemas, crud
from routers import api
import io, uuid, os, openpyxl
from fastapi import status

app = FastAPI(title="Budget Coder (FastAPI + Jinja2)")

app_root = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(app_root, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates_dir = os.path.join(app_root, "templates")
templates = Jinja2Templates(directory=templates_dir)

# Create tables
Base.metadata.create_all(bind=engine)

# API router
app.include_router(api.router)

# Utilities
def uuid4():
    return str(uuid.uuid4())

def pad2(s: str) -> str:
    s = "".join(ch for ch in str(s) if ch.isdigit())
    return s.zfill(2)[-2:]

# Pages
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    budget = crud.list_budget(db)
    actuals = crud.list_actuals(db)
    # Build line items view (budget vs actuals)
    budget_lookup = {(b.acct5, b.line): b.description for b in budget}
    joined = {}
    for b in budget:
        k = (b.acct5, b.line)
        joined[k] = {"acct5": b.acct5, "line": b.line, "budget_desc": b.description, "budget": b.amount, "actual": 0.0, "actual_desc": None}
    for a in actuals:
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
    return templates.TemplateResponse("index.html", {"request": request, "managers": managers, "accounts": accounts, "items": items, "actuals": actuals})

# ---- Managers CRUD (single-record writes) ----
@app.post("/managers/create")
def managers_create(name: str = Form(...), db: Session = Depends(get_db)):
    crud.create_manager(db, schemas.ManagerCreate(id=uuid4(), name=name))
    return RedirectResponse("/", status_code=303)

@app.post("/managers/delete/{id}")
def managers_delete(id: str, db: Session = Depends(get_db)):
    crud.delete_manager(db, id)
    return RedirectResponse("/", status_code=303)

@app.get("/managers/edit/{id}", response_class=HTMLResponse)
def managers_edit_get(id: str, request: Request, db: Session = Depends(get_db)):
    edit_manager = crud.get_manager(db, id)
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    budget = crud.list_budget(db)
    actuals = crud.list_actuals(db)
    budget_lookup = {(b.acct5, b.line): b.description for b in budget}
    joined = {}
    for b in budget:
        k = (b.acct5, b.line)
        joined[k] = {"acct5": b.acct5, "line": b.line, "budget_desc": b.description, "budget": b.amount, "actual": 0.0, "actual_desc": None}
    for a in actuals:
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
    return templates.TemplateResponse("index.html", {"request": request, "managers": managers, "accounts": accounts, "items": items, "actuals": actuals, "edit_manager": edit_manager})

@app.post("/managers/edit/{id}")
def managers_edit_post(id: str, name: str = Form(...), db: Session = Depends(get_db)):
    crud.update_manager(db, id, schemas.ManagerBase(name=name))
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

# ---- Accounts CRUD ----
@app.post("/accounts/create")
def accounts_create(key: str = Form(...), description: str = Form(...), manager_id: str = Form(None), db: Session = Depends(get_db)):
    crud.create_account(db, schemas.AccountCreate(id=uuid4(), key=key, description=description, manager_id=manager_id or None))
    return RedirectResponse("/", status_code=303)

@app.post("/accounts/delete/{id}")
def accounts_delete(id: str, db: Session = Depends(get_db)):
    crud.delete_account(db, id)
    return RedirectResponse("/", status_code=303)

@app.get("/accounts/edit/{id}", response_class=HTMLResponse)
def accounts_edit_get(id: str, request: Request, db: Session = Depends(get_db)):
    edit_account = crud.get_account(db, id)
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    budget = crud.list_budget(db)
    actuals = crud.list_actuals(db)
    budget_lookup = {(b.acct5, b.line): b.description for b in budget}
    joined = {}
    for b in budget:
        k = (b.acct5, b.line)
        joined[k] = {"acct5": b.acct5, "line": b.line, "budget_desc": b.description, "budget": b.amount, "actual": 0.0, "actual_desc": None}
    for a in actuals:
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
    return templates.TemplateResponse("index.html", {"request": request, "managers": managers, "accounts": accounts, "items": items, "actuals": actuals, "edit_account": edit_account})

@app.post("/accounts/edit/{id}")
def accounts_edit_post(id: str,
    key: str = Form(...),
    description: str = Form(...),
    manager_id: str = Form(None),
    db: Session = Depends(get_db)):
    crud.update_account(db, id, schemas.AccountBase(key=key, description=description, manager_id=manager_id or None))
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

# ---- Budget items ----
@app.post("/budget/create")
def budget_create(acct5: str = Form(...), line: str = Form(...), description: str = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    line = pad2(line)
    crud.create_budget_item(db, schemas.LineItemCreate(id=uuid4(), acct5=acct5, line=line, description=description, amount=amount))
    return RedirectResponse("/", status_code=303)

@app.post("/budget/delete/{id}")
def budget_delete(id: str, db: Session = Depends(get_db)):
    crud.delete_budget_item(db, id)
    return RedirectResponse("/", status_code=303)

# ---- Actuals items ----
@app.post("/actuals/create")
def actuals_create(
    acct5: str = Form(...),
    line: str = Form(...),
    description: str = Form(...),
    amount: float = Form(...),
    seq: str = Form(None),  # Accept as string
    tr_date: str = Form(...),  # Now required
    db: Session = Depends(get_db)
):
    line = pad2(line)
    seq_val = None if not seq else float(seq)
    crud.create_actual_item(
        db,
        schemas.LineItemCreate(
            id=uuid4(),
            acct5=acct5,
            line=line,
            description=description,
            amount=amount,
            seq=seq_val,
            tr_date=tr_date
        )
    )
    return RedirectResponse("/", status_code=303)

@app.post("/actuals/delete/{id}")
def actuals_delete(id: str, db: Session = Depends(get_db)):
    crud.delete_actual_item(db, id)
    return RedirectResponse("/", status_code=303)

# ---- CSV export ----
@app.get("/export/{kind}")
def export_xlsx(kind: str, db: Session = Depends(get_db)):
    if kind == "managers":
        rows = crud.list_managers(db)
        headers = ["id","name"]
        data = [[str(r.id), r.name] for r in rows]
    elif kind == "accounts":
        rows = crud.list_accounts(db)
        headers = ["id","GL","description","manager_id"]
        data = [[str(r.id), r.key, r.description, r.manager_id or ""] for r in rows]
    elif kind == "budget":
        rows = crud.list_budget(db)
        headers = ["id","GL","line","description","amount"]
        # Force acct5 and line to be strings
        data = [[str(r.id), str(r.acct5), str(r.line), r.description, f"{r.amount:.2f}"] for r in rows]
    elif kind == "actuals":
        rows = crud.list_actuals(db)
        headers = ["id","GL","line","description","amount"]
        data = [[str(r.id), str(r.acct5), str(r.line), r.description, f"{r.amount:.2f}"] for r in rows]
    else:
        headers, data = ["message"], [["unknown kind"]]

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in data:
        ws.append(row)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={kind}.xlsx"})

@app.get("/actuals/edit/{id}", response_class=HTMLResponse)
def actuals_edit_get(id: str, request: Request, db: Session = Depends(get_db)):
    actual = crud.get_actual_item(db, id)
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    budget = crud.list_budget(db)
    actuals = crud.list_actuals(db)
    # Pass edit_actual to template
    # Reuse home logic for joined items
    budget_lookup = {(b.acct5, b.line): b.description for b in budget}
    joined = {}
    for b in budget:
        k = (b.acct5, b.line)
        joined[k] = {"acct5": b.acct5, "line": b.line, "budget_desc": b.description, "budget": b.amount, "actual": 0.0, "actual_desc": None}
    for a in actuals:
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
            joined[k]["actual"] = a.amount
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
    return templates.TemplateResponse("index.html", {"request": request, "managers": managers, "accounts": accounts, "items": items, "actuals": actuals, "edit_actual": actual})

@app.post("/actuals/edit/{id}")
def actuals_edit_post(id: str,
    acct5: str = Form(...),
    line: str = Form(...),
    description: str = Form(...),
    amount: float = Form(...),
    seq: str = Form(None),
    tr_date: str = Form(None),
    db: Session = Depends(get_db)):
    line = pad2(line)
    seq_val = None if not seq else float(seq)
    crud.update_actual_item(db, id, schemas.LineItemBase(acct5=acct5, line=line, description=description, amount=amount, seq=seq_val))
    # Update tr_date if present
    actual = crud.get_actual_item(db, id)
    if actual and tr_date is not None:
        actual.tr_date = tr_date
        db.commit(); db.refresh(actual)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
