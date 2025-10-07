from fastapi import Header, HTTPException, status

ADMIN_KEY = "super-secret-admin"  # ganti saat demo kalau mau

def require_admin(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin key")
