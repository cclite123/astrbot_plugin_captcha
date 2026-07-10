# 验证码克星 (astrbot_plugin_captcha)

> 自动识别并点击 QQ 群聊中的机器人验证码，基于视觉大模型实现干扰验证码图片的智能识别。

[![AstrBot](https://img.shields.io/badge/AstrBot-%3E%3D4.0.0-blue)](https://github.com/AstrBotDevs/AstrBot)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 功能特性

- **自动识别验证码** — 监听群聊消息，自动捕获来自官方机器人的干扰验证码图片
- **视觉大模型驱动** — 调用支持图片理解的 AI 模型（豆包、OpenAI 兼容接口等）识别图中物品
- **智能按钮匹配** — 将模型识别结果与内联键盘选项匹配，模拟物理点击完成验证
- **安全过滤机制** — 仅处理 @ 自身机器人的验证码，避免误点他人验证
- **WebUI 配置管理** — 所有配置项均可通过 AstrBot 管理面板可视化编辑，无需修改代码
- **详细调试日志** — 可开关的调试模式，完整记录识别过程和耗时

## 工作原理

```
群聊消息 → 过滤官方机器人 → 匹配验证码关键词 → 确认 @ 自身
    → 提取图片 URL + 解析按钮选项
    → 视觉模型识别图片中的目标物品
    → 匹配正确按钮 → OneBot 协议模拟点击
```

## 安装

### 方式一：通过 AstrBot 插件市场安装（推荐）

1. 打开 AstrBot WebUI 管理面板
2. 进入 **插件市场**，搜索 `astrbot_plugin_captcha`
3. 点击 **安装**，等待安装完成

### 方式二：手动安装

将插件克隆到 AstrBot 的插件目录下：

```bash
cd AstrBot/data/plugins
git clone https://github.com/cclite123/astrbot_plugin_captcha.git
```

安装 Python 依赖：

```bash
pip install -r requirements.txt
```

在 AstrBot WebUI 的插件管理处 **重载插件** 即可生效。

## 配置说明

安装后，在 AstrBot WebUI → **插件** → **验证码克星** 中配置以下参数：

| 配置项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `official_bot_id` | string | `3889001741` | 需要自动点击验证码的官方 QQ 机器人 ID |
| `vision_api_key` | string | _(空)_ | 视觉模型的 API Key，**必填** |
| `vision_base_url` | string | `https://ark.cn-beijing.volces.com/api/v3` | 视觉模型 API 地址，支持 OpenAI 兼容接口 |
| `vision_model` | string | _(空)_ | 视觉模型 ID / Endpoint ID，**必填** |
| `debug_print` | bool | `true` | 是否在控制台输出详细识别日志 |
| `stop_after_handle` | bool | `true` | 处理完毕后是否阻止事件继续传播 |

### API 密钥设置

本插件需要一个支持 **视觉理解（Vision）** 能力的大模型 API。以下以火山引擎豆包为例：

1. 前往 [火山引擎控制台](https://console.volcengine.com/ark) 创建应用
2. 获取 **API Key** 并填入 `vision_api_key`
3. 创建视觉模型的 **Endpoint**（如 `ep-xxxxx`），填入 `vision_model`
4. `vision_base_url` 保持默认即可

也支持其他 OpenAI 兼容接口，只需修改 `vision_base_url` 和 `vision_api_key` 即可适配。

## 支持平台

| 平台适配器 | 支持状态 |
|---|---|
| aiocqhttp (OneBot v11) | ✅ 支持 |

> **注意：** 按钮点击功能依赖 OneBot 协议的 `click_inline_keyboard_button` 扩展 API，请确保所使用的协议实现支持该接口。

### NapCat 必需配置

使用 NapCatQQ 时，请在 **NapCat WebUI → 网络配置** 中，编辑 AstrBot 实际连接的
WebSocket 或反向 WebSocket 配置并开启 `debug`，然后重启或重载该连接。

NapCat 仅在网络连接的 `debug` 开启时，才会在 OneBot 上报中附加包含
`inlineKeyboardElement` 的原始消息。未开启时，标准 OneBot 消息转换会丢弃官方 Bot
的键盘按钮，插件将只能取得验证码文字和图片，无法取得点击所需的 `bot_appid`、
`button_id` 与 `callback_data`。这里的 NapCat 网络 `debug` 与插件配置中的
`debug_print` 是两个不同的开关。

## 依赖项

- **Python** >= 3.9
- **AstrBot** >= 4.0.0
- **openai** >= 1.0.0（用于调用视觉模型 API）

## 项目结构

```
astrbot_plugin_captcha/
├── main.py              # 插件主程序
├── metadata.yaml        # 插件元数据
├── _conf_schema.json    # 配置项 Schema（WebUI 配置驱动）
├── config.json          # 本地配置文件（可选）
├── requirements.txt     # Python 依赖声明
├── .gitignore           # Git 忽略规则
└── README.md            # 项目说明文档
```

## 常见问题

### Q: 插件安装后没有反应？

请检查以下几点：
1. 插件是否已在 AstrBot WebUI 中成功加载（插件列表中可见）
2. `vision_api_key` 和 `vision_model` 是否已正确配置
3. `official_bot_id` 是否与实际发送验证码的机器人 ID 一致
4. 开启 `debug_print` 查看控制台日志，确认消息是否被过滤

### Q: 视觉模型调用失败？

- 确认 API Key 有效且有足够配额
- 确认模型 ID 支持视觉（图片理解）能力
- 检查网络是否可以访问 `vision_base_url` 指定的 API 地址

### Q: 点击按钮失败？

- 确认使用的平台适配器支持 `click_inline_keyboard_button` 扩展 API
- 检查 AstrBot 日志中是否有 `call_action` 相关错误
- 部分 OneBot 实现可能需要额外配置才能使用扩展 API

### Q: 验证码不是发给我的机器人，为什么也会被处理？

插件内置了安全检查机制，只会处理 @ 自身机器人的验证码消息。如果出现误触发，请确认 `official_bot_id` 配置是否正确。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的功能分支：`git checkout -b feature/my-feature`
3. 提交更改：`git commit -m "feat: add my feature"`
4. 推送分支：`git push origin feature/my-feature`
5. 提交 Pull Request

提交代码前请确保：
- 代码经过 `ruff` 格式化
- 功能经过测试验证
- 包含必要的注释说明

## 许可证

本项目基于 [MIT License](LICENSE) 开源。
