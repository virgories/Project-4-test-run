# ---- ensure root is on sys.path ----
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app                        # <-- ini wajib ada
from modules.users.routes.auth import ADMIN_KEY
from schema.schemas import MIN_BALANCE, INTERBANK_FEE, MAX_TRANSFER_PER_TX


client = TestClient(app)

def admin_hdr():
    return {"X-Admin-Key": ADMIN_KEY}

def test_user_crud_and_deposit_withdraw_transfer():
    # create two users (bank A & bank B)
    r = client.post("/users", headers=admin_hdr(), json={"full_name":"Alice","bank_name":"BANKA"})
    assert r.status_code == 200
    a1 = r.json()["account_no"]

    r = client.post("/users", headers=admin_hdr(), json={"full_name":"Bob","bank_name":"BANKB"})
    assert r.status_code == 200
    a2 = r.json()["account_no"]

    # admin can read users (no balance)
    r = client.get(f"/users/{a1}", headers=admin_hdr())
    assert r.status_code == 200 and "full_name" in r.json()

    # deposit ke a1
    r = client.post("/banking/deposit", json={"account_no": a1, "amount": MIN_BALANCE + 200_000})
    assert r.status_code == 200

    # withdraw valid (menyisakan MIN_BALANCE)
    r = client.post("/banking/withdraw", json={"account_no": a1, "amount": 100_000})
    assert r.status_code == 200

    # transfer antarbank: biaya harus terpotong
    # sisa sebelum transfer
    bal_before = client.get(f"/banking/balance/{a1}").json()["balance"]
    r = client.post("/banking/transfer", json={"src_account_no": a1, "dst_account_no": a2, "amount": 50_000})
    assert r.status_code == 200
    bal_after = client.get(f"/banking/balance/{a1}").json()["balance"]
    assert bal_before - bal_after == 50_000 + INTERBANK_FEE

    # penerima bertambah
    bal_dst = client.get(f"/banking/balance/{a2}").json()["balance"]
    assert bal_dst == 50_000

def test_limits():
    # buat akun baru
    a = client.post("/users", headers=admin_hdr(), json={"full_name":"Carol","bank_name":"BANKA"}).json()["account_no"]
    client.post("/banking/deposit", json={"account_no": a, "amount": MIN_BALANCE + 1_000_000})

    # limit nominal per transaksi
    r = client.post("/banking/transfer", json={"src_account_no": a, "dst_account_no": a, "amount": MAX_TRANSFER_PER_TX + 1})
    assert r.status_code == 400

    # limit saldo minimum (force gagal)
    r = client.post("/banking/withdraw", json={"account_no": a, "amount": 1_000_000_000})
    assert r.status_code == 400

def test_patch_cannot_change_bank_name():
    # create user
    r = client.post("/users", headers=admin_hdr(), json={"full_name":"X","bank_name":"BANKA"})
    a = r.json()["account_no"]

    # coba ganti bank_name -> harus 422 (forbid extra) ATAU 400 (guard)
    r = client.patch(f"/users/{a}", headers=admin_hdr(), json={"bank_name":"BANKB"})
    assert r.status_code in (400, 422)

    # pastikan bank_name tetap BANKA
    r = client.get(f"/users/{a}", headers=admin_hdr())
    assert r.json()["bank_name"] == "BANKA"

