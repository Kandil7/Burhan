# scripts/smoke — manual API smoke scripts

These scripts talk to a **running** Burhan server on `http://localhost:8000`
and print a pass/fail summary per endpoint. They are not pytest files and are
never collected by the test suite; the files carry the `smoke_` prefix to make
that structurally obvious (the architecture test in `tests/test_architecture.py`
fails if any file outside `tests/` is named `test_*.py`).

Start the server first, then run one of these:

```powershell
python scripts/smoke/smoke_all_endpoints.py        # 20 HTTP endpoints, compact
python scripts/smoke/smoke_all_endpoints_suite.py  # longer, detailed output
python scripts/smoke/smoke_api.py                  # single-query walkthrough
```

See the module docstring of each script for what it hits and what it asserts.
