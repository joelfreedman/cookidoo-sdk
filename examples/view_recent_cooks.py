"""
Example: View Recently Cooked Recipes from Thermomix
"""

from cookidoo import CookidooClient

client = CookidooClient()
history = client.get_cooking_history(limit=10)

print(f"--- Recently Cooked Recipes ({len(history)}) ---")
for entry in history:
    time_str = entry.cooked_at.strftime("%Y-%m-%d %H:%M")
    print(f"[{time_str}] {entry.title} (ID: {entry.recipe.id})")
