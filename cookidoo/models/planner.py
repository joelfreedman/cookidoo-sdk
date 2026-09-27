"""Meal planning and My Week data models."""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PlannedDaysSummary(BaseModel):
    dayKeys: List[str] = Field(default_factory=list, description="List of date strings 'YYYY-MM-DD' that contain planned recipes")

class PlannedDay(BaseModel):
    id: str = Field(description="Day identifier (usually YYYY-MM-DD)")
    dayKey: str = Field(description="Date string 'YYYY-MM-DD'")
    author: Optional[str] = Field(default=None, description="Author user ID")
    date: Optional[datetime] = Field(default=None, description="Planned date")
    created: Optional[datetime] = Field(default=None, description="Creation timestamp")
    modified: Optional[datetime] = Field(default=None, description="Last modification timestamp")
    recipeCount: int = Field(default=0, description="Total number of recipes planned")
    recipeIds: List[str] = Field(default_factory=list, description="IDs of official Cookidoo recipes")
    customerRecipeIds: List[str] = Field(default_factory=list, description="IDs of created / custom recipes")
    market: Optional[str] = Field(default="us", description="Market / region")
