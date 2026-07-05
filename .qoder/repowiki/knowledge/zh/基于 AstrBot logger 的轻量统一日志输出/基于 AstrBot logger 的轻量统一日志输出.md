---
kind: logging_system
name: 基于 AstrBot logger 的轻量统一日志输出
category: logging_system
scope:
    - '**'
source_files:
    - main.py
---

本插件未引入独立的日志框架，而是通过一个统一的 _console 包装函数，将日志同时写入 AstrBot 框架提供的 logger 以及标准输出（print），形成双写策略。所有业务模块均通过该函数输出，避免散落各处调用。

核心实现：main.py 中 _console(tag, msg, level) 函数负责格式化 [Captcha][{tag}] {msg} 前缀，并动态选择 logger.info/warning/error；若框架 logger 不可用则静默失败，最终一律 print(line, flush=True) 保证控制台可见。

日志级别：仅使用 info、warning、error 三级，由调用方显式传入；默认 info。
结构化字段：采用标签 + 消息的简单结构，tag 区分来源模块（如 BOOT、CONFIG、CAPTCHA、VISION、CLICK、MATCH、PLATFORM、CLIENT、FATAL、EXIT），不输出 JSON 或额外键值对。
调试开关：提供 _dbg(tag, msg) 方法，受配置项 debug_print 控制，仅在开启时调用 _console，用于高频中间状态输出。
异常堆栈：关键异常路径在 level="error" 的同时附加 traceback.format_exc()，便于定位问题。
无持久化/轮转：日志仅输出到 stdout 与 AstrBot 宿主进程日志，无文件落盘、分级文件或滚动策略。

开发者约定：
1. 统一通过 _console(tag, msg, level) 输出，禁止直接 print 或调用第三方 logger。
2. 为每个功能域定义稳定 tag（BOOT/CONFIG/CAPTCHA/VISION/CLICK/MATCH/PLATFORM/CLIENT/FATAL/EXIT）。
3. 需要可开关的详细跟踪时使用 _dbg，而非 _console。
4. 错误场景使用 level="error"，警告使用 level="warning"，其余默认 info。
5. 不在日志中记录敏感信息（如 API Key、用户隐私数据）。