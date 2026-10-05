"""Created and Custom Recipes data models."""

from typing import List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

class RecipeYield(BaseModel):
    value: Union[int, float] = Field(default=4, description="Number of portions/servings")
    unitText: str = Field(default="portion", description="Unit text (e.g. portion, pieces)")

class CustomRecipeContent(BaseModel):
    name: str = Field(description="Recipe title")
    image: Optional[str] = Field(default=None, description="Image URL if set")
    recipeIngredient: List[str] = Field(default_factory=list, description="List of ingredients")
    recipeInstructions: List[str] = Field(default_factory=list, description="List of instructions with Thermomix TTS annotations")
    tool: List[str] = Field(default_factory=lambda: ["TM6"], description="Thermomix appliances (e.g. TM6, TM5, TM7)")
    recipeYield: RecipeYield = Field(default_factory=RecipeYield, description="Recipe yield/portions")

class CustomRecipe(BaseModel):
    recipeId: str = Field(description="Unique custom recipe ID")
    authorId: Optional[str] = Field(default=None, description="Owner author ID")
    createdAt: Optional[datetime] = Field(default=None, description="Creation timestamp")
    modifiedAt: Optional[datetime] = Field(default=None, description="Last modified timestamp")
    status: Optional[str] = Field(default="ACTIVE", description="Recipe status")
    workStatus: Optional[str] = Field(default="PRIVATE", description="Visibility status")
    recipeContent: CustomRecipeContent = Field(description="Content of the custom recipe")

    @property
    def name(self) -> str:
        return self.recipeContent.name

    @property
    def ingredients(self) -> List[str]:
        return self.recipeContent.recipeIngredient

    @property
    def instructions(self) -> List[str]:
        return self.recipeContent.recipeInstructions

    @property
    def image(self) -> Optional[str]:
        return self.recipeContent.image

    @property
    def portions(self) -> Union[int, float]:
        return self.recipeContent.recipeYield.value

    @property
    def tools(self) -> List[str]:
        return self.recipeContent.tool


class CustomRecipeListResponse(BaseModel):
    items: List[CustomRecipe] = Field(default_factory=list)
