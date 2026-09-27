"""
Example: Manage & Create Custom Recipes on Cookidoo

Demonstrates:
1. Listing all custom recipes in your account.
2. Fetching details of a custom recipe.
3. Creating a brand new custom recipe with ingredients and Thermomix steps.
4. Uploading a photo for the custom recipe (or setting/removing image).
5. Updating and cleaning up recipes.
"""

import io
from PIL import Image
from cookidoo import CookidooClient

client = CookidooClient()

# -------------------------------------------------------------
# 1. List existing custom recipes
# -------------------------------------------------------------
print("=== 1. Existing Custom Recipes ===")
recipes = client.get_created_recipes()
print(f"Total Custom Recipes: {len(recipes)}\n")
for r in recipes[:5]:
    photo_status = "📷 Yes" if r.image and "placeholder" not in r.image else "No photo"
    print(f"- {r.name} (ID: {r.recipeId}) [{photo_status}] - {len(r.ingredients)} ingredients, {len(r.instructions)} steps")

# -------------------------------------------------------------
# 2. View details of first recipe
# -------------------------------------------------------------
if recipes:
    sample = client.get_created_recipe(recipes[0].recipeId)
    print(f"\n=== 2. Details for: {sample.name} ===")
    print(f"Image: {sample.image}")
    print("Ingredients:")
    for ing in sample.ingredients[:3]:
        print(f"  • {ing}")
    print("Instructions:")
    for idx, step in enumerate(sample.instructions[:2], 1):
        print(f"  {idx}. {step}")

# -------------------------------------------------------------
# 3. Create a Brand New Custom Recipe
# -------------------------------------------------------------
print("\n=== 3. Creating a New Custom Recipe ===")
new_recipe = client.create_custom_recipe(
    name="Homemade Brioche Loaf (SDK Example)",
    ingredients=[
        "250 g strong white bread flour",
        "30 g caster sugar",
        "1 tsp dried instant yeast",
        "3 large eggs, beaten",
        "125 g unsalted butter, softened",
        "1/2 tsp fine sea salt"
    ],
    instructions=[
        "Place milk, sugar and yeast in mixing bowl and warm 2 min/37°C/speed 2.",
        "Add flour, eggs and salt, then knead Dough /3 min.",
        "Gradually add softened butter through hole in lid while kneading Dough /3 min.",
        "Transfer to an oiled bowl, cover with a damp cloth, and prove in fridge overnight."
    ],
    portions=6,
    tool="TM6"
)

print(f"Created: '{new_recipe.name}' (ID: {new_recipe.recipeId})")
print(f"  Yield: {new_recipe.portions} portions")
print(f"  Ingredients: {len(new_recipe.ingredients)} items")
print(f"  Steps: {len(new_recipe.instructions)} steps")

# -------------------------------------------------------------
# 4. Uploading Photo to Custom Recipe
# -------------------------------------------------------------
print("\n=== 4. Uploading Photo for Custom Recipe ===")
# Generate a test image in memory (or pass a file path: "my_bread.jpg")
img = Image.new("RGB", (300, 300), color=(225, 170, 80))
buf = io.BytesIO()
img.save(buf, format="JPEG")

updated_with_photo = client.upload_recipe_image(new_recipe.recipeId, buf.getvalue(), format="jpg")
print(f"Photo uploaded successfully! Live URL: {updated_with_photo.image}")

# Optional: remove photo
cleared = client.remove_recipe_image(new_recipe.recipeId)
print(f"Photo removed. Image reset to: {cleared.image}")

# -------------------------------------------------------------
# 5. Clean Up (Delete the test recipe)
# -------------------------------------------------------------
print("\n=== 5. Cleaning Up Test Recipe ===")
deleted = client.delete_custom_recipe(new_recipe.recipeId)
print(f"Deleted test recipe {new_recipe.recipeId}: {deleted}")
