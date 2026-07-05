---
kind: build_system
name: 构建与发布系统（AstrBot 插件）
category: build_system
scope:
    - '**'
source_files:
    - main.py
    - metadata.yaml
    - requirements.txt
    - _conf_schema.json
---

本项目是一个 AstrBot 插件，采用“单文件 + 清单”的极简发布模型，不存在传统意义上的编译、打包或 CI 流水线。其“构建系统”实质由以下三部分构成：

1. **依赖声明** — `requirements.txt` 仅声明一个运行时依赖 `openai>=1.0.0`，安装方式为 `pip install -r requirements.txt`。
2. **插件元数据** — `metadata.yaml` 描述插件名称、版本（`1.0.0`）、作者、支持的 AstrBot 版本（`>=4.0.0`）及平台（`aiocqhttp`、`qq_official`），是 AstrBot 插件市场/加载器识别插件的唯一入口。
3. **分发产物** — 仓库根目录直接提供预打包的 `astrbot_plugin_captcha.zip` 作为可安装产物；源码本身即为单个 `main.py`，无需额外编译步骤。

**约定与约束**
- 插件入口类必须继承 `Star` 并通过 `@register(...)` 装饰器注册，参数顺序为 `(name, author, description, version, repo_url)`，其中 `version` 需与 `metadata.yaml` 保持一致。
- 配置优先从 AstrBot WebUI 注入的 `config` 对象读取，回退到同目录 `config.json`；`_conf_schema.json` 用于驱动 WebUI 表单生成。
- 不支持跨平台交叉编译、Docker 镜像或多阶段构建；部署方式是将整个目录（含 `main.py`、`metadata.yaml`、`requirements.txt`、`config.json`）放入 AstrBot 的插件目录，或通过提供的 zip 包安装。
- 无 Makefile、Dockerfile、CI 配置文件、setup.py/pyproject.toml 等标准构建工件，因此本仓库未实现任何自动化构建或测试流程。