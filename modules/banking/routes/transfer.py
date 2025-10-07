from fastapi import APIRouter, HTTPException
from datetime import datetime, date, UTC
from uuid import uuid4

from core.db import DB
from schema.schemas import (
    TransferRequest, Transaction, StatementResponse,
    MIN_BALANCE, INTERBANK_FEE, MAX_TRANSFER_PER_TX, DAILY_TX_COUNT_LIMIT
)

router = APIRouter(prefix="/banking", tags=["Banking"])

def _today_count(account_no: str) -> int:
    today = date.today()
    return sum(1 for tx in DB.txs[account_no] if tx.created_at.date() == today)

@router.post("/transfer", response_model=list[StatementResponse])
def transfer(req: TransferRequest):
    # validasi akun
    if req.src_account_no not in DB.users or not DB.users[req.src_account_no].is_active:
        raise HTTPException(status_code=404, detail="Source account not found or inactive")
    if req.dst_account_no not in DB.users or not DB.users[req.dst_account_no].is_active:
        raise HTTPException(status_code=404, detail="Destination account not found or inactive")

    # limit jumlah transaksi harian
    if _today_count(req.src_account_no) >= DAILY_TX_COUNT_LIMIT:
        raise HTTPException(status_code=400, detail="Daily transaction count limit reached")

    # limit nominal per transaksi
    if req.amount > MAX_TRANSFER_PER_TX:
        raise HTTPException(status_code=400, detail="Exceeds per-transaction transfer limit")

    src_user = DB.users[req.src_account_no]
    dst_user = DB.users[req.dst_account_no]
    interbank = src_user.bank_name != dst_user.bank_name
    fee = INTERBANK_FEE if interbank else 0

    needed = req.amount + fee
    bal = DB.secrets[req.src_account_no].balance
    if bal - needed < MIN_BALANCE:
        raise HTTPException(status_code=400, detail="Insufficient funds respecting MIN_BALANCE + fees")

    now = datetime.now(UTC)  # menghindari DeprecationWarning

    # debit sumber
    DB.secrets[req.src_account_no].balance -= req.amount
    tx_out = Transaction(
        id=str(uuid4()), account_no=req.src_account_no,
        tx_type="TRANSFER_OUT", amount=req.amount, created_at=now,
        note=f"to {req.dst_account_no}"
    )
    DB.txs[req.src_account_no].append(tx_out)

    # biaya antarbank (jika perlu)
    tx_fee = None
    if fee:
        DB.secrets[req.src_account_no].balance -= fee
        tx_fee = Transaction(
            id=str(uuid4()), account_no=req.src_account_no,
            tx_type="FEE", amount=fee, created_at=now,
            note=f"interbank fee to {dst_user.bank_name}"
        )
        DB.txs[req.src_account_no].append(tx_fee)

    # kredit tujuan
    DB.secrets[req.dst_account_no].balance += req.amount
    tx_in = Transaction(
        id=str(uuid4()), account_no=req.dst_account_no,
        tx_type="TRANSFER_IN", amount=req.amount, created_at=now,
        note=f"from {req.src_account_no}"
    )
    DB.txs[req.dst_account_no].append(tx_in)

    # SELALU kembalikan list[StatementResponse]
    src_txs = [tx_out] + ([tx_fee] if tx_fee else [])
    return [
        StatementResponse(account_no=req.src_account_no, transactions=src_txs),
        StatementResponse(account_no=req.dst_account_no, transactions=[tx_in]),
    ]
