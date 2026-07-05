---
kind: error_handling
name: 基于统一日志与 try/except 的轻量错误处理
category: error_handling
scope:
    - '**'
source_files:
    - main.py
---

本仓库为单文件 AstrBot 插件（`main.py`），未定义任何自定义异常类型、错误码或错误包装器，也未使用 `panic/recover` 等机制。整体采用“try/except + 统一日志”的轻量策略：

- **统一日志入口**：模块级 `_console(tag, msg, level)` 函数同时写入 AstrBot 内置 `logger` 和标准输出，所有异常路径均通过该函数以 `level="error"` / `"warning"` 级别记录，并附带 `traceback.format_exc()` 堆栈。
- **分层 try/except 包裹**：每个对外暴露的异步入口（`on_group_msg`）、核心流程（`_handle_captcha`）以及外部调用点（视觉模型 `_call_vision_model`、OneBot 点击 `_click_button`、客户端获取 `_get_onebot_client`）都单独用 `try/except Exception as e` 捕获，失败时记录日志后返回 `None` 或静默跳过，不向上抛出。
- **无自定义异常类型**：代码中从未 `raise` 任何自定义错误类，也没有 sentinel error 或错误码枚举；上层调用方通过返回值 `None` 或后续分支判断来感知失败（例如 `_call_vision_model` 返回 `None` 时上层直接 `return`）。
- **兜底与降级**：匹配不到按钮时 `_match_button` 回退到第一个选项；无法获取 OneBot client 时打印 warning 并跳过点击；平台不支持时同样降级。
- **生命周期清理**：`terminate` 钩子仅做日志输出，不做异常保护。

由于项目规模极小且完全依赖宿主框架的事件循环，开发者无需遵循额外的错误传播约定，只需在新增 I/O 或解析逻辑处沿用“try/except + `_console(..., level='error')` + 返回 None/跳过”的模式即可。