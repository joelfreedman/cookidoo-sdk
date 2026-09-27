"""
Cookidoo CLI Interface.
"""

import argparse
from datetime import date
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from .client import CookidooClient

console = Console()
load_dotenv()


def show_history(client: CookidooClient, limit: int = 15):
    console.print(f"[bold cyan]Fetching Recently Cooked Recipes (Last {limit})...[/bold cyan]\n")
    entries = client.get_cooking_history(limit=limit)
    if not entries:
        console.print("[yellow]No cooking history found.[/yellow]")
        return

    table = Table(title="🍳 Thermomix Cooking History", show_header=True, header_style="bold magenta")
    table.add_column("Date & Time", style="cyan", width=22)
    table.add_column("Recipe Title", style="bold green")
    table.add_column("Recipe ID", style="dim", width=12)

    for entry in entries:
        dt_str = entry.cooked_at.strftime("%Y-%m-%d %H:%M")
        table.add_row(dt_str, entry.title, entry.recipe.id)

    console.print(table)


def show_custom_recipes(client: CookidooClient):
    console.print("[bold cyan]Fetching Created / Custom Recipes...[/bold cyan]\n")
    recipes = client.get_created_recipes()
    if not recipes:
        console.print("[yellow]No custom recipes found.[/yellow]")
        return

    table = Table(title="📝 Created / Custom Recipes", show_header=True, header_style="bold magenta")
    table.add_column("Recipe ID", style="dim")
    table.add_column("Recipe Title", style="bold green", min_width=25)
    table.add_column("Portions", justify="right", width=9)
    table.add_column("Ingredients", justify="right")
    table.add_column("Steps", justify="right")
    table.add_column("Photo", style="cyan")

    for r in recipes:
        has_photo = "Yes" if r.image and "placeholder" not in r.image else "No"
        table.add_row(
            r.recipeId,
            r.name,
            str(r.portions),
            str(len(r.ingredients)),
            str(len(r.instructions)),
            has_photo
        )

    console.print(table)


def show_plan(client: CookidooClient, day_key: str = None):
    target_date = day_key or date.today().strftime("%Y-%m-%d")
    console.print(f"[bold cyan]Fetching Meal Plan for: {target_date}...[/bold cyan]\n")
    day = client.get_planned_day(target_date)

    if not day or day.recipeCount == 0:
        console.print(f"[yellow]No meals scheduled for {target_date}.[/yellow]")
        days = client.get_planned_days()
        if days:
            console.print(f"\n[dim]Upcoming planned days in calendar: {', '.join(days[-10:])}[/dim]")
        return

    table = Table(title=f"📅 Meal Plan for {target_date}", show_header=True, header_style="bold magenta")
    table.add_column("Type", style="cyan", width=12)
    table.add_column("Recipe ID / Name", style="bold green")

    for rid in day.recipeIds:
        table.add_row("Official", rid)
    for crid in day.customerRecipeIds:
        table.add_row("Custom", crid)

    console.print(table)


def search_recipes(client: CookidooClient, query: str):
    console.print(f"[bold cyan]Searching Cookidoo recipes for: '{query}'...[/bold cyan]\n")
    result = client.search(query, hits_per_page=10)
    if not result.recipes:
        console.print("[yellow]No matching recipes found.[/yellow]")
        return

    table = Table(title=f"🔍 Results for '{query}' ({result.totalHits} total)", show_header=True, header_style="bold magenta")
    table.add_column("Recipe ID", style="dim", width=10)
    table.add_column("Title", style="bold green")
    table.add_column("Rating", justify="right", width=8)
    table.add_column("Prep Time", justify="right", width=12)
    table.add_column("Total Time", justify="right", width=12)

    for r in result.recipes:
        prep = f"{r.preparationTime // 60}m" if r.preparationTime else "-"
        total = f"{r.totalTime // 60}m" if r.totalTime else "-"
        rating = f"★ {r.rating:.1f}" if r.rating else "-"
        table.add_row(r.id, r.title, rating, prep, total)

    console.print(table)


