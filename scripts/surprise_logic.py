# -*- coding: utf-8 -*-
"""
麦当当惊喜官 · surprise_logic.py
【参考实现 / 演示脚本】

本项目定位为 **WorkBuddy Skill**：核心逻辑由 `skill/SKILL.md` 定义，
由 WorkBuddy 的 LLM 在对话中执行。本文件是「场景识别 + 仪式文案生成」的
参考实现，供 LLM 与开发者参考，**不负责工具编排、算价与下单**。

职责：
  1. 从自然语言中识别场合（detect_scene）
  2. 按场合生成仪式感话术（build_copy）

不负责（由 SKILL.md 指引 LLM 完成）：
  - MCP 工具编排（campaign-calendar / query-meals / ...）
  - 价格计算、预算核对、降级方案
  - 创建订单
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# 场景定义
# ---------------------------------------------------------------------------

SCENES = ("anniversary", "birthday", "apology", "confession", "long_distance")

SCENE_LABELS = {
    "anniversary": "纪念日",
    "birthday": "生日",
    "apology": "道歉",
    "confession": "表白",
    "long_distance": "异地惊喜",
}

# 关键词 → 场景（按出现顺序匹配，命中即返回）
SCENE_KEYWORDS = {
    "anniversary": ["周年", "纪念日", "在一起", "结婚", "入职周年"],
    "birthday": ["生日", "生日快乐", "岁", "蛋糕", "许愿"],
    "apology": ["道歉", "对不起", "惹", "生气", "哄", "原谅我", "我错了"],
    "confession": ["表白", "告白", "喜欢", "crush", "求交往", "在一起吗"],
    "long_distance": ["异地", "远方", "外地", "另一座城", "寄过去", "送过去", "远程"],
}

# 关系词 → 称呼（用于话术与关系字段）
RELATION_KEYWORDS = {
    "恋人": ["女朋友", "男朋友", "老婆", "老公", "对象", "爱人", "媳妇", "先生", "太太"],
    "朋友": ["朋友", "闺蜜", "兄弟", "同学", "室友", "哥们", "姐妹", "死党"],
    "家人": ["爸", "妈", "爹", "娘", "爷爷", "奶奶", "儿子", "女儿", "姐", "哥", "弟", "妹"],
}


# 仪式感话术库。
# ⚠️ 话术素材的权威来源是 skill/SKILL.md；此处为「程序化按单位选用」的演示副本，
#    修改话术请先改 SKILL.md，再同步此处，避免两处漂移。
# 纪念日按「单位」分键（修复"周年/天/个月混用导致文案错误"）；其余场景为模板列表。
# 模板变量：{value}=时长数字，{who}=称呼。
SCENE_COPY = {
    "anniversary": {
        "周年": ["{value}周年快乐。今天的第一份仪式感，就用麦当劳补上。"],
        "年": ["{value}周年快乐。今天的第一份仪式感，就用麦当劳补上。"],
        "天": ["和{who}在一起的第{value}天，想吃一顿不用挑店的饭。"],
        "个月": ["和{who}在一起的第{value}个月，想吃一顿不用挑店的饭。"],
        "_default": ["今天值得纪念。第一份仪式感，就用麦当劳补上。"],
    },
    "birthday": [
        "生日快乐！愿望可以慢慢想，薯条要趁热吃。",
        "今年的愿望先不贪心，先把{who}喂饱再说。",
    ],
    "apology": [
        "对不起，这份麦当劳先替我到位，人随后就到。",
        "是我错了。麦辣鸡翅的辣，都比不过我现在的心急。",
    ],
    "confession": [
        "不知道送什么，就先送你一顿我们都喜欢的麦当劳吧。",
        "如果你愿意，这顿之后，我们可以常一起吃。",
    ],
    "long_distance": [
        "人还没到，饭先到了。",
        "距离有点远，但这份心意是热的。",
    ],
}


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------


@dataclass
class SceneIntent:
    """识别出的用户意图"""
    scene: str                          # SCENES 之一
    label: str                          # 中文场景名
    relation: Optional[str] = None      # 对象/关系（恋人/朋友/家人）
    is_long_distance: bool = False      # 是否异地
    detail_value: str = ""              # 时长数字，如 "2"
    detail_unit: str = ""               # 时长单位："周年"|"年"|"天"|"个月"
    who: str = "你"                     # 称呼


# ---------------------------------------------------------------------------
# 1. 场景识别
# ---------------------------------------------------------------------------


def _detect_relation(text: str) -> Tuple[Optional[str], str]:
    """返回 (关系, 称呼)。未识别时关系为 None，称呼默认"你"。"""
    for relation, keywords in RELATION_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return relation, kw
    return None, "你"


def _extract_anniversary(text: str) -> Tuple[str, str]:
    """提取纪念时长，返回 (value, unit)。提取不到返回 ("", "")。

    保留单位是关键：周年 / 年 / 天 / 个月对应不同话术模板，
    避免"365 天"被拼成"365 周年"这类错误。
    """
    m = re.search(r"(\d+)\s*(周年|年|个月|天)", text)
    if not m:
        return "", ""
    return m.group(1), m.group(2)


def detect_scene(text: str) -> Optional[SceneIntent]:
    """从自然语言中识别场合。

    异地判断独立进行：只要文本含异地关键词，无论主场景是什么都视为异地。
    """
    if not text:
        return None

    is_ld = any(kw in text for kw in SCENE_KEYWORDS["long_distance"])
    relation, who = _detect_relation(text)
    value, unit = _extract_anniversary(text)

    for scene in ("anniversary", "birthday", "apology", "confession"):
        for kw in SCENE_KEYWORDS[scene]:
            if kw in text:
                return SceneIntent(
                    scene=scene,
                    label=SCENE_LABELS[scene],
                    relation=relation,
                    is_long_distance=is_ld,
                    detail_value=value,
                    detail_unit=unit,
                    who=who,
                )

    if is_ld:
        return SceneIntent(
            scene="long_distance",
            label=SCENE_LABELS["long_distance"],
            relation=relation,
            is_long_distance=True,
            detail_value=value,
            detail_unit=unit,
            who=who,
        )
    return None


# ---------------------------------------------------------------------------
# 2. 仪式话术生成
# ---------------------------------------------------------------------------


def build_copy(intent: SceneIntent, index: int = 0) -> str:
    """按场景（纪念日再按单位）取一条话术模板并填充变量。"""
    block = SCENE_COPY.get(intent.scene) or SCENE_COPY["anniversary"]
    if isinstance(block, dict):
        templates = block.get(intent.detail_unit) or block["_default"]
    else:
        templates = block
    template = templates[index % len(templates)]
    return template.format(
        value=intent.detail_value,
        who=intent.who or "你",
    )


# ---------------------------------------------------------------------------
# Demo（无需 MCP Token 即可运行，用于演示场景识别与文案生成）
# ---------------------------------------------------------------------------


def _demo() -> None:
    # 说明：本 demo 用关键词做"是否异地"的演示性判断；
    # 真实运行时，"她在上海""他在广州"这类地名级异地，由 LLM 层理解并提示用户提供地址。
    samples = [
        "今天是我和女朋友在一起 2 周年，预算 80，帮我搞点仪式感",
        "我们在一起 365 天了，想小小庆祝一下",
        "惹对象生气了，想给她点一份麦当劳道歉",
        "朋友明天生日，想给他整个惊喜",
        "异地恋，想给远方的她远程点一份惊喜",
    ]
    for s in samples:
        intent = detect_scene(s)
        if intent:
            dur = f"{intent.detail_value}{intent.detail_unit}" if intent.detail_value else "（无）"
            print(f"输入: {s}")
            print(f"  场景: {intent.label}（异地={intent.is_long_distance}，关系={intent.relation or '未明'}，时长={dur}）")
            print(f"  话术: {build_copy(intent)}")
        else:
            print(f"输入: {s}\n  场景: 未识别，需向用户追问场合")
        print("-" * 60)


if __name__ == "__main__":
    _demo()
