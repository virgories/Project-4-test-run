from fastapi import APIRouter, HTTPException
from core.db import DB                              # <—
from schema.schemas import BalanceResponse

router = APIRouter(prefix="/banking", tags=["Banking"])

@router.get("/balance/{account_no}", response_model=BalanceResponse)
def get_balance(account_no: str):
    if account_no not in DB.users or not DB.users[account_no].is_active:
        raise HTTPException(status_code=404, detail="Account not found or inactive")
    return BalanceResponse(account_no=account_no, balance=DB.secrets[account_no].balance)
