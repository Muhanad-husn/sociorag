# Phase 6 Unstaged Files Management

## Files to Keep and Commit

### New Documentation Files
- PHASE6_HOUSEKEEPING_REPORT.md
- docs/api_endpoints_reference.md
- docs/phase6_housekeeping_summary.md
- docs/phase6_implementation_summary.md 
- docs/phase6_progress_status_report.md
- docs/phase7_implementation_plan.md

### New API Implementation Files
- backend/app/api/admin.py
- backend/app/api/documents.py
- backend/app/api/export.py 
- backend/app/api/history.py (rename to history_new.py since that's what's imported)
- backend/app/api/search.py
- backend/app/api/websocket.py (rename to websocket_new.py since that's what's imported)

### New Scripts
- scripts/backup_phase6.ps1
- scripts/prepare_phase7.ps1
- scripts/test_phase6_api.py

### Modified Files
- README.md
- backend/app/api/qa.py
- instructions/phase6_deep_dive_plan.md
- requirements.txt

## Files to Discard

### Backup Files (Redundant)
- backend/app/api/export_backup.py
- backend/app/api/search_backup.py
- backend/app/api/search_backup2.py
- backend/app/api/search_backup3.py
- backend/app/api/search_new.py
- backend/app/api/websocket_backup.py

### Generated/Temporary Files (Should not be tracked)
- graph.db-shm
- graph.db-wal

### Redundant Scripts
- scripts/test_api_endpoints.py (if functionality covered by test_phase6_api.py)

## Action Plan

1. Rename history.py to history_new.py (as imported in main.py)
2. Rename websocket.py to websocket_new.py (as imported in main.py)
3. Add and commit files to keep
4. Remove backup and temporary files
