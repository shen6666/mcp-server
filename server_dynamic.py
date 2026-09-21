from mcp.server import FastMCP
from mcp.types import ToolAnnotations

from auth import allowed_tools, can_use, current_identity
from errors import not_found,forbidden,invalid_arg,internal_error

import sys
USER_ID, ROLE = current_identity()

mcp = FastMCP(name="idm-mcp")
FAKE_DB = {
    "ds-001": {
        "name": "用户行为日志",
        "owner": "u-100",
        "rows": 128_000,
        "contact_phone": "13800000000",
    }
}
from pathlib import Path
WORKSPACE_DIR = (Path(__file__).resolve().parent / "workspace").resolve()

def get_dataset(dataset_id: str) -> str:
    """按数据集 ID 查询详情。"""
    dataset = FAKE_DB.get(dataset_id)
    if dataset is None:
        return not_found("数据集",dataset_id,list(FAKE_DB))

    if ROLE == "admin":
        return str(dataset)

    masked = {
        key: value
        for key, value in dataset.items()
        if key != "contact_phone"
    }
    return str(masked)

def read_file(file_path: str) -> str:
    """读取工作区中的 UTF-8 文本文件，file_path 必须是相对路径。"""
    try:
        full_path = (WORKSPACE_DIR / file_path).resolve()

        # 安全检查：用解析后的父子关系判断，避免公共前缀误判
        if not full_path.is_relative_to(WORKSPACE_DIR):
            return "错误：不允许访问工作区之外的路径"

        # 检查文件是否存在
        if not full_path.exists():
            return f"错误：文件不存在 - {file_path}"

        if not full_path.is_file():
            return f"错误：不是一个文件 - {file_path}"

        # 检查文件大小（防止读取超大文件）
        file_size = full_path.stat().st_size
        if file_size > 1024 * 1024:  # 1MB 限制
            return f"错误：文件过大（{file_size} 字节），最大支持 1MB"

        content = full_path.read_text(encoding="utf-8")

        return content if content else "（文件为空）"
    
    except UnicodeDecodeError:
        return "错误：无法以文本模式读取该文件（可能是二进制文件）"
    except PermissionError:
        return "错误：没有读取权限"
    except Exception as e:
        return f"错误：{e}"

def calculate(expression: str) -> str:
    """安全地计算数学表达式"""
    try:
        # 只允许数字和基本运算符，防止代码注入
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return f"错误：表达式包含非法字符"
        
        result = eval(expression)
        return str(result)
    except ZeroDivisionError:
        return "错误：除数不能为零"
    except Exception as e:
        return f"错误：{e}"

def request_http_get(url: str) -> str:
    """发送http的get请求工具"""
    import requests
    try:
        resp = requests.get(url, timeout=10)
        return resp.text
    except requests.exceptions.ConnectionError:
        return f"连接失败：无法访问 {url}"
    except requests.exceptions.Timeout:
        return f"请求超时：{url}"
    except Exception as e:
        return f"请求出错：{str(e)}"

def search_dataset(keyword: str) -> str:
    """按关键词搜索数据集，返回匹配的数据集 ID 列表。"""
    hits = [
        ds_id
        for ds_id, ds in FAKE_DB.items()
        if keyword in ds["name"]
    ]
    return str(hits) if hits else "没有匹配的数据集"

def delete_dataset(dataset_id: str) -> str:
    """删除数据集，需要 admin 角色。"""
    if not can_use(ROLE, "delete_dataset"):
        return forbidden("删除数据集")
    if dataset_id not in FAKE_DB:
        return not_found("数据集", dataset_id, list(FAKE_DB), destructive=True)
    FAKE_DB.pop(dataset_id, None)
    return f"已删除 {dataset_id}"

def update_dataset(dataset_id: str,new_name:str) -> str:
    """修改数据集名称，需要admin角色"""
    if not can_use(ROLE, "delete_dataset"):
        return (
            "错误：当前角色无权修改数据集。"
            "请不要重试，改为向用户说明需要管理员权限。"
        )
    dataset = FAKE_DB.get(dataset_id)
    if dataset is None:
        return f"错误：数据集不存在 - {dataset_id}"

    dataset["name"] = new_name
    return f"已成功更新数据集：{dataset_id} 的名称为：{new_name}"

import json
@mcp.resource("idm://dataset/schema",mime_type="application/json")
def dataset_schema():
    """数据集的字段字典。"""
    return json.dumps(
        {
            "dataset_id": "数据集唯一标识，形如 ds-001",
            "name": "数据集名称",
            "owner": "责任人工号",
            "rows": "数据行数"
        },
        ensure_ascii=False,
        indent=2
    )

@mcp.resource("idm://dataset/{dataset_id}",mime_type="application/json")
def dataset_detail(dataset_id:str):
    """按数据集 ID 读取数据集。"""
    print(f"收到查询：{dataset_id}",file=sys.stderr)
    dataset = FAKE_DB.get(dataset_id)
    if dataset is None:
        return '{"error": "数据集不存在"}'
    return str(dataset)

@mcp.prompt()
def dataset_health_check(dataset_id: str) -> str:
    """生成一段数据集体检的提问。"""
    return (
        f"请检查数据集 {dataset_id}：\n"
        f"1. 先查它的详情\n"
        f"2. 对照字段字典说明每个字段的含义\n"
        f"3. 指出行数是否异常"
    )

# 按角色注册
ALL_TOOLS = {
    "get_dataset": (get_dataset, ToolAnnotations(readOnlyHint=True)),
    "search_dataset": (search_dataset, ToolAnnotations(readOnlyHint=True)),
    "read_file": (read_file, ToolAnnotations(readOnlyHint=True)),
    "calculate": (calculate, ToolAnnotations(readOnlyHint=True)),
    "request_http_get": (request_http_get, ToolAnnotations(readOnlyHint=True)),
    "delete_dataset": (delete_dataset,ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False)),
    "update_dataset": (update_dataset,ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False)),
}

for name, (fn, annotations) in ALL_TOOLS.items():
    if name in allowed_tools(ROLE):
        mcp.add_tool(fn, annotations=annotations)

print(f"身份 {USER_ID}/{ROLE}，注册 {len(allowed_tools(ROLE))} 个工具", file=sys.stderr)

if __name__ == "__main__":
    print("idm-mcp 启动中", file=sys.stderr)   # 日志必须走 stderr
    mcp.run(transport="stdio")