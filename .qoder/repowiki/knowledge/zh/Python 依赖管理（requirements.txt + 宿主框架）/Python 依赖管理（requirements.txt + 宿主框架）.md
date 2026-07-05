---
kind: dependency_management
name: Python 依赖管理（requirements.txt + 宿主框架）
category: dependency_management
scope:
    - '**'
source_files:
    - requirements.txt
    - main.py
---

本仓库是一个 Python 插件，依赖管理采用最简化的 requirements.txt 声明式方式，由宿主框架 AstrBot 负责加载与运行。

1. 使用的系统/方法
- 使用 Python 标准依赖清单文件 requirements.txt 声明第三方包。
- 未使用 pipenv、poetry、conda 等更复杂的工具，也未进行 vendoring。
- 运行时依赖通过 import 在 main.py 中引入，无额外构建或打包脚本。

2. 关键文件
- requirements.txt：唯一的外部依赖声明入口，仅声明 openai>=1.0.0。
- main.py：插件主模块，通过 from openai import AsyncOpenAI 和 from astrbot.api.* 引入运行时依赖。
- metadata.yaml / _conf_schema.json / config.json：插件元数据与配置，不直接参与依赖管理，但定义了运行时所需的 API Key、base_url 等外部服务凭据。

3. 架构与约定
- 依赖粒度极小：除 openai SDK 外，其余均为 AstrBot 框架提供的内部模块（astrbot.api.*），这些依赖由宿主环境提供，不在本仓库中声明。
- 版本约束宽松：openai 使用 >=1.0.0 的最低版本下限，未锁定具体版本，也不存在 lockfile（如 requirements.lock、pipfile.lock）。
- 无私有源/镜像配置：requirements.txt 未指定 index-url 或 --extra-index-url，默认使用 PyPI。
- 无 vendor 目录或 git submodule，所有第三方包均按常规 pip 安装流程获取。

4. 开发者应遵循的规则
- 新增第三方依赖时，请在 requirements.txt 中添加对应条目，并尽量给出合理的版本范围（建议至少包含最小兼容版本）。
- 避免引入大型运行时依赖；优先复用 AstrBot 已提供的能力。
- 若需要固定可复现构建，建议后续引入 pip-tools/pip-compile 生成锁定文件，或在 CI 中记录实际安装的版本快照。
- 敏感信息（如 vision_api_key、vision_base_url）通过 config.json 或 AstrBot WebUI 注入，不要硬编码进代码或 requirements.txt。