"""
Unit and integration tests for Cookidoo local offline library, tagging,
sentiment voting, planning count, exclusions, substitutions, and 50-recipe sync quota.
"""

import os
import tempfile
import pytest
from datetime import datetime, timezone

from cookidoo.client import CookidooClient
from cookidoo.models import OfflineRecipe, CustomRecipe, RecipeDetail
from cookidoo.models.custom_recipe import CustomRecipeContent, RecipeYield
from cookidoo.storage import CookidooStorage
from cookidoo.sync import CookidooSyncManager


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def storage(temp_db):
    return CookidooStorage(db_path=temp_db)


def test_storage_basic_crud(storage):
    recipe = OfflineRecipe(
        id="cust-101",
        name="Artisan Sourdough",
        source="CUSTOMER",
        ingredients=["500g bread flour", "350g water", "100g starter", "10g salt"],
        instructions=["Mix and autolyse", "Bulk ferment with stretch and folds", "Shape and cold retard", "Bake at 230C"],
        portions=1,
        prep_time=1800,
        total_time=86400,
        tags=["bread", "baking", "weekend"],
        vote=1,
        is_active_on_cookidoo=True,
    )
    saved = storage.save_recipe(recipe)
    assert saved.id == "cust-101"
    assert saved.name == "Artisan Sourdough"
    assert "bread" in saved.tags
    assert saved.vote == 1

    fetched = storage.get_recipe("cust-101")
    assert fetched is not None
    assert fetched.name == "Artisan Sourdough"
    assert len(fetched.ingredients) == 4
    assert len(fetched.instructions) == 4
    assert fetched.is_active_on_cookidoo is True


def test_storage_tagging(storage):
    recipe = OfflineRecipe(id="r500", name="Official Minestrone", source="VORWERK")
    storage.save_recipe(recipe)

    # Add tags
    updated = storage.tag_recipe("r500", ["soup", "winter", "healthy"])
    assert set(updated.tags) == {"soup", "winter", "healthy"}

    # Add duplicate tag
    updated = storage.tag_recipe("r500", ["soup", "italian"])
    assert set(updated.tags) == {"soup", "winter", "healthy", "italian"}

    # Remove tag
    updated = storage.untag_recipe("r500", "winter")
    assert "winter" not in updated.tags
    assert "soup" in updated.tags


def test_storage_voting(storage):
    recipe = OfflineRecipe(id="r600", name="Risotto ai Funghi", source="VORWERK")
    storage.save_recipe(recipe)

    # Upvote
    up = storage.vote_recipe("r600", 1)
    assert up.vote == 1

    # Downvote
    down = storage.vote_recipe("r600", -1)
    assert down.vote == -1

    # Clear
    neutral = storage.vote_recipe("r600", 0)
    assert neutral.vote == 0


def test_storage_exclusion_and_substitution(storage):
    original = OfflineRecipe(id="r700", name="Classic Lasagna", source="VORWERK")
    storage.save_recipe(original)

    # Exclude from planner/recommendations
    excl = storage.exclude_recipe("r700", excluded=True)
    assert excl.is_excluded is True

    # Configure substitution to a custom GF lasagna
    sub = storage.set_substitution("r700", "cust-gf-lasagna")
    assert sub.substitution_recipe_id == "cust-gf-lasagna"

    # Verify fetch
    fetched = storage.get_recipe("r700")
    assert fetched.is_excluded is True
    assert fetched.substitution_recipe_id == "cust-gf-lasagna"

    # Clear substitution
    cleared = storage.set_substitution("r700", None)
    assert cleared.substitution_recipe_id is None


