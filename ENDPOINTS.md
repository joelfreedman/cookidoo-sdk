# Cookidoo® Reverse-Engineered Endpoints Reference

Documented and verified against `cookidoo.thermomix.com` using live authenticated session.

---

## 1. Authentication & Session Architecture

### Login Flow (Vorwerk CIAM OAuth2 + PKCE)
1. **Entry URL**: `GET https://cookidoo.thermomix.com/profile/{locale}/login`
2. **Redirect 1**: `https://cookidoo.thermomix.com/oauth2/start?market=us&ui_locales={locale}&rd=/profile/{locale}/login`
3. **Redirect 2**: `https://eu.login.vorwerk.com/ciam/login?market=us&requestId=...&ui_locales={locale}&view_type=login`
4. **Form Credentials**:
   - `input#username` (email)
   - `input#password` (password)
   - `button#login-submit-btn` (submit)
5. **Post-Login Session Cookies**:
   - `v-authenticated`: `"true"`
   - `_oauth2_proxy`: Session token (HTTP-only)
   - `v-locale`: e.g. `"en-US"`
   - `v-country`: e.g. `"US"`

Once cookies are stored, subsequent API requests can run directly over standard HTTP (`httpx` / `requests`) using the cookie jar without running a browser.

---

## 2. User Profile Endpoint

- **URL**: `GET https://cookidoo.thermomix.com/profile/api/user`
- **Headers**:
  ```http
  Accept: application/json
  Cookie: <session_cookies>
  ```
- **Response (200 OK)**:
  ```json
  {
    "dcid": "8b2b53ea-3bf4-45da-b9e0-b308def80d8a",
    "country_of_residence": "US",
    "firstname": "Megan",
    "lastname": null
  }
  ```

---

## 3. Cooking History ("Recently Cooked")

- **URL**: `GET https://cookidoo.thermomix.com/organize/{locale}/api/cooking-history`
- **Method**: `GET`
- **Headers**:
  ```http
  Accept: application/json
  ```
- **Response (200 OK)**:
  ```json
  {
    "userId": "8b2b53ea-3bf4-45da-b9e0-b308def80d8a",
    "entries": [
      {
        "details": {
          "timestamp": "2026-09-26T19:56:59.882Z"
        },
        "recipe": {
          "id": "r63350",
          "asciiTitle": "Sandwich bread",
          "language": "en-US",
          "assets": {
            "images": {
              "square": "https://assets.tmecosys.com/image/upload/{transformation}/..."
            }
          }
        }
      }
    ]
  }
  ```

---

## 4. Meal Planning ("My Week")

### A. Query Planned Days in a Date Range
- **URL**: `GET https://cookidoo.thermomix.com/planning/{locale}/api/my-day/planned-recipes/{startDate}?span=1`
- **Example**: `GET /planning/en-US/api/my-day/planned-recipes/2026-09-01?span=1`
- **Response (200 OK)**:
  ```json
  {
    "dayKeys": [
      "2026-09-01",
      "2026-09-04",
      "2026-09-20",
      "2026-09-25",
      "2026-09-26"
    ]
  }
  ```

### B. Query Planned Recipes for a Specific Day
- **URL**: `GET https://cookidoo.thermomix.com/planning/{locale}/api/my-day/{dayKey}`
- **Example**: `GET /planning/en-US/api/my-day/2026-09-26`
- **Response (200 OK)**:
  ```json
  {
    "id": "2026-09-26",
    "dayKey": "2026-09-26",
    "author": "8b2b53ea-3bf4-45da-b9e0-b308def80d8a",
    "date": "2026-09-26T00:00:00.000Z",
    "created": "2026-09-26T19:48:33.679Z",
    "modified": "2026-09-26T22:34:26.265Z",
    "recipeCount": 2,
    "recipeIds": ["r68026", "r63350"],
    "customerRecipeIds": []
  }
  ```

### C. Add Recipe to a Planned Day
- **URL**: `POST https://cookidoo.thermomix.com/planning/{locale}/api/my-day`
- **Form Data (or urlencoded)**:
  ```ini
  _method=put
  recipeSource=VORWERK
  dayKey=2026-10-01
  recipeIds=r63350
  ```
- *Note for Custom Recipes*: use `recipeSource=CUSTOMER` and pass the custom recipe ID.

### D. Remove Recipe from a Planned Day
- **URL**: `POST https://cookidoo.thermomix.com/planning/{locale}/api/my-day/{dayKey}/recipes/{recipeId}?recipeSource=VORWERK`
- **Form Data**:
  ```ini
  _method=delete
  dayKey=2026-10-01
  recipeId=r63350
  recipeSource=VORWERK
  ```

