# idm-mcp 接入文档

一个数据管理平台的 MCP server，提供数据集查询与运维操作，带角色权限控制。接入后可在 Kiro、Claude Code 或任意支持 MCP 的客户端里直接用自然语言操作。

---

## 前置条件

只需要装 uv，Python 会由它自动准备。

Windows：

```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

macOS / Linux：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

验证：

```powershell
uv --version
```

不需要手动安装 Python，也不需要手动装依赖包。

---

## 第 1 步：获取代码

```powershell
git clone <仓库地址>
cd idm-mcp
uv sync
```

`uv sync` 会自动下载 Python 3.11 和所需依赖，首次执行耗时取决于网络。

**这一步不能跳过。** 如果直接配置客户端，首次连接时 uv 才开始装依赖，很可能超过客户端的等待时间导致连接失败。

MCP 的 stdio 传输要求 server 与客户端在同一台机器上，客户端启动的是本地子进程，因此代码必须先拉到本地。

---

## 第 2 步：配置客户端

编辑 `.kiro/settings/mcp.json`，在 `mcpServers` 下加入：

```json
{
  "mcpServers": {
    "idm": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "<你的仓库路径>",
        "python",
        "<你的仓库路径>/server_dynamic.py"
      ],
      "env": {
        "IDM_USER_ID": "u-100",
        "IDM_ROLE": "admin"
      },
      "disabled": false
    }
  }
}
```

### 必须修改的两处

把两个 `<你的仓库路径>` 换成实际 clone 的位置，例如 `d:/work/idm-mcp`。路径可以在任何位置，但两处必须一致。

Windows 下建议用正斜杠 `/`，或把反斜杠写成 `\\`。

### 可选配置

`IDM_ROLE` 决定可用的工具集：

| 值 | 效果 |
|---|---|
| `admin` | 全部 7 个工具，含写操作 |
| `viewer` | 仅 5 个只读工具，敏感字段脱敏 |

`IDM_USER_ID` 目前仅用于日志标识。

---

## 第 3 步：验证

在 Kiro 的 MCP Server 面板重连，然后提问：

```text
帮我查一下 ds-001
```

预期回答中包含数据集名称「用户行为日志」。

如果连接失败或没有反应，看下面的排查。

---

## 能力清单

### 工具

| 工具 | 类型 | 需要角色 | 说明 |
|---|---|---|---|
| `get_dataset` | 只读 | viewer | 按 ID 查询详情，非 admin 隐藏 `contact_phone` |
| `search_dataset` | 只读 | viewer | 按关键词搜索数据集 |
| `read_file` | 只读 | viewer | 读取 `workspace/` 下的 UTF-8 文本，仅接受相对路径 |
| `calculate` | 只读 | viewer | 计算数学表达式 |
| `request_http_get` | 只读 | viewer | 发起 HTTP GET 请求 |
| `delete_dataset` | 写、不可撤销 | admin | 删除数据集 |
| `update_dataset` | 写 | admin | 修改数据集名称 |

写操作已标记 `destructiveHint=True`，支持该标记的客户端会在执行前要求确认。

### 资源

| 标识 | 说明 |
|---|---|
| `idm://dataset/schema` | 字段字典，静态内容 |
| `idm://dataset/{dataset_id}` | 单个数据集详情，带模板参数 |

带模板的资源不出现在 `list_resources` 中，需通过 `list_resource_templates` 获取。

### 提示词

| 名称 | 参数 | 说明 |
|---|---|---|
| `dataset_health_check` | `dataset_id` | 生成一段数据集体检的提问 |

---

## 权限说明

角色在 server 启动时由 `IDM_ROLE` 环境变量确定，进程生命周期内不变。

权限分两层：

**工具可见性。** viewer 看不到写操作工具，强行调用会返回 `Unknown tool`，因为工具根本没有注册。

**字段可见性。** viewer 调用 `get_dataset` 时 `contact_phone` 会被隐藏。

改角色需要修改配置并重连，因为每个连接对应一个独立的 server 进程。

---

## 排查

**第一次连接超时，第二次就好了**

首次启动时 uv 在安装依赖，超过了客户端的等待时间。先在终端执行一次 `uv sync`，装完再连。依赖就绪后 server 启动约 1 秒。

**提示找不到 mcp 包**

配置里必须带 `uv run --directory <仓库路径>`，否则会用系统 Python 而不是仓库的虚拟环境。检查路径是否写对。

**客户端报 JSON 解析错误**

说明有内容被写进了 stdout。stdio 传输下 stdout 是协议流，如果你改了代码，所有日志必须走 stderr。注意不加 `flush=True` 时不会立刻报错，属于潜伏问题。

**工具数量比预期少**

按 `IDM_ROLE` 裁剪。viewer 只有 5 个只读工具，改成 `admin` 后重连可看到 7 个。

**看不到 server 的运行日志**

接入客户端后没有终端可看。在 server 代码里把日志配到文件：

```python
logging.basicConfig(
    level=logging.INFO,
    filename="server.log",
    format="%(asctime)s %(levelname)s %(message)s",
)
```

命令行调试时另有一个坑：PowerShell 默认不显示原生子进程的 stderr，需要加 `2>&1` 才能看到。

**read_file 总说文件不存在**

它只能读 `workspace/` 目录下的文件，且必须用相对路径。仓库里应有 `workspace/sample.md` 可用于验证。

---

## 本地自测

不接客户端也能验证 server 是否正常：

```powershell
uv run python client.py        # 跨进程连接，列出全部工具、资源与提示词
uv run python verify_day4.py   # 对比 admin 与 viewer 的可见工具集
uv run python verify_day5.py   # 错误语义与敏感信息泄露的负向断言
```

三个脚本都不需要模型，不产生 API 费用。

---

## 环境

| 项 | 值 |
|---|---|
| Python | 3.11 及以上，由 uv 自动准备 |
| 依赖 | `mcp` 1.30.0 |
| SDK 实现的协议版本 | `2025-11-25` |
| 传输 | stdio |
