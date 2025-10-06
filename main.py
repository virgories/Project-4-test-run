from fastapi import FastAPI, HTTPException, Header, Depends
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime, date
from uuid import uuid4
from pydantic import BaseModel, Field, constr

# ====== Konstanta aturan sistem ======
MIN_BALANCE = 50_000            # saldo minimum wajib tersisa
INTERBANK_FEE = 6_500           # biaya transfer antar bank
MAX_TRANSFER_PER_TX = 5_000_000 # maksimum nominal per transaksi
DAILY_TX_COUNT_LIMIT = 10       # limit jumlah transaksi harian

# ====== Data Model ======
BankCode = constr(min_length=2, max_length=10)
AccountNo = constr(min_length=6, max_length=20)

class UserCreate(BaseModel):
    full_name: str
    bank_name: BankCode

class UserPublic(BaseModel):
    account_no: AccountNo
    full_name: str
    bank_name: str
    is_active: bool = True

class DepositRequest(BaseModel):
    account_no: AccountNo
    amount: int = Field(gt=0)

class WithdrawRequest(BaseModel):
    account_no: AccountNo
    amount: int = Field(gt=0)

class TransferRequest(BaseModel):
    src_account_no: AccountNo
    dst_account_no: AccountNo
    amount: int = Field(gt=0)

class BalanceResponse(BaseModel):
    account_no: AccountNo
    balance: int

class Transaction(BaseModel):
    id: str
    account_no: AccountNo
    tx_type: str
    amount: int
    created_at: datetime
    note: Optional[str] = None

class StatementResponse(BaseModel):
    account_no: AccountNo
    transactions: List[Transaction]

# ====== Admin Auth Sederhana ======
ADMIN_KEY = "super-secret-admin"

def require_admin(x_admin_key: str = Header(..., alias="X-Admin-Key")):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")

# ====== Database Sederhana (in-memory) ======
class InMemoryDB:
    def __init__(self):
        self.users: Dict[str, UserPublic] = {}
        self.secrets: Dict[str, int] = {}
        self.txs: Dict[str, List[Transaction]] = defaultdict(list)

DB = InMemoryDB()

def next_account_no(seq=[100000]):
    seq[0] += 1
    return str(seq[0])

# ====== App ======
app = FastAPI(title="Digital Banking API (Standalone)", version="0.1")

@app.get("/")
def root():
    return {"message": "Digital Banking API running"}

# ====== Admin Endpoints ======
@app.post("/users", response_model=UserPublic, dependencies=[Depends(require_admin)])
def create_user(payload: UserCreate):
    acc = next_account_no()
    user = UserPublic(account_no=acc, full_name=payload.full_name, bank_name=payload.bank_name)
    DB.users[acc] = user
    DB.secrets[acc] = 0
    return user

@app.get("/users", response_model=List[UserPublic], dependencies=[Depends(require_admin)])
def list_users():
    return list(DB.users.values())

@app.get("/users/{account_no}", response_model=UserPublic, dependencies=[Depends(require_admin)])
def get_user(account_no: str):
    if account_no not in DB.users:
        raise HTTPException(404, "User not found")
    return DB.users[account_no]

@app.delete("/users/{account_no}", status_code=204, dependencies=[Depends(require_admin)])
def deactivate_user(account_no: str):
    if account_no not in DB.users:
        raise HTTPException(404, "User not found")
    user = DB.users[account_no]
    user.is_active = False
    DB.users[account_no] = user

# ====== Banking Endpoints ======
@app.post("/banking/deposit", response_model=StatementResponse)
def deposit(req: DepositRequest):
    if req.account_no not in DB.users or not DB.users[req.account_no].is_active:
        raise HTTPException(404, "Account not found or inactive")
    DB.secrets[req.account_no] += req.amount
    tx = Transaction(id=str(uuid4()), account_no=req.account_no, tx_type="DEPOSIT",
                     amount=req.amount, created_at=datetime.utcnow(), note="cash-in")
    DB.txs[req.account_no].append(tx)
    return StatementResponse(account_no=req.account_no, transactions=[tx])

