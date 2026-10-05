"""
Example: Creating a Rich Thermomix Guided-Cooking Recipe.

Demonstrates how to include:
1. Exact Weights & Scale triggers (e.g. 'Weigh 40 g Parmesan...')
2. Time, Temperature & Speed (TTS) guided cooking chips:
   - Temperatures: 37°C, 100°C, 120°C, Varoma
   - Speeds: Soft (0.5), 1, 1.5, 2, 3.5, 5, 7, 8, 10, Turbo
   - Times: Seconds (sec) and Minutes (min)
3. Reverse Blade Direction (counter-clockwise icon '\\ue003' or 'reverse')
4. Knead / Dough Mode (wheat icon '\\ue001' or 'Dough')
5. Accessories & Lids: Butterfly Whisk, Simmering Basket, Varoma, MC on/off
"""

from cookidoo import CookidooClient

client = CookidooClient()

# ---------------------------------------------------------------------
# Rich Recipe Definition
# ---------------------------------------------------------------------
RECIPE_NAME = "Gourmet Wild Mushroom Risotto with Varoma Scallops (Rich TTS Example)"

INGREDIENTS = [
    # Grated cheese topping
    "40 g Parmesan cheese, cut in 2 cm cubes",
    # Aromatics & base
    "2 cloves garlic, peeled",
    "150 g shallots or brown onion, halved",
    "40 g extra virgin olive oil",
    # Grains & liquids
    "300 g Carnaroli or Arborio risotto rice",
    "100 g dry white wine",
    "750 g hot chicken or vegetable stock",
    "1 tsp fine sea salt",
    "1/4 tsp freshly cracked black pepper",
    # Mushrooms & finish
    "200 g mixed wild mushrooms (cremini, shiitake, oyster), sliced",
    "30 g cold unsalted butter, cubed",
    "2 tbsp fresh flat-leaf parsley, finely chopped",
    # Multi-level Varoma steaming
    "150 g tender asparagus spears or broccolini",
    "250 g fresh jumbo sea scallops, patted dry"
]

INSTRUCTIONS = [
    # 1. High Speed Grating (Scale + Time + Speed 10)
    "Weigh 40 g Parmesan cheese (cut into 2 cm cubes) into the mixing bowl. "
    "Grate 10 sec/speed 10. Transfer grated cheese to a small bowl and set aside.",

    # 2. Precise Chopping (Scale + Aromatics + Speed 5)
    "Weigh 150 g halved shallots, 2 garlic cloves, and 40 g extra virgin olive oil into the mixing bowl. "
    "Chop 5 sec/speed 5. Scrape down sides of mixing bowl with spatula.",

    # 3. High-Temperature Sautéing (Time + 120°C + Speed 1 + MC off)
    "Sauté aromatics 3 min/120°C/speed 1 without the measuring cup.",

    # 4. Toasting Grain (Scale + 100°C + Reverse Blade + Speed 1)
    # The reverse blade symbol '\ue003' (or 'reverse') ensures the grains are not cut or crushed!
    "Weigh in 300 g Arborio risotto rice. "
    "Toast grains 3 min/100°C/\ue003/speed 1 (reverse, measuring cup off).",

    # 5. Deglazing (Liquid Scale + 100°C + Reverse Blade)
    "Add 100 g dry white wine through hole in mixing bowl lid. "
    "Deglaze 1 min/100°C/\ue003/speed 1.5 without measuring cup.",

    # 6. Multi-Level Steaming (Stock Scale + Varoma Temp + Reverse Blade + Varoma dish & tray)
    "Weigh in 750 g hot stock, 1 tsp salt, and 1/4 tsp black pepper. "
    "Place Varoma dish into position on mixing bowl lid, weigh in 150 g asparagus spears. "
    "Insert Varoma tray, arrange 250 g sea scallops in a single layer, and secure Varoma lid. "
    "Cook 12 min/Varoma/\ue003/speed 1 (reverse).",

    # 7. Sauté Mushrooms with Butterfly Whisk (Whisk + 100°C + Reverse Blade + Soft Speed)
    "Carefully remove Varoma and set aside warm. Insert Butterfly Whisk. "
    "Weigh 200 g sliced wild mushrooms into mixing bowl. "
    "Cook 3 min/100°C/\ue003/speed soft (reverse, speed 0.5).",

    # 8. Mantecatura & Emulsification (Cold Butter + Parmesan + Reverse)
    "Remove Butterfly Whisk. Add reserved grated Parmesan and 30 g cold cubed butter. "
    "Stir 1 min/\ue003/speed 2 with measuring cup in place. "
    "Allow risotto to rest in mixing bowl for 2 minutes before serving garnished with fresh parsley, "
    "steamed asparagus, and seared scallops.",

    # 9. Optional Accompaniment: Flatbread / Dough Knead Mode (Scale + Dough icon '\ue001' + Time)
    "For rapid companion flatbreads: Empty and rinse mixing bowl. "
    "Weigh in 200 g flour, 110 g water, 1 tsp yeast, and 1/2 tsp salt. "
    "Knead Dough \ue001/2 min. Shape and griddle for 2 minutes per side."
]


def main():
    print("==================================================================")
    print("Creating Rich Thermomix Guided-Cooking Recipe on Cookidoo")
    print("==================================================================\n")

    # 1. Create on Cookidoo (or save directly to offline library)
    print("Uploading rich TM7 recipe to Cookidoo account...")
    recipe = client.create_custom_recipe(
        name=RECIPE_NAME,
        ingredients=INGREDIENTS,
        instructions=INSTRUCTIONS,
        portions=4,
        tools=["TM7", "TM6"]
    )

    print(f"\nCreated Recipe on Cookidoo:")
    print(f"  • ID: {recipe.recipeId}")
    print(f"  • Title: {recipe.name}")
    print(f"  • Devices/Tools: {recipe.tools}")
    print(f"  • Portions: {recipe.portions}")
    print(f"  • Ingredients Count: {len(recipe.ingredients)}")
    print(f"  • Instructions Count: {len(recipe.instructions)}\n")

    # 2. Inspect Guided Cooking Chips
    print("--- Detailed Step-by-Step Guided Cooking Chips ---")
    for i, step in enumerate(recipe.instructions, 1):
        print(f"\nStep {i}:")
        print(f"  {step}")

    print("\n==================================================================")
    print("How the Thermomix TM6 Displays These Instructions:")
    print("  1. 'Weigh 40 g ...' -> Green scale button opens digital scales.")
    print("  2. '10 sec/speed 10' -> Speed dial set to maximum 10 for 10 sec.")
    print("  3. '3 min/120°C/speed 1' -> High temp sautéing (120°C).")
    print("  4. '\ue003' or 'reverse' -> Activates reverse blade direction (blunt edge).")
    print("  5. '12 min/Varoma/...' -> Sets maximum steam temperature (Varoma).")
    print("  6. 'Dough \ue001/2 min' -> Activates automatic interval kneading mode.")
    print("==================================================================")


if __name__ == "__main__":
    main()
