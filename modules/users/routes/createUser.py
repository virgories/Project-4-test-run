from fastapi import APIRouter, Depends
from schema.schemas import UserCreate, UserPublic, AccountSecret
from modules.users.routes.auth import require_admin
from core.db import DB, next_account_no


router = APIRouter(prefix="/users", tags=["Users"])

@router.post("", response_model=UserPublic, dependencies=[Depends(require_admin)])
def create_user(payload: UserCreate):
    account_no = next_account_no()
    user = UserPublic(
        account_no=account_no,
        full_name=payload.full_name,
        bank_name=payload.bank_name,
        is_active=True
    )
    DB.users[account_no] = user
    DB.secrets[account_no] = AccountSecret(balance=0)
    return user
