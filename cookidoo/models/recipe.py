"""General recipe and search data models."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RecipeSummary(BaseModel):
    id: str = Field(description="Recipe ID, e.g. r63350")
    title: str = Field(description="Recipe title")
    rating: Optional[float] = Field(default=None, description="Average rating")
    numberOfRatings: Optional[int] = Field(default=None, description="Total ratings count")
    totalTime: Optional[int] = Field(default=None, description="Total time in seconds")
    preparationTime: Optional[int] = Field(default=None, description="Prep time in seconds")
    category: Optional[str] = Field(default=None, description="Recipe category")
    image: Optional[str] = Field(default=None, description="Thumbnail / image URL")
    url: Optional[str] = Field(default=None, description="Web path or URL")

class RecipeSearchResult(BaseModel):
    query: str
    totalHits: int
    page: int
    hitsPerPage: int
    recipes: List[RecipeSummary] = Field(default_factory=list)

class RecipeDetail(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    prepTime: Optional[str] = None
    totalTime: Optional[str] = None
    recipeYield: Optional[str] = None
    ingredients: List[str] = Field(default_factory=list)
    instructions: List[str] = Field(default_factory=list)
    image: Optional[str] = None
    note: Optional[str] = None

