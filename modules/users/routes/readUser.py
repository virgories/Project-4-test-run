from fastapi import APIRouter, Depends, HTTPException
from modules.users.routes.auth import require_admin
from schema.schemas import UserPublic
from core.db import DB

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{account_no}", response_model=UserPublic, dependencies=[Depends(require_admin)])
def get_user(account_no: str):
    user = DB.users.get(account_no)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("", response_model=list[UserPublic], dependencies=[Depends(require_admin)])
def list_users():
    return list(DB.users.values())