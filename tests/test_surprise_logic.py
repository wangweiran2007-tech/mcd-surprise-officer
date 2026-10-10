# -*- coding: utf-8 -*-
"""surprise_logic 单元测试。

覆盖：场景识别、周年单位提取（重点防回归）、关系识别、文案生成。
运行：在本目录（仓库根）执行 `pytest`。
"""
import pytest

import surprise_logic as sl


# ---------------------------------------------------------------------------
# detect_scene 场景识别
# ---------------------------------------------------------------------------


class TestDetectScene:
    def test_anniversary_with_year(self):
        intent = sl.detect_scene("今天是我和女朋友在一起 2 周年，帮我搞点仪式感")
        assert intent is not None
        assert intent.scene == "anniversary"
        assert intent.label == "纪念日"
        assert intent.relation == "恋人"
        assert intent.who == "女朋友"
        assert intent.detail_value == "2"
        assert intent.detail_unit == "周年"
        assert intent.is_long_distance is False

    def test_anniversary_with_days(self):
        intent = sl.detect_scene("我们在一起 365 天了")
        assert intent.scene == "anniversary"
        assert intent.detail_value == "365"
        assert intent.detail_unit == "天"

    def test_birthday(self):
        intent = sl.detect_scene("朋友明天生日，想给他整个惊喜")
        assert intent.scene == "birthday"
        assert intent.relation == "朋友"

    def test_apology(self):
        intent = sl.detect_scene("惹对象生气了，想道歉")
        assert intent.scene == "apology"
        assert intent.relation == "恋人"

    def test_confession(self):
        intent = sl.detect_scene("想跟喜欢的同学表白")
        assert intent.scene == "confession"
        assert intent.relation == "朋友"

    def test_pure_long_distance(self):
        intent = sl.detect_scene("异地恋，想给远方的她远程点一份惊喜")
        assert intent.scene == "long_distance"
        assert intent.is_long_distance is True

    def test_long_distance_independent_of_main_scene(self):
        # 关键：异地判断独立——主场景是生日，但含异地词 → 仍视为异地
        intent = sl.detect_scene("异地恋，想给对象过生日")
        assert intent.scene == "birthday"
        assert intent.is_long_distance is True

    def test_empty_and_none(self):
        assert sl.detect_scene("") is None
        assert sl.detect_scene(None) is None

    def test_no_keyword(self):
        assert sl.detect_scene("今天天气真不错") is None

    def test_priority_birthday_before_apology(self):
        # 匹配顺序 anniversary→birthday→apology→confession，"生日"先于"惹"命中
        intent = sl.detect_scene("生日那天惹她生气了")
        assert intent.scene == "birthday"


# ---------------------------------------------------------------------------
# _extract_anniversary 周年单位提取（建议 3 修复点，重点防回归）
# ---------------------------------------------------------------------------


class TestExtractAnniversary:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("在一起 2 周年", ("2", "周年")),
            ("在一起 365 天", ("365", "天")),
            ("认识 3 个月", ("3", "个月")),
            ("结婚 1 年", ("1", "年")),
            ("没有时长信息", ("", "")),
        ],
    )
    def test_units(self, text, expected):
        assert sl._extract_anniversary(text) == expected


# ---------------------------------------------------------------------------
# _detect_relation 关系识别
# ---------------------------------------------------------------------------


class TestDetectRelation:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("我女朋友", ("恋人", "女朋友")),
            ("我同学", ("朋友", "同学")),
            ("给我妈点一份", ("家人", "妈")),
            ("随便一个人", (None, "你")),
        ],
    )
    def test_relation(self, text, expected):
        assert sl._detect_relation(text) == expected


# ---------------------------------------------------------------------------
# build_copy 文案生成
# ---------------------------------------------------------------------------


def _intent(scene, unit="", value="", who="你"):
    return sl.SceneIntent(
        scene=scene,
        label=sl.SCENE_LABELS[scene],
        detail_unit=unit,
        detail_value=value,
        who=who,
    )


class TestBuildCopy:
    def test_anniversary_year(self):
        copy = sl.build_copy(_intent("anniversary", unit="周年", value="2"))
        assert copy == "2周年快乐。今天的第一份仪式感，就用麦当劳补上。"

    def test_anniversary_days_not_year(self):
        # 防回归：365 天绝不能输出"365 周年"
        copy = sl.build_copy(_intent("anniversary", unit="天", value="365"))
        assert "第365天" in copy
        assert "周年" not in copy

    def test_anniversary_months(self):
        copy = sl.build_copy(_intent("anniversary", unit="个月", value="3"))
        assert "第3个月" in copy

    def test_anniversary_default_when_no_unit(self):
        copy = sl.build_copy(_intent("anniversary"))
        assert copy == "今天值得纪念。第一份仪式感，就用麦当劳补上。"

    def test_birthday_who_filled(self):
        copy = sl.build_copy(_intent("birthday", who="闺蜜"), index=1)
        assert "闺蜜" in copy

    def test_index_rotation(self):
        copy0 = sl.build_copy(_intent("birthday"), index=0)
        copy2 = sl.build_copy(_intent("birthday"), index=2)
        assert copy0 == copy2  # 2 % len(templates) == 0

    def test_no_format_error_when_value_absent(self):
        # 其他场景模板无 {value} 占位，多传不报错
        copy = sl.build_copy(_intent("apology"))
        assert "对不起" in copy


# ---------------------------------------------------------------------------
# 集成：detect_scene → build_copy 全链路
# ---------------------------------------------------------------------------


class TestEndToEnd:
    @pytest.mark.parametrize(
        "text,must_contain",
        [
            ("今天是我和女朋友在一起 2 周年", "2周年快乐"),
            ("我们在一起 365 天了", "第365天"),
            ("惹对象生气了", "对不起"),
            ("朋友明天生日", "生日快乐"),
            ("异地恋，想给远方的她惊喜", "人还没到"),
        ],
    )
    def test_scene_to_copy(self, text, must_contain):
        intent = sl.detect_scene(text)
        assert intent is not None
        assert must_contain in sl.build_copy(intent)