def show_custom_lists(client: CookidooClient):
    console.print("[bold cyan]Fetching Custom Recipe Lists / Collections...[/bold cyan]\n")
    lists = client.get_custom_lists()
    if not lists:
        console.print("[yellow]No custom lists found.[/yellow]")
        return

    table = Table(title="📁 Custom Recipe Lists / Collections", show_header=True, header_style="bold magenta")
    table.add_column("List ID", style="dim")
    table.add_column("Collection Title", style="bold green", min_width=25)
    table.add_column("Recipes", justify="right", width=10)
    table.add_column("Modified", style="cyan", width=14)

    for cl in lists:
        mod_date = cl.modified[:10] if cl.modified else "-"
        table.add_row(cl.id, cl.title, str(cl.recipeCount), mod_date)

    console.print(table)


def show_list_detail(client: CookidooClient, list_id: str):
    console.print(f"[bold cyan]Fetching List Detail for: {list_id}...[/bold cyan]\n")
    cl = client.get_custom_list(list_id)
    recipes = cl.recipes

    table = Table(title=f"📁 {cl.title} ({len(recipes)} recipes)", show_header=True, header_style="bold magenta")
    table.add_column("Recipe ID", style="dim", width=12)
    table.add_column("Recipe Title", style="bold green")
    table.add_column("Type", style="cyan", width=10)
    table.add_column("Total Time", justify="right", width=12)

    for r in recipes:
        time_str = f"{int(float(r.totalTime)) // 60}m" if r.totalTime else "-"
        table.add_row(r.id, r.title, r.type, time_str)

    console.print(table)


def show_recipe_note(client: CookidooClient, recipe_id: str):
    console.print(f"[bold cyan]Fetching Note for Recipe: {recipe_id}...[/bold cyan]\n")
    note = client.get_recipe_note(recipe_id)
    if not note:
        console.print(f"[yellow]No personal note found for recipe {recipe_id}.[/yellow]")
        return

    table = Table(title=f"📝 Personal Note for {recipe_id}", show_header=True, header_style="bold magenta")
    table.add_column("Field", style="cyan", width=15)
    table.add_column("Value", style="bold green")
    table.add_row("Note ID", note.noteId)
    table.add_row("Recipe ID", note.recipeId)
    table.add_row("Content", note.text)
    if note.modifiedAt:
        table.add_row("Last Modified", note.modifiedAt.strftime("%Y-%m-%d %H:%M"))
    console.print(table)


