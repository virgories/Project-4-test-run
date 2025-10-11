from fastapi import APIRouter, HTTPException
from datetime import datetime, UTC
from uuid import uuid4

from core.db import DB
from schema.schemas import DepositRequest, Transaction, StatementResponse

router = APIRouter(prefix="/banking", tags=["Banking"])

@router.post("/deposit", response_model=StatementResponse)
def deposit(req: DepositRequest):
    if req.account_no not in DB.users or not DB.users[req.account_no].is_active:
        raise HTTPException(status_code=404, detail="Account not found or inactive")

    DB.secrets[req.account_no].balance += req.amount
    tx = Transaction(
        id=str(uuid4()), account_no=req.account_no,
        tx_type="DEPOSIT", amount=req.amount,
        created_at=datetime.now(UTC), note="cash-in"
    )
    DB.txs[req.account_no].append(tx)
    return StatementResponse(account_no=req.account_no, transactions=[tx])
