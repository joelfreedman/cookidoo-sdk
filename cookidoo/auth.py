"""
Authentication and Session Manager for Cookidoo.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import httpx
from .exceptions import CookidooAuthError

DEFAULT_LOCALE = "en-US"
DEFAULT_BASE_URL = "https://cookidoo.thermomix.com"


class CookidooAuth:
    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        session_file: Optional[str or Path] = None,
        locale: str = DEFAULT_LOCALE,
        base_url: str = DEFAULT_BASE_URL
    ):
        self.email = email or os.getenv("COOKIDOO_EMAIL")
        self.password = password or os.getenv("COOKIDOO_PASSWORD")
        self.locale = locale or os.getenv("COOKIDOO_LOCALE", DEFAULT_LOCALE)
        self.base_url = base_url.rstrip("/")

        if session_file:
            self.session_path = Path(session_file)
        else:
            default_path = os.getenv("COOKIDOO_SESSION_FILE", ".cookidoo_session.json")
            self.session_path = Path(default_path)

        self._cookies: Dict[str, str] = {}
        self._load_cached_session()

    def _load_cached_session(self) -> bool:
        """Loads cached session cookies from file if present."""
        if self.session_path.exists():
            try:
                with open(self.session_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cookies_list = data.get("cookies", [])
                    self._cookies = {c["name"]: c["value"] for c in cookies_list if "name" in c and "value" in c}
                    return len(self._cookies) > 0
            except Exception:
                return False
        return False

    def save_session(self, cookies: list) -> None:
        """Saves session cookies to JSON file."""
        data = {
            "locale": self.locale,
            "base_url": self.base_url,
            "cookies": cookies
        }
        with open(self.session_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self._cookies = {c["name"]: c["value"] for c in cookies if "name" in c and "value" in c}

    def is_session_valid(self) -> bool:
        """Checks if current session cookies are authenticated against Cookidoo API."""
        if not self._cookies:
            return False
        try:
            with httpx.Client(cookies=self._cookies, timeout=10.0) as client:
                resp = client.get(
                    f"{self.base_url}/profile/api/user",
                    headers={"Accept": "application/json"}
                )
                return resp.status_code == 200
        except Exception:
            return False

    def authenticate(self, headless: bool = True, force_refresh: bool = False) -> Dict[str, str]:
        """
        Authenticates against Cookidoo. If cached cookies are valid, reuses them.
        Otherwise performs browser CIAM login via Playwright to generate fresh session cookies.
        """
        if not force_refresh and self.is_session_valid():
            return self._cookies

        if not self.email or not self.password:
            raise CookidooAuthError(
                "COOKIDOO_EMAIL and COOKIDOO_PASSWORD credentials are required for login."
            )

        # Import playwright lazily so it is only required during login
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise CookidooAuthError(
                "playwright is required for browser login. Run: pip install playwright && playwright install chromium"
            )

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                login_url = f"{self.base_url}/profile/{self.locale}/login"
                page.goto(login_url, wait_until="networkidle")

                # Dismiss cookie banner
                try:
                    accept_btn = page.locator("#onetrust-accept-btn-handler, button:has-text('Accept All')")
                    if accept_btn.is_visible(timeout=2500):
                        accept_btn.click()
                except Exception:
                    pass

                # Fill CIAM form
                page.wait_for_selector('#username, input[name="username"], input[type="email"]', timeout=15000)
                page.fill('#username, input[name="username"], input[type="email"]', self.email)
                page.fill('#password, input[name="password"], input[type="password"]', self.password)
                page.locator('#login-submit-btn, button[type="submit"]').click()

                # Wait for redirect back to cookidoo
                page.wait_for_function(
                    "() => window.location.hostname.includes('cookidoo.thermomix.com') && !window.location.href.includes('/ciam/')",
                    timeout=60000
                )
                page.wait_for_timeout(2000)

                cookies = context.cookies()
                self.save_session(cookies)
                return self._cookies
            except Exception as e:
                raise CookidooAuthError(f"Login failed: {e}") from e
            finally:
                browser.close()

    @property
    def cookies(self) -> Dict[str, str]:
        if not self._cookies or not self.is_session_valid():
            self.authenticate()
        return self._cookies
