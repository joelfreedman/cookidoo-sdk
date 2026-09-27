"""
Example: Manage Custom Recipe Lists / Collections (CRUD).

Demonstrates:
1. Listing existing collections.
2. Creating a new collection.
3. Adding recipes to the collection.
4. Viewing collection details and recipes.
5. Renaming the collection.
6. Removing a recipe from the collection.
7. Deleting the collection.
"""

from cookidoo import CookidooClient


def main():
    client = CookidooClient()

    print("=== 1. Listing User Collections ===")
    collections = client.get_custom_lists()
    print(f"Found {len(collections)} collections:")
    for cl in collections:
        print(f" - [{cl.id}] {cl.title} ({cl.recipeCount} recipes)")

    print("\n=== 2. Creating a New Collection ===")
    test_title = "Weekend Baking Experiments"
    my_list = client.create_custom_list(test_title)
    print(f"Created list: '{my_list.title}' with ID: {my_list.id}")

    try:
        print("\n=== 3. Adding Recipes to Collection ===")
        # Sandwich Bread (official Vorwerk recipe r63350)
        client.add_recipes_to_custom_list(my_list.id, ["r63350"])
        print("Added 'Sandwich Bread' (r63350)")

        print("\n=== 4. Fetching Detailed Collection ===")
        detail = client.get_custom_list(my_list.id)
        print(f"Collection: {detail.title} (Recipe count: {detail.recipeCount})")
        for r in detail.recipes:
            print(f" - {r.title} ({r.id}) [Type: {r.type}]")

        print("\n=== 5. Renaming Collection ===")
        updated = client.update_custom_list(my_list.id, "Holiday Baking Favorites")
        print(f"Renamed collection to: '{updated.title}'")

        print("\n=== 6. Removing Recipe from Collection ===")
        client.remove_recipe_from_custom_list(my_list.id, "r63350")
        print("Removed r63350 from collection.")

        refreshed = client.get_custom_list(my_list.id)
        print(f"Remaining recipes in collection: {refreshed.recipeCount}")

    finally:
        print("\n=== 7. Deleting Collection ===")
        client.delete_custom_list(my_list.id)
        print(f"Deleted collection {my_list.id} cleanly.")


if __name__ == "__main__":
    main()
