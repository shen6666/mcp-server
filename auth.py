"""按角色决定可见工具集。"""
import os
READ_ONLY = {"get_dataset", "search_dataset", "read_file","calculate","request_http_get"}
WRITE_TOOLS = {"update_dataset", "delete_dataset"}

ROLE_TOOLS = {
    "viewer": READ_ONLY,
    "admin": READ_ONLY | WRITE_TOOLS,
}

def current_identity() -> tuple[str, str]:
    """从环境变量读取本次连接的身份。"""
    return (
        os.environ.get("IDM_USER_ID", "anonymous"),
        os.environ.get("IDM_ROLE", "viewer")
    )

def allowed_tools(role: str) -> set[str]:
    """该角色可见的工具名集合。"""
    return ROLE_TOOLS.get(role, READ_ONLY)

def can_use(role: str, tool_name: str) -> bool:
    return tool_name in allowed_tools(role)