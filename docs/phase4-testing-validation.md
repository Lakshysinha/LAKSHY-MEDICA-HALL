# Phase 4 - Testing, Validation & Reliability

Implemented tests:
- low-stock threshold logic.
- sale updates stock correctly.
- invalid sale quantity guard.
- API health/login/medicine/sales/summary flow.

Command:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

Additional static check:

```bash
python -m py_compile run.py wsgi.py pharmacy_app/*.py tests/test_*.py scripts/backup_restore.py
```
