"""
Model for Cookidoo Recipe Notes (personal notes attached to recipes).
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class RecipeNote(BaseModel):
    """Personal note attached to a recipe."""
    noteId: str = Field(description="Unique note ID")
    userId: Optional[str] = Field(default=None, description="User ID who created the note")
    recipeId: str = Field(description="Recipe ID (e.g. 'r63350')")
    text: str = Field(description="Personal note text (max 1000 chars)")
    createdAt: Optional[datetime] = Field(default=None, description="Creation timestamp")
    modifiedAt: Optional[datetime] = Field(default=None, description="Last modified timestamp")