@app.post("/banking/withdraw", response_model=StatementResponse)
def withdraw(req: WithdrawRequest):
    if req.account_no not in DB.users or not DB.users[req.account_no].is_active:
        raise HTTPException(404, "Account not found or inactive")
    bal = DB.secrets[req.account_no]
    if bal - req.amount < MIN_BALANCE:
        raise HTTPException(400, "Insufficient funds (respecting MIN_BALANCE)")
    DB.secrets[req.account_no] -= req.amount
    tx = Transaction(id=str(uuid4()), account_no=req.account_no, tx_type="WITHDRAW",
                     amount=req.amount, created_at=datetime.utcnow(), note="cash-out")
    DB.txs[req.account_no].append(tx)
    return StatementResponse(account_no=req.account_no, transactions=[tx])

@app.post("/banking/transfer", response_model=List[StatementResponse])
def transfer(req: TransferRequest):
    if req.src_account_no not in DB.users or not DB.users[req.src_account_no].is_active:
        raise HTTPException(404, "Source not found or inactive")
    if req.dst_account_no not in DB.users or not DB.users[req.dst_account_no].is_active:
        raise HTTPException(404, "Destination not found or inactive")
    if req.amount > MAX_TRANSFER_PER_TX:
        raise HTTPException(400, "Exceeds transfer limit per transaction")

    # limit transaksi harian
    today = date.today()
    if sum(1 for tx in DB.txs[req.src_account_no] if tx.created_at.date() == today) >= DAILY_TX_COUNT_LIMIT:
        raise HTTPException(400, "Daily transaction limit reached")

    interbank = DB.users[req.src_account_no].bank_name != DB.users[req.dst_account_no].bank_name
    fee = INTERBANK_FEE if interbank else 0
    need = req.amount + fee
    if DB.secrets[req.src_account_no] - need < MIN_BALANCE:
        raise HTTPException(400, "Insufficient funds (need + fee + MIN_BALANCE)")

    now = datetime.utcnow()
    # debit
    DB.secrets[req.src_account_no] -= req.amount
    tx_out = Transaction(id=str(uuid4()), account_no=req.src_account_no, tx_type="TRANSFER_OUT",
                         amount=req.amount, created_at=now, note=f"to {req.dst_account_no}")
    DB.txs[req.src_account_no].append(tx_out)

    if fee:
        DB.secrets[req.src_account_no] -= fee
        tx_fee = Transaction(id=str(uuid4()), account_no=req.src_account_no, tx_type="FEE",
                             amount=fee, created_at=now, note="interbank fee")
        DB.txs[req.src_account_no].append(tx_fee)
    else:
        tx_fee = None

    # credit
    DB.secrets[req.dst_account_no] += req.amount
    tx_in = Transaction(id=str(uuid4()), account_no=req.dst_account_no, tx_type="TRANSFER_IN",
                        amount=req.amount, created_at=now, note=f"from {req.src_account_no}")
    DB.txs[req.dst_account_no].append(tx_in)

    resp = [StatementResponse(account_no=req.src_account_no, transactions=[tx_out] + ([tx_fee] if tx_fee else [])),
            StatementResponse(account_no=req.dst_account_no, transactions=[tx_in])]
    return resp

@app.get("/banking/balance/{account_no}", response_model=BalanceResponse)
def get_balance(account_no: str):
    if account_no not in DB.users or not DB.users[account_no].is_active:
        raise HTTPException(404, "Account not found or inactive")
    return BalanceResponse(account_no=account_no, balance=DB.secrets[account_no])

@app.get("/banking/statement/{account_no}", response_model=StatementResponse)
def get_statement(account_no: str):
    if account_no not in DB.users or not DB.users[account_no].is_active:
        raise HTTPException(404, "Account not found or inactive")
    return StatementResponse(account_no=account_no, transactions=DB.txs[account_no])

~