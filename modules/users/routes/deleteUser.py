from fastapi import APIRouter, Depends, HTTPException
from modules.users.routes.auth import require_admin
from core.db import DB


router = APIRouter(prefix="/users", tags=["Users"])

@router.delete("/{account_no}", status_code=204, dependencies=[Depends(require_admin)])
def delete_user(account_no: str):
    if account_no not in DB.users:
        raise HTTPException(status_code=404, detail="User not found")
   
    user = DB.users[account_no]
    user.is_active = False
    DB.users[account_no] = user
    return
