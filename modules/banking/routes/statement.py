from fastapi import APIRouter, HTTPException, Header
from schema.schemas import StatementResponse
from modules.users.routes.auth import ADMIN_KEY
from core.db import DB

router = APIRouter(prefix="/banking", tags=["Banking"])

@router.get("/statement/{account_no}", response_model=StatementResponse)
def get_statement(
    account_no: str,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
):
    
    if x_admin_key == ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admins are not allowed to view statements")

    if account_no not in DB.users or not DB.users[account_no].is_active:
        raise HTTPException(status_code=404, detail="Account not found or inactive")
    return StatementResponse(account_no=account_no, transactions=DB.txs[account_no])
