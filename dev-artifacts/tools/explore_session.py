"""
Cookidoo Session Explorer & Network Interceptor

Logs into cookidoo.thermomix.com using credentials from .env or interactive browser login,
extracts authenticated session cookies/tokens, visits key sections (My Week, Created Recipes,
Cooking History), and dumps intercepted API endpoints to JSON files for SDK development.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Setup base paths
SDK_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(SDK_ROOT / ".env")

CAPTURED_DIR = Path(__file__).resolve().parent.parent / "captured_endpoints"
CAPTURED_DIR.mkdir(exist_ok=True)
SESSION_FILE = SDK_ROOT / ".cookidoo_session.json"


class NetworkCollector:
    def __init__(self):
        self.captured_calls = []

    def on_response(self, response):
        try:
            url = response.url
            content_type = response.headers.get("content-type", "")
            # Focus on API, JSON, GraphQL, and planning/recipe responses
            is_api = any(kw in url for kw in ["/api/", "/planning/", "/recipes/", "/ciam/", "/user/", "/created-recipes"])
            is_json = "application/json" in content_type

            if is_api or is_json:
                entry = {
                    "method": response.request.method,
                    "url": url,
                    "status": response.status,
                    "headers": {k: v for k, v in response.request.headers.items() if k.lower() in ["authorization", "cookie", "accept", "content-type", "x-csrf-token"]},
                    "response_headers": {k: v for k, v in response.headers.items() if k.lower() in ["content-type", "set-cookie"]},
                }
                try:
                    if is_json:
                        entry["body"] = response.json()
                    elif len(response.body()) < 10000:
                        entry["body"] = response.text()
                except Exception:
                    pass

                self.captured_calls.append(entry)
                print(f"  [API {response.status}] {response.request.method} {url[:90]}")
        except Exception as e:
            pass


def explore(interactive=False, headless=False):
    email = os.getenv("COOKIDOO_EMAIL")
    password = os.getenv("COOKIDOO_PASSWORD")
    locale = os.getenv("COOKIDOO_LOCALE", "en-US")
    base_url = "https://cookidoo.thermomix.com"

    if not interactive and (not email or not password or "your-email" in email):
        print("\n[ERROR] COOKIDOO_EMAIL or COOKIDOO_PASSWORD not configured.")
        print(f"Please fill in your credentials in: {SDK_ROOT / '.env'}")
        print("Or run with --interactive to log in manually through a browser window.\n")
        sys.exit(1)

    collector = NetworkCollector()

    print("\n=======================================================")
    print("      Cookidoo Network Explorer & Session Capture      ")
    print("=======================================================")
    print(f"Target: {base_url} (Locale: {locale})")
    print(f"Headless: {headless}")
    print(f"Interactive Mode: {interactive or not email}")
    print("-------------------------------------------------------\n")

    with sync_playwright() as p:
        # Launch browser with standard viewport
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=100 if not headless else 0,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Attach network response listener
        page.on("response", collector.on_response)

        try:
            login_url = f"{base_url}/profile/{locale}/login"
            print(f"1. Navigating to login page: {login_url}")
            page.goto(login_url, wait_until="networkidle")

            # Check if cookie consent banner is present and accept if found
            try:
                accept_banner = page.locator("#onetrust-accept-btn-handler, button:has-text('Accept All')")
                if accept_banner.is_visible(timeout=3000):
                    accept_banner.click()
                    print("  -> Dismissed cookie banner.")
            except Exception:
                pass

            if email and password and not interactive:
                print(f"2. Entering credentials for: {email}")
                # Wait for username field on CIAM login page
                page.wait_for_selector('#username, input[name="username"], input[type="email"]', timeout=15000)
                page.fill('#username, input[name="username"], input[type="email"]', email)
                page.fill('#password, input[name="password"], input[type="password"]', password)
                
                # Submit login form
                submit_btn = page.locator('#login-submit-btn, button[type="submit"]')
                submit_btn.click()
                print("  -> Login submitted. Waiting for authentication navigation...")
            else:
                print("\n>>> Please complete your login in the browser window. <<<")
                print(">>> If a 2FA code is sent to your phone/email, enter it now. <<<")

            # Wait for authenticated state (redirect back to cookidoo.thermomix.com)
            page.wait_for_function(
                "() => window.location.hostname.includes('cookidoo.thermomix.com') && !window.location.href.includes('/ciam/')",
                timeout=60000
            )
            print("3. Authentication SUCCESSFUL! Logged in and returned to cookidoo.thermomix.com")
            page.wait_for_timeout(3000)

            # Accept cookie banner on cookidoo if it appears
            try:
                accept_banner = page.locator("#onetrust-accept-btn-handler, button:has-text('Accept All')")
                if accept_banner.is_visible(timeout=3000):
                    accept_banner.click()
                    print("  -> Dismissed cookie banner.")
            except Exception:
                pass

            # Save session cookies & storage
            cookies = context.cookies()
            storage = page.evaluate("() => ({ localStorage: { ...localStorage }, sessionStorage: { ...sessionStorage } })")
            session_data = {
                "locale": locale,
                "base_url": base_url,
                "cookies": cookies,
                "storage": storage
            }
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2)
            print(f"  -> Saved session ({len(cookies)} cookies) to: {SESSION_FILE}")

            # 4. Explore target feature pages
            sections = [
                ("Cooking Profile & For You", f"{base_url}/foundation/{locale}/for-you"),
                ("My Week / Planner", f"{base_url}/foundation/{locale}/my-week"),
                ("Created Recipes", f"{base_url}/foundation/{locale}/created-recipes"),
                ("Saved Collections", f"{base_url}/foundation/{locale}/my-recipes"),
                ("My Devices", f"{base_url}/profile/{locale}/devices"),
                ("Data Usage & Activity", f"{base_url}/profile/{locale}/data-usage"),
            ]

            for name, url in sections:
                print(f"\nVisiting section: {name} -> {url}")
                try:
                    page.goto(url, wait_until="networkidle", timeout=20000)
                    page.wait_for_timeout(3000)  # allow dynamic ajax requests to settle
                    # Take screenshot of key sections
                    slug = name.lower().replace(" ", "_").replace("/", "_")
                    page.screenshot(path=str(CAPTURED_DIR / f"{slug}.png"))
                except Exception as ex:
                    print(f"  Warning on {url}: {ex}")

            # Save all intercepted calls
            output_file = CAPTURED_DIR / "network_calls.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(collector.captured_calls, f, indent=2)

            print(f"\n=======================================================")
            print(f"Exploration Complete! Captured {len(collector.captured_calls)} network API calls.")
            print(f"Raw calls saved to: {output_file}")
            print("=======================================================\n")

        except Exception as e:
            print(f"\n[ERROR during exploration]: {e}")
            page.screenshot(path=str(SDK_ROOT / "error_debug.png"))
            raise e
        finally:
            browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cookidoo Session Explorer")
    parser.add_argument("--interactive", action="store_true", help="Open visible browser to log in manually / handle 2FA")
    parser.add_argument("--headless", action="store_true", help="Run browser headlessly")
    args = parser.parse_args()

    explore(interactive=args.interactive, headless=args.headless)