---

## 5. Created Recipes ("Custom Recipes")

### A. List All Created Recipes
- **URL**: `GET https://cookidoo.thermomix.com/created-recipes/{locale}`
- **Headers**:
  ```http
  Accept: application/json
  ```
- **Response (200 OK)**:
  ```json
  {
    "meta": {
      "recipeLimit": 300,
      "recipeLimitThreshold": 5
    },
    "items": [
      {
        "recipeId": "01M2ZZ93XW9F4XDVA75YPWCEJJ",
        "authorId": "8b2b53ea-3bf4-45da-b9e0-b308def80d8a",
        "createdAt": "2026-09-20T17:54:30.972Z",
        "modifiedAt": "2026-09-20T18:11:22.471Z",
        "status": "ACTIVE",
        "workStatus": "PRIVATE",
        "recipeContent": {
          "name": "Gluten Free Orange Syrup Almond Cake",
          "image": "https://ugc.assets.tmecosys.com/image/upload/{transformation}/...",
          "recipeIngredient": ["..."],
          "recipeInstructions": ["..."],
          "tool": ["TM6"],
          "recipeYield": { "value": 4, "unitText": "portion" }
        }
      }
    ]
  }
  ```

### B. Get Single Created Recipe Detail
- **URL**: `GET https://cookidoo.thermomix.com/created-recipes/{locale}/{recipeId}`
- **Headers**: `Accept: application/json`

### C. Create New Blank Custom Recipe
- **URL**: `POST https://cookidoo.thermomix.com/created-recipes/{locale}`
- **Payload**:
  ```json
  {
    "recipeContent": {
      "name": "My Custom Bread",
      "recipeIngredient": [],
      "recipeInstructions": [],
      "tool": ["TM6"],
      "recipeYield": { "value": 4, "unitText": "portion" }
    }
  }
  ```

### D. Update (PATCH) Custom Recipe
- **URL**: `PATCH https://cookidoo.thermomix.com/created-recipes/{locale}/{recipeId}`
- **Payload**: Structured `recipeContent` with:
  - Ingredients array
  - Instructions array with TTS Thermomix annotations:
    - Time/Temp/Speed: e.g. `"3 min/37°C/speed 2"`
    - Reverse blade direction: `\ue003` (or ``)

### E. Delete Custom Recipe
- **URL**: `DELETE https://cookidoo.thermomix.com/created-recipes/{locale}/{recipeId}`

### F. Photo Upload & Asset Linking Architecture
Cookidoo does **not** accept arbitrary external image URLs. The API validates the `image` field against a strict regex schema:
`^((prod|nonprod)/img/customer-recipe/)?[A-Za-z0-9-_]{1,}.(bmp|jpe|jpeg|jpg|png)$` (or `null` to remove).

To attach a photo to a recipe:
1. **Request Signature**:
   - **URL**: `POST https://cookidoo.thermomix.com/created-recipes/{locale}/image/signature`
   - **Payload**:
     ```json
     {
       "timestamp": 1790527349,
       "source": "uw",
       "custom_coordinates": "0,0,300,300"
     }
     ```
   - **Response**: `{"signature": "<sha256_hash>"}`
2. **Direct Upload to Vorwerk Cloudinary**:
   - **URL**: `POST https://vorwerk-users-gc.api-fast-eu.cloudinary.com/v1_1/vorwerk-users-gc/image/upload`
   - **Multipart Form Data**:
     - `file`: `<binary_image_data>`
     - `api_key`: `993585863591145`
     - `timestamp`: `<timestamp>`
     - `signature`: `<signature_from_step_1>`
     - `upload_preset`: `prod-customer-recipe-signed`
     - `source`: `uw`
     - `custom_coordinates`: `0,0,300,300`
   - **Response (200 OK)**:
     ```json
     {
       "public_id": "prod/img/customer-recipe/<unique_asset_id>",
       "format": "jpg"
     }
     ```
3. **Attach to Custom Recipe**:
   - **URL**: `PATCH https://cookidoo.thermomix.com/created-recipes/{locale}/{recipeId}`
   - **Payload**:
     ```json
     {
       "image": "prod/img/customer-recipe/<unique_asset_id>.jpg",
       "isImageOwnedByUser": true
     }
     ```
4. **Remove Photo**:
   - **URL**: `PATCH https://cookidoo.thermomix.com/created-recipes/{locale}/{recipeId}`
   - **Payload**: `{"image": null}`

---

## 6. User Lists & Collections ("My Lists")

