"""
Live integration and unit tests for CookidooClient.
"""

from datetime import date, timedelta
import pytest
from cookidoo import CookidooClient
from cookidoo.models import (
    UserProfile,
    CookingHistoryEntry,
    CustomRecipe,
    RecipeSearchResult,
    RecipeDetail,
    PlannedDay,
)


import os
import tempfile

@pytest.fixture(scope="session")
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    c = CookidooClient(db_path=path)
    yield c
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def test_get_profile(client):
    profile = client.get_profile()
    assert isinstance(profile, UserProfile)
    assert profile.dcid is not None
    assert profile.firstname is not None


def test_get_cooking_history(client):
    history = client.get_cooking_history(limit=5)
    assert isinstance(history, list)
    assert len(history) > 0
    entry = history[0]
    assert isinstance(entry, CookingHistoryEntry)
    assert entry.title is not None
    assert entry.cooked_at is not None


def test_get_created_recipes(client):
    recipes = client.get_created_recipes()
    assert isinstance(recipes, list)
    assert len(recipes) > 0
    recipe = recipes[0]
    assert isinstance(recipe, CustomRecipe)
    assert recipe.name is not None
    assert len(recipe.ingredients) > 0


def test_search_recipes(client):
    result = client.search(query="risotto", hits_per_page=5)
    assert isinstance(result, RecipeSearchResult)
    assert result.totalHits > 0
    assert len(result.recipes) > 0
    assert "risotto" in result.recipes[0].title.lower() or result.recipes[0].rating is not None


def test_get_recipe_details(client):
    detail = client.get_recipe_details("r63350")
    assert isinstance(detail, RecipeDetail)
    assert detail.id == "r63350"
    assert "bread" in detail.name.lower()
    assert len(detail.ingredients) > 0
    assert len(detail.instructions) > 0


def test_meal_plan_lifecycle(client):
    target_date = (date.today() + timedelta(days=60)).strftime("%Y-%m-%d")
    test_recipe = "r63350"

    # 1. Add to plan
    added = client.add_to_plan(day_key=target_date, recipe_id=test_recipe)
    assert added is True

    try:
        # 2. Verify planned day
        plan = client.get_planned_day(target_date)
        assert isinstance(plan, PlannedDay)
        assert plan.dayKey == target_date
        assert test_recipe in plan.recipeIds
    finally:
        # 3. Clean up
        removed = client.remove_from_plan(day_key=target_date, recipe_id=test_recipe)
        assert removed is True

    # 4. Verify cleaned up
    cleaned_plan = client.get_planned_day(target_date)
    assert cleaned_plan is None


def test_create_and_delete_custom_recipe(client):
    test_name = "Pytest Custom Focaccia"
    recipe = client.create_custom_recipe(
        name=test_name,
        ingredients=["300 g flour", "200 g water", "5 g salt"],
        instructions=["Warm water 2 min/37°C/speed 2.", "Knead Dough /2 min."],
        portions=4
    )
    assert isinstance(recipe, CustomRecipe)
    assert recipe.recipeId is not None
    assert recipe.name == test_name
    assert len(recipe.ingredients) == 3
    assert len(recipe.instructions) == 2

    # Clean up
    deleted = client.delete_custom_recipe(recipe.recipeId)
    assert deleted is True


def test_custom_list_lifecycle(client):
    test_title = "Pytest Temporary Collection"
    test_recipe = "r63350"

    # 1. Create list
    created = client.create_custom_list(test_title)
    assert created.id is not None
    assert created.title == test_title

    try:
        # 2. Add recipe
        added = client.add_recipes_to_custom_list(created.id, [test_recipe])
        assert added is True

        # 3. Get detail
        detail = client.get_custom_list(created.id)
        assert detail.recipeCount == 1
        assert test_recipe in detail.recipeIds
        assert len(detail.recipes) == 1
        assert detail.recipes[0].id == test_recipe

        # 4. Rename list
        renamed = client.update_custom_list(created.id, "Pytest Renamed Collection")
        assert renamed.title == "Pytest Renamed Collection"

        # 5. Remove recipe
        removed = client.remove_recipe_from_custom_list(created.id, test_recipe)
        assert removed is True
    finally:
        # 6. Delete list
        deleted = client.delete_custom_list(created.id)
        assert deleted is True


def test_custom_recipe_image_upload_and_removal(client):
    from PIL import Image
    import io

    # 1. Create recipe
    recipe = client.create_custom_recipe(name="Pytest Photo Recipe")
    assert recipe.recipeId is not None

    try:
        # 2. Create small test image buffer
        img = Image.new("RGB", (200, 200), color=(100, 180, 240))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        # 3. Upload photo
        updated = client.upload_recipe_image(recipe.recipeId, buf.getvalue(), format="jpg")
        assert updated.image is not None
        assert "ugc.assets.tmecosys.com" in updated.image or "prod/img" in updated.image

        # 4. Remove photo
        cleared = client.remove_recipe_image(recipe.recipeId)
        assert "recipe_image_placeholder" in (cleared.image or "") or cleared.image is None
    finally:
        # 5. Delete recipe
        deleted = client.delete_custom_recipe(recipe.recipeId)
        assert deleted is True


def test_recipe_note_lifecycle(client):
    test_recipe = "r63350"
    note_content = "Pytest personal note: add rosemary to crust."

    # 1. Ensure clean initial state
    try:
        client.delete_recipe_note(test_recipe)
    except Exception:
        pass

    # 2. Create note
    created = client.create_recipe_note(test_recipe, note_content)
    assert created.noteId is not None
    assert created.text == note_content
    assert created.recipeId == test_recipe

    try:
        # 3. Read note
        read_note = client.get_recipe_note(test_recipe)
        assert read_note is not None
        assert read_note.text == note_content

        # 4. Update note
        updated_content = "Pytest personal note: add rosemary and sea salt."
        updated = client.update_recipe_note(test_recipe, updated_content)
        assert updated.text == updated_content

        # 5. Upsert / save_recipe_note
        upserted = client.save_recipe_note(test_recipe, "Pytest personal note: upserted final text.")
        assert upserted.text == "Pytest personal note: upserted final text."

        # 6. Verify in recipe details
        details = client.get_recipe_details(test_recipe, include_note=True)
        assert details.note == "Pytest personal note: upserted final text."
    finally:
        # 7. Delete note
        deleted = client.delete_recipe_note(test_recipe)
        assert deleted is True

    # 8. Verify clean post-state
    assert client.get_recipe_note(test_recipe) is None


