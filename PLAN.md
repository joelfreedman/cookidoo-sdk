# Cookidoo Python SDK: Architecture & Exploration Plan

## 1. Project Objective & Vision
Build a clean, robust, and strongly-typed Python SDK for **Cookidoo® (Thermomix)** (`cookidoo.thermomix.com`) that enables:
1. **Cooking History & Recently Cooked**: Viewing recently cooked recipes and cooking activity.
2. **Custom Recipes ("Created Recipes")**: Creating, editing, and managing custom recipes with native Thermomix step annotations (time, temperature, blade speed, direction, Varoma, ingredient chips).
3. **Meal Planning ("My Week")**: Managing weekly meal schedules (viewing planned recipes, scheduling recipes for specific dates, moving, and removing items).
4. **Recipe Search & Library**: Searching the official recipe database, fetching ingredients, steps, and collections.
5. **Shopping List & Collections**: Managing the user's shopping list and custom collections.

---

## 2. Technical Strategy & Reverse-Engineering Approach

Cookidoo does not provide a public developer API. It uses Vorwerk's internal microservices, protected by:
- **CIAM OAuth2 & PKCE Authentication** with redirect chains and session cookies (`v-authenticated`, `_oauth2_proxy`, Vorwerk auth tokens).
- **Anti-bot protections** (Cloudflare / TLS fingerprinting / CSRF verification) that periodically break naive HTTP script logins.
- **Regional routing**: Different domains and base paths depending on locale (e.g. `cookidoo.thermomix.com`, `cookidoo.de`, `/foundation/en-US/`, etc.).

### Hybrid Architecture
To ensure maximum reliability and prevent brittleness:
1. **Browser-Assisted Auth / Headless Session Manager**:
   - Supports importing an active browser session (cookies / bearer tokens) or using Playwright / browser agent for interactive login and 2FA.
   - Extracts the authenticated session state, storing it in an encrypted or local `.cookidoo_session.json` cache with automatic renewal.
2. **Direct REST / JSON Client**:
   - Once authenticated, all operational requests (reading history, scheduling meal plans, creating custom recipes) execute through direct, lightweight HTTP requests (`aiohttp` / `requests` / `httpx`).
3. **Structured Pydantic Models**:
   - Strict validation and serialisation for recipes, steps, ingredients, meal plans, and calendar days.

---

## 3. Milestones & Task Breakdown

### Milestone 1: Reconnaissance, Session Interception & Auth Handshake [COMPLETED]
* [x] **Task 1.1**: Set up the exploration harness:
  - Created network logger `tools/explore_session.py` with Playwright Chromium.
* [x] **Task 1.2**: Map the authentication flow:
  - Discovered and mapped Vorwerk CIAM OAuth2 PKCE login (`eu.login.vorwerk.com/ciam/login`).
  - Captured session cookies: `_oauth2_proxy`, `v-authenticated`, `XSRF-TOKEN`, `csrf_`.
* [x] **Task 1.3**: Implement `CookidooAuth`:
  - Implemented session persistence in `.cookidoo_session.json` and automatic re-authentication.
* [x] **Verification Gate 1**: PASSED
  - Queried `https://cookidoo.thermomix.com/profile/api/user` with 200 OK (User: Megan, DCID: `8b2b53ea-3bf4-45da-b9e0-b308def80d8a`).

---

### Milestone 2: Reverse-Engineering & Mapping Target Endpoints [COMPLETED]
* [x] **Task 2.1: Cooking History & Recently Cooked**:
  - Endpoint mapped: `GET /organize/{locale}/api/cooking-history` (200 OK, 53 historical entries retrieved).
* [x] **Task 2.2: Meal Planning ("My Week")**:
  - Endpoints mapped:
    - `GET /planning/{locale}/api/my-day/planned-recipes/{date}?span=1`
    - `GET /planning/{locale}/api/my-day/{dayKey}`
    - `PUT /planning/{locale}/api/my-day` (JSON payload + CSRF headers)
    - `DELETE /planning/{locale}/api/my-day/{dayKey}/recipes/{recipeId}`
* [x] **Task 2.3: Custom Recipes ("Created Recipes")**:
  - Endpoints mapped:
    - `GET /created-recipes/{locale}` (list all)
    - `GET /created-recipes/{locale}/{id}` (detail JSON)
    - `POST /created-recipes/{locale}` (create)
    - `PATCH /created-recipes/{locale}/{id}` (update steps & ingredients)
    - `DELETE /created-recipes/{locale}/{id}` (delete)
* [x] **Task 2.4: Search & Catalog**:
  - Mapped high-speed Algolia search API: `https://3ta8nt85xj-dsn.algolia.net/1/indexes/*/queries`
  - Mapped official recipe details via schema.org LD+JSON.
