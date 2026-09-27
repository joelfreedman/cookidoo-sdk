"""
Example: Meal Planning for the Week ("My Week")
"""

from datetime import date, timedelta
from cookidoo import CookidooClient

client = CookidooClient()

# 1. Fetch all planned days for the current month
planned_dates = client.get_planned_days()
print(f"Upcoming planned dates: {planned_dates}")

# 2. View details of a specific day
if planned_dates:
    latest_day = planned_dates[-1]
    plan = client.get_planned_day(latest_day)
    print(f"\nPlan for {latest_day}:")
    print(f"  Official recipes: {plan.recipeIds}")
    print(f"  Custom recipes: {plan.customerRecipeIds}")

# 3. Schedule a recipe for next Saturday
target = (date.today() + timedelta(days=6)).strftime("%Y-%m-%d")
recipe_id = "r63350"  # Sandwich bread
print(f"\nScheduling {recipe_id} for {target}...")
client.add_to_plan(day_key=target, recipe_id=recipe_id)
print("Recipe scheduled successfully!")
