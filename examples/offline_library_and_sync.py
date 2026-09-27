"""
Example: Cookidoo Offline Recipe Library, Tagging, Voting, Substitution, and Quota Sync.

Demonstrates:
1. Automatic offline caching of every recipe interacted with.
2. Adding custom tags to official and created recipes.
3. Upvoting (+1), downvoting (-1), and sentiment tracking.
4. Tracking how many times a recipe is added to the weekly meal plan.
5. Marking recipes as excluded from planning / recommendations.
6. Configuring substitutions (e.g., substituting an official pasta with a custom GF recipe).
7. Managing the 50-recipe Cookidoo quota: syncing active recipes while keeping unlimited offline.
"""

from dotenv import load_dotenv
from cookidoo import CookidooClient, OfflineRecipe

load_dotenv()


def main():
    print("==================================================")
    print("Cookidoo Offline Library & Sync Demonstration")
    print("==================================================\n")

    client = CookidooClient()

    # 1. Automatic Offline Caching
    print("1. Ingesting recipes into local offline storage...")
    # Fetching created recipes and recent cooking history automatically caches them
    client.get_created_recipes()
    client.get_cooking_history(limit=5)
    
    # Also fetch details for an official Vorwerk recipe (caches full ingredients & steps offline)
    sample_official_id = "r63350"  # Sandwich bread
    try:
        detail = client.get_recipe_details(sample_official_id, include_note=True)
        print(f"Cached official recipe offline: '{detail.name}' ({detail.id}) with {len(detail.ingredients)} ingredients.")
    except Exception as e:
        print(f"Sample fetch note: {e}")

    # 2. Tagging Recipes
    print("\n2. Tagging recipes with custom categories...")
    tagged = client.tag_recipe(sample_official_id, ["staple", "baking", "comfort-food"])
    print(f"Recipe '{tagged.name}' tags: {tagged.tags}")

    # 3. Sentiment Voting (Upvote / Downvote)
    print("\n3. Recording sentiment votes...")
    upvoted = client.vote_recipe(sample_official_id, 1)
    print(f"Upvoted '{upvoted.name}': Vote = {upvoted.vote} (+1)")

    # 4. Exclusion Flag
    print("\n4. Exclusion from meal planning...")
    excl = client.exclude_recipe(sample_official_id, excluded=False)
    print(f"Recipe '{excl.name}' excluded status: {excl.is_excluded}")

    # 5. Recipe Substitution
    print("\n5. Configuring Recipe Substitutions...")
    # Create or reference a custom substitute
    substitute_id = "cust_gf_bread_001"
    client.storage.save_recipe(OfflineRecipe(
        id=substitute_id,
        name="Artisan Gluten-Free Sandwich Bread",
        source="CUSTOMER",
        ingredients=["400g gluten free flour blend", "10g xanthan gum", "300g warm water", "7g yeast"],
        instructions=["Whisk dry ingredients in bowl", "Add water and knead 3 min", "Proof and bake at 200C for 35m"],
        tags=["gluten-free", "baking"],
        vote=1,
        is_active_on_cookidoo=False  # Stored offline
    ))
    
    # Point the official sandwich bread to the custom gluten-free substitute
    sub_mapped = client.set_recipe_substitution(sample_official_id, substitute_id)
    print(f"Configured substitution for '{sub_mapped.name}' ({sub_mapped.id}) -> Substitute ID: {sub_mapped.substitution_recipe_id}")

    # 6. Listing Offline Recipes
    print("\n6. Querying local offline library...")
    all_offline = client.list_offline_recipes()
    print(f"Total offline recipes cached: {len(all_offline)}")

    baking_recipes = client.list_offline_recipes(tag="baking")
    print(f"Recipes tagged 'baking': {[r.name for r in baking_recipes]}")

    upvoted_recipes = client.list_offline_recipes(vote=1)
    print(f"Upvoted recipes: {[r.name for r in upvoted_recipes]}")

    # 7. Quota Management & Sync
    print("\n7. Quota Management (Maximum 50 created recipes on Cookidoo)...")
    active_count = client.storage.count_active_created_recipes()
    print(f"Active created recipes on Cookidoo: {active_count}/{client.sync_manager.max_active}")
    print(f"Total offline recipes in database: {client.storage.count_all_recipes()}")
    print("Offline recipes can be kept indefinitely without counting towards your Cookidoo quota.")
    print("Use `client.sync_active_recipes([recipe_ids...])` to choose exactly which recipes are synced to your Cookidoo account at any time.")


if __name__ == "__main__":
    main()
