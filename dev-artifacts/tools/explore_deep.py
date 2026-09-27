"""
Deep probe of:
1. Cooking History (/organize/en-US/cooking-history)
2. Created Recipes (/created-recipes/en-US)
3. Planned day recipes (/planning/en-US/api/my-day/...)
"""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

SDK_ROOT = Path(__file__).resolve().parent.parent.parent
SESSION_FILE = SDK_ROOT / ".cookidoo_session.json"
CAPTURED_DIR = Path(__file__).resolve().parent.parent / "captured_endpoints"

with open(SESSION_FILE) as f:
    session_data = json.load(f)

cookies = session_data["cookies"]
base_url = session_data.get("base_url", "https://cookidoo.thermomix.com")
locale = session_data.get("locale", "en-US")

captured = []

def on_response(response):
    url = response.url
    ct = response.headers.get("content-type", "")
    if any(k in url for k in ["/organize/", "/created-recipes/", "/planning/", "/api/", "/recipes/"]):
        data = None
        if "json" in ct:
            try:
                data = response.json()
            except Exception:
                pass
        entry = {
            "method": response.request.method,
            "url": url,
            "status": response.status,
            "content_type": ct,
            "body": data
        }
        captured.append(entry)
        print(f"[{response.status}] {response.request.method} {url}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    context.add_cookies(cookies)
    page = context.new_page()
    page.on("response", on_response)

    print("\n--- A. Exploring Cooking History ---")
    page.goto(f"{base_url}/organize/{locale}/cooking-history", wait_until="networkidle")
    page.wait_for_timeout(3000)
    page.screenshot(path=str(CAPTURED_DIR / "cooking_history_live.png"))
    
    # Extract recipe items displayed in cooking history
    history_items = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('.core-tile, wf-image-tile, [data-sp-context]')).map(el => {
            const link = el.querySelector('a');
            const title = el.querySelector('h3, .core-tile__title, .wf-image-tile__title');
            const subtitle = el.querySelector('.core-tile__subtitle, .core-tile__description');
            return {
                title: title ? title.innerText.trim() : null,
                href: link ? link.href : null,
                context: el.getAttribute('data-sp-context'),
                subtitle: subtitle ? subtitle.innerText.trim() : null
            };
        });
    }""")
    print(f"Found {len(history_items)} items in Cooking History HTML!")
    for item in history_items[:10]:
        print("  -", item)

    print("\n--- B. Exploring Created Recipes ---")
    page.goto(f"{base_url}/created-recipes/{locale}", wait_until="networkidle")
    page.wait_for_timeout(3000)
    page.screenshot(path=str(CAPTURED_DIR / "created_recipes_page.png"))

    created_items = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('.core-tile, wf-image-tile, [data-sp-context], button, a')).map(el => {
            return {
                tag: el.tagName,
                text: el.innerText ? el.innerText.trim() : '',
                href: el.getAttribute('href') || ''
            };
        }).filter(x => x.text && (x.text.includes('Create') || x.text.includes('Import') || x.href.includes('recipe')));
    }""")
    print("Created recipes elements:", created_items[:10])

    print("\n--- C. Testing Planned Recipes Endpoints ---")
    # Fetch planned recipes for 2026-09-26
    test_urls = [
        f"{base_url}/planning/{locale}/api/my-day/2026-09-26",
        f"{base_url}/planning/{locale}/calendar/day?date=2026-09-26",
        f"{base_url}/planning/{locale}/api/my-day/calendar-items/2026-09-26",
        f"{base_url}/organize/{locale}/api/cooking-history",
        f"{base_url}/created-recipes/{locale}/api/recipes"
    ]
    for u in test_urls:
        res = page.evaluate(f"""async (url) => {{
            try {{
                const r = await fetch(url, {{ headers: {{ 'Accept': 'application/json' }} }});
                return {{ status: r.status, ok: r.ok, json: r.headers.get('content-type')?.includes('json') ? await r.json() : await r.text() }};
            }} catch(e) {{
                return {{ error: e.message }};
            }}
        }}""", u)
        print(f"Fetch {u} -> Status: {res.get('status')}")
        if res.get("status") == 200:
            print("  Response preview:", str(res.get("json"))[:300])

    with open(CAPTURED_DIR / "deep_probe_calls.json", "w") as f:
        json.dump(captured, f, indent=2)

    browser.close()
