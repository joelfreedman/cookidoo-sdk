"""
Cookidoo Client implementation.
"""

from datetime import date, datetime
import json
import re
import time
from typing import Any, Dict, List, Optional, Union
import httpx

from .auth import CookidooAuth, DEFAULT_BASE_URL, DEFAULT_LOCALE
from .exceptions import (
    CookidooAuthError,
    CookidooError,
    CookidooNotFoundError,
    CookidooRateLimitError,
)
from .models import (
    CookingHistoryEntry,
    CookingHistoryResponse,
    CustomList,
    CustomListRecipeItem,
    CustomRecipe,
    CustomRecipeContent,
    RecipeYield,
    PlannedDay,
    PlannedDaysSummary,
    RecipeDetail,
    RecipeNote,
    RecipeSearchResult,
    RecipeSummary,
    UserProfile,
    OfflineRecipe,
)



ALGOLIA_APP_ID = "3TA8NT85XJ"
ALGOLIA_SEARCH_KEY = "MDdhMjFmM2MzZDBmN2ViZmYxZDRlMmRjOWY2NmYyMzczYjRkMDU1MDUwZTdmNGIzNTA2ODgwNjlkMzgwMTBmZWF0dHJpYnV0ZXNUb1JldHJpZXZlPWlkJTJDdGl0bGUlMkNpbWFnZSUyQ3JhdGluZyUyQ251bWJlck9mUmF0aW5ncyUyQ3RvdGFsVGltZSUyQ2NhdGVnb3J5JTJDcHVibGlzaGVkQXQlMkNkZXNjcmlwdGlvbiUyQ3VybCZmaWx0ZXJzPWFsbG93ZWRSb2xlcyUzQXB1YmxpYyUyME9SJTIwcmVjaXBlcy1wcm9kdWN0aW9uLmZhY2V0cy5leGFjdF9tYXRjaGVzLmFsbG93ZWRSb2xlcy52YWx1ZSUzQXB1YmxpYyZyZXN0cmljdEluZGljZXM9cmVjaXBlcy1wcm9kdWN0aW9uLWJ5LWVtcHR5U2VhcmNoU2NvcmUlMkNyZWNpcGVzLXByb2R1Y3Rpb24lMkNyZWNpcGVzLXByb2R1Y3Rpb24tYnktcHVibGlzaGVkQXQtZGVzYyUyQ3JlY2lwZXMtcHJvZHVjdGlvbi1ieS10aXRsZS1hc2MlMkNyZWNpcGVzLXByb2R1Y3Rpb24tYnktcmF0aW5nLWRlc2MlMkNyZWNpcGVzLXByb2R1Y3Rpb24tYnktdG90YWxUaW1lLWFzYyUyQ3JlY2lwZXMtcHJvZHVjdGlvbi1ieS1wcmVwYXJhdGlvblRpbWUtYXNjJTJDY2F0ZWdvcnktc3VnZ2VzdGlvbnMtcHJvZHVjdGlvbiUyQ3N1Z2dlc3Rpb25zLXJlY2lwZXMtcHJvZHVjdGlvbiUyQ2NvbGxlY3Rpb25zLXByb2R1Y3Rpb24lMkNjb2xsZWN0aW9ucy1wcm9kdWN0aW9uLWJ5LXB1Ymxpc2hlZEF0LWRlc2MlMkNjb2xsZWN0aW9ucy1wcm9kdWN0aW9uLWJ5LXRpdGxlLWFzYyUyQ2VkaXRvcmlhbC1wcm9kdWN0aW9uJTJDZWRpdG9yaWFsLXByb2R1Y3Rpb24tYnktdGl0bGUtYXNjJnZhbGlkVW50aWw9MTc5MTEzMDI1MA=="

CLOUDINARY_CLOUD_NAME = "vorwerk-users-gc"
CLOUDINARY_API_KEY = "993585863591145"
CLOUDINARY_UPLOAD_PRESET = "prod-customer-recipe-signed"
CLOUDINARY_UPLOAD_URL = f"https://vorwerk-users-gc.api-fast-eu.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/image/upload"



