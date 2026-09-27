"""
Cookidoo Recipe Synchronization & Quota Manager.

Maintains an unlimited offline recipe collection while enforcing a strict limit
(e.g., maximum 50 recipes) of active custom recipes present on Cookidoo at any one time.
"""

from typing import Dict, List, Optional, Set
from .client import CookidooClient
from .exceptions import CookidooError
from .models import OfflineRecipe
from .storage import CookidooStorage

DEFAULT_MAX_ACTIVE_RECIPES = 50


class CookidooSyncManager:
    """
    Manages synchronizing recipes between local offline storage and Cookidoo,
    ensuring active created recipes on Cookidoo do not exceed the configured limit (<= 50).
    """

    def __init__(
        self,
        client: CookidooClient,
        storage: Optional[CookidooStorage] = None,
        max_active: int = DEFAULT_MAX_ACTIVE_RECIPES
    ):
        self.client = client
        self.storage = storage or CookidooStorage()
        self.max_active = max_active

    def pull_all_from_cookidoo(self) -> List[OfflineRecipe]:
        """
        Fetches all current custom recipes from Cookidoo and saves full offline copies.
        Updates active flags so local storage reflects what is currently live in Cookidoo.
        """
        remote_recipes = self.client.get_created_recipes()
        remote_ids: Set[str] = {r.recipeId for r in remote_recipes}

        # 1. Update existing local recipes that might have been removed on Cookidoo
        local_actives = self.storage.list_recipes(source="CUSTOMER", active_only=True)
        for local_rec in local_actives:
            if local_rec.remote_id not in remote_ids and local_rec.id not in remote_ids:
                local_rec.is_active_on_cookidoo = False
                self.storage.save_recipe(local_rec)

        # 2. Ingest / update all remote recipes locally
        synced: List[OfflineRecipe] = []
        for r in remote_recipes:
            offline = self.storage.upsert_from_custom_recipe(r, is_active=True)
            synced.append(offline)

        return synced

    def activate_recipe(
        self,
        recipe_id: str,
        auto_evict: bool = True
    ) -> OfflineRecipe:
        """
        Uploads/activates a local offline recipe to Cookidoo so it is ready to cook on Thermomix.
        If active count is at max limit (50) and auto_evict is True, archives the least recently
        planned or cooked recipe from Cookidoo first.
        """
        recipe = self.storage.get_recipe(recipe_id)
        if not recipe:
            raise KeyError(f"Recipe '{recipe_id}' does not exist in local library.")

        # Check if already active
        if recipe.is_active_on_cookidoo and recipe.remote_id:
            try:
                # Verify still exists remotely
                self.client.get_created_recipe(recipe.remote_id)
                return recipe
            except Exception:
                recipe.is_active_on_cookidoo = False

        # Check quota
        current_active = self.storage.count_active_created_recipes()
        if current_active >= self.max_active:
            if not auto_evict:
                raise CookidooError(
                    f"Cookidoo active recipe quota reached ({current_active}/{self.max_active}). "
                    f"Archive some recipes before activating new ones, or set auto_evict=True."
                )

            # Auto-evict least recently used recipe
            active_list = self.storage.list_recipes(source="CUSTOMER", active_only=True)
            # Sort by last_planned_at asc, last_cooked_at asc
            active_list.sort(key=lambda r: (r.last_planned_at or r.created_at, r.times_planned))
            evict_target = active_list[0]
            self.archive_recipe(evict_target.id)

        # Create on Cookidoo
        created_remote = self.client.create_custom_recipe(
            name=recipe.name,
            ingredients=recipe.ingredients,
            instructions=recipe.instructions,
            portions=recipe.portions or 4
        )

        # Attach image if we have a valid photo asset or local image file
        if recipe.image_url and "customer-recipe/" in recipe.image_url:
            try:
                # Extract asset name (e.g. prod/img/customer-recipe/xyz.jpg)
                asset_ref = recipe.image_url.split("{transformation}/")[-1]
                self.client.set_recipe_image(created_remote.recipeId, asset_ref)
            except Exception:
                pass

        # Update local storage
        recipe.remote_id = created_remote.recipeId
        recipe.is_active_on_cookidoo = True
        return self.storage.save_recipe(recipe)

    def archive_recipe(self, recipe_id: str) -> OfflineRecipe:
        """
        Removes a custom recipe from Cookidoo to free up account quota,
        while maintaining the complete recipe data in local offline storage.
        """
        recipe = self.storage.get_recipe(recipe_id)
        if not recipe:
            raise KeyError(f"Recipe '{recipe_id}' does not exist in local library.")

        remote_id = recipe.remote_id or (recipe.id if recipe.id.startswith("01") else None)
        if remote_id:
            try:
                self.client.delete_custom_recipe(remote_id)
            except Exception:
                pass

        recipe.is_active_on_cookidoo = False
        recipe.remote_id = None
        return self.storage.save_recipe(recipe)

    def sync_active_selection(self, desired_recipe_ids: List[str]) -> Dict[str, List[str]]:
        """
        Reconciles the user's desired active recipe set (up to max_active) with Cookidoo:
        - Recipes in desired_recipe_ids not currently active are uploaded/pushed to Cookidoo.
        - Currently active recipes NOT in desired_recipe_ids are archived from Cookidoo (kept offline).
        """
        if len(desired_recipe_ids) > self.max_active:
            raise ValueError(
                f"Desired active set contains {len(desired_recipe_ids)} recipes, "
                f"which exceeds maximum limit of {self.max_active}."
            )

        desired_set = set(desired_recipe_ids)
        current_active = self.storage.list_recipes(source="CUSTOMER", active_only=True)

        archived: List[str] = []
        kept: List[str] = []
        activated: List[str] = []

        # 1. Archive recipes not in desired set
        for rec in current_active:
            if rec.id not in desired_set and rec.remote_id not in desired_set:
                self.archive_recipe(rec.id)
                archived.append(rec.id)
            else:
                kept.append(rec.id)

        # 2. Activate missing desired recipes
        for req_id in desired_recipe_ids:
            rec = self.storage.get_recipe(req_id)
            if not rec:
                continue
            if not rec.is_active_on_cookidoo:
                self.activate_recipe(rec.id, auto_evict=False)
                activated.append(rec.id)

        return {
            "activated": activated,
            "archived": archived,
            "kept": kept,
            "current_active": self.storage.count_active_created_recipes(),
            "total_active": self.storage.count_active_created_recipes(),
            "max_active": self.max_active,
        }
