from fastapi import FastAPI, Request, Depends, Form, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db import Base, engine, get_db
import schemas, crud, models
from routers import api
import uuid, os
from fastapi import status
from utils.middleware import ContextProcessorMiddleware
from dotenv import load_dotenv
from sqlalchemy import text, select, func
import crud

load_dotenv()  # Load environment variables from .env file

app = FastAPI(title=os.getenv('APPNAME', 'Budget Coder (FastAPI + Jinja2)'))
app.add_middleware(ContextProcessorMiddleware)

app_root = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("APP_ROOT", app_root)
static_dir = os.path.join(app_root, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates_dir = os.path.join(app_root, "templates")
templates = Jinja2Templates(directory=templates_dir)

# Create tables
Base.metadata.create_all(bind=engine)

# Lightweight migration: add vendor_name to actual_items if missing (SQLite)
with engine.connect() as conn:
    try:
        cols = conn.execute(text("PRAGMA table_info(actual_items)")).fetchall()
        colnames = [c[1] for c in cols]
        if 'vendor_name' not in colnames:
            conn.execute(text("ALTER TABLE actual_items ADD COLUMN vendor_name TEXT"))
        # Add vouchno column if missing
        if 'vouchno' not in colnames:
            conn.execute(text("ALTER TABLE actual_items ADD COLUMN vouchno TEXT"))
    except Exception as _e:
        pass

# API router
app.include_router(api.router)

# Utilities
def uuid4():
    return str(uuid.uuid4())

def pad2(s: str) -> str:
    s = "".join(ch for ch in str(s) if ch.isdigit())
    return s.zfill(2)[-2:]

def build_line_items(db, acct5_filter=None, desc_filter=None, manager_filter=None):
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    budget = crud.list_budget(db)
    actuals = crud.list_actuals(db)
    # Build account to manager mapping
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
    return items

def build_budget_items(db, acct5_filter=None, desc_filter=None, manager_filter=None):
    accounts = crud.list_accounts(db)
    budget = crud.list_budget(db)
    # Build account to manager mapping
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
    return items

def build_actual_items(db, acct5_filter=None, desc_filter=None, vendor_filter=None, manager_filter=None):
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
        if vendor_filter and vendor_filter.lower() not in (a.vendor_name or '').lower():
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
    return items

# Pages
@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    actuals = crud.list_actuals(db)
    qp = request.query_params
    acct5_filter = qp.get('acct5') or None
    return templates.TemplateResponse("index.html", {"request": request, "managers": managers, "accounts": accounts, "actuals": actuals, "acct5_filter": acct5_filter, **request.state.context})

@app.get("/managers", response_class=HTMLResponse)
def managers_page(request: Request, db: Session = Depends(get_db)):
    managers = crud.list_managers(db)
    return templates.TemplateResponse("managers.html", {"request": request, "managers": managers, **request.state.context})

@app.get("/accounts", response_class=HTMLResponse)
def accounts_page(request: Request, db: Session = Depends(get_db)):
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    qp = request.query_params
    import_summary = None
    error_message = None
    try:
        if 'created' in qp or 'updated' in qp or 'total' in qp:
            import_summary = {
                'created': int(qp.get('created', '0')),
                'updated': int(qp.get('updated', '0')),
                'total': int(qp.get('total', '0')),
            }
        if 'msg' in qp:
            error_message = qp.get('msg')
    except Exception:
        pass
    return templates.TemplateResponse("accounts.html", {"request": request, "managers": managers, "accounts": accounts, "import_summary": import_summary, "error_message": error_message, **request.state.context})

@app.get("/budgets", response_class=HTMLResponse)
def budgets_page(request: Request, db: Session = Depends(get_db)):
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    return templates.TemplateResponse("budgets.html", {"request": request, "accounts": accounts, "managers": managers, **request.state.context})

@app.get("/assign", response_class=HTMLResponse)
def assign_page(request: Request, db: Session = Depends(get_db)):
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    return templates.TemplateResponse("assign.html", {"request": request, "managers": managers, "accounts": accounts, **request.state.context})

# ---- Managers CRUD (single-record writes) ----
@app.post("/managers/create")
def managers_create(name: str = Form(...), db: Session = Depends(get_db)):
    crud.create_manager(db, schemas.ManagerCreate(id=uuid4(), name=name))
    return RedirectResponse("/managers", status_code=303)

@app.post("/managers/delete/{id}")
def managers_delete(id: str, db: Session = Depends(get_db)):
    crud.delete_manager(db, id)
    return RedirectResponse("/managers", status_code=303)

@app.get("/managers/edit/{id}", response_class=HTMLResponse)
def managers_edit_get(id: str, request: Request, db: Session = Depends(get_db)):
    edit_manager = crud.get_manager(db, id)
    managers = crud.list_managers(db)
    return templates.TemplateResponse("managers.html", {"request": request, "managers": managers, "edit_manager": edit_manager, **request.state.context})

@app.post("/managers/edit/{id}")
def managers_edit_post(id: str, name: str = Form(...), isdefault: str = Form(...), db: Session = Depends(get_db)):
    crud.update_manager(db, id, schemas.ManagerBase(name=name), isdefault=isdefault)
    return RedirectResponse("/managers", status_code=status.HTTP_303_SEE_OTHER)

# ---- Accounts CRUD ----
@app.post("/accounts/create")
def accounts_create(key: str = Form(...), description: str = Form(...), manager_id: str = Form(None), db: Session = Depends(get_db)):
    crud.create_account(db, schemas.AccountCreate(id=uuid4(), key=key, description=description, manager_id=manager_id or None))
    return RedirectResponse("/accounts", status_code=303)

@app.post("/accounts/delete/{id}")
def accounts_delete(id: str, db: Session = Depends(get_db)):
    crud.delete_account(db, id)
    return RedirectResponse("/accounts", status_code=303)

@app.get("/accounts/edit/{id}", response_class=HTMLResponse)
def accounts_edit_get(id: str, request: Request, db: Session = Depends(get_db)):
    edit_account = crud.get_account(db, id)
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    return templates.TemplateResponse("accounts.html", {"request": request, "managers": managers, "accounts": accounts, "edit_account": edit_account, **request.state.context})

@app.post("/accounts/edit/{id}")
def accounts_edit_post(id: str,
    key: str = Form(...),
    description: str = Form(...),
    manager_id: str = Form(None),
    db: Session = Depends(get_db)):
    crud.update_account(db, id, schemas.AccountBase(key=key, description=description, manager_id=manager_id or None))
    return RedirectResponse("/accounts", status_code=status.HTTP_303_SEE_OTHER)

# ---- Budget items ----
@app.post("/budget/create")
def budget_create(acct5: str = Form(...), line: str = Form(...), description: str = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    line = pad2(line)
    crud.create_budget_item(db, schemas.LineItemCreate(id=uuid4(), acct5=acct5, line=line, description=description, amount=amount))
    return RedirectResponse("/budgets", status_code=303)

@app.post("/budget/delete/{id}")
def budget_delete(id: str, db: Session = Depends(get_db)):
    crud.delete_budget_item(db, id)
    return RedirectResponse("/budgets", status_code=303)

# ---- Actuals items ----
@app.post("/actuals/create")
def actuals_create(
    acct5: str = Form(...),
    line: str = Form(...),
    description: str = Form(...),
    amount: float = Form(...),
    seq: str = Form(None),  # Accept as string
    tr_date: str = Form(...),  # Now required
    vendor_name: str = Form(None),
    vouchno: str = Form(None),
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
            tr_date=tr_date,
            vendor_name=vendor_name,
            vouchno=vouchno
        )
    )
    return RedirectResponse("/actuals", status_code=303)

@app.post("/actuals/delete/{id}")
def actuals_delete(id: str, db: Session = Depends(get_db)):
    try:
        ok = crud.delete_actual_item(db, id)
        if not ok:
            return RedirectResponse("/actuals?msg=Not+found", status_code=303)
        return RedirectResponse("/actuals", status_code=303)
    except Exception as e:
        from urllib.parse import quote_plus
        return RedirectResponse(f"/actuals?msg={quote_plus(str(e))}", status_code=303)

@app.get("/actuals/edit/{id}", response_class=HTMLResponse)
def actuals_edit_get(id: str, request: Request, db: Session = Depends(get_db)):
    actual = crud.get_actual_item(db, id)
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    actuals = crud.list_actuals(db)
    return templates.TemplateResponse("actuals.html", {"request": request, "managers": managers, "accounts": accounts, "actuals": actuals, "edit_actual": actual, **request.state.context})

@app.post("/actuals/edit/{id}")
def actuals_edit_post(id: str,
    acct5: str = Form(...),
    line: str = Form(...),
    description: str = Form(...),
    amount: float = Form(...),
    seq: str = Form(None),
    tr_date: str = Form(None),
    vendor_name: str = Form(None),
    vouchno: str = Form(None),
    db: Session = Depends(get_db)):
    line = pad2(line)
    seq_val = None if not seq else float(seq)
    crud.update_actual_item(db, id, schemas.LineItemBase(acct5=acct5, line=line, description=description, amount=amount, seq=seq_val, tr_date=tr_date, vendor_name=vendor_name, vouchno=vouchno))
    return RedirectResponse("/actuals", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/actuals/import")
def actuals_import(db: Session = Depends(get_db)):
    from data import Data
    from urllib.parse import quote_plus
    created = 0
    total = 0
    try:
        d = Data()
        rows = d.load_actual_items() or []
        total = len(rows)
        for r in rows:
            acct5 = (r.get('gl') or '').strip()
            line = pad2(r.get('line') or '')
            desc = (r.get('description') or '').strip()
            amount = float(r.get('amount') or 0.0)
            seq = r.get('seq')
            seq_val = None if not seq else float(seq)
            tr_date = r.get('tr_date') or None
            vendor_name = (r.get('vendor_name') or '').strip() or None
            vouchno = (r.get('vouchno') or '').strip() or None
            if not acct5 or not line or not desc or amount == 0.0:
                continue
            crud.create_actual_item(db, schemas.LineItemCreate(
                id=uuid4(),
                acct5=acct5,
                line=line,
                description=desc,
                amount=amount,
                seq=seq_val,
                tr_date=tr_date,
                vendor_name=vendor_name,
                vouchno=vouchno
            ))
            created += 1
    except Exception as e:
        msg = quote_plus(str(e))
        return RedirectResponse(f"/actuals?msg={msg}", status_code=303)
    return RedirectResponse(f"/actuals?created={created}&total={total}", status_code=303)

@app.get("/api/get/gl-list", response_model=dict)
def test1():
    from data import Data
    d = Data()
    results = d.load_gl_list()
    return {"data": results}

@app.post("/accounts/assign")
def accounts_assign(payload: dict = Body(...), db: Session = Depends(get_db)):
    account_id = payload.get("account_id")
    account_ids = payload.get("account_ids") or ([] if not account_id else [account_id])
    manager_id = payload.get("manager_id")
    if not account_ids:
        return JSONResponse({"ok": False, "error": "No account IDs provided"}, status_code=400)
    assigned = 0
    for aid in account_ids:
        acc = crud.get_account(db, aid)
        if not acc:
            continue
        acc.manager_id = manager_id or None
        assigned += 1
    if assigned:
        db.commit()
    return {"ok": True, "assigned": assigned, "manager_id": manager_id}

# Inline budget upsert (create/update by acct5+line)
@app.post("/budget/upsert")
def budget_upsert(
    acct5: str = Form(...),
    line: str = Form(...),
    description: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db)
):
    line = pad2(line)
    obj, created = crud.upsert_budget_item(db, acct5=acct5, line=line, description=description, amount=amount)
    return {"ok": True, "created": created, "item": {"id": obj.id, "acct5": obj.acct5, "line": obj.line, "description": obj.description, "amount": obj.amount}}

@app.get("/budget/next-line")
def budget_next_line(acct5: str, db: Session = Depends(get_db)):
    nxt = crud.next_line_for_account(db, models.BudgetItem, acct5)
    return {"next": nxt}

@app.get("/actuals", response_class=HTMLResponse)
def actuals_page(request: Request, db: Session = Depends(get_db)):
    managers = crud.list_managers(db)
    accounts = crud.list_accounts(db)
    return templates.TemplateResponse("actuals.html", {"request": request, "managers": managers, "accounts": accounts, **request.state.context})

@app.get("/api/actual-items")
def api_actual_items(request: Request, db: Session = Depends(get_db)):
    qp = request.query_params
    acct5_filter = qp.get('acct5') or None
    desc_filter = qp.get('description') or None
    vendor_filter = qp.get('vendor') or None
    manager_filter = qp.get('manager') or None
    items = build_actual_items(db, acct5_filter, desc_filter, vendor_filter, manager_filter)
    return JSONResponse(content=items)

@app.get("/api/line-items")
def api_line_items(request: Request, db: Session = Depends(get_db)):
    qp = request.query_params
    acct5_filter = qp.get('acct5') or None
    desc_filter = qp.get('description') or None
    manager_filter = qp.get('manager') or None
    items = build_line_items(db, acct5_filter, desc_filter, manager_filter)
    return JSONResponse(content=items)

@app.get("/api/budget-items")
def api_budget_items(request: Request, db: Session = Depends(get_db)):
    qp = request.query_params
    acct5_filter = qp.get('acct5') or None
    desc_filter = qp.get('description') or None
    manager_filter = qp.get('manager') or None
    items = build_budget_items(db, acct5_filter, desc_filter, manager_filter)
    return JSONResponse(content=items)

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

@app.get("/voucher-lines", response_class=HTMLResponse)
def voucher_lines_html(request: Request, vouchno: str = None, db: Session = Depends(get_db)):
    if not vouchno:
        return HTMLResponse("<div class='text-red-600'>No voucher number provided.</div>")
    # Query for voucher lines (replace with your actual query logic)
    try:
        from data.db_connector import DB
        app_root = os.getenv("APP_ROOT", ".")
        sql_path = os.path.join(app_root, "sql", "03-voucher-lines.sql")
        if not os.path.exists(sql_path):
            return HTMLResponse("<div class='text-red-600'>SQL file not found.</div>")
        sql = open(sql_path, "r").read()
        sql = sql.replace("{vouchno}", "?")
        dbconn = DB()
        tax = 0.0
        shipping = 0.0
        total_amount = 0.0
        results = []
        try:
            cursor = dbconn.connection.cursor()
            rows = cursor.execute(sql, vouchno)
            results = [DB.extract_row(row) for row in rows]
            tax = float(results[0].get('tax', 0.0) or 0.0) if results else 0.0
            shipping = float(results[0].get('freight', 0.0) or 0.0) if results else 0.0
            for r in results:
                amt = float(r.get('amount', 0.0) or 0.0)
                total_amount += amt
            total_amount += tax + shipping
        finally:
            try:
                dbconn.connection.close()
            except Exception:
                pass
    except Exception as e:
        return HTMLResponse(f"<div class='text-red-600'>Error: {str(e)}</div>")
    # Render the template
    return templates.TemplateResponse("_voucher_lines.html",
                                      {"request": request,
                                       "rows": results,
                                       "vouchno": vouchno,
                                       "tax": tax,
                                       "shipping": shipping,
                                       "total_amount": total_amount,})

