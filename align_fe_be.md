You are working on an MVP fullstack project.

## Context
- Backend is already implemented and MUST be treated as the source of truth.
- A frontend exists in `./frontend` and was previously using mock data.
- The frontend includes internal instructions/comments on how data should be consumed.
- Your task is to connect the frontend to the backend with minimal, surgical changes.

---

## Core Rules (STRICT)
- DO NOT modify backend logic or APIs
- DO NOT redesign architecture
- DO NOT over-engineer
- REMOVE all mock data from the frontend
- ADAPT frontend to backend (not the reverse)

---

## Objective
Replace all frontend mock data with real backend API calls and ensure the UI works correctly.

---

## Instructions

### 1. Explore Frontend First
- Traverse `./frontend`
- Identify:
  - Where mock data is used
  - API call placeholders (if any)
  - Expected data structures (interfaces, types, props)

- Pay special attention to:
  - Inline comments / instructions inside the frontend
  - Any documented data format requirements

---

### 2. Locate Backend Endpoints
- Explore backend routes
- Identify available endpoints and their response formats

---

### 3. Align Frontend → Backend (CRITICAL)
For each place using mock data:
- Replace mock data with real API calls to backend
- If data shape differs:
  - Transform data inside the frontend ONLY

Example:
```ts
function adaptBackendResponse(data) {
  // map backend format → frontend expected format
}
DO NOT change backend response structure
4. Remove Mock Data
Delete:
Static mock files
Hardcoded arrays/objects used as fake data
Ensure no component depends on mock data anymore
5. Minimal API Layer (if needed)
Create a simple API utility (e.g., /frontend/src/api/)
Centralize API calls (fetch/axios)
6. Ensure UI Stability
Verify:
Components render correctly with real data
No undefined/null crashes
Basic loading and error handling exists (keep minimal)
7. Clean & Minimal
Remove unused code
Keep changes small and localized
Do NOT introduce new abstractions unless necessary
Output
List of removed mock data locations
Mapping of frontend components → backend endpoints
Any data transformations added
Files modified
Key Principle

This is an MVP:

Prioritize working integration over perfection
Frontend must conform to backend
Keep everything simple and direct