def show_offline_recipes(
    client: CookidooClient,
    tag: str = None,
    vote: int = None,
    excluded: bool = None,
    active_only: bool = False,
    source: str = None,
    query: str = None,
):
    title_suffix = []
    if tag:
        title_suffix.append(f"tag='{tag}'")
    if vote is not None:
        title_suffix.append(f"vote={vote}")
    if excluded is not None:
        title_suffix.append(f"excluded={excluded}")
    if active_only:
        title_suffix.append("active_only=True")
    if source:
        title_suffix.append(f"source='{source}'")
    if query:
        title_suffix.append(f"search='{query}'")

    filter_desc = f" ({', '.join(title_suffix)})" if title_suffix else ""
    console.print(f"[bold cyan]Fetching Local Offline Library{filter_desc}...[/bold cyan]\n")

    recipes = client.list_offline_recipes(
        source=source,
        active_only=active_only,
        tag=tag,
        excluded=excluded,
        vote=vote,
        query=query,
    )

    if not recipes:
        console.print("[yellow]No offline recipes found matching criteria.[/yellow]")
        return

    table = Table(
        title=f"📚 Local Offline Recipe Library ({len(recipes)} recipes)",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Recipe ID", style="dim", width=12)
    table.add_column("Title", style="bold green", min_width=24)
    table.add_column("Source", style="cyan", width=10)
    table.add_column("Cookidoo Active", justify="center", width=15)
    table.add_column("Vote", justify="center", width=6)
    table.add_column("Planned", justify="right", width=8)
    table.add_column("Tags", style="yellow", width=18)
    table.add_column("Excluded", justify="center", width=9)
    table.add_column("Substitute", style="dim", width=12)

    for r in recipes:
        vote_icon = "👍 +1" if r.vote > 0 else ("👎 -1" if r.vote < 0 else "-")
        active_icon = "[green]✓ Yes[/green]" if r.is_active_on_cookidoo else "[dim]No[/dim]"
        excluded_icon = "[red]🚫 Yes[/red]" if r.is_excluded else "-"
        tags_str = ", ".join(r.tags) if r.tags else "-"
        sub_str = r.substitution_recipe_id or "-"
        table.add_row(
            r.id,
            r.name,
            r.source,
            active_icon,
            vote_icon,
            str(r.times_planned),
            tags_str,
            excluded_icon,
            sub_str,
        )

    console.print(table)


def show_offline_recipe_detail(client: CookidooClient, recipe_id: str):
    console.print(f"[bold cyan]Fetching Offline Recipe Detail for: {recipe_id}...[/bold cyan]\n")
    recipe = client.get_offline_recipe(recipe_id)
    if not recipe:
        console.print(f"[yellow]Recipe '{recipe_id}' is not in local offline storage.[/yellow]")
        return

    table = Table(title=f"📖 {recipe.name} ({recipe.id})", show_header=True, header_style="bold magenta")
    table.add_column("Attribute", style="cyan", width=20)
    table.add_column("Details", style="bold green")

    table.add_row("ID", recipe.id)
    table.add_row("Remote ID", recipe.remote_id or "-")
    table.add_row("Source", recipe.source)
    table.add_row("Active on Cookidoo", "Yes" if recipe.is_active_on_cookidoo else "No (Offline only)")
    vote_str = "+1 (Upvoted)" if recipe.vote > 0 else ("-1 (Downvoted)" if recipe.vote < 0 else "0 (Neutral)")
    table.add_row("Vote", vote_str)
    table.add_row("Times Planned", str(recipe.times_planned))
    table.add_row("Excluded from Planning", "Yes (Excluded)" if recipe.is_excluded else "No")
    table.add_row("Substitution Recipe ID", recipe.substitution_recipe_id or "-")
    table.add_row("Tags", ", ".join(recipe.tags) if recipe.tags else "None")
    table.add_row("Portions", str(recipe.portions) if recipe.portions else "-")
    prep_str = f"{recipe.prep_time // 60}m" if recipe.prep_time else "-"
    total_str = f"{recipe.total_time // 60}m" if recipe.total_time else "-"
    table.add_row("Prep / Total Time", f"{prep_str} / {total_str}")
    if recipe.notes:
        table.add_row("Personal Note", recipe.notes)
    if recipe.last_planned_at:
        table.add_row("Last Planned", recipe.last_planned_at.strftime("%Y-%m-%d %H:%M"))
    if recipe.last_cooked_at:
        table.add_row("Last Cooked", recipe.last_cooked_at.strftime("%Y-%m-%d %H:%M"))

    console.print(table)

    if recipe.ingredients:
        ing_table = Table(title="🥕 Ingredients", show_header=False)
        ing_table.add_column("Ingredient", style="white")
        for ing in recipe.ingredients:
            ing_table.add_row(f"• {ing}")
        console.print(ing_table)

    if recipe.instructions:
        inst_table = Table(title="👩‍🍳 Instructions", show_header=False)
        inst_table.add_column("Step", style="white")
        for i, step in enumerate(recipe.instructions, 1):
            inst_table.add_row(f"{i}. {step}")
        console.print(inst_table)


def main():
    parser = argparse.ArgumentParser(description="Cookidoo CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # history
    hist_parser = subparsers.add_parser("history", help="Show cooking history")
    hist_parser.add_argument("--limit", type=int, default=15, help="Number of recipes to show")

    # custom recipes
    subparsers.add_parser("recipes", help="List created / custom recipes on Cookidoo")

    # custom lists
    subparsers.add_parser("lists", help="List all custom recipe lists / collections")

    # list detail
    list_parser = subparsers.add_parser("list", help="View recipes inside a custom list")
    list_parser.add_argument("list_id", help="Custom list ID")

    # list create
    create_list_parser = subparsers.add_parser("list-create", help="Create a new custom list")
    create_list_parser.add_argument("title", help="List title")

    # list add recipe
    add_list_parser = subparsers.add_parser("list-add", help="Add recipe to a custom list")
    add_list_parser.add_argument("list_id", help="Custom list ID")
    add_list_parser.add_argument("recipe_id", help="Recipe ID to add (e.g. 'r63350')")

    # list remove recipe
    rem_list_parser = subparsers.add_parser("list-remove", help="Remove recipe from a custom list")
    rem_list_parser.add_argument("list_id", help="Custom list ID")
    rem_list_parser.add_argument("recipe_id", help="Recipe ID to remove")

    # list delete
    del_list_parser = subparsers.add_parser("list-delete", help="Delete a custom list")
    del_list_parser.add_argument("list_id", help="Custom list ID to delete")

    # recipe photo upload
    photo_parser = subparsers.add_parser("recipe-upload-image", help="Upload a photo for a custom recipe")
    photo_parser.add_argument("recipe_id", help="Custom recipe ID")
    photo_parser.add_argument("image_path", help="Local path to photo file (.jpg, .png)")

    # recipe photo remove
    rem_photo_parser = subparsers.add_parser("recipe-remove-image", help="Remove photo from a custom recipe")
    rem_photo_parser.add_argument("recipe_id", help="Custom recipe ID")

    # recipe note get
    note_parser = subparsers.add_parser("note", help="View personal note for a recipe")
    note_parser.add_argument("recipe_id", help="Recipe ID (e.g. 'r63350')")

    # recipe note set / upsert
    note_set_parser = subparsers.add_parser("note-set", help="Create or update personal note for a recipe")
    note_set_parser.add_argument("recipe_id", help="Recipe ID (e.g. 'r63350')")
    note_set_parser.add_argument("text", help="Note text (up to 1000 characters)")

    # recipe note delete
    note_del_parser = subparsers.add_parser("note-delete", help="Delete personal note for a recipe")
    note_del_parser.add_argument("recipe_id", help="Recipe ID (e.g. 'r63350')")

    # offline-recipes (view local offline library)
    off_parser = subparsers.add_parser("offline-recipes", help="List recipes in local offline library")
    off_parser.add_argument("--tag", help="Filter by tag")
    off_parser.add_argument("--vote", type=int, choices=[1, -1, 0], help="Filter by vote (+1, -1, 0)")
    off_parser.add_argument("--excluded", action="store_true", help="Show only excluded recipes")
    off_parser.add_argument("--active", action="store_true", help="Show only recipes active on Cookidoo")
    off_parser.add_argument("--source", choices=["CUSTOMER", "VORWERK"], help="Filter by source")
    off_parser.add_argument("--search", help="Search titles/ingredients")

    # offline-recipe detail
    off_detail_parser = subparsers.add_parser("offline-recipe", help="View detailed offline recipe card")
    off_detail_parser.add_argument("recipe_id", help="Recipe ID (e.g. 'r63350' or custom ID)")

    # tag recipe
    tag_parser = subparsers.add_parser("tag", help="Add one or more custom tags to a recipe")
    tag_parser.add_argument("recipe_id", help="Recipe ID (official or created)")
    tag_parser.add_argument("tags", nargs="+", help="Tags to add")

    # untag recipe
    untag_parser = subparsers.add_parser("untag", help="Remove a tag from a recipe")
    untag_parser.add_argument("recipe_id", help="Recipe ID")
    untag_parser.add_argument("tag", help="Tag to remove")

    # vote recipe
    vote_parser = subparsers.add_parser("vote", help="Upvote (+1), downvote (-1), or clear (0) a recipe")
    vote_parser.add_argument("recipe_id", help="Recipe ID")
    vote_parser.add_argument("score", choices=["up", "down", "clear", "1", "-1", "0"], help="Vote score")

    # exclude recipe
    exclude_parser = subparsers.add_parser("exclude", help="Mark a recipe as excluded (or unexclude)")
    exclude_parser.add_argument("recipe_id", help="Recipe ID")
    exclude_parser.add_argument("--remove", action="store_true", help="Un-exclude recipe")

    # substitute recipe
    sub_parser = subparsers.add_parser("substitute", help="Point recipe to an alternate created recipe")
    sub_parser.add_argument("recipe_id", help="Original recipe ID")
    sub_parser.add_argument("substitute_id", nargs="?", default=None, help="Substitute recipe ID")
    sub_parser.add_argument("--clear", action="store_true", help="Clear existing substitution")

    # sync
    sync_parser = subparsers.add_parser("sync", help="Sync offline recipes with Cookidoo quota (<= 50)")
    sync_parser.add_argument("--pull", action="store_true", help="Pull all recipes from Cookidoo into offline storage")
    sync_parser.add_argument("--activate", help="Activate a local recipe on Cookidoo (auto-evicting if >= 50)")
    sync_parser.add_argument("--archive", help="Archive an active recipe from Cookidoo (keeps full offline copy)")
    sync_parser.add_argument("--desired", nargs="+", help="Reconcile active Cookidoo recipes with desired ID list")

    # plan
    plan_parser = subparsers.add_parser("plan", help="Show meal plan for date")
    plan_parser.add_argument("date", nargs="?", default=None, help="Date in YYYY-MM-DD format (default: today)")

    # search
    search_parser = subparsers.add_parser("search", help="Search Cookidoo recipes")
    search_parser.add_argument("query", help="Search query (e.g. 'risotto')")

    args = parser.parse_args()

    client = CookidooClient()

    if args.command == "history":
        show_history(client, limit=args.limit)
    elif args.command == "recipes":
        show_custom_recipes(client)
    elif args.command == "lists":
        show_custom_lists(client)
    elif args.command == "list":
        show_list_detail(client, list_id=args.list_id)
    elif args.command == "list-create":
        nl = client.create_custom_list(title=args.title)
        console.print(f"[bold green]Created custom list '{nl.title}' with ID: {nl.id}[/bold green]")
    elif args.command == "list-add":
        client.add_recipes_to_custom_list(list_id=args.list_id, recipe_ids=[args.recipe_id])
        console.print(f"[bold green]Added recipe {args.recipe_id} to list {args.list_id}[/bold green]")
    elif args.command == "list-remove":
        client.remove_recipe_from_custom_list(list_id=args.list_id, recipe_id=args.recipe_id)
        console.print(f"[bold green]Removed recipe {args.recipe_id} from list {args.list_id}[/bold green]")
    elif args.command == "list-delete":
        client.delete_custom_list(list_id=args.list_id)
        console.print(f"[bold green]Deleted custom list {args.list_id}[/bold green]")
    elif args.command == "recipe-upload-image":
        r = client.upload_recipe_image(recipe_id=args.recipe_id, image_file_or_bytes=args.image_path)
        console.print(f"[bold green]Successfully uploaded photo for recipe '{r.name}': {r.image}[/bold green]")
    elif args.command == "recipe-remove-image":
        r = client.remove_recipe_image(recipe_id=args.recipe_id)
        console.print(f"[bold green]Removed photo for recipe '{r.name}'[/bold green]")
    elif args.command == "note":
        show_recipe_note(client, recipe_id=args.recipe_id)
    elif args.command == "note-set":
        saved_note = client.save_recipe_note(recipe_id=args.recipe_id, text=args.text)
        console.print(f"[bold green]Saved note for recipe {args.recipe_id}: '{saved_note.text}'[/bold green]")
    elif args.command == "note-delete":
        client.delete_recipe_note(recipe_id=args.recipe_id)
        console.print(f"[bold green]Deleted personal note for recipe {args.recipe_id}[/bold green]")
    elif args.command == "offline-recipes":
        show_offline_recipes(
            client,
            tag=args.tag,
            vote=args.vote,
            excluded=True if args.excluded else None,
            active_only=args.active,
            source=args.source,
            query=args.search,
        )
    elif args.command == "offline-recipe":
        show_offline_recipe_detail(client, recipe_id=args.recipe_id)
    elif args.command == "tag":
        res = client.tag_recipe(args.recipe_id, args.tags)
        console.print(f"[bold green]Tagged recipe '{res.name}' ({res.id}): {res.tags}[/bold green]")
    elif args.command == "untag":
        res = client.untag_recipe(args.recipe_id, args.tag)
        console.print(f"[bold green]Removed tag '{args.tag}' from recipe '{res.name}' ({res.id}). Current tags: {res.tags}[/bold green]")
    elif args.command == "vote":
        val_map = {"up": 1, "1": 1, "down": -1, "-1": -1, "clear": 0, "0": 0}
        score = val_map[args.score]
        res = client.vote_recipe(args.recipe_id, score)
        icon = "👍 +1" if score > 0 else ("👎 -1" if score < 0 else "Neutral 0")
        console.print(f"[bold green]Recorded vote {icon} for recipe '{res.name}' ({res.id})[/bold green]")
    elif args.command == "exclude":
        excluded_flag = not args.remove
        res = client.exclude_recipe(args.recipe_id, excluded=excluded_flag)
        status_str = "Excluded from planning" if excluded_flag else "Re-included in planning"
        console.print(f"[bold green]{status_str}: '{res.name}' ({res.id})[/bold green]")
    elif args.command == "substitute":
        sub_id = None if args.clear else args.substitute_id
        res = client.set_recipe_substitution(args.recipe_id, sub_id)
        if sub_id:
            console.print(f"[bold green]Set substitute for '{res.name}' ({res.id}) -> {sub_id}[/bold green]")
        else:
            console.print(f"[bold green]Cleared substitution for '{res.name}' ({res.id})[/bold green]")
    elif args.command == "sync":
        if args.pull:
            pulled = client.sync_manager.pull_all_from_cookidoo()
            console.print(f"[bold green]Successfully pulled {len(pulled)} recipes from Cookidoo to offline storage.[/bold green]")
        elif args.activate:
            act = client.sync_manager.activate_recipe(args.activate)
            console.print(f"[bold green]Activated recipe '{act.name}' ({act.id}) on Cookidoo (Remote ID: {act.remote_id})[/bold green]")
        elif args.archive:
            arc = client.sync_manager.archive_recipe(args.archive)
            console.print(f"[bold green]Archived recipe '{arc.name}' ({arc.id}) from Cookidoo (kept offline in local library)[/bold green]")
        elif args.desired:
            reconcile_res = client.sync_active_recipes(args.desired)
            console.print(f"[bold green]Reconciled active recipes. Activated: {len(reconcile_res['activated'])}, Archived: {len(reconcile_res['archived'])}, Current active: {reconcile_res['current_active']}/{reconcile_res['max_active']}[/bold green]")
        else:
            active_count = client.storage.count_active_created_recipes()
            console.print(f"[bold cyan]Cookidoo Active Created Recipes: {active_count}/{client.sync_manager.max_active}[/bold cyan]")
            console.print("[dim]Use --pull, --activate <id>, --archive <id>, or --desired <ids...> to manage sync.[/dim]")
    elif args.command == "plan":
        show_plan(client, day_key=args.date)
    elif args.command == "search":
        search_recipes(client, query=args.query)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

