# 麦当当惊喜官 · McSurprise Officer

> 麦当劳程序员创意开发大赛（1024 程序员节 · M-CODE）参赛作品
> 基于麦当劳中国 MCP 能力开发的 Skill

**一句话介绍**：生日、纪念日、道歉、表白、异地送礼——你说场合，它用麦当劳把事办了。

---

## 项目介绍

市面上的点餐类 Skill 都在回答同一个问题——"怎么点得省"。**麦当当惊喜官**回答的是另一个问题——"**怎么把一顿饭变成一份心意**"。

它把"想在麦当劳制造仪式感"这件很模糊的事，拆成一条清晰的链路：识别场合 → 查当下活动 → 组合惊喜套餐 → 核对预算 → 配一句走心话术 → 确认下单。全榜 182 个参赛项目中，"省钱/健康点餐"类已超百个，而聚焦**情感与纪念日场景**的作品近乎空白。

## 目标用户

- 想在麦当劳给朋友、伴侣制造小惊喜，但不知道怎么选、怎么说的年轻人
- 不懂搭配、只想要"一个拿得出手的方案"的用户
- 想给远方的朋友、家人远程送一份心意的用户

## 功能特性

- [x] **场合识别**：纪念日 / 生日 / 道歉 / 表白 / 异地送礼，自动匹配文案风格
- [x] **活动联动**：实时查询当月联名、限定活动，优先融入方案
- [x] **惊喜套餐**：基于门店在售餐品组合，支持套餐可替换项
- [x] **预算核对**：实时算价，超预算自动给低配方案
- [x] **仪式话术**：按场合生成不油腻、不堆砌的走心文案
- [x] **异地送达**：支持远程下单到对方地址，自动核验可配送性

## 使用的麦当劳 MCP 工具

| Tool | 用途 |
|---|---|
| `campaign-calendar` | 查询当月活动、联名、限定 |
| `query-nearby-stores` | 查询附近可用门店 |
| `query-meals` | 拉取门店在售餐品 |
| `query-meal-detail` | 查看套餐详情与可替换项 |
| `calculate-price` | 计算总价与优惠 |
| `create-order` | 创建订单，返回支付链接 |
| `delivery-query-addresses` / `delivery-create-address` | 异地场景：收货地址管理 |
| `delivery-query-stores` | 异地场景：核验可配送门店 |
| `now-time-info` | 判断日期、时段 |

## 安装方法

### 前置条件
1. 申请麦当劳 MCP Token：https://open.mcd.cn/mcp （手机号登录 → 控制台 → 激活 → 复制 Token）
2. MCP Client 需支持 Streamable HTTP 协议（推荐 WorkBuddy，亦兼容 Cursor / Trae / Cherry Studio 等）

### 配置 MCP
`mcp-config.example.json` 只含环境变量占位符。请**通过环境变量 `MCD_MCP_TOKEN` 注入**你的实际 Token（不要把真实 Token 写进配置文件或提交仓库）：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamablehttp",
      "url": "https://mcp.mcd.cn",
      "headers": {
        "Authorization": "Bearer ${MCD_MCP_TOKEN}"
      }
    }
  }
}
```

### 安装 Skill
将 `skill/SKILL.md` 复制到你的 MCP Client 技能目录，启用后即可在对话中触发。

## 使用示例

**示例 1 · 纪念日**（2026-10-10 实测真实单品）
```
用户：今天是我和女朋友在一起 2 周年，预算 60，帮我搞点仪式感
Skill：🍔 惊喜方案 · 两周年纪念日
        套餐组合：全明星双人分享餐八件套（汉堡+主食+小食+饮料，主食可换龙焰鸡腿堡）
        合计：49.9 元（现价，原价 117.5 元）　预算核对：未超
        仪式话术：「2 周年快乐。今天的第一份仪式感，就用麦当劳补上。」
        活动亮点：本月麦当劳联动 G-DRAGON，韩式风味系列上新
        确认下单请回复「下单」
```

**示例 2 · 表白**（2026-10-10 实测真实单品）
```
用户：想跟喜欢的同学表白，不知道送什么
Skill：🍔 惊喜方案 · 表白
        套餐组合：“我就喜欢”鸡薯双全盒（5块心形薯饼+5块麦乐鸡+韩式蘸酱）+ 蓝莓爆爆珠麦旋风
        合计：31.9 元　预算核对：未超
        仪式话术：「这份里有 5 块心形薯饼——你看，连薯条都是爱你的形状。」
        确认下单请回复「下单」
```

**示例 3 · 异地道歉**
```
用户：惹对象生气了，她在上海，想给她点一份麦当劳道歉
Skill：（调用 delivery-create-address 记录对方地址 → delivery-query-stores 核验可配送）
        🍔 惊喜方案 · 道歉
        …（套餐 + 话术「对不起，这份麦当劳先替我到位，人随后就到。」）
```

## 项目结构

本项目核心逻辑由 `skill/SKILL.md` 定义、在 WorkBuddy 对话中执行；`scripts/` 为「场景识别与文案生成」的**参考实现**（演示脚本），供 LLM 与开发者参考，不承担下单。

```
.
├── README.md                  # 本文件
├── LICENSE                    # MIT 许可证
├── CONTEST_DECLARATION.md     # 参赛声明（官方原件，不可修改）
├── MCP_INTEGRATION.md         # MCP 接入说明
├── mcp-config.example.json    # 脱敏 MCP 配置示例（仅环境变量占位符）
├── workbuddy.md               # WorkBuddy 开发对话上下文
├── pyproject.toml             # 环境与依赖声明（运行时仅标准库）
├── skill/
│   └── SKILL.md               # Skill 定义（核心逻辑）
├── scripts/
│   └── surprise_logic.py      # 场景识别与文案生成的参考实现（演示脚本，非下单逻辑）
└── tests/
    └── test_surprise_logic.py # pytest 单元测试
```

## 开发与测试

运行时仅依赖 Python 标准库；`scripts/` 为参考实现，`skill/SKILL.md` 为核心逻辑。

```bash
pip install -e ".[dev]"   # 安装开发依赖（pytest）；或直接 pip install pytest
pytest                     # 运行 tests/ 单元测试（当前 31 例）
```

## 免责声明

本项目为麦当劳程序员创意开发大赛参赛作品，由参赛者独立开发，**非麦当劳官方产品**。
项目输出仅供参考，不构成医疗、营养或其他专业建议；餐品信息、价格及供应状态以麦当劳官方渠道的实时结果为准。

## 许可

MIT License
