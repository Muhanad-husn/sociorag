# Changelog for v1.0.1

## Release Date: May 27, 2025
**Tag:** v1.0.1  
**Commit:** 110524f  
**Type:** Hotfix

## 🛠️ Fixed Issues

### Backend Import Paths
- Fixed import paths in 32 Python files from `app.` to `backend.app.`
- Updated server startup command in `main.py` to use correct module path
- Created utility script `fix_imports.py` to automate import path updates

### API Endpoints
- Fixed "Method Not Allowed" error in LLM settings API endpoint
- Implemented workaround for frozen config by updating .env file
- Added notification for restart requirement after settings change

### Testing Improvements
- Added comprehensive test suite for admin endpoints
- Added specific test for LLM settings API
- Created sample PDF generator for E2E testing

## 📊 Testing Results
- All admin endpoint tests passing (100%)
- Complete E2E test suite passing (100%)
- System ready for production use

## 📝 Documentation Updates
- Added implementation report
- Added test report
- Updated version control documentation

## 🔄 Migration Notes
- Server restart is required after applying this update
- No database schema changes were made
- No API contract changes that would affect clients