def test_storage_filtering_and_queries(storage):
    # Seed recipes
    r1 = OfflineRecipe(id="r1", name="Gluten-Free Pancakes", source="CUSTOMER", tags=["breakfast", "gf"], vote=1, is_active_on_cookidoo=True)
    r2 = OfflineRecipe(id="r2", name="Traditional Beef Stew", source="VORWERK", tags=["dinner", "comfort"], vote=1, is_active_on_cookidoo=False)
    r3 = OfflineRecipe(id="r3", name="Coriander Chicken Curry", source="VORWERK", tags=["dinner", "spicy"], vote=-1, is_excluded=True)
    r4 = OfflineRecipe(id="r4", name="Quick Tomato Soup", source="VORWERK", tags=["soup", "quick"], vote=0)

    for r in [r1, r2, r3, r4]:
        storage.save_recipe(r)

    # Filter by tag
    gf_recipes = storage.list_recipes(tag="gf")
    assert len(gf_recipes) == 1
    assert gf_recipes[0].id == "r1"

    # Filter by vote
    upvoted = storage.list_recipes(vote=1)
    assert len(upvoted) == 2

    downvoted = storage.list_recipes(vote=-1)
    assert len(downvoted) == 1
    assert downvoted[0].id == "r3"

    # Filter by exclusion
    excluded = storage.list_recipes(excluded=True)
    assert len(excluded) == 1
    assert excluded[0].id == "r3"

    # Filter by active
    active = storage.list_recipes(active_only=True)
    assert len(active) == 1
    assert active[0].id == "r1"

    # Search query
    searched = storage.list_recipes(query="tomato")
    assert len(searched) == 1
    assert searched[0].id == "r4"


def test_planner_counter_and_cooked_tracking(storage):
    recipe = OfflineRecipe(id="r800", name="Pizza Margherita", source="VORWERK")
    storage.save_recipe(recipe)

    assert recipe.times_planned == 0
    assert recipe.last_planned_at is None

    # Increment planned count
    p1 = storage.increment_planned_count("r800")
    assert p1.times_planned == 1
    assert p1.last_planned_at is not None

    p2 = storage.increment_planned_count("r800")
    assert p2.times_planned == 2

    # Record cooked
    c1 = storage.record_cooked("r800")
    assert c1.last_cooked_at is not None


def test_sync_manager_quota_enforcement(storage):
    # Mock client
    class FakeClient:
        def __init__(self):
            self.created = {}
            self.counter = 0

        def create_custom_recipe(self, name, ingredients, instructions, portions=4):
            self.counter += 1
            remote_id = f"remote-{self.counter}"
            rec = CustomRecipe(
                recipeId=remote_id,
                recipeContent=CustomRecipeContent(
                    name=name,
                    recipeIngredient=ingredients,
                    recipeInstructions=instructions,
                    recipeYield=RecipeYield(value=portions),
                )
            )
            self.created[remote_id] = rec
            return rec

        def delete_custom_recipe(self, recipe_id):
            if recipe_id in self.created:
                del self.created[recipe_id]

        def get_created_recipe(self, recipe_id):
            return self.created[recipe_id]

    fake_client = FakeClient()
    # Set quota max to 3 for testing
    sync_mgr = CookidooSyncManager(client=fake_client, storage=storage, max_active=3)

    # Create 4 offline customer recipes in storage
    for i in range(1, 5):
        storage.save_recipe(OfflineRecipe(
            id=f"local-{i}",
            name=f"Recipe {i}",
            source="CUSTOMER",
            ingredients=["ing 1"],
            instructions=["step 1"],
            times_planned=i,  # local-1 has lowest times_planned
            is_active_on_cookidoo=False
        ))

    # Activate 3 recipes -> should hit quota (3/3)
    sync_mgr.activate_recipe("local-1")
    sync_mgr.activate_recipe("local-2")
    sync_mgr.activate_recipe("local-3")

    assert storage.count_active_created_recipes() == 3
    assert len(fake_client.created) == 3

    # Activate 4th recipe with auto_evict=True
    # local-1 had lowest times_planned (1), so local-1 should be auto-evicted from Cookidoo
    # but still retained 100% in local storage!
    sync_mgr.activate_recipe("local-4", auto_evict=True)

    assert storage.count_active_created_recipes() == 3
    assert len(fake_client.created) == 3

    evicted = storage.get_recipe("local-1")
    assert evicted is not None
    assert evicted.is_active_on_cookidoo is False
    assert evicted.name == "Recipe 1"  # Data fully preserved offline

    activated_4 = storage.get_recipe("local-4")
    assert activated_4.is_active_on_cookidoo is True
    assert activated_4.remote_id in fake_client.created


