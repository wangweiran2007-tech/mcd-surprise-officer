# MCP 接入说明

> 本文档说明麦当当惊喜官实际使用的麦当劳 MCP Server、Tool、调用流程和业务价值。

## 1. MCP Server

| 项目 | 值 |
|---|---|
| Server 名称 | 麦当劳中国 MCP Server（`mcd-mcp`） |
| 接入地址 | `https://mcp.mcd.cn` |
| 传输协议 | Streamable HTTP |
| 鉴权方式 | 请求头 `Authorization: Bearer <MCP_TOKEN>` |
| 官方平台 | https://open.mcd.cn/mcp |
| 使用指南 | https://github.com/M-China/mcd-mcp-server |

## 2. 使用的 Tool 清单

| # | Tool | 用途 | 调用说明 |
|---:|---|---|---|
| 1 | `campaign-calendar` | 查询当月活动、联名、限定 | 入参：当前月份；返回活动列表，用于挑选与场合契合的联名/限定 |
| 2 | `query-nearby-stores` | 查询附近可用门店 | 入参：地址；返回门店列表，同城场景定位服务门店 |
| 3 | `query-meals` | 拉取门店在售餐品 | 入参：门店信息；返回分类菜单（编码、标签），用于组套餐 |
| 4 | `query-meal-detail` | 查看套餐详情与可替换项 | 入参：餐品编码；返回套餐组成与可替换选项 |
| 5 | `calculate-price` | 计算总价与优惠 | 入参：选购商品列表（可含券）；返回商品金额、优惠金额、应付总价 |
| 6 | `create-order` | 创建订单 | 入参：门店、就餐方式、商品列表；返回订单详情与支付链接 |
| 7 | `delivery-query-addresses` | 获取可配送地址列表 | 异地场景：查历史收货地址 |
| 8 | `delivery-create-address` | 新增配送地址 | 异地场景：录入对方收货地址 |
| 9 | `delivery-query-stores` | 查询可配送门店 | 异地场景：核验对方地址可配送性 |
| 10 | `now-time-info` | 获取当前时间 | 判断日期、时段，辅助确定活动是否在进行中 |

## 3. 调用流程

> 与 `skill/SKILL.md` 的「调用流程（七步）」编号一致，此处补充工具参数细节。仅步骤 [2] 因同城/异地而不同。

```
[1] campaign-calendar        查当月活动，筛出与场合契合的联名/限定
   ↓
[2] 定位门店（二选一）
   ├─ 同城 → query-nearby-stores（按用户地址就近门店）
   └─ 异地 → delivery-query-addresses（读历史地址）
             / delivery-create-address（录入对方地址）
             → delivery-query-stores（核验可配送；不可配送则提示到店自取/换店）
   ↓
[3] query-meals              拉取该门店在售餐品
   ↓
[4] query-meal-detail        对候选套餐查详情与可替换项
   ↓
[5] calculate-price          计算总价（含券），核对预算
   ↓
[6] 生成「惊喜方案卡」（套餐 + 总价 + 话术 + 活动亮点）
   ↓
[7] 用户确认 → create-order  创建订单，返回支付链接
```

## 4. 关键实现说明

- **非结构化返回处理**：`query-meals`、`campaign-calendar` 返回的可能是紧凑表格或 Markdown 文本，由 LLM 按 `skill/SKILL.md` 的流程指引完成解析与匹配（按场合关键词筛选活动、按餐品标签组合套餐）；`scripts/surprise_logic.py` 仅提供「场景识别 + 仪式话术生成」的参考实现（`detect_scene` / `build_copy`），不参与解析与匹配。
- **预算降级**：`calculate-price` 返回总价后，若超预算，由 LLM 按 SKILL.md 指引用同品类低一档餐品重算一次，给出"低配方案 + 节省金额"，由用户选择（脚本侧无自动降级逻辑）。
- **限流控制**：官方限流 600 次/分钟，本 Skill 每次完整流程最多 8 次调用，远低于上限；对活动日历结果做会话内缓存，避免重复拉取。
- **真实数据约束**：所有餐品、价格、活动均以 MCP 实时返回为准；取不到的字段一律标注「未取到」，不填估算值。

## 5. 业务价值

- **解决的真实问题**：用户想在麦当劳制造仪式感，但不知道"选什么、怎么说、怎么送"。本 Skill 把这件模糊的事拆成可执行的下单链路。
- **必须依赖 MCP 的原因**：当月活动、门店在售餐品、套餐可替换项、可配送性、实时价格全部是**门店级、时间级实时数据**，静态数据无法替代；尤其是"当下有什么联名活动"只有 `campaign-calendar` 能给出。
- **业务价值**：把"一次点餐"升级为"一次心意交付"，覆盖纪念日、生日、道歉、表白、异地送礼五类高频情感场景。

## 6. 安全与合规

- [x] 仓库内**不含任何真实 Token / 密钥 / 密码 / 账号凭证**
- [x] 配置文件仅使用环境变量占位符（`${MCD_MCP_TOKEN}`）
- [x] 未调用任何超出 MCP 官方开放范围的接口
- [x] 已遵守麦当劳 MCP 服务规则：https://cdn.mcd.cn/cms/pages/MCPServerRules.html
