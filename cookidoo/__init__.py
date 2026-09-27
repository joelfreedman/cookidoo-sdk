"""
Cookidoo Python SDK.
"""

from .client import CookidooClient
from .auth import CookidooAuth
from .storage import CookidooStorage
from .sync import CookidooSyncManager
from .exceptions import (
    CookidooError,
    CookidooAuthError,
    CookidooNotFoundError,
    CookidooRateLimitError,
    CookidooValidationError,
)
from .models import (
    UserProfile,
    CookingHistoryEntry,
    PlannedDay,
    PlannedDaysSummary,
    CustomRecipe,
    CustomRecipeContent,
    RecipeYield,
    RecipeSummary,
    RecipeSearchResult,
    CustomList,
    RecipeNote,
    OfflineRecipe,
)

__version__ = "0.1.0"
__all__ = [
    "CookidooClient",
    "CookidooAuth",
    "CookidooStorage",
    "CookidooSyncManager",
    "CookidooError",
    "CookidooAuthError",
    "CookidooNotFoundError",
    "CookidooRateLimitError",
    "CookidooValidationError",
    "UserProfile",
    "CookingHistoryEntry",
    "PlannedDay",
    "PlannedDaysSummary",
    "CustomRecipe",
    "CustomRecipeContent",
    "RecipeYield",
    "RecipeSummary",
    "RecipeSearchResult",
    "CustomList",
    "RecipeNote",
    "OfflineRecipe",
]

