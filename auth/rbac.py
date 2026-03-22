# auth/rbac.py
# RBAC = Role Based Access Control
# Different users have different permissions.
# Example: A field_agent can record distributions but cannot delete records.

from fastapi import Depends, HTTPException, status
from auth.jwt import get_current_user

# Map each role to a list of what it can do
ROLE_PERMISSIONS = {
    "super_admin":       ["read", "write", "delete", "manage_users", "view_analytics"],
    "district_officer":  ["read", "write", "view_analytics"],
    "field_agent":       ["read", "write_distribution"],
    "auditor":           ["read", "view_analytics"],
}


def require_permission(permission: str):
    """
    A function that returns a FastAPI dependency.
    Usage: Depends(require_permission("write"))
    If the user doesn't have the required permission → returns 403 Forbidden.
    """
    def dependency(current_user=Depends(get_current_user)):
        role = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
        allowed = ROLE_PERMISSIONS.get(role, [])
        if permission not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Your role '{role}' cannot perform '{permission}'"
            )
        return current_user
    return dependency
