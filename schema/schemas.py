from pydantic import BaseModel, Field, constr
from typing import Optional, Literal, List
from datetime import datetime


MIN_BALANCE: int = 50_000           
INTERBANK_FEE: int = 6_500          
MAX_TRANSFER_PER_TX: int = 5_000_000  
DAILY_TX_COUNT_LIMIT: int = 10        

BankCode = constr(strip_whitespace=True, min_length=2, max_length=10)
AccountNo = constr(strip_whitespace=True, min_length=6, max_length=20)

class UserCreate(BaseModel):
    full_name: constr(min_length=3)
    bank_name: constr(min_length=2, max_length=10)

class UserUpdate(BaseModel):
    full_name: Optional[constr(min_length=3)] = None
    is_active: Optional[bool] = None

    class Config:
        extra = "forbid"

class UserPublic(BaseModel):
    account_no: AccountNo
    full_name: str
    bank_name: str
    is_active: bool

class AccountSecret(BaseModel):
    balance: int = 0


TxType = Literal["DEPOSIT", "WITHDRAW", "TRANSFER_OUT", "TRANSFER_IN", "FEE"]

class Transaction(BaseModel):
    id: str
    account_no: AccountNo
    tx_type: TxType
    amount: int
    created_at: datetime
    note: Optional[str] = None

class DepositRequest(BaseModel):
    account_no: AccountNo
    amount: int = Field(gt=0)

class WithdrawRequest(BaseModel):
    account_no: AccountNo
    amount: int = Field(gt=0)

class TransferRequest(BaseModel):
    src_account_no: AccountNo
    dst_account_no: AccountNo
    amount: int = Field(gt=0)

class BalanceResponse(BaseModel):
    account_no: AccountNo
    balance: int

class StatementResponse(BaseModel):
    account_no: AccountNo
    transactions: List[Transaction]
