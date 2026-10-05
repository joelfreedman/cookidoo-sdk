# Cookidoo® Python SDK (`cookidoo-sdk`)

A high-performance, strongly-typed Python SDK and CLI for **Cookidoo® (Thermomix)** (`cookidoo.thermomix.com`).

Built by reverse-engineering Vorwerk's internal microservices, OAuth2 CIAM authentication, and Algolia search catalog.

---

## 🌟 Features

- **🍳 Cooking History & Recently Cooked**:
  - View real-time device cooking history, timestamps, and recipe IDs synced from your Thermomix (TM6 / TM5).
- **📝 Created / Custom Recipes**:
  - Fetch, create, update, and delete custom recipes in your Cookidoo account.
  - Full support for Thermomix Time/Temperature/Speed (TTS) annotations and ingredient lists.
- **📅 Meal Planning ("My Week")**:
  - View planned dates and recipes for any month or specific day.
  - Programmatically schedule official and custom recipes to any date (`add_to_plan`).
  - Move or remove planned recipes (`remove_from_plan`).
- **🔍 Blazing-Fast Search (Algolia)**:
  - Instant full-text search across thousands of Cookidoo recipes with rating, time, and popularity sorting.
- **⚡ Lightweight & Resilient**:
  - Direct HTTP client (`httpx`) using session cookie jars—no browser overhead for everyday API operations.
  - Automatic CSRF token injection (`X-XSRF-TOKEN` / `X-CSRF-TOKEN`).
  - Automated headless session renewal via Playwright when cookies expire.

---

## 📦 Installation

```bash
cd cookido-sdk
pip install -e .
```

---

## 🔑 Authentication Setup

Create a `.env` file in `cookido-sdk/`:
```ini
COOKIDOO_EMAIL=your-email@example.com
COOKIDOO_PASSWORD=your-password
COOKIDOO_LOCALE=en-US
```

---

## 💻 CLI Quickstart

The SDK comes with a built-in command-line tool `cookidoo`:

### 1. View Recently Cooked Recipes
```bash
cookidoo history --limit 10
```

### 2. View Custom / Created Recipes
```bash
cookidoo recipes
```

### 3. Check Meal Plan for Today or Specific Date
```bash
cookidoo plan
cookidoo plan 2026-09-26
```

### 4. Search Cookidoo Recipe Catalog
```bash
cookidoo search "risotto"
cookidoo search "sourdough bread"
```

---

## 🐍 Python SDK Usage

### Initialize Client
```python
from cookidoo import CookidooClient

client = CookidooClient()
```

### 1. Cooking History
```python
history = client.get_cooking_history(limit=10)
for entry in history:
    print(f"[{entry.cooked_at.strftime('%Y-%m-%d %H:%M')}] {entry.title} (ID: {entry.recipe.id})")
```

### 2. Meal Planning ("My Week")
```python
# Query planned dates
planned_days = client.get_planned_days()
print("Planned dates:", planned_days)

# Schedule a recipe for a date
client.add_to_plan(day_key="2026-10-15", recipe_id="r63350")

# Read back the plan
day_plan = client.get_planned_day("2026-10-15")
print(f"Recipes planned: {day_plan.recipeIds}")

# Remove recipe from plan
client.remove_from_plan(day_key="2026-10-15", recipe_id="r63350")
```

### 3. Custom Recipes & Photo Uploading
```python
# List created recipes
recipes = client.get_created_recipes()
for r in recipes:
    print(f"{r.name} - Photo: {r.image} - {len(r.ingredients)} ingredients, {len(r.instructions)} steps")

# Create a new rich custom recipe with TM7 guided cooking
new_recipe = client.create_custom_recipe(
    name="Gourmet Wild Mushroom Risotto",
    ingredients=[
        "40 g Parmesan cheese",
        "150 g shallots, halved",
        "40 g olive oil",
        "300 g Arborio rice",
        "750 g hot stock"
    ],
    instructions=[
        "Weigh 40 g Parmesan into mixing bowl. Grate 10 sec/speed 10.",
        "Weigh 150 g shallots and 40 g olive oil into bowl. Chop 5 sec/speed 5.",
        "Sauté 3 min/120°C/speed 1 without measuring cup.",
        "Weigh 300 g rice. Toast 3 min/100°C/\ue003/speed 1 (reverse).",
        "Weigh 750 g stock. Cook 12 min/Varoma/\ue003/speed 1 (reverse)."
    ],
    portions=4,
    tools=["TM7", "TM6"]  # Supports TM7, TM6, TM5
)
print("Appliances:", new_recipe.tools)

# Upload a photo directly to Vorwerk Cloudinary and link it to recipe
updated = client.upload_recipe_image(new_recipe.recipeId, "risotto.jpg")
print("Photo URL:", updated.image)

# Remove photo (resets to Cookidoo default placeholder)
client.remove_recipe_image(new_recipe.recipeId)
```

