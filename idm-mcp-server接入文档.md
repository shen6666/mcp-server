### 关键能力清单

read_file  读取工作区中的 UTF-8 文本文件，file_path 必须是相对路径
calculate  安全地计算数学表达式
request_http_get  发送http的get请求工具
get_dataset  按 ID 查详情，非 admin 隐藏手机号
search_dataset	按关键词搜索数据集
delete_dataset	删除数据集，需要admin权限
update_dataset	修改数据集名称，需要admin权限

### 1. 装依赖

uv add mcp

### 2. 配置客户端

修改kiro的配置文件，文件地址：.kiro/settings/mcp.json

把以下内容

```json
{
  "mcpServers": {
    "idm": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "e:/exec/agent-lab",
        "python",
        "e:/exec/agent-lab/02-idm-mcp/server_dynamic.py"
      ],
      "env": {
        "IDM_USER_ID": "u-100",
        "IDM_ROLE": "admin"
      },
      "disabled": true
    }
  }
}
```

### 3. 验证

重连 MCP Server 后，问：「帮我查一下 ds-001」

预期回答包含数据集名称「用户行为日志」。