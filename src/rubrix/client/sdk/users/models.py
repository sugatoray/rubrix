from typing import List, Optional

from pydantic import BaseModel


class User(BaseModel):
    """User data model"""

    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    user_groups: List[str] = None

    @property
    def current_group(self) -> Optional[str]:
        return self.user_groups[0] if self.user_groups else None
