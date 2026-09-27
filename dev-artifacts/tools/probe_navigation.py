"""
Probe Cookidoo navigation links and explore My Week, Created Recipes, and History.
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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    context.add_cookies(cookies)
    page = context.new_page()

    captured_requests = []

    def log_response(response):
        url = response.url
        content_type = response.headers.get("content-type", "")
        if any(kw in url for kw in ["/api/", "/planning/", "/recipes/", "/organize/", "/created-recipes/", "/activity", "/user"]):
            try:
                data = None
                if "application/json" in content_type:
                    data = response.json()
                captured_requests.append({
                    "method": response.request.method,
                    "url": url,
                    "status": response.status,
                    "body": data
                })
                print(f"[{response.status}] {response.request.method} {url}")
            except Exception:
                pass

    page.on("response", log_response)

    print("Loading homepage with authenticated session...")
    page.goto(f"{base_url}/foundation/{locale}/for-you", wait_until="networkidle")

    # Click Menu button
    print("Clicking Menu...")
    menu_btn = page.locator("button:has-text('Menu'), button.core-header__btn--menu, [aria-label*='Menu'], .core-nav-trigger")
    if menu_btn.count() > 0:
        menu_btn.first.click()
        page.wait_for_timeout(1000)

    # Extract all links
    links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a')).map(a => ({
            text: a.innerText.trim(),
            href: a.href
        })).filter(l => l.href && l.href.includes('cookidoo'));
    }""")

    print("\n=== DISCOVERED NAVIGATION LINKS ===")
    for l in links:
        if l["text"]:
            print(f"- {l['text']}: {l['href']}")

    page.screenshot(path=str(CAPTURED_DIR / "menu_opened.png"))

    # Save navigation links
    with open(CAPTURED_DIR / "navigation_links.json", "w") as f:
        json.dump(links, f, indent=2)

    browser.close()
