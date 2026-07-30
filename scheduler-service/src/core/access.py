from dataclasses import dataclass, field


@dataclass
class ResolvedAccess:
    """Resolved effective permissions + role metadata for a user.

    permissions format: {app_id: {method: [path_patterns]}}
    path_patterns are fnmatch globs: "/*", "/users/*", "/users/*/block"
    """

    permissions: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    role_name: str | None = None
    is_admin: bool = False