class CookidooClient:
    """
    Main SDK Client for Cookidoo (Thermomix).
    """

    def __init__(
        self,
        auth: Optional[CookidooAuth] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        locale: str = DEFAULT_LOCALE,
        base_url: str = DEFAULT_BASE_URL,
        session_file: Optional[str] = None,
        db_path: Optional[str] = None,
        storage: Optional[Any] = None,
        max_active_recipes: int = 50
    ):
        self.locale = locale
        self.base_url = base_url.rstrip("/")
        self.auth = auth or CookidooAuth(
            email=email,
            password=password,
            locale=locale,
            base_url=base_url,
            session_file=session_file
        )
        self._http = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept-Language": f"{locale},en;q=0.9",
            },
            timeout=15.0
        )
        from .storage import CookidooStorage
        from .sync import CookidooSyncManager
        self.storage = storage or (CookidooStorage(db_path=db_path) if db_path else CookidooStorage())
        self.sync_manager = CookidooSyncManager(client=self, storage=self.storage, max_active=max_active_recipes)
        self._algolia_key: Optional[str] = None


    def _request(
        self,
        method: str,
        path_or_url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> httpx.Response:
        url = path_or_url if path_or_url.startswith("http") else f"{self.base_url}/{path_or_url.lstrip('/')}"
        req_headers = {"Accept": "application/json, text/plain, */*"}
        if headers:
            req_headers.update(headers)

        cookies = self.auth.cookies
        self._http.cookies.update(cookies)

        # Automatically attach CSRF tokens for mutating requests
        if method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
            xsrf = cookies.get("XSRF-TOKEN")
            csrf = cookies.get("csrf_")
            if xsrf:
                req_headers["X-XSRF-TOKEN"] = xsrf
            if csrf:
                req_headers["X-CSRF-TOKEN"] = csrf

        resp = self._http.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            data=data,
            headers=req_headers
        )

        if resp.status_code == 401:
            # Session expired, re-authenticate once
            self.auth.authenticate(force_refresh=True)
            cookies = self.auth.cookies
            self._http.cookies.update(cookies)
            if method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
                xsrf = cookies.get("XSRF-TOKEN")
                csrf = cookies.get("csrf_")
                if xsrf:
                    req_headers["X-XSRF-TOKEN"] = xsrf
                if csrf:
                    req_headers["X-CSRF-TOKEN"] = csrf

            resp = self._http.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                data=data,
                headers=req_headers
            )

        if resp.status_code == 401:
            raise CookidooAuthError("Unauthorized: Session is invalid.")
        elif resp.status_code == 404:
            raise CookidooNotFoundError(f"Resource not found at {url}")
        elif resp.status_code == 429:
            raise CookidooRateLimitError("Rate limit exceeded. Please back off and retry.")
        elif resp.status_code >= 400:
            raise CookidooError(f"Cookidoo API error [{resp.status_code}]: {resp.text}")

        return resp

    # -------------------------------------------------------------
    # 1. User Profile
    # -------------------------------------------------------------
    def get_profile(self) -> UserProfile:
        """Fetches the current user profile."""
        resp = self._request("GET", "profile/api/user")
        return UserProfile.model_validate(resp.json())

    # -------------------------------------------------------------
    # 2. Cooking History ("Recently Cooked")
    # -------------------------------------------------------------
    def get_cooking_history(self, limit: int = 50) -> List[CookingHistoryEntry]:
        """
        Retrieves the user's cooking history (recently cooked recipes on Thermomix).
        Automatically saves/updates entries in local offline storage.
        """
        resp = self._request("GET", f"organize/{self.locale}/api/cooking-history")
        data = resp.json()
        parsed = CookingHistoryResponse.model_validate(data)
        entries = sorted(parsed.entries, key=lambda x: x.details.timestamp, reverse=True)
        result = entries[:limit]

        for entry in result:
            try:
                self.storage.upsert_from_history_entry(entry)
            except Exception:
                pass

        return result

    # -------------------------------------------------------------
    # 3. Meal Planning ("My Week")
    # -------------------------------------------------------------
    def get_planned_days(self, start_date: Optional[str] = None) -> List[str]:
        """
        Gets a list of all dates ('YYYY-MM-DD') that have planned recipes.
        If start_date is not given, defaults to current month ('YYYY-MM-01').
        """
        if not start_date:
            today = date.today()
            start_date = f"{today.year}-{today.month:02d}-01"
        resp = self._request("GET", f"planning/{self.locale}/api/my-day/planned-recipes/{start_date}?span=1")
        summary = PlannedDaysSummary.model_validate(resp.json())
        return summary.dayKeys

    def get_planned_day(self, day_key: str) -> Optional[PlannedDay]:
        """
        Retrieves planned recipes for a specific day key (e.g. '2026-09-26').
        Returns None if no plan exists for that day.
        """
        try:
            resp = self._request("GET", f"planning/{self.locale}/api/my-day/{day_key}")
            return PlannedDay.model_validate(resp.json())
        except CookidooNotFoundError:
            return None

    def add_to_plan(
        self,
        day_key: str,
        recipe_id: str,
        recipe_source: str = "VORWERK"
    ) -> bool:
        """
        Schedules a recipe for a specific date in 'My Week'.
        If the recipe has an alternate substitution configured in local storage,
        the substitution is automatically used instead (and activated on Cookidoo if needed).
        Increments the recipe's local planning frequency counter.
        """
        target_id = recipe_id
        target_source = recipe_source

        # Check for configured substitution
        try:
            stored = self.storage.get_recipe(recipe_id)
            if stored and stored.substitution_recipe_id:
                sub = self.storage.get_recipe(stored.substitution_recipe_id)
                if sub:
                    if sub.source == "CUSTOMER" and not sub.is_active_on_cookidoo:
                        sub = self.sync_manager.activate_recipe(sub.id)
                    target_id = sub.remote_id or sub.id
                    target_source = sub.source
        except Exception:
            pass

        payload = {
            "dayKey": day_key,
            "recipeIds": [target_id],
            "recipeSource": target_source
        }
        resp = self._request(
            "PUT",
            f"planning/{self.locale}/api/my-day",
            json_data=payload
        )
        success = resp.status_code in (200, 201, 204)
        if success:
            try:
                self.storage.increment_planned_count(recipe_id)
                if target_id != recipe_id:
                    self.storage.increment_planned_count(target_id)
            except Exception:
                pass
        return success

    def remove_from_plan(
        self,
        day_key: str,
        recipe_id: str,
        recipe_source: str = "VORWERK"
    ) -> bool:
        """
        Removes a planned recipe from a specific day in 'My Week'.
        If the recipe has an alternate substitution configured, resolves the substitution.
        """
        target_id = recipe_id
        target_source = recipe_source
        try:
            stored = self.storage.get_recipe(recipe_id)
            if stored and stored.substitution_recipe_id:
                sub = self.storage.get_recipe(stored.substitution_recipe_id)
                if sub:
                    target_id = sub.remote_id or sub.id
                    target_source = sub.source
        except Exception:
            pass

        url = f"planning/{self.locale}/api/my-day/{day_key}/recipes/{target_id}?recipeSource={target_source}"
        resp = self._request(
            "DELETE",
            url
        )
        return resp.status_code in (200, 204)

    # -------------------------------------------------------------
    # 4. Custom Recipes ("Created Recipes")
    # -------------------------------------------------------------
    def get_created_recipes(self) -> List[CustomRecipe]:
        """
        Lists all custom/created recipes in the user's account.
        Automatically caches them in local offline storage.
        """
        resp = self._request("GET", f"created-recipes/{self.locale}")
        data = resp.json()
        items = data.get("items", [])
        parsed = [CustomRecipe.model_validate(item) for item in items]
        for cr in parsed:
            try:
                self.storage.upsert_from_custom_recipe(cr, is_active=True)
            except Exception:
                pass
        return parsed


    def get_created_recipe(self, recipe_id: str) -> CustomRecipe:
        """
        Fetches full details of a specific created custom recipe.
        """
        resp = self._request("GET", f"created-recipes/{self.locale}/{recipe_id}")
        return CustomRecipe.model_validate(resp.json())

    def create_custom_recipe(
        self,
        name: str,
        ingredients: Optional[List[str]] = None,
        instructions: Optional[List[Union[str, Dict]]] = None,
        portions: int = 4,
        tools: Optional[Union[str, List[str]]] = None,
        tool: Optional[str] = None
    ) -> CustomRecipe:
        """
        Creates a new custom recipe on Cookidoo with ingredients, steps, portion yield,
        and device compatibility (e.g. TM7, TM6, TM5).

        :param name: Recipe title
        :param ingredients: List of ingredient strings
        :param instructions: List of step strings or structured step dicts with annotations
        :param portions: Number of servings (portions)
        :param tools: Target Thermomix appliances (e.g. "TM7", ["TM7"], ["TM6", "TM7"])
        :param tool: Legacy single tool alias (e.g. "TM6")
        """
        # Step 1: Create draft recipe
        resp = self._request(
            "POST",
            f"created-recipes/{self.locale}",
            json_data={"recipeName": name}
        )
        data = resp.json()
        recipe_id = data.get("recipeId")

        # Step 2: Patch ingredients if provided
        if ingredients:
            self._request(
                "PATCH",
                f"created-recipes/{self.locale}/{recipe_id}",
                json_data={"ingredients": [{"type": "INGREDIENT", "text": ing} for ing in ingredients]}
            )

        # Step 3: Patch instructions if provided (supports strings or structured steps with annotations)
        if instructions:
            step_objects = []
            for step in instructions:
                if isinstance(step, dict):
                    step_dict = dict(step)
                    if "type" not in step_dict:
                        step_dict["type"] = "STEP"
                    step_objects.append(step_dict)
                else:
                    step_objects.append({"type": "STEP", "text": str(step)})

            self._request(
                "PATCH",
                f"created-recipes/{self.locale}/{recipe_id}",
                json_data={"instructions": step_objects}
            )

        # Step 4: Patch portions/yield if different from default
        if portions != 4:
            self._request(
                "PATCH",
                f"created-recipes/{self.locale}/{recipe_id}",
                json_data={"yield": {"value": portions, "unitText": "portion"}}
            )

        # Step 5: Patch device tools if specified (e.g. TM7, TM6, TM5)
        target_tools = tools if tools is not None else tool
        if target_tools is not None:
            if isinstance(target_tools, str):
                tools_list = [target_tools.upper()]
            else:
                tools_list = [t.upper() for t in target_tools]
            self._request(
                "PATCH",
                f"created-recipes/{self.locale}/{recipe_id}",
                json_data={"tools": tools_list}
            )

        # Return full refreshed custom recipe
        return self.get_created_recipe(recipe_id)

    def import_custom_recipe(self, recipe_url: str) -> CustomRecipe:
        """
        Imports an official Cookidoo recipe by URL into Created Recipes.
        """
        resp = self._request(
            "POST",
            f"created-recipes/{self.locale}",
            json_data={"recipeUrl": recipe_url}
        )
        return CustomRecipe.model_validate(resp.json())

    def update_custom_recipe(
        self,
        recipe_id: str,
        name: Optional[str] = None,
        ingredients: Optional[List[str]] = None,
        instructions: Optional[List[Union[str, Dict]]] = None,
        portions: Optional[int] = None,
        tools: Optional[Union[str, List[str]]] = None
    ) -> CustomRecipe:
        """
        Updates an existing custom recipe's title, ingredients, instructions, portions, or appliances.
        """
        if name:
            self._request("PATCH", f"created-recipes/{self.locale}/{recipe_id}", json_data={"name": name})
        if ingredients is not None:
            self._request(
                "PATCH",
                f"created-recipes/{self.locale}/{recipe_id}",
                json_data={"ingredients": [{"type": "INGREDIENT", "text": ing} for ing in ingredients]}
            )
        if instructions is not None:
            step_objects = []
            for step in instructions:
                if isinstance(step, dict):
                    step_dict = dict(step)
                    if "type" not in step_dict:
                        step_dict["type"] = "STEP"
                    step_objects.append(step_dict)
                else:
                    step_objects.append({"type": "STEP", "text": str(step)})

            self._request(
                "PATCH",
                f"created-recipes/{self.locale}/{recipe_id}",
                json_data={"instructions": step_objects}
            )
        if portions is not None:
            self._request(
                "PATCH",
                f"created-recipes/{self.locale}/{recipe_id}",
                json_data={"yield": {"value": portions, "unitText": "portion"}}
            )
        if tools is not None:
            if isinstance(tools, str):
                tools_list = [tools.upper()]
            else:
                tools_list = [t.upper() for t in tools]
            self._request(
                "PATCH",
                f"created-recipes/{self.locale}/{recipe_id}",
                json_data={"tools": tools_list}
            )
        return self.get_created_recipe(recipe_id)

    def delete_custom_recipe(self, recipe_id: str) -> bool:
        """
        Deletes a custom recipe by ID.
        """
        resp = self._request("DELETE", f"created-recipes/{self.locale}/{recipe_id}")
        return resp.status_code in (200, 204)

    def upload_recipe_image(
        self,
        recipe_id: str,
        image_file_or_bytes: Union[str, bytes],
        format: str = "jpg",
        custom_coordinates: Optional[str] = None
    ) -> CustomRecipe:
        """
        Uploads a photo for a created custom recipe directly to Vorwerk's Cloudinary storage
        and links it to the recipe.

        :param recipe_id: The created recipe ID.
        :param image_file_or_bytes: Path to local image file (e.g. 'focaccia.jpg') or raw bytes.
        :param format: 'jpg', 'jpeg', or 'png' (defaults to 'jpg').
        :param custom_coordinates: Optional crop coordinates (e.g. '0,0,300,300').
        """
        if isinstance(image_file_or_bytes, str):
            with open(image_file_or_bytes, "rb") as f:
                img_bytes = f.read()
            ext = image_file_or_bytes.split(".")[-1].lower()
            if ext in ("jpg", "jpeg", "png"):
                format = ext if ext != "jpeg" else "jpg"
        else:
            img_bytes = image_file_or_bytes

        # Determine dimensions for coordinates
        if not custom_coordinates:
            try:
                from PIL import Image
                import io
                with Image.open(io.BytesIO(img_bytes)) as pil_img:
                    w, h = pil_img.size
                    custom_coordinates = f"0,0,{w},{h}"
            except Exception:
                custom_coordinates = "0,0,300,300"

        ts = int(time.time())

        # Step 1: Request signature from Cookidoo
        sig_resp = self._request(
            "POST",
            f"created-recipes/{self.locale}/image/signature",
            json_data={
                "timestamp": ts,
                "source": "uw",
                "custom_coordinates": custom_coordinates
            }
        )
        signature = sig_resp.json().get("signature")

        # Step 2: Upload to Vorwerk Cloudinary
        data = {
            "api_key": CLOUDINARY_API_KEY,
            "timestamp": str(ts),
            "signature": signature,
            "upload_preset": CLOUDINARY_UPLOAD_PRESET,
            "source": "uw",
            "custom_coordinates": custom_coordinates
        }
        content_type = "image/png" if format == "png" else "image/jpeg"
        files = {
            "file": (f"recipe.{format}", img_bytes, content_type)
        }
        upload_resp = httpx.post(CLOUDINARY_UPLOAD_URL, data=data, files=files, timeout=25.0)
        if upload_resp.status_code != 200:
            raise CookidooError(f"Cloudinary upload failed [{upload_resp.status_code}]: {upload_resp.text}")

        upload_data = upload_resp.json()
        public_id = upload_data.get("public_id")
        actual_fmt = upload_data.get("format", format)
        image_ref = f"{public_id}.{actual_fmt}"

        # Step 3: Attach to custom recipe
        return self.set_recipe_image(recipe_id, image_reference=image_ref, owned_by_user=True)

    def set_recipe_image(
        self,
        recipe_id: str,
        image_reference: str,
        owned_by_user: bool = True
    ) -> CustomRecipe:
        """
        Sets a custom recipe's image to a Vorwerk asset reference
        (e.g. 'prod/img/customer-recipe/w4wyke7twqrhvlecv15q.jpg').
        """
        self._request(
            "PATCH",
            f"created-recipes/{self.locale}/{recipe_id}",
            json_data={
                "image": image_reference,
                "isImageOwnedByUser": owned_by_user
            }
        )
        return self.get_created_recipe(recipe_id)

    def remove_recipe_image(self, recipe_id: str) -> CustomRecipe:
        """
        Removes the photo attached to a custom recipe.
        """
        self._request(
            "PATCH",
            f"created-recipes/{self.locale}/{recipe_id}",
            json_data={"image": None}
        )
        return self.get_created_recipe(recipe_id)

    # -------------------------------------------------------------
    # 5. User Lists & Collections ("My Lists")
    # -------------------------------------------------------------
    def get_custom_lists(self) -> List[CustomList]:
        """
        Lists all custom recipe lists / collections owned by the user.
        """
        resp = self._request("GET", f"organize/{self.locale}/api/custom-list")
        data = resp.json()
        items = data.get("customlists", [])
        return [CustomList.model_validate(item) for item in items]

    def get_custom_list(self, list_id: str) -> CustomList:
        """
        Fetches detailed information for a custom list, including its recipes.
        """
        resp = self._request("GET", f"organize/{self.locale}/api/custom-list/{list_id}")
        return CustomList.model_validate(resp.json())

    def create_custom_list(self, title: str) -> CustomList:
        """
        Creates a new empty recipe list / collection.
        """
        resp = self._request(
            "POST",
            f"organize/{self.locale}/api/custom-list",
            json_data={"title": title}
        )
        data = resp.json()
        content = data.get("content", {})
        return CustomList.model_validate(content)

    def update_custom_list(self, list_id: str, title: str) -> CustomList:
        """
        Updates / renames an existing custom list.
        """
        self._request(
            "PUT",
            f"organize/{self.locale}/api/custom-list/{list_id}",
            json_data={"title": title}
        )
        return self.get_custom_list(list_id)

    def add_recipes_to_custom_list(self, list_id: str, recipe_ids: List[str]) -> bool:
        """
        Adds one or more recipes (by ID) to a custom list.
        """
        resp = self._request(
            "PUT",
            f"organize/{self.locale}/api/custom-list/{list_id}",
            json_data={"recipeIds": recipe_ids}
        )
        return resp.status_code in (200, 204)

    def remove_recipe_from_custom_list(self, list_id: str, recipe_id: str) -> bool:
        """
        Removes a recipe from a custom list.
        """
        resp = self._request(
            "DELETE",
            f"organize/{self.locale}/api/custom-list/{list_id}/recipes/{recipe_id}"
        )
        return resp.status_code in (200, 204)

    def delete_custom_list(self, list_id: str) -> bool:
        """
        Deletes a custom list / collection.
        """
        resp = self._request("DELETE", f"organize/{self.locale}/api/custom-list/{list_id}")
        return resp.status_code in (200, 204)


    # -------------------------------------------------------------
    # 6. Recipe Notes (Personal Notes on Published / Official Recipes)
    # -------------------------------------------------------------
    def get_recipe_note(self, recipe_id: str) -> Optional[RecipeNote]:
        """
        Retrieves the personal note associated with a recipe.
        Returns None if no note exists for the recipe.
        """
        resp = self._request("GET", f"recipe-notes/{self.locale}/recipes/{recipe_id}")
        if resp.status_code == 204 or not resp.text.strip():
            return None
        return RecipeNote.model_validate(resp.json())

    def create_recipe_note(self, recipe_id: str, text: str) -> RecipeNote:
        """
        Creates a new personal note for a recipe (up to 1000 characters).
        Raises CookidooError if a note already exists (use save_recipe_note instead).
        """
        resp = self._request(
            "POST",
            f"recipe-notes/{self.locale}/recipes",
            json_data={"recipeId": recipe_id, "text": text}
        )
        return RecipeNote.model_validate(resp.json())

    def update_recipe_note(self, recipe_id: str, text: str) -> RecipeNote:
        """
        Updates an existing personal note for a recipe.
        """
        resp = self._request(
            "PUT",
            f"recipe-notes/{self.locale}/recipes/{recipe_id}",
            json_data={"text": text}
        )
        return RecipeNote.model_validate(resp.json())

    def save_recipe_note(self, recipe_id: str, text: str) -> RecipeNote:
        """
        Upsert helper: Creates a new note if none exists, or updates the existing note.
        """
        existing = self.get_recipe_note(recipe_id)
        if existing:
            return self.update_recipe_note(recipe_id, text)
        return self.create_recipe_note(recipe_id, text)

    def delete_recipe_note(self, recipe_id: str) -> bool:
        """
        Deletes the personal note associated with a recipe.
        """
        resp = self._request("DELETE", f"recipe-notes/{self.locale}/recipes/{recipe_id}")
        return resp.status_code in (200, 204)

    def _get_algolia_key(self, force_refresh: bool = False) -> str:
        """
        Retrieves the dynamic Algolia search API key from Cookidoo search configuration.
        Auto-refreshes when expired or upon request.
        """
        if self._algolia_key and not force_refresh:
            return self._algolia_key

        try:
            resp = self._http.get(f"{self.base_url}/search/{self.locale}")
            if resp.status_code == 200:
                idx = resp.text.find('"apiKey":"')
                if idx != -1:
                    end_idx = resp.text.find('"', idx + 10)
                    if end_idx != -1:
                        self._algolia_key = resp.text[idx + 10:end_idx]
                        return self._algolia_key
        except Exception:
            pass

        return self._algolia_key or ALGOLIA_SEARCH_KEY

    # -------------------------------------------------------------
    # 7. Search & Catalog (Algolia)
    # -------------------------------------------------------------
    def search(
        self,
        query: str,
        page: int = 0,
        hits_per_page: int = 20,
        sort_by: str = "relevance"
    ) -> RecipeSearchResult:
        """
        Fast full-text search across official Cookidoo recipes.
        sort_by options: 'relevance', 'rating', 'totalTime', 'publishedAt'
        """
        index_name = "recipes-production"
        if sort_by == "rating":
            index_name = "recipes-production-by-rating-desc"
        elif sort_by == "totalTime":
            index_name = "recipes-production-by-totalTime-asc"
        elif sort_by == "publishedAt":
            index_name = "recipes-production-by-publishedAt-desc"

        algolia_key = self._get_algolia_key()
        url = f"https://{ALGOLIA_APP_ID.lower()}-dsn.algolia.net/1/indexes/*/queries"
        headers = {
            "x-algolia-application-id": ALGOLIA_APP_ID,
            "x-algolia-api-key": algolia_key,
            "Content-Type": "application/json"
        }
        params = f"query={query}&page={page}&hitsPerPage={hits_per_page}"
        payload = {
            "requests": [
                {
                    "indexName": index_name,
                    "params": params
                }
            ]
        }
        resp = self._http.post(url, headers=headers, json=payload, timeout=10.0)
        if resp.status_code in (400, 403):
            # Refresh expired key and retry once
            algolia_key = self._get_algolia_key(force_refresh=True)
            headers["x-algolia-api-key"] = algolia_key
            resp = self._http.post(url, headers=headers, json=payload, timeout=10.0)

        if resp.status_code != 200:
            raise CookidooError(f"Search failed with code {resp.status_code}")

        res = resp.json()["results"][0]
        hits = res.get("hits", [])
        recipes = [
            RecipeSummary(
                id=h.get("id"),
                title=h.get("title", ""),
                rating=h.get("rating"),
                numberOfRatings=h.get("numberOfRatings"),
                totalTime=h.get("totalTime"),
                preparationTime=h.get("preparationTime"),
                category=h.get("category"),
                image=h.get("image"),
                url=h.get("url")
            )
            for h in hits
        ]
        return RecipeSearchResult(
            query=query,
            totalHits=res.get("nbHits", 0),
            page=res.get("page", 0),
            hitsPerPage=res.get("hitsPerPage", hits_per_page),
            recipes=recipes
        )

    def get_recipe_details(self, recipe_id: str, include_note: bool = True) -> RecipeDetail:
        """
        Fetches full recipe details (ingredients, preparation steps, times, personal note)
        for any official recipe ID (e.g. 'r63350').
        """
        resp = self._request(
            "GET",
            f"recipes/recipe/{self.locale}/{recipe_id}",
            headers={"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        )
        html = resp.text

        ld_json_blocks = re.findall(r"<script type=\"application/ld\+json\">(.*?)</script>", html, re.DOTALL)
        for block in ld_json_blocks:
            try:
                data = json.loads(block)
                if data.get("@type") == "Recipe":
                    raw_instructions = data.get("recipeInstructions", [])
                    instructions = [
                        step.get("text") if isinstance(step, dict) else str(step)
                        for step in raw_instructions
                    ]
                    # Clean any HTML tags inside instructions
                    instructions = [re.sub(r"<[^>]+>", "", step).strip() for step in instructions]

                    user_note = None
                    if include_note:
                        try:
                            note_obj = self.get_recipe_note(recipe_id)
                            if note_obj:
                                user_note = note_obj.text
                        except Exception:
                            user_note = None

                    detail = RecipeDetail(
                        id=recipe_id,
                        name=data.get("name", ""),
                        description=data.get("description"),
                        prepTime=data.get("prepTime"),
                        totalTime=data.get("totalTime"),
                        recipeYield=str(data.get("recipeYield")) if data.get("recipeYield") else None,
                        ingredients=data.get("recipeIngredient", []),
                        instructions=instructions,
                        image=data.get("image"),
                        note=user_note
                    )
                    # Automatically save complete copy offline
                    try:
                        self.storage.upsert_from_recipe_detail(detail)
                    except Exception:
                        pass
                    return detail
            except Exception:
                continue

        raise CookidooNotFoundError(f"Could not parse recipe details for {recipe_id}")

    # -------------------------------------------------------------
    # 8. Offline Library, Tagging, Voting & Sync
    # -------------------------------------------------------------
    def tag_recipe(self, recipe_id: str, tags: List[str]) -> OfflineRecipe:
        """
        Adds one or more custom tags to a recipe in the local offline library.
        Tags can be added to both official published recipes and created custom recipes.
        """
        return self.storage.tag_recipe(recipe_id, tags)

    def untag_recipe(self, recipe_id: str, tag: str) -> OfflineRecipe:
        """Removes a custom tag from a recipe in the local offline library."""
        return self.storage.untag_recipe(recipe_id, tag)

    def vote_recipe(self, recipe_id: str, vote: int) -> OfflineRecipe:
        """
        Records user sentiment (+1 for upvote, -1 for downvote, 0 for neutral) for any recipe.
        """
        return self.storage.vote_recipe(recipe_id, vote)

    def exclude_recipe(self, recipe_id: str, excluded: bool = True) -> OfflineRecipe:
        """
        Marks or unmarks a recipe to be excluded from meal planning or recommendations.
        """
        return self.storage.exclude_recipe(recipe_id, excluded)

    def set_recipe_substitution(self, recipe_id: str, substitute_id: Optional[str]) -> OfflineRecipe:
        """
        Configures an alternate substitution recipe (e.g. mapping official pasta to a custom GF pasta).
        When the SDK schedules this recipe in the weekly planner, the substitute is used automatically.
        """
        return self.storage.set_substitution(recipe_id, substitute_id)

    def get_offline_recipe(self, recipe_id: str) -> Optional[OfflineRecipe]:
        """
        Retrieves a complete recipe and its metadata (tags, vote, planning count, substitutions)
        from local offline storage.
        """
        return self.storage.get_recipe(recipe_id)

    def list_offline_recipes(
        self,
        source: Optional[str] = None,
        active_only: bool = False,
        tag: Optional[str] = None,
        excluded: Optional[bool] = None,
        vote: Optional[int] = None,
        query: Optional[str] = None
    ) -> List[OfflineRecipe]:
        """
        Lists all recipes cached in local offline storage with filtering options.
        """
        return self.storage.list_recipes(
            source=source,
            active_only=active_only,
            tag=tag,
            excluded=excluded,
            vote=vote,
            query=query
        )

    def sync_active_recipes(self, desired_recipe_ids: List[str]) -> Dict[str, Any]:
        """
        Reconciles your active Cookidoo recipes with your desired selection, ensuring
        total active created recipes on Cookidoo do not exceed the configured limit (<= 50).
        """
        return self.sync_manager.sync_active_selection(desired_recipe_ids)


