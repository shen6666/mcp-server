"""语义化错误：所有错误文案集中定义，确保风格一致。"""

def not_found(kind: str, ident: str, available: list[str] | None = None, *,destructive: bool = False) -> str:
    """可纠正错误：目标不存在。

    注意不引导模型自行替换目标——目标不存在属于用户意图问题，
    正确答案不唯一，自动替换在写操作上会造成误操作。
    """
    msg = f"错误：{kind} {ident} 不存在。"
    if available:
        msg += f"当前可用的有：{available}。"
        if destructive:
            msg += "禁止自行改用其他目标，必须先向用户确认。"
        else:
            msg += "请向用户确认需要哪一个，不要自行替换。"
    return msg

def forbidden(action: str, required_role: str = "admin") -> str:
    """终态错误：权限不足，明确关闭重试。"""
    return (
        f"错误：当前角色无权{action}。"
        f"这是权限限制，重试不会成功。"
        f"请向用户说明需要 {required_role} 权限。"
    )

def invalid_arg(name: str, reason: str, example: str = "") -> str:
    """可纠正错误：参数不合法。"""
    msg = f"错误：参数 {name} 不合法，{reason}。"
    if example:
        msg += f"正确示例：{example}。"
    return msg

import logging

logger = logging.getLogger(__name__)

def internal_error(operation: str, exc: Exception) -> RuntimeError:
    """系统异常：完整信息进日志，返回值只给安全文案。

    用法：raise errors.internal_error("查询数据集", exc) from None
    """
    logger.exception("%s 失败", operation)
    return RuntimeError(f"{operation}时内部服务异常，请稍后重试或联系管理员")
