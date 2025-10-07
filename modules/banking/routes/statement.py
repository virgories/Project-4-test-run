from fastapi import APIRouter, HTTPException
from core.db import DB                              # <—
from schema.schemas import StatementResponse

router = APIRouter(prefix="/banking", tags=["Banking"])

@router.get("/statement/{account_no}", response_model=StatementResponse)
def get_statement(account_no: str):
    if account_no not in DB.users or not DB.users[account_no].is_active:
        raise HTTPException(status_code=404, detail="Account not found or inactive")
    return StatementResponse(account_no=account_no, transactions=DB.txs[account_no])
