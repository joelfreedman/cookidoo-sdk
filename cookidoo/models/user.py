"""User profile data model."""

from typing import Optional
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    dcid: str = Field(description="Unique Vorwerk customer identity ID")
    country_of_residence: str = Field(description="Country code of user, e.g. US")
    firstname: Optional[str] = Field(default=None, description="First name")
    lastname: Optional[str] = Field(default=None, description="Last name")
