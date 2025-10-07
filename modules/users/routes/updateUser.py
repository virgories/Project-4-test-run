from fastapi import APIRouter, Depends, HTTPException
from modules.users.routes.auth import require_admin
from schema.schemas import UserUpdate, UserPublic
from core.db import DB


router = APIRouter(prefix="/users", tags=["Users"])

@router.patch("/{account_no}", response_model=UserPublic, dependencies=[Depends(require_admin)])
def update_user(account_no: str, payload: UserUpdate):
    user = DB.users.get(account_no)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    data = user.dict()
    for k, v in payload.dict(exclude_unset=True).items():
        data[k] = v
    updated = UserPublic(**data)
    DB.users[account_no] = updated
    return updated
