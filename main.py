"""
astrbot_plugin_captcha - 验证码自动识别与点击插件

自动识别 QQ 群聊中机器人发送的干扰验证码图片，
通过视觉模型识别图中物品，并模拟点击对应按钮完成验证。
"""

import os
import re
import json
import time
import traceback
from typing import Optional

from openai import AsyncOpenAI

from astrbot.api import logger, AstrBotConfig
from astrbot.api.star import Context, Star, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.event.filter import EventMessageType


def _console(tag: str, msg: str, level: str = "info") -> None:
    """统一日志输出，同时写入 AstrBot logger 和控制台。"""
    line = f"[Captcha][{tag}] {msg}"
    try:
        log_func = getattr(logger, level if level in ("info", "warning", "error") else "info")
        log_func(line)
    except Exception:
        pass
    print(line, flush=True)


@register(
    "astrbot_plugin_captcha",
    "时光",
    "验证码自动识别与点击：自动识别 QQ 群聊中的干扰验证码图片并模拟点击对应按钮",
    "1.0.0",
    "",
)
class CaptchaPlugin(Star):
    """验证码自动识别与点击插件。"""

    _AT_ID_PATTERN = re.compile(r"at_(?:tinyid|qq)=(\d+)")
    _IMG_URL_PATTERN = re.compile(r"!\[.*?\]\((https://qqbot\.ugcimg\.cn/.*?)\)")
    _TARGET_NUM_PATTERN = re.compile(r"第(\d+)个表情")

    _DEFAULT_CONFIG = {
        "official_bot_id": "3889001741",
        "vision_api_key": "",
        "vision_base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "vision_model": "",
        "debug_print": True,
        "stop_after_handle": True,
    }

    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.cfg = self._load_config(config)
        self.vision_client = None  # 延迟初始化，首次调用时创建
        self._init_vision_client()

        _console("BOOT", "============ 验证码克星启动 ============")
        _console("BOOT", f"官方Bot ID  : {self.cfg.get('official_bot_id')}")
        _console("BOOT", f"视觉模型    : {self.cfg.get('vision_model') or '未配置'}")
        _console("BOOT", f"API Key     : {'已配置' if self.cfg.get('vision_api_key') else '未配置'}")
        _console("BOOT", f"调试日志    : {'开启' if self.cfg.get('debug_print') else '关闭'}")
        _console("BOOT", "========================================")

    def _init_vision_client(self):
        """初始化视觉模型客户端，仅在 API Key 非空时创建。"""
        api_key = self.cfg.get("vision_api_key", "")
        if not api_key:
            _console("BOOT", "视觉模型 API Key 未配置，视觉识别功能暂不可用。", level="warning")
            return
        self.vision_client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.cfg.get("vision_base_url", "https://ark.cn-beijing.volces.com/api/v3"),
        )

    def _load_config(self, config: AstrBotConfig = None) -> dict:
        """加载配置，优先使用 AstrBot WebUI 配置，回退到本地 config.json。"""
        cfg = dict(self._DEFAULT_CONFIG)

        if config is not None:
            try:
                cfg.update(config)
                _console("CONFIG", "已加载 AstrBot WebUI 配置。")
                return cfg
            except Exception as e:
                _console("CONFIG", f"读取 AstrBot 配置失败: {e}", level="error")

        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg.update(json.load(f))
                _console("CONFIG", f"已加载本地配置: {config_path}")
        except Exception as e:
            _console("CONFIG", f"加载本地配置失败: {e}", level="error")

        return cfg

    def _dbg(self, tag: str, msg: str) -> None:
        """仅在调试模式开启时输出日志。"""
        if self.cfg.get("debug_print", True):
            _console(tag, msg)

    @classmethod
    def _is_at_me(cls, event: AstrMessageEvent, msg_str: str) -> bool:
        """判断验证码消息是否 @ 了当前机器人。"""
        try:
            if getattr(event, "is_at_or_wake_command", False):
                return True
        except Exception:
            pass

        try:
            self_id = str(event.message_obj.self_id)
            at_ids = cls._AT_ID_PATTERN.findall(msg_str)
            if self_id in at_ids:
                return True
        except Exception:
            pass

        return False

    @filter.event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_msg(self, event: AstrMessageEvent):
        """监听群聊消息，过滤并处理验证码消息。"""
        try:
            sender_id = str(event.get_sender_id())
            if sender_id != str(self.cfg.get("official_bot_id", "")):
                return

            msg_str = event.message_str or ""
            if "请点击图中第" not in msg_str:
                return

            if not self._is_at_me(event, msg_str):
                self._dbg("SAFE", "验证码不是 @ 我，跳过避免误点。")
                return

            await self._handle_captcha(event, msg_str)

            if self.cfg.get("stop_after_handle", True):
                event.stop_event()

        except Exception as e:
            _console("FATAL", f"入口异常: {e}\n{traceback.format_exc()}", level="error")

    async def _handle_captcha(self, event: AstrMessageEvent, msg_str: str) -> None:
        """验证码识别与点击的核心处理流程。"""
        t0 = time.time()
        _console("CAPTCHA", "============== 🎯 验证码处理开始 ==============")

        try:
            # 解析目标编号
            target_num = self._parse_target_num(msg_str)
            self._dbg("CAPTCHA", f"目标编号 = {target_num}")

            # 提取图片 URL
            img_url = self._extract_image_url(msg_str)
            if not img_url:
                _console("CAPTCHA", "未找到验证码图片链接，跳过处理。", level="error")
                return
            self._dbg("CAPTCHA", f"图片URL = {img_url}")

            # 解析按钮与关键参数
            msg_seq, bot_appid, buttons_data = self._parse_keyboard_data(event)
            if not (buttons_data and msg_seq and bot_appid):
                _console(
                    "CAPTCHA",
                    f"关键参数缺失: msg_seq={msg_seq!r}, bot_appid={bot_appid!r}, "
                    f"buttons={len(buttons_data)}",
                    level="error",
                )
                return

            _console("CAPTCHA", f"目标第 {target_num} 个 | 按钮数 {len(buttons_data)}")

            # 调用视觉模型识别图片
            labels = [b["label"] for b in buttons_data]
            ai_answer = await self._call_vision_model(img_url, target_num, labels)
            if not ai_answer:
                _console("VISION", "视觉模型未返回有效结果，跳过处理。", level="error")
                return
            _console("VISION", f"模型回答: 【{ai_answer}】")

            # 匹配按钮并模拟点击
            target_btn = self._match_button(ai_answer, buttons_data)
            _console("CLICK", f"准备点击按钮：【{target_btn['label']}】")

            await self._click_button(event, bot_appid, msg_seq, target_btn)

        except Exception as e:
            _console("CAPTCHA", f"全局异常: {e}\n{traceback.format_exc()}", level="error")
        finally:
            elapsed = time.time() - t0
            _console("CAPTCHA", f"============== 🎯 验证码处理结束（耗时 {elapsed:.2f}s）==============")

    def _parse_target_num(self, msg_str: str) -> int:
        """从消息文本中解析目标表情编号。"""
        m = self._TARGET_NUM_PATTERN.search(msg_str)
        return int(m.group(1)) if m else 1

    def _extract_image_url(self, msg_str: str) -> Optional[str]:
        """从消息文本中提取验证码图片 URL。"""
        m = self._IMG_URL_PATTERN.search(msg_str)
        return m.group(1) if m else None

    def _parse_keyboard_data(self, event: AstrMessageEvent):
        """从原始消息数据中解析内联键盘按钮信息，返回 (msg_seq, bot_appid, buttons_data)。"""
        raw_event = getattr(event.message_obj, "raw_message", {}) or {}
        if not isinstance(raw_event, dict):
            raw_event = getattr(raw_event, "__dict__", {}) or {}
        raw_dict = raw_event.get("raw", {}) or {}

        msg_seq = str(raw_dict.get("msgSeq", ""))
        bot_appid = ""
        buttons_data = []

        for el in raw_dict.get("elements", []):
            if not isinstance(el, dict):
                continue
            keyboard = el.get("inlineKeyboardElement")
            if not keyboard:
                continue
            bot_appid = str(keyboard.get("botAppid", ""))
            for row in keyboard.get("rows", []):
                for btn in row.get("buttons", []):
                    buttons_data.append({
                        "label": btn.get("label", ""),
                        "button_id": str(btn.get("id", "")),
                        "callback_data": str(btn.get("data", "")),
                    })

        return msg_seq, bot_appid, buttons_data

    async def _call_vision_model(self, img_url: str, target_num: int, labels: list) -> Optional[str]:
        """调用视觉大模型识别验证码图片中的目标物品。"""
        if self.vision_client is None:
            _console("VISION", "视觉模型客户端未初始化（API Key 未配置），无法识别。", level="error")
            return None

        prompt = (
            f"这是一张QQ机器人的干扰验证码图片。请从左到右识别图中的物品。"
            f"题目要求找出第 {target_num} 个物品是什么。"
            f"请在以下给定的选项中选出一个最匹配的：{labels}。"
            f"只回复选项本身的文字或Emoji，不要标点、不要解释。"
        )

        self._dbg("VISION", "提交图片给视觉模型...")
        try:
            resp = await self.vision_client.chat.completions.create(
                model=self.cfg.get("vision_model", ""),
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": img_url}},
                    ],
                }],
                max_tokens=16,
            )
        except Exception as e:
            _console("VISION", f"调用视觉模型失败: {e}\n{traceback.format_exc()}", level="error")
            return None

        content = resp.choices[0].message.content if resp.choices else None
        return (content or "").strip() or None

    @staticmethod
    def _match_button(ai_answer: str, buttons_data: list) -> dict:
        """将视觉模型答案与按钮选项匹配，未命中时兜底选第一个。"""
        matched = next(
            (b for b in buttons_data
             if b["label"] and (b["label"] in ai_answer or ai_answer in b["label"])),
            None,
        )
        if not matched:
            _console("MATCH", f"AI 答案【{ai_answer}】不在选项内，兜底点击第一个按钮", level="warning")
            return buttons_data[0]
        return matched

    async def _click_button(self, event: AstrMessageEvent, bot_appid: str, msg_seq: str, target_btn: dict) -> None:
        """通过 OneBot 协议模拟点击内联键盘按钮。"""
        client = self._get_onebot_client(event)
        if client is None:
            _console("CLICK", "未获取到 OneBot 底层 client，无法执行点击操作。", level="error")
            return

        group_id = str(event.get_group_id())
        payload = {
            "group_id": group_id,
            "bot_appid": bot_appid,
            "button_id": target_btn["button_id"],
            "callback_data": target_btn["callback_data"],
            "msg_seq": msg_seq,
        }
        self._dbg("CLICK", f"payload = {payload}")

        try:
            res = await client.call_action("click_inline_keyboard_button", **payload)
            _console("CLICK", f"物理点击成功，服务器返回: {res}")
        except Exception as e:
            _console("CLICK", f"call_action 调用失败: {e}\n{traceback.format_exc()}", level="error")

    @staticmethod
    def _get_onebot_client(event: AstrMessageEvent) -> Optional[object]:
        """获取 OneBot 协议的底层 client，不可用时返回 None。"""
        try:
            platform_name = (event.get_platform_name() or "").lower()
            if "aiocqhttp" not in platform_name and "onebot" not in platform_name:
                _console("PLATFORM", f"当前平台 [{platform_name}] 不支持按钮点击操作。", level="warning")
                return None
            bot = getattr(event, "bot", None)
            if bot and hasattr(bot, "call_action"):
                return bot
        except Exception as e:
            _console("CLIENT", f"获取 OneBot client 异常: {e}", level="error")
        return None

    async def terminate(self) -> None:
        """插件卸载时的清理回调。"""
        _console("EXIT", "🎯 验证码克星插件已卸载。")
