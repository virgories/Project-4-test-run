from fastapi import FastAPI
from modules.users.routes import createUser, readUser, updateUser, deleteUser
from modules.banking.routes import deposit, withdraw, transfer, balance, statement

app = FastAPI(title="Digital Banking API (UTS)", version="1.0.0")

# include routers
app.include_router(createUser.router)
app.include_router(readUser.router)
app.include_router(updateUser.router)
app.include_router(deleteUser.router)

app.include_router(deposit.router)
app.include_router(withdraw.router)
app.include_router(transfer.router)
app.include_router(balance.router)
app.include_router(statement.router)

@app.get("/")
def root():
    return {"message": "OK"}
