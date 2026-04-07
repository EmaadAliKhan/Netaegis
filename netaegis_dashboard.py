"""
NetAegis — compatibility shim.

Prefer:
    streamlit run app.py

This file exists so older docs / scripts that reference ``netaegis_dashboard.py``
still work. The DB package is ``backend.common``, not ``app``, so the
Streamlit entry can safely live in ``app.py``.
"""
from app import main

main()
