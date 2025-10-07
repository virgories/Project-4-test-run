# core/db.py
from typing import Dict, List
from collections import defaultdict
from schema.schemas import AccountSecret, Transaction, UserPublic

class InMemoryDB:
    def __init__(self):
        self.users: Dict[str, UserPublic] = {}
        self.secrets: Dict[str, AccountSecret] = {}
        self.txs: Dict[str, List[Transaction]] = defaultdict(list)

DB = InMemoryDB()

def next_account_no(seq=[100000]):
    seq[0] += 1
    return str(seq[0])
