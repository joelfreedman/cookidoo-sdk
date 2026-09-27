"""
Models for offline recipe storage, tagging, voting, and substitution tracking.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OfflineRecipe(BaseModel):
    """
    Offline representation of a recipe (either official Vorwerk or user created)
    with local metadata: custom tags, upvote/downvote, planner counts, exclusions,
    and substitution pointers.
    """
    id: str = Field(description="Unique recipe ID (e.g. 'r63350' for official, or created recipe ID)")
    remote_id: Optional[str] = Field(default=None, description="Cookidoo remote ID if currently active on Cookidoo")
    name: str = Field(description="Recipe title")
    source: str = Field(default="CUSTOMER", description="'CUSTOMER' for user created, 'VORWERK' for official")
    
    # Content details
    ingredients: List[str] = Field(default_factory=list, description="Ingredients list")
    instructions: List[str] = Field(default_factory=list, description="Instructions / steps list")
    portions: Optional[int] = Field(default=4, description="Portions / servings")
    prep_time: Optional[int] = Field(default=None, description="Preparation time in seconds")
    total_time: Optional[int] = Field(default=None, description="Total time in seconds")
    image_url: Optional[str] = Field(default=None, description="Image URL or asset reference")
    notes: Optional[str] = Field(default=None, description="Personal user notes")
    raw_data: Dict[str, Any] = Field(default_factory=dict, description="Raw recipe payload")

    # Local enhancements
    tags: List[str] = Field(default_factory=list, description="Custom tags (e.g. 'quick', 'kid-friendly')")
    vote: int = Field(default=0, description="+1 for upvote, -1 for downvote, 0 for neutral")
    times_planned: int = Field(default=0, description="Count of times added to meal planner by SDK")
    is_excluded: bool = Field(default=False, description="Whether to exclude from recommendations / planning")
    substitution_recipe_id: Optional[str] = Field(default=None, description="ID of substitute recipe (e.g. GF version)")

    # Sync and lifecycle
    is_active_on_cookidoo: bool = Field(default=False, description="Whether currently present in Cookidoo account")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_cooked_at: Optional[datetime] = None
    last_planned_at: Optional[datetime] = None
