"""
Local SQLite-backed Offline Recipe Library and Metadata Storage.
"""

from datetime import datetime, timezone
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

from .models import (
    CookingHistoryEntry,
    CustomRecipe,
    OfflineRecipe,
    RecipeDetail,
)

DEFAULT_DB_PATH = os.path.join(os.getcwd(), ".cookidoo_library.db")


class CookidooStorage:
    """
    Manages local offline recipe database, custom tags, up/down voting,
    planner frequency counts, exclusions, and substitution mappings.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS recipes (
                id TEXT PRIMARY KEY,
                remote_id TEXT,
                name TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'CUSTOMER',
                ingredients TEXT NOT NULL DEFAULT '[]',
                instructions TEXT NOT NULL DEFAULT '[]',
                portions INTEGER DEFAULT 4,
                prep_time INTEGER,
                total_time INTEGER,
                image_url TEXT,
                notes TEXT,
                raw_data TEXT NOT NULL DEFAULT '{}',
                tags TEXT NOT NULL DEFAULT '[]',
                vote INTEGER NOT NULL DEFAULT 0,
                times_planned INTEGER NOT NULL DEFAULT 0,
                is_excluded INTEGER NOT NULL DEFAULT 0,
                substitution_recipe_id TEXT,
                is_active_on_cookidoo INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_cooked_at TEXT,
                last_planned_at TEXT
            )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON recipes (source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_remote_id ON recipes (remote_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_active ON recipes (is_active_on_cookidoo)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_excluded ON recipes (is_excluded)")
            conn.commit()

    def _row_to_model(self, row: sqlite3.Row) -> OfflineRecipe:
        return OfflineRecipe(
            id=row["id"],
            remote_id=row["remote_id"],
            name=row["name"],
            source=row["source"],
            ingredients=json.loads(row["ingredients"]),
            instructions=json.loads(row["instructions"]),
            portions=row["portions"],
            prep_time=row["prep_time"],
            total_time=row["total_time"],
            image_url=row["image_url"],
            notes=row["notes"],
            raw_data=json.loads(row["raw_data"]),
            tags=json.loads(row["tags"]),
            vote=row["vote"],
            times_planned=row["times_planned"],
            is_excluded=bool(row["is_excluded"]),
            substitution_recipe_id=row["substitution_recipe_id"],
            is_active_on_cookidoo=bool(row["is_active_on_cookidoo"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            last_cooked_at=datetime.fromisoformat(row["last_cooked_at"]) if row["last_cooked_at"] else None,
            last_planned_at=datetime.fromisoformat(row["last_planned_at"]) if row["last_planned_at"] else None,
        )

    def save_recipe(self, recipe: OfflineRecipe, preserve_metadata: bool = False) -> OfflineRecipe:
        """
        Saves or updates an offline recipe.
        If preserve_metadata is True (e.g. during remote ingestion), existing local metadata
        (tags, vote, times_planned, exclusion, substitution) is preserved.
        """
        existing = self.get_recipe(recipe.id)
        now_str = datetime.now(timezone.utc).isoformat()

        tags = recipe.tags
        vote = recipe.vote
        times_planned = recipe.times_planned
        is_excluded = recipe.is_excluded
        substitution_recipe_id = recipe.substitution_recipe_id
        last_cooked_at = recipe.last_cooked_at
        last_planned_at = recipe.last_planned_at
        created_at_str = recipe.created_at.isoformat() if recipe.created_at else now_str

        if existing:
            created_at_str = existing.created_at.isoformat()
            if preserve_metadata:
                if not tags and existing.tags:
                    tags = existing.tags
                if vote == 0 and existing.vote != 0:
                    vote = existing.vote
                if times_planned == 0 and existing.times_planned > 0:
                    times_planned = existing.times_planned
                if not is_excluded and existing.is_excluded:
                    is_excluded = existing.is_excluded
                if not substitution_recipe_id and existing.substitution_recipe_id:
                    substitution_recipe_id = existing.substitution_recipe_id
                if not last_cooked_at and existing.last_cooked_at:
                    last_cooked_at = existing.last_cooked_at
                if not last_planned_at and existing.last_planned_at:
                    last_planned_at = existing.last_planned_at

        with self._get_connection() as conn:
            conn.execute("""
            INSERT OR REPLACE INTO recipes (
                id, remote_id, name, source, ingredients, instructions, portions,
                prep_time, total_time, image_url, notes, raw_data, tags, vote,
                times_planned, is_excluded, substitution_recipe_id, is_active_on_cookidoo,
                created_at, updated_at, last_cooked_at, last_planned_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recipe.id,
                recipe.remote_id or (existing.remote_id if existing else None),
                recipe.name,
                recipe.source,
                json.dumps(recipe.ingredients),
                json.dumps(recipe.instructions),
                recipe.portions,
                recipe.prep_time,
                recipe.total_time,
                recipe.image_url,
                recipe.notes or (existing.notes if existing else None),
                json.dumps(recipe.raw_data),
                json.dumps(tags),
                vote,
                times_planned,
                1 if is_excluded else 0,
                substitution_recipe_id,
                1 if recipe.is_active_on_cookidoo else 0,
                created_at_str,
                now_str,
                last_cooked_at.isoformat() if last_cooked_at else None,
                last_planned_at.isoformat() if last_planned_at else None,
            ))
            conn.commit()

        return self.get_recipe(recipe.id)

    def get_recipe(self, recipe_id: str) -> Optional[OfflineRecipe]:
        """Fetches an offline recipe by its local ID or remote ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM recipes WHERE id = ? OR remote_id = ?", (recipe_id, recipe_id))
            row = cursor.fetchone()
            if row:
                return self._row_to_model(row)
        return None

    def delete_recipe(self, recipe_id: str) -> bool:
        """Deletes a recipe from local offline storage."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM recipes WHERE id = ? OR remote_id = ?", (recipe_id, recipe_id))
            conn.commit()
            return cursor.rowcount > 0

    def list_recipes(
        self,
        source: Optional[str] = None,
        active_only: bool = False,
        tag: Optional[str] = None,
        excluded: Optional[bool] = None,
        vote: Optional[int] = None,
        query: Optional[str] = None
    ) -> List[OfflineRecipe]:
        """
        Lists and filters offline recipes by source, active status, tag, exclusion, or vote.
        """
        sql = "SELECT * FROM recipes WHERE 1=1"
        params = []

        if source:
            sql += " AND source = ?"
            params.append(source.upper())

        if active_only:
            sql += " AND is_active_on_cookidoo = 1"

        if excluded is not None:
            sql += " AND is_excluded = ?"
            params.append(1 if excluded else 0)

        if vote is not None:
            sql += " AND vote = ?"
            params.append(vote)

        if query:
            sql += " AND (name LIKE ? OR ingredients LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])

        sql += " ORDER BY updated_at DESC"

        with self._get_connection() as conn:
            cursor = conn.execute(sql, params)
            recipes = [self._row_to_model(row) for row in cursor.fetchall()]

        if tag:
            recipes = [r for r in recipes if tag.lower() in [t.lower() for t in r.tags]]

        return recipes

    def count_active_created_recipes(self) -> int:
        """Counts how many user-created recipes are currently flagged as active on Cookidoo."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM recipes WHERE source = 'CUSTOMER' AND is_active_on_cookidoo = 1"
            )
            return cursor.fetchone()[0]

    def count_all_recipes(self) -> int:
        """Counts total recipes cached in local offline database."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM recipes")
            return cursor.fetchone()[0]

    # -------------------------------------------------------------
    # Metadata Operations: Tags, Votes, Planning, Exclusion
    # -------------------------------------------------------------
    def tag_recipe(self, recipe_id: str, tags: List[str]) -> OfflineRecipe:
        """Adds custom tags to a recipe."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise KeyError(f"Recipe '{recipe_id}' not found in local library.")
        current_tags = set(recipe.tags)
        for t in tags:
            clean = t.strip()
            if clean:
                current_tags.add(clean)
        recipe.tags = sorted(list(current_tags))
        return self.save_recipe(recipe)

    def untag_recipe(self, recipe_id: str, tag: str) -> OfflineRecipe:
        """Removes a custom tag from a recipe."""
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise KeyError(f"Recipe '{recipe_id}' not found in local library.")
        clean = tag.strip().lower()
        recipe.tags = [t for t in recipe.tags if t.lower() != clean]
        return self.save_recipe(recipe)

    def vote_recipe(self, recipe_id: str, vote: int) -> OfflineRecipe:
        """
        Sets user vote (+1 upvote, -1 downvote, 0 neutral).
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise KeyError(f"Recipe '{recipe_id}' not found in local library.")
        recipe.vote = 1 if vote > 0 else (-1 if vote < 0 else 0)
        return self.save_recipe(recipe)

    def exclude_recipe(self, recipe_id: str, excluded: bool = True) -> OfflineRecipe:
        """
        Marks or unmarks a recipe as excluded (e.g. public recipes you do not want recommended).
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise KeyError(f"Recipe '{recipe_id}' not found in local library.")
        recipe.is_excluded = excluded
        return self.save_recipe(recipe)

    def set_substitution(self, recipe_id: str, substitute_id: Optional[str]) -> OfflineRecipe:
        """
        Configures an alternate substitution recipe (e.g. pointer from official to created recipe).
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise KeyError(f"Recipe '{recipe_id}' not found in local library.")
        recipe.substitution_recipe_id = substitute_id
        return self.save_recipe(recipe)

    def increment_planned_count(self, recipe_id: str) -> OfflineRecipe:
        """
        Increments the counter tracking how many times the recipe has been scheduled in the planner.
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            # Create a placeholder if not yet cached
            recipe = OfflineRecipe(id=recipe_id, name=recipe_id, source="VORWERK")
        recipe.times_planned += 1
        recipe.last_planned_at = datetime.now(timezone.utc)
        return self.save_recipe(recipe)

    def record_cooked(self, recipe_id: str, cooked_at: Optional[datetime] = None) -> OfflineRecipe:
        """
        Records that a recipe was cooked on the Thermomix.
        """
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            recipe = OfflineRecipe(id=recipe_id, name=recipe_id, source="VORWERK")
        recipe.last_cooked_at = cooked_at or datetime.now(timezone.utc)
        return self.save_recipe(recipe)

    # -------------------------------------------------------------
    # Ingestion / Synchronization Helpers
    # -------------------------------------------------------------
    def upsert_from_custom_recipe(self, custom: CustomRecipe, is_active: bool = True) -> OfflineRecipe:
        """Ingests a CustomRecipe from Cookidoo into local storage."""
        model = OfflineRecipe(
            id=custom.recipeId,
            remote_id=custom.recipeId,
            name=custom.name,
            source="CUSTOMER",
            ingredients=custom.ingredients,
            instructions=custom.instructions,
            portions=int(custom.portions),
            image_url=custom.image,
            is_active_on_cookidoo=is_active,
            raw_data=custom.model_dump(mode="json")
        )
        return self.save_recipe(model, preserve_metadata=True)

    def upsert_from_recipe_detail(self, detail: RecipeDetail) -> OfflineRecipe:
        """Ingests an official Vorwerk RecipeDetail into local storage."""
        model = OfflineRecipe(
            id=detail.id,
            remote_id=detail.id,
            name=detail.name,
            source="VORWERK",
            ingredients=detail.ingredients,
            instructions=detail.instructions,
            image_url=detail.image,
            notes=detail.note,
            raw_data=detail.model_dump(mode="json")
        )
        return self.save_recipe(model, preserve_metadata=True)

    def upsert_from_history_entry(self, entry: CookingHistoryEntry) -> OfflineRecipe:
        """Ingests a CookingHistoryEntry into local storage."""
        recipe_id = entry.recipe.id
        existing = self.get_recipe(recipe_id)
        if existing:
            existing.last_cooked_at = entry.cooked_at
            return self.save_recipe(existing, preserve_metadata=True)

        model = OfflineRecipe(
            id=recipe_id,
            name=entry.title,
            source="VORWERK",
            image_url=entry.image_url,
            last_cooked_at=entry.cooked_at,
            raw_data=entry.model_dump(mode="json")
        )
        return self.save_recipe(model, preserve_metadata=True)