### A. List All Collections
- **URL**: `GET https://cookidoo.thermomix.com/organize/{locale}/api/custom-list`
- **Method**: `GET`
- **Response (200 OK)**:
  ```json
  {
    "userId": "8b2b53ea-3bf4-45da-b9e0-b308def80d8a",
    "customlists": [
      {
        "id": "01KK2RQJJM1JGD33SB0W7W6P5C",
        "title": "Passover",
        "recipeCount": 1,
        "recipeIds": ["r749206"],
        "created": "2026-03-06T23:46:38.808Z",
        "modified": "2026-03-06T23:46:59.786Z"
      }
    ]
  }
  ```

### B. Get Single List Detail
- **URL**: `GET https://cookidoo.thermomix.com/organize/{locale}/api/custom-list/{listId}`
- **Method**: `GET`
- **Response (200 OK)**:
  Includes list metadata and `chapters[0]["recipes"]` containing individual recipe items with title, type, and total cooking time.

### C. Create New Collection
- **URL**: `POST https://cookidoo.thermomix.com/organize/{locale}/api/custom-list`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "title": "My New Collection"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "message": "Recipe list was successfully created",
    "content": {
      "id": "01M3HVNS9HRHXJ93H5PBSHK5CJ",
      "title": "My New Collection",
      "recipeCount": 0,
      "recipeIds": []
    }
  }
  ```

### D. Rename Collection
- **URL**: `PUT https://cookidoo.thermomix.com/organize/{locale}/api/custom-list/{listId}`
- **Payload**: `{"title": "Renamed Title"}`
- **Response (200 OK)**: `{"message": "Recipe list was successfully updated"}`

### E. Add Recipe(s) to Collection
- **URL**: `PUT https://cookidoo.thermomix.com/organize/{locale}/api/custom-list/{listId}`
- **Payload**:
  ```json
  {
    "recipeIds": ["r63350"]
  }
  ```
- **Response (200 OK)**

### F. Remove Recipe from Collection
- **URL**: `DELETE https://cookidoo.thermomix.com/organize/{locale}/api/custom-list/{listId}/recipes/{recipeId}`
- **Response (200 OK)**

### G. Delete Collection
- **URL**: `DELETE https://cookidoo.thermomix.com/organize/{locale}/api/custom-list/{listId}`
- **Response (200 OK)**

---

## 7. Recipe Notes (Personal Notes on Recipes)

Users can attach personal tips, variations, and notes (up to 1000 characters) to any published or official Cookidoo recipe.

### A. Get Note for Recipe
- **URL**: `GET https://cookidoo.thermomix.com/recipe-notes/{locale}/recipes/{recipeId}`
- **Response**:
  - `200 OK` (when note exists):
    ```json
    {
      "noteId": "01M3HWAJ3ERZXTRMR5CVADT5MP",
      "userId": "8b2b53ea-3bf4-45da-b9e0-b308def80d8a",
      "recipeId": "r63350",
      "text": "Add extra garlic and herbs to dough.",
      "createdAt": "2026-09-27T16:49:12.305Z",
      "modifiedAt": "2026-09-27T16:49:12.305Z"
    }
    ```
  - `204 No Content` (when no note exists for this recipe)

### B. Create Note
- **URL**: `POST https://cookidoo.thermomix.com/recipe-notes/{locale}/recipes`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "recipeId": "r63350",
    "text": "Add extra garlic and herbs to dough."
  }
  ```
- **Response (201 Created)**: Returns the newly created `RecipeNote` JSON.
- *Note*: If a note already exists for this `recipeId`, Cookidoo returns `400 Bad Request`. Use the update endpoint or `save_recipe_note` upsert helper.

### C. Update Note
- **URL**: `PUT https://cookidoo.thermomix.com/recipe-notes/{locale}/recipes/{recipeId}`
- **Method**: `PUT`
- **Payload**:
  ```json
  {
    "text": "Updated note: add rosemary and sea salt."
  }
  ```
- **Response (200 OK)**: Returns the updated `RecipeNote` JSON.

### D. Delete Note
- **URL**: `DELETE https://cookidoo.thermomix.com/recipe-notes/{locale}/recipes/{recipeId}`
- **Method**: `DELETE`
- **Response (204 No Content)**

---

## 8. Recipe Catalog Search (Algolia)

- **Application ID**: `3TA8NT85XJ`
- **Host**: `https://3ta8nt85xj-dsn.algolia.net/1/indexes/*/queries`
- **Headers**:
  ```http
  x-algolia-application-id: 3TA8NT85XJ
  x-algolia-api-key: <token_from_search_page>
  Content-Type: application/json
  ```
- **Payload**:
  ```json
  {
    "requests": [
      {
        "indexName": "recipes-production",
        "params": "query=bread&hitsPerPage=20"
      }
    ]
  }
  ```


