# Frontend Testing Files

This directory contains HTML-based test files for frontend functionality testing.

## Test Files

### `test_history_api.html`
- **Purpose**: Basic API connectivity test for the history endpoint
- **Usage**: Open in browser to test if the history API returns data
- **Features**: Simple fetch request to `/api/history/` endpoint

### `debug_history_api.html`
- **Purpose**: Multi-method API testing with axios integration
- **Usage**: Open in browser and click test buttons
- **Features**: 
  - Direct API calls using fetch
  - Axios calls (replicating frontend behavior)
  - CORS testing
  - Real-time result display

### `complete_history_test.html`
- **Purpose**: Comprehensive frontend functionality validation
- **Usage**: Open in browser for full test suite
- **Features**:
  - API connectivity testing
  - Data structure validation
  - Frontend simulation
  - Error scenario testing
  - Performance measurements
  - Complete history page workflow simulation

## How to Use

1. **Start the backend server**: Ensure the SocioRAG backend is running on `http://127.0.0.1:8000`
2. **Open test files**: Use any modern web browser to open the HTML files
3. **Run tests**: Click the test buttons and observe results
4. **Debug issues**: Use browser developer tools to inspect console output

## Test Scenarios Covered

- ✅ API endpoint availability
- ✅ Response data structure validation
- ✅ Frontend API integration patterns
- ✅ Error handling and edge cases
- ✅ Performance characteristics
- ✅ CORS configuration
- ✅ React component simulation

## Created During

These files were created during the SocioRAG history page investigation and verification session on May 31, 2025, to troubleshoot and validate the frontend history functionality.
