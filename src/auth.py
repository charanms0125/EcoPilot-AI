"""
EcoPilot AI: Role-Based Access Control (RBAC) & Authorization Engine
Enforces strict principle of least privilege across four distinct user roles:
1. Viewer: Read-only observation of telemetry, baselines, and reports.
2. Analyst: Telemetry ingestion, tariff simulation, and alert triage.
3. Approver: Energy conservation task authorization and sign-off.
4. Administrator: System maintenance, migration execution, and protected database reset.
"""

from typing import Set, Dict, Any, Optional, Callable
from enum import Enum
from functools import wraps
import os


class Role(str, Enum):
    """System user roles with hierarchical capability boundaries."""

    VIEWER = "viewer"
    ANALYST = "analyst"
    APPROVER = "approver"
    ADMINISTRATOR = "administrator"

    @classmethod
    def from_str(cls, val: Optional[str]) -> "Role":
        """Parse string to Role enum with safe fallback to VIEWER."""
        if not val:
            return cls.VIEWER
        cleaned = str(val).strip().lower()
        for r in cls:
            if r.value == cleaned:
                return r
        return cls.VIEWER


class Permission(str, Enum):
    """Granular action permissions."""

    VIEW_DASHBOARD = "view_dashboard"
    VIEW_TELEMETRY = "view_dashboard"
    UPLOAD_DATA = "upload_data"
    RUN_SIMULATION = "run_simulation"
    EXECUTE_SIMULATION = "run_simulation"
    UPDATE_ALERT_STATUS = "update_alert_status"
    APPROVE_RECOMMENDATION = "approve_recommendation"
    EXECUTE_RECOMMENDATION = "approve_recommendation"
    REJECT_RECOMMENDATION = "reject_recommendation"
    COMPLETE_ACTION = "complete_action"
    SAVE_VERIFICATION = "save_verification"
    RESET_DATABASE = "reset_database"
    SYSTEM_RESET = "reset_database"
    SYSTEM_ADMIN = "system_admin"


# Role to Granted Permissions Mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        Permission.VIEW_DASHBOARD,
    },
    Role.ANALYST: {
        Permission.VIEW_DASHBOARD,
        Permission.UPLOAD_DATA,
        Permission.RUN_SIMULATION,
        Permission.UPDATE_ALERT_STATUS,
    },
    Role.APPROVER: {
        Permission.VIEW_DASHBOARD,
        Permission.UPLOAD_DATA,
        Permission.RUN_SIMULATION,
        Permission.UPDATE_ALERT_STATUS,
        Permission.APPROVE_RECOMMENDATION,
        Permission.REJECT_RECOMMENDATION,
        Permission.COMPLETE_ACTION,
        Permission.SAVE_VERIFICATION,
    },
    Role.ADMINISTRATOR: {
        Permission.VIEW_DASHBOARD,
        Permission.UPLOAD_DATA,
        Permission.RUN_SIMULATION,
        Permission.UPDATE_ALERT_STATUS,
        Permission.APPROVE_RECOMMENDATION,
        Permission.REJECT_RECOMMENDATION,
        Permission.COMPLETE_ACTION,
        Permission.SAVE_VERIFICATION,
        Permission.RESET_DATABASE,
        Permission.SYSTEM_ADMIN,
    },
}

# Role Hierarchical Weight (Administrator > Approver > Analyst > Viewer)
ROLE_HIERARCHY: Dict[Role, int] = {
    Role.VIEWER: 1,
    Role.ANALYST: 2,
    Role.APPROVER: 3,
    Role.ADMINISTRATOR: 4,
}


def get_role_permissions(role: Role | str) -> Set[Permission]:
    """Return the set of permissions granted to a given role."""
    r = role if isinstance(role, Role) else Role.from_str(role)
    return set(ROLE_PERMISSIONS.get(r, set()))


_CURRENT_ROLE: Optional[Role] = None


def get_current_role() -> Role:
    """
    Retrieve the current active execution role.
    Checks thread/process state, then ECOPILOT_ROLE environment variable, defaulting to ADMINISTRATOR in dev.
    """
    global _CURRENT_ROLE
    if _CURRENT_ROLE is not None:
        return _CURRENT_ROLE
    env_role = os.getenv("ECOPILOT_ROLE", "administrator")
    return Role.from_str(env_role)


def set_current_role(role: Role | str) -> None:
    """Explicitly set the active execution role (for session management or testing)."""
    global _CURRENT_ROLE
    _CURRENT_ROLE = role if isinstance(role, Role) else Role.from_str(role)


def check_permission(permission: Permission | str, role: Optional[Role | str] = None) -> bool:
    """
    Check if a specific role possesses the requested permission.
    If role is not specified, checks the current active role.
    """
    active_role = role if isinstance(role, Role) else (Role.from_str(role) if role else get_current_role())
    perm = permission if isinstance(permission, Permission) else Permission(str(permission))

    allowed_perms = ROLE_PERMISSIONS.get(active_role, set())
    return perm in allowed_perms


def has_minimum_role(required_role: Role | str, current_role: Optional[Role | str] = None) -> bool:
    """Verify if current role meets or exceeds required hierarchical tier."""
    active_r = current_role if isinstance(current_role, Role) else (Role.from_str(current_role) if current_role else get_current_role())
    req_r = required_role if isinstance(required_role, Role) else Role.from_str(required_role)

    return ROLE_HIERARCHY.get(active_r, 0) >= ROLE_HIERARCHY.get(req_r, 0)


def require_permission(permission: Permission | str, role: Optional[Role | str] = None) -> Callable:
    """
    Decorator enforcing authorization for sensitive business logic functions.
    Raises PermissionError if the caller does not hold the necessary grant.
    """
    perm = permission if isinstance(permission, Permission) else Permission(str(permission))

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            caller_role = role if role is not None else kwargs.get("caller_role") or get_current_role()
            if not check_permission(perm, caller_role):
                raise PermissionError(
                    f"Access Denied: Action requires '{perm.value}' permission. "
                    f"Current active role '{caller_role.value if isinstance(caller_role, Role) else caller_role}' is unauthorized."
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator
