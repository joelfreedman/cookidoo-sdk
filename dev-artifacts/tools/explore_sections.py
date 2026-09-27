"""
Navigate through core sections using UI interactions:
- My Recipes (Created Recipes, Saved Collections, Bookmarks)
- My Week (Weekly meal planner & scheduled recipes)
- Cooking History / Recently Cooked
"""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

SDK_ROOT = Path(__file__).resolve().parent.parent.parent
SESSION_FILE = SDK_ROOT / ".cookidoo_session.json"
CAPTURED_DIR = Path(__file__).resolve().parent.parent / "captured_endpoints"
CAPTURED_DIR.mkdir(exist_ok=True)

with open(SESSION_FILE) as f:
    session_data = json.load(f)

cookies = session_data["cookies"]
base_url = session_data.get("base_url", "https://cookidoo.thermomix.com")
locale = session_data.get("locale", "en-US")

recorded_api_calls = []

def on_response(response):
    try:
        url = response.url
        content_type = response.headers.get("content-type", "")
        # Capture API, backend microservices, planning, organize, and created recipes
        is_relevant = any(k in url for k in [
            "/api/", "/planning/", "/organize/", "/created-recipes/",
            "/recipes/", "/shopping/", "/user/", "/profile/", "/tmecosys"
        ])
        if is_relevant:
            body = None
            if "application/json" in content_type:
                try:
                    body = response.json()
                except Exception:
                    pass
            elif "text" in content_type or "xml" in content_type:
                try:
                    t = response.text()
                    if len(t) < 5000:
                        body = t
                except Exception:
                    pass

            entry = {
                "method": response.request.method,
                "url": url,
                "status": response.status,
                "content_type": content_type,
                "request_headers": {k: v for k, v in response.request.headers.items() if k.lower() in [
                    "authorization", "accept", "content-type", "x-csrf-token", "x-xsrf-token"
                ]},
                "body": body
            }
            recorded_api_calls.append(entry)
            print(f"[{response.status}] {response.request.method} {url}")
    except Exception:
        pass


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    context.add_cookies(cookies)
    page = context.new_page()
    page.on("response", on_response)

    print("--- 1. Visiting For You ---")
    page.goto(f"{base_url}/foundation/{locale}/for-you", wait_until="networkidle")
    # Accept cookie banner if present
    try:
        accept_btn = page.locator("#onetrust-accept-btn-handler")
        if accept_btn.is_visible(timeout=2000):
            accept_btn.click()
    except Exception:
        pass

    # Open Menu
    def open_menu():
        menu_btn = page.locator("button:has-text('Menu'), button.core-header__btn--menu, [aria-label*='Menu'], .core-nav-trigger")
        if menu_btn.count() > 0:
            menu_btn.first.click()
            page.wait_for_timeout(1000)

    print("\n--- 2. Navigating to My Week ---")
    open_menu()
    page.locator("a:has-text('My Week'), button:has-text('My Week')").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)
    print("Current URL:", page.url)
    page.screenshot(path=str(CAPTURED_DIR / "my_week_live.png"))

    print("\n--- 3. Navigating to My Recipes ---")
    open_menu()
    page.locator("a:has-text('My Recipes'), button:has-text('My Recipes')").first.click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)
    print("Current URL:", page.url)
    page.screenshot(path=str(CAPTURED_DIR / "my_recipes_live.png"))

    # See subtabs in My Recipes (e.g. Created Recipes, Saved collections, Bookmarks)
    subtabs = page.evaluate("""() => Array.from(document.querySelectorAll('a, button')).map(el => ({
        text: el.innerText.trim(),
        href: el.getAttribute('href') || ''
    })).filter(x => x.text && (x.text.includes('Created') || x.text.includes('Saved') || x.text.includes('Bookmark') || x.text.includes('Recent')))""")
    print("Subtabs in My Recipes:", subtabs)

    # Click Created Recipes if found
    created_recipe_tab = page.locator("text='Created recipes', text='Created Recipes', a[href*='created-recipes'], a[href*='custom-recipes']")
    if created_recipe_tab.count() > 0:
        print("\n--- 4. Clicking Created Recipes ---")
        created_recipe_tab.first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        print("Created Recipes URL:", page.url)
        page.screenshot(path=str(CAPTURED_DIR / "created_recipes_live.png"))

    print("\n--- 5. Navigating to Shopping List ---")
    open_menu()
    shopping_btn = page.locator("text='Shopping list', text='Shopping List', a[href*='shopping']")
    if shopping_btn.count() > 0:
        shopping_btn.first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        print("Shopping List URL:", page.url)
        page.screenshot(path=str(CAPTURED_DIR / "shopping_list_live.png"))

    # Dump all recorded calls
    output_path = CAPTURED_DIR / "detailed_api_calls.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(recorded_api_calls, f, indent=2)

    print(f"\nCaptured {len(recorded_api_calls)} detailed API calls to {output_path}")
    browser.close()
