"""
Models for Cookidoo custom lists (collections / bookmarks).
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CustomListRecipeItem(BaseModel):
    """A recipe item inside a custom list."""
    id: str
    title: str
    asciiTitle: Optional[str] = None
    type: str = "VORWERK"
    prepTime: Optional[str] = None
    totalTime: Optional[str] = None
    squareImage: Optional[str] = None
    landscapeImage: Optional[str] = None


class CustomListChapter(BaseModel):
    """Chapter inside a custom list."""
    title: str = ""
    recipeIds: List[str] = Field(default_factory=list)
    recipes: List[CustomListRecipeItem] = Field(default_factory=list)


class CustomList(BaseModel):
    """User-created recipe list / collection."""
    id: str
    title: str
    asciiTitle: Optional[str] = None
    author: Optional[str] = None
    recipeCount: int = 0
    recipeIds: List[str] = Field(default_factory=list)
    created: Optional[str] = None
    modified: Optional[str] = None
    listThumbnail: Optional[str] = None
    listType: Optional[str] = "CUSTOMLIST"
    shared: bool = False
    chapters: Optional[List[CustomListChapter]] = None
    assets: Optional[Dict[str, Any]] = None

    @property
    def recipes(self) -> List[CustomListRecipeItem]:
        """Flattened list of recipe items across chapters."""
        if not self.chapters:
            return []
        all_recipes = []
        for chapter in self.chapters:
            all_recipes.extend(chapter.recipes)
        return all_recipes
