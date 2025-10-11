
import os, sys, pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.db import reset_all

@pytest.fixture(autouse=True)
def _reset():
    reset_all()
    yield
    reset_all()
