from fastapi import APIRouter, HTTPException, Header
from schema.schemas import BalanceResponse
from modules.users.routes.auth import ADMIN_KEY
from core.db import DB

router = APIRouter(prefix="/banking", tags=["Banking"])

@router.get("/balance/{account_no}", response_model=BalanceResponse)
def get_balance(
    account_no: str,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
):
    # blokir admin melihat saldo
    if x_admin_key == ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admins are not allowed to view balances")

    if account_no not in DB.users or not DB.users[account_no].is_active:
        raise HTTPException(status_code=404, detail="Account not found or inactive")
    return BalanceResponse(account_no=account_no, balance=DB.secrets[account_no].balance)