* [x] **Verification Gate 2**: PASSED
  - Generated comprehensive [ENDPOINTS.md](file:///Users/joelfreedman/Workspace/cookido-sdk/ENDPOINTS.md).

---

### Milestone 3: Python SDK Implementation (`cookidoo-sdk`) [COMPLETED]
* [x] **Task 3.1: Project Scaffolding**:
  - Implemented modular architecture: `cookidoo.client`, `cookidoo.auth`, `cookidoo.models`, `cookidoo.exceptions`.
* [x] **Task 3.2: Implement Pydantic Data Models**:
  - Implemented models for `CookingHistoryEntry`, `PlannedDay`, `CustomRecipe`, `RecipeSearchResult`, `RecipeDetail`.
* [x] **Task 3.3: Implement Client & Services**:
  - Full CRUD operations with automatic CSRF token injection and retry.
* [x] **Verification Gate 3**: PASSED
  - Package installed in editable mode (`pip install -e .`).

---

### Milestone 4: End-to-End Live Verification & Polish [COMPLETED]
* [x] **Task 4.1: Live End-to-End Integration Tests**:
  - Pytest suite `tests/test_client.py` passing 6/6 tests against live endpoints.
  - Successfully scheduled, verified, and removed a planned recipe for `2026-11-20`.
* [x] **Task 4.2: Rich CLI Tool (`cookidoo`)**:
  - `cookidoo history`
  - `cookidoo recipes`
  - `cookidoo plan`
  - `cookidoo search <query>`
* [x] **Task 4.3: Documentation & Examples**:
  - Full documentation in [README.md](file:///Users/joelfreedman/Workspace/cookido-sdk/README.md).
  - Standalone runnable scripts in `examples/`.

---

### Milestone 5: Custom Lists / Collections & Photo Uploading [COMPLETED]
* [x] **Task 5.1: Custom Lists / Collections Full CRUD**:
  - Reverse-engineered `GET /organize/{locale}/api/custom-list` (list collections)
  - `GET /organize/{locale}/api/custom-list/{listId}` (detail & recipe chapters)
  - `POST /organize/{locale}/api/custom-list` (create collection)
  - `PUT /organize/{locale}/api/custom-list/{listId}` (rename & add recipes)
  - `DELETE /organize/{locale}/api/custom-list/{listId}/recipes/{recipeId}` (remove recipe)
  - `DELETE /organize/{locale}/api/custom-list/{listId}` (delete collection)
* [x] **Task 5.2: Recipe Photo Capabilities (File Upload vs URL Reference)**:
  - Reverse-engineered Cookidoo's Cloudinary storage backend (`vorwerk-users-gc` at `ugc.assets.tmecosys.com`).
  - Identified that arbitrary external image URLs are rejected by schema validation regex (`^((prod|nonprod)/img/customer-recipe/)?[A-Za-z0-9-_]{1,}.(bmp|jpe|jpeg|jpg|png)$`).
  - Implemented direct multipart file upload in pure Python via `httpx`:
    1. Signature retrieval via `POST /created-recipes/{locale}/image/signature`
    2. Upload to Cloudinary (`https://vorwerk-users-gc.api-fast-eu.cloudinary.com/v1_1/vorwerk-users-gc/image/upload`)
    3. Patching recipe via `PATCH /created-recipes/{locale}/{recipeId}`
    4. Removing photo (`image: null`)
* [x] **Task 5.3: CLI, Examples, and Tests**:
  - Added `cookidoo lists`, `list`, `list-create`, `list-add`, `list-remove`, `list-delete`, `recipe-upload-image`, `recipe-remove-image`.
  - Created `examples/manage_collections.py` and updated `examples/manage_custom_recipes.py`.
  - Added `test_custom_list_lifecycle` and `test_custom_recipe_image_upload_and_removal` (9/9 tests passing).

---

### Milestone 6: Personal Recipe Notes for Published Recipes [COMPLETED]
* [x] **Task 6.1: Reverse-Engineering Recipe Notes Service**:
  - Mapped `GET /recipe-notes/{locale}/recipes/{recipeId}` (returns 200 with JSON or 204 No Content).
  - Mapped `POST /recipe-notes/{locale}/recipes` with `{"recipeId": "...", "text": "..."}` (201 Created).
  - Mapped `PUT /recipe-notes/{locale}/recipes/{recipeId}` with `{"text": "..."}` (200 OK).
  - Mapped `DELETE /recipe-notes/{locale}/recipes/{recipeId}` (204 No Content).
* [x] **Task 6.2: SDK & Model Implementation**:
  - Created `RecipeNote` Pydantic model (`cookidoo/models/note.py`).
  - Implemented `get_recipe_note`, `create_recipe_note`, `update_recipe_note`, `save_recipe_note` (upsert), and `delete_recipe_note` in `CookidooClient`.
  - Integrated `note` field directly into `client.get_recipe_details(recipe_id)`.
* [x] **Task 6.3: CLI, Example, and Live Integration Test**:
  - Added CLI commands: `cookidoo note <recipe_id>`, `cookidoo note-set <recipe_id> <text>`, `cookidoo note-delete <recipe_id>`.
  - Created `examples/manage_recipe_notes.py`.
  - Added `test_recipe_note_lifecycle` to `tests/test_client.py` (10/10 tests passing).

---

### Milestone 7: Offline Library, Tagging, Voting, Substitutions & 50-Recipe Sync Quota [COMPLETED]
* [x] **Task 7.1: Zero-Dependency SQLite Storage Engine**:
  - Implemented `CookidooStorage` (`cookidoo/storage.py`) backed by `.cookidoo_library.db`.
  - Built `OfflineRecipe` model (`cookidoo/models/offline_recipe.py`) storing full ingredients, instructions, notes, custom tags, upvote/downvote scores, planning counters, exclusions, and substitution links.
  - Transparent auto-caching: Every recipe accessed via history, created recipes, search, or recipe details is saved offline automatically.
* [x] **Task 7.2: Custom Tagging, Voting, and Exclusions**:
  - `tag_recipe` and `untag_recipe` for both official Vorwerk and user-created recipes.
  - Sentiment tracking: `vote_recipe` with +1 (upvote), -1 (downvote), or 0 (neutral).
  - Exclusions: `exclude_recipe` flag to prevent recipes from being suggested or planned.
  - Planner frequency: `increment_planned_count` tracked every time a recipe is added to the weekly planner.
* [x] **Task 7.3: Smart Recipe Substitutions in Meal Planner**:
  - `set_recipe_substitution`: Link any recipe to an alternate custom recipe (e.g. mapping official pasta to a custom gluten-free version).
  - Integrated into `client.add_to_plan`: automatically detects substitutions, activates the substitute if offline, schedules the substitute on Thermomix, and tracks usage counts for both.
* [x] **Task 7.4: 50-Recipe Cookidoo Quota Sync Manager**:
  - Implemented `CookidooSyncManager` (`cookidoo/sync.py`):
    - Stores an unlimited number of created recipes offline.
    - Strictly enforces the Cookidoo maximum limit of 50 active recipes.
    - `activate_recipe` pushes/creates on Cookidoo with auto-eviction of least recently planned/cooked recipes when at quota.
    - `archive_recipe` deletes from Cookidoo to free up quota while keeping 100% full offline record.
    - `sync_active_selection` reconciles Cookidoo state with any desired subset of recipes.
* [x] **Task 7.5: CLI, Examples, and Tests**:
  - Added CLI commands: `offline-recipes`, `offline-recipe`, `tag`, `untag`, `vote`, `exclude`, `substitute`, `sync`.
  - Created runnable example `examples/offline_library_and_sync.py`.
  - Added unit and integration tests in `tests/test_storage_and_sync.py` (all 19 tests in test suite passing).

---

## 4. Verification & Testing Matrix

| Stage | Feature | Verification Method | Pass Criteria |
|---|---|---|---|
| **Gate 1** | Authentication | Session validation script | Valid session cookie/token obtained; `/profile` returns 200 OK with user ID |
| **Gate 2** | History Discovery | Network flow inspection & probe script | JSON response containing recently cooked recipe IDs, dates, and names |
| **Gate 3** | Meal Plan CRUD | Automated integration test | Query week -> Add recipe to specific date -> Verify in response -> Delete recipe |
| **Gate 4** | Custom Recipe CRUD | Step annotation builder test | Create custom recipe -> Validate TTS chips render correctly -> Delete draft recipe |
| **Gate 5** | Collections CRUD | Automated integration test | Create list -> Add recipe -> Verify -> Rename -> Remove -> Delete list |
| **Gate 6** | Photo Upload | Cloudinary signed upload test | Direct Python upload -> Asset ID linked -> Live image verified -> Cleaned up |
| **Gate 7** | Recipe Notes CRUD | Automated integration test | Create note -> Read -> Update -> Read -> Delete -> Verify 204 |
| **Gate 8** | Offline & Quota Sync | Storage & sync test suite | Full offline caching -> Tagging -> Upvote/downvote -> Substituted in planner -> 50 quota enforced with auto-eviction |


