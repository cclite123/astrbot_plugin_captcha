---
kind: configuration_system
name: AstrBot 插件配置系统：双源合并加 JSON Schema 驱动
category: configuration_system
scope:
    - '**'
source_files:
    - main.py
    - config.json
    - _conf_schema.json
    - metadata.yaml
    - requirements.txt
---

## 1. 使用的系统与框架
- 基于 AstrBot 插件框架，通过 @register 注册插件，由 AstrBot 在加载时注入 AstrBotConfig。
- 配置来源采用双源合并策略：优先使用 AstrBot WebUI 管理的运行时配置（config: AstrBotConfig），未传入则回退到插件目录下的本地 config.json 文件。
- 使用 _conf_schema.json 作为 JSON Schema 描述文件，供 AstrBot WebUI 渲染配置表单、提供字段说明与默认值。
- 视觉模型客户端使用 OpenAI Python SDK（openai.AsyncOpenAI），通过 vision_api_key / vision_base_url 指向任意 OpenAI 兼容接口（如豆包 Ark）。

## 2. 关键文件与位置
- main.py — 插件主类 CaptchaPlugin，包含 _DEFAULT_CONFIG 默认值与 _load_config() 合并逻辑。
- config.json — 本地配置文件，存放实际运行参数（API Key、模型 ID、调试开关等）。
- _conf_schema.json — 配置项的元数据定义，被 AstrBot WebUI 读取以生成管理界面。
- metadata.yaml — 插件元信息（名称、版本、依赖平台），不属于运行时配置但影响部署。
- requirements.txt — 声明 openai>=1.0.0 依赖。

## 3. 架构与设计约定
- 默认值集中维护：_DEFAULT_CONFIG 字典是单一事实源，_conf_schema.json 中的 default 必须与其保持一致，避免两套默认值不同步。
- 加载顺序：_load_config 先拷贝默认值 -> 尝试用 AstrBot 注入的 config 覆盖 -> 失败则从 config.json 覆盖 -> 返回最终 dict。任一阶段异常仅记录日志，不中断启动。
- 字段命名规范：所有配置键均为小写下划线风格（vision_api_key、stop_after_handle 等），类型限定为 string/bool，无嵌套结构。
- 敏感字段标记：vision_api_key 在 schema 中设置 "obvious_hint": true，提示 WebUI 将其渲染为密码输入框。
- 运行时行为开关：debug_print 控制 _dbg() 是否输出详细识别过程；stop_after_handle 控制处理完成后是否调用 event.stop_event() 阻止事件继续传播。
- 无环境变量支持：当前实现未读取任何 .env 或进程环境变量，所有配置均通过文件或 WebUI 注入。

## 4. 开发者应遵循的规则
- 新增配置项时必须同时更新三处：_DEFAULT_CONFIG、_conf_schema.json、以及 __init__ 中初始化逻辑对字段的读取位置。
- 不要直接修改 config.json 中的默认值；如需变更默认行为，请修改 _DEFAULT_CONFIG 和 _conf_schema.json 的 default 字段。
- 所有对外部服务的凭据（API Key、Base URL、Model ID）都应放在配置中，禁止硬编码到源码。
- 若需要引入新的配置来源（如环境变量），应在 _load_config 中增加中间层，保持"默认 -> 注入 -> 文件"的合并顺序不变。
- 配置校验不在本插件内完成，依赖 AstrBot 根据 _conf_schema.json 的类型与必填规则进行前置校验。