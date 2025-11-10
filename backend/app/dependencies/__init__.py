"""
Dependencies Package
Authentication and authorization dependencies
"""
from app.dependencies.auth import (
    get_current_user,
    get_optional_user,
    get_current_active_admin,
    get_current_active_hr_manager,
    require_role,
    verify_organization_access,
    oauth2_scheme
)

__all__ = [
    "get_current_user",
    "get_optional_user",
    "get_current_active_admin",
    "get_current_active_hr_manager",
    "require_role",
    "verify_organization_access",
    "oauth2_scheme"
]