def test_sync_manager_reconciliation(storage):
    class FakeClient:
        def __init__(self):
            self.created = {}
            self.counter = 0

        def create_custom_recipe(self, name, ingredients, instructions, portions=4):
            self.counter += 1
            remote_id = f"remote-{self.counter}"
            rec = CustomRecipe(
                recipeId=remote_id,
                recipeContent=CustomRecipeContent(
                    name=name,
                    recipeIngredient=ingredients,
                    recipeInstructions=instructions,
                    recipeYield=RecipeYield(value=portions),
                )
            )
            self.created[remote_id] = rec
            return rec

        def delete_custom_recipe(self, recipe_id):
            if recipe_id in self.created:
                del self.created[recipe_id]

        def get_created_recipe(self, recipe_id):
            return self.created[recipe_id]

    fake_client = FakeClient()
    sync_mgr = CookidooSyncManager(client=fake_client, storage=storage, max_active=50)

    # Save 3 recipes offline
    for i in range(1, 4):
        storage.save_recipe(OfflineRecipe(
            id=f"rec-{i}",
            name=f"Recipe {i}",
            source="CUSTOMER",
            ingredients=["water"],
            instructions=["mix"],
            is_active_on_cookidoo=False
        ))

    # Reconcile with desired: ["rec-1", "rec-2"]
    res = sync_mgr.sync_active_selection(["rec-1", "rec-2"])
    assert len(res["activated"]) == 2
    assert res["current_active"] == 2

    # Now reconcile with desired: ["rec-2", "rec-3"] -> rec-1 should be archived, rec-3 activated
    res2 = sync_mgr.sync_active_selection(["rec-2", "rec-3"])
    assert "rec-1" in res2["archived"]
    assert "rec-3" in res2["activated"]
    assert res2["current_active"] == 2

    # rec-1 must still be stored offline
    r1 = storage.get_recipe("rec-1")
    assert r1 is not None
    assert r1.is_active_on_cookidoo is False


def test_client_planner_substitution_and_counter(monkeypatch, temp_db):
    """
    Tests that calling client.add_to_plan automatically substitutes the recipe
    if configured, activates the substitute if needed, and increments the planning count.
    """
    client = CookidooClient(db_path=temp_db)

    # 1. Seed official pasta recipe and custom GF pasta recipe
    client.storage.save_recipe(OfflineRecipe(
        id="r-pasta-1",
        name="Spaghetti Bolognese",
        source="VORWERK",
        substitution_recipe_id="cust-gf-pasta"
    ))
    client.storage.save_recipe(OfflineRecipe(
        id="cust-gf-pasta",
        name="Gluten-Free Spaghetti Bolognese",
        source="CUSTOMER",
        ingredients=["GF pasta", "mince"],
        instructions=["cook sauce", "boil pasta"],
        is_active_on_cookidoo=True,
        remote_id="remote-gf-123"
    ))

    # Mock _request on client
    last_requests = []
    class DummyResp:
        status_code = 200
        def json(self): return {}

    def fake_request(method, endpoint, **kwargs):
        last_requests.append((method, endpoint, kwargs))
        return DummyResp()

    monkeypatch.setattr(client, "_request", fake_request)

    # Schedule r-pasta-1
    result = client.add_to_plan("2026-10-01", "r-pasta-1")
    assert result is True

    # Check request payload - target ID should be substituted to remote-gf-123 and source CUSTOMER!
    assert len(last_requests) == 1
    method, endpoint, kwargs = last_requests[0]
    payload = kwargs["json_data"]
    assert payload["recipeIds"] == ["remote-gf-123"]
    assert payload["recipeSource"] == "CUSTOMER"

    # Check that planned counters were incremented
    orig = client.storage.get_recipe("r-pasta-1")
    sub = client.storage.get_recipe("cust-gf-pasta")
    assert orig.times_planned == 1
    assert sub.times_planned == 1