### 4. Custom Lists & Collections ("My Lists" CRUD)
```python
# 1. List user collections
collections = client.get_custom_lists()
for col in collections:
    print(f"[{col.id}] {col.title} ({col.recipeCount} recipes)")

# 2. Create a new collection
my_list = client.create_custom_list("Weekend Baking")

# 3. Add recipes (official 'r63350' or custom recipe IDs)
client.add_recipes_to_custom_list(my_list.id, ["r63350"])

# 4. View collection details and recipes
detail = client.get_custom_list(my_list.id)
for recipe in detail.recipes:
    print(f" - {recipe.title} ({recipe.id})")

# 5. Rename collection
client.update_custom_list(my_list.id, "Holiday Baking")

# 6. Remove recipe from collection
client.remove_recipe_from_custom_list(my_list.id, "r63350")

# 7. Delete collection
client.delete_custom_list(my_list.id)
```

### 5. Recipe Notes (CRUD Personal Notes on Published Recipes)
```python
# 1. Read note for a recipe (returns None if no note)
note = client.get_recipe_note("r63350")
if note:
    print(f"Personal Note: {note.text}")

# 2. Save / Upsert a note (creates if new, updates if exists)
saved = client.save_recipe_note("r63350", "Tip: Prove dough for an extra 20 min in winter.")
print(f"Saved note: {saved.text}")

# 3. Update note explicitly
client.update_recipe_note("r63350", "Tip: Prove dough for 20 min and brush with butter.")

# 4. View recipe details with note included
detail = client.get_recipe_details("r63350", include_note=True)
print(f"Recipe: {detail.name}, Note: {detail.note}")

# 5. Delete note
client.delete_recipe_note("r63350")
```

### 6. Search and Recipe Details
```python
# Search
results = client.search(query="lasagna", hits_per_page=5)
for r in results.recipes:
    print(f"{r.title} - Rating: {r.rating} - Prep: {r.preparationTime}s")

# Get full recipe details (ingredients, instructions)
detail = client.get_recipe_details("r63350")
print(f"Recipe: {detail.name}")
print("Ingredients:", detail.ingredients)
print("Instructions:", detail.instructions)
```

### 7. Offline Recipe Library, Tagging, Voting, Substitutions & Quota Sync
The SDK includes a zero-dependency SQLite-backed offline library (`.cookidoo_library.db`) that automatically caches **every recipe you interact with** (official or custom, cooked, searched, or planned).

```python
# 1. Add custom tags to ANY recipe (official or created)
client.tag_recipe("r63350", ["comfort-food", "baking", "weekend"])

# 2. Record sentiment votes (+1 upvote, -1 downvote, 0 neutral)
client.vote_recipe("r63350", 1)

# 3. Mark recipe as excluded from meal planning / recommendations
client.exclude_recipe("r63350", excluded=True)

# 4. Point a recipe to an alternate custom substitution (e.g. GF version)
# When scheduled via client.add_to_plan(), the substitute is automatically activated & scheduled!
client.set_recipe_substitution("r63350", substitute_id="my_custom_gf_bread")

# 5. Query offline recipes with filters
baking_recipes = client.list_offline_recipes(tag="baking", vote=1)
for r in baking_recipes:
    print(f"[{r.source}] {r.name} - Planned: {r.times_planned} times")

# 6. Cookidoo 50-Recipe Quota Sync:
# Keep hundreds of recipes offline; push only your desired active selection (<= 50) to Cookidoo:
sync_report = client.sync_active_recipes(["rec_id_1", "rec_id_2", "rec_id_3"])
print(f"Active on Cookidoo: {sync_report['current_active']}/{sync_report['max_active']}")
```

---

## 💻 Offline Library & Sync CLI

```bash
# View offline library
cookidoo offline-recipes
cookidoo offline-recipes --tag baking --vote 1

# View full offline card (ingredients, steps, tags, votes, times planned)
cookidoo offline-recipe r63350

# Tag recipes
cookidoo tag r63350 quick-dinner italian
cookidoo untag r63350 italian

# Upvote / Downvote
cookidoo vote r63350 up
cookidoo vote r63350 down
cookidoo vote r63350 clear

# Exclude recipe from meal planner
cookidoo exclude r63350
cookidoo exclude r63350 --remove

# Map substitution recipe
cookidoo substitute r63350 cust_gf_bread_001
cookidoo substitute r63350 --clear

# Synchronize 50-recipe quota with Cookidoo
cookidoo sync
cookidoo sync --pull
cookidoo sync --activate cust_gf_bread_001
cookidoo sync --archive cust_gf_bread_001
cookidoo sync --desired rec1 rec2 rec3
```

---

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v
```

All 19 integration and unit tests run live against Cookidoo and pass in ~10 seconds.

---

## 📚 Technical Documentation

- See [ENDPOINTS.md](file:///Users/joelfreedman/Workspace/cookido-sdk/ENDPOINTS.md) for full reverse-engineered API documentation, HTTP methods, headers, schemas, and photo upload architecture.
- See [PLAN.md](file:///Users/joelfreedman/Workspace/cookido-sdk/PLAN.md) for project milestones and architectural details.


