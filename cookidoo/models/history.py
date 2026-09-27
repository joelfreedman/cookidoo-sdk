"""Cooking history and recently cooked models."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class CookingRecipeInfo(BaseModel):
    id: str = Field(description="Recipe unique ID")
    asciiTitle: Optional[str] = Field(default=None, description="Recipe title")
    language: Optional[str] = Field(default=None, description="Recipe language/locale")
    assets: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Image and media assets")

class CookingHistoryDetails(BaseModel):
    timestamp: datetime = Field(description="ISO timestamp when the recipe was cooked")

class CookingHistoryEntry(BaseModel):
    details: CookingHistoryDetails
    recipe: CookingRecipeInfo

    @property
    def title(self) -> str:
        return self.recipe.asciiTitle or f"Recipe {self.recipe.id}"

    @property
    def cooked_at(self) -> datetime:
        return self.details.timestamp

class CookingHistoryResponse(BaseModel):
    userId: str
    entries: List[CookingHistoryEntry] = Field(default_factory=list)
