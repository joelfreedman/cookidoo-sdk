"""
Example: Manage Recipe Notes (CRUD) for Published / Official Recipes.

Demonstrates:
1. Checking if a recipe has a personal note.
2. Creating a new personal note.
3. Updating an existing note.
4. Retrieving full recipe details with the note integrated.
5. Deleting the personal note.
"""

from cookidoo import CookidooClient


def main():
    client = CookidooClient()
    recipe_id = "r63350"  # Sandwich Bread (official Vorwerk recipe)

    print("=== 1. Checking Existing Note ===")
    existing_note = client.get_recipe_note(recipe_id)
    if existing_note:
        print(f"Existing note found: '{existing_note.text}'")
    else:
        print("No personal note currently attached.")

    print("\n=== 2. Creating / Saving Personal Note ===")
    note_content = "Tip: Prove dough for an extra 20 minutes if baking in cold weather."
    saved_note = client.save_recipe_note(recipe_id, note_content)
    print(f"Note saved! [ID: {saved_note.noteId}]")
    print(f"Content: '{saved_note.text}'")

    print("\n=== 3. Updating the Note ===")
    updated_content = "Tip: Prove dough for 20 extra minutes and brush with melted butter before baking."
    updated_note = client.update_recipe_note(recipe_id, updated_content)
    print(f"Updated note: '{updated_note.text}'")

    print("\n=== 4. Fetching Recipe Details with Note ===")
    detail = client.get_recipe_details(recipe_id, include_note=True)
    print(f"Recipe: {detail.name}")
    print(f"Attached Personal Note: '{detail.note}'")

    print("\n=== 5. Deleting Personal Note ===")
    deleted = client.delete_recipe_note(recipe_id)
    print(f"Note deleted successfully: {deleted}")

    # Confirm clean
    refreshed_note = client.get_recipe_note(recipe_id)
    print(f"Post-delete note verification: {refreshed_note}")


if __name__ == "__main__":
    main()
