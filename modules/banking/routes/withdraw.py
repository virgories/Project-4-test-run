from fastapi import APIRouter, HTTPException
from datetime import datetime, UTC
from uuid import uuid4
from core.db import DB                              # <—
from schema.schemas import WithdrawRequest, Transaction, StatementResponse, MIN_BALANCE

router = APIRouter(prefix="/banking", tags=["Banking"])

@router.post("/withdraw", response_model=StatementResponse)
def withdraw(req: WithdrawRequest):
    if req.account_no not in DB.users or not DB.users[req.account_no].is_active:
        raise HTTPException(status_code=404, detail="Account not found or inactive")

    bal = DB.secrets[req.account_no].balance
    if bal - req.amount < MIN_BALANCE:
        raise HTTPException(status_code=400, detail="Insufficient funds respecting MIN_BALANCE")

    DB.secrets[req.account_no].balance -= req.amount
    tx = Transaction(
        id=str(uuid4()), account_no=req.account_no,
        tx_type="WITHDRAW", amount=req.amount,
        created_at=datetime.now(UTC), note="cash-out"
    )
    DB.txs[req.account_no].append(tx)
    return StatementResponse(account_no=req.account_no, transactions=[tx])
