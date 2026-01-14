<!-- markdownlint-disable MD036 MD041 -->

# 标准数据模型规范 (Standard Data Model Specification)

> **版本**: v2.0  
> **创建日期**: 2025-12-07  
> **状态**: Draft for Review  
> **依赖**: [Data_Integrity_Protocol.md](./Data_Integrity_Protocol.md)  

---

## 1. 设计哲学

### 核心原则

**"铁打的标准模型，流水的适配器"**

无论用户上传的是微信账单、支付宝账单、手写 Excel，还是 PDF 扫描件，进入系统后都必须转换为统一的 `StandardRecord` 格式。这是系统唯一的"通用语言"。

### 设计目标

1. **向后兼容**：未来新增字段时，旧数据仍能正常使用。
2. **多维分析**：支持按"分类"、"标签"、"成员"、"平台"等任意维度查询。
3. **多币种支持**：区分人民币、美元等不同货币的消费。
4. **完全溯源**：任何记录都能追溯到原始导入文件的具体行。

---

## 2. 核心数据结构

### 2.1 StandardRecord (标准记录)

这是系统内部唯一的数据存储格式。

```python
@dataclass
class StandardRecord:
    """
    GithubLedger 标准记录格式
    所有导入数据必须转换为此格式后才能存储
    """
    
    # ============ 1. 身份信息 ============
    id: str  # UUID v4, 唯一标识符
    """
    示例: "550e8400-e29b-41d4-a716-446655440000"
    用途: 防重计算、关联查询、数据更新
    """
    
    import_timestamp: datetime  # 导入时间 (ISO8601)
    """
    示例: "2025-12-07T14:30:00+08:00"
    用途: 审计追踪、版本管理
    """
    
    # ============ 2. 交易核心信息 ============
    transaction_time: datetime | date  # 交易发生时间
    """
    示例: 
    - datetime: 2025-03-15T14:30:45+08:00 (微信账单精确到秒)
    - date: 2025-03-15 (银行账单仅日期)
    
    重要: 必须遵守"精度适配原则"，不得将 date 自动升级为 datetime
    """
    
    amount: Decimal  # 金额 (使用 Decimal 防止浮点误差)
    """
    示例: Decimal("37.68")
    单位: 由 currency 字段定义
    注意: 必须保留原始精度 (如 20 不得自动变成 20.00)
    """
    
    currency: str = "CNY"  # 货币代码 (ISO 4217)
    """
    示例: "CNY", "USD", "EUR"
    默认: 人民币 (CNY)
    用途: 支持多币种统计、汇率换算
    """
    
    direction: Literal["expense", "income"]  # 收支方向
    """
    - expense: 支出
    - income: 收入
    
    注意: 退款算 income，转账不计入（除非用户明确要求）
    """
    
    # ============ 3. 消费实体信息 ============
    merchant: str | None = None  # 商户名称
    """
    示例: "瑞幸咖啡", "OpenAI", "元元早餐店"
    来源: 
    - 优先从账单的"商户"列提取
    - 若无此列，AI 从备注中提取
    - 若仍无法提取，保持 None
    
    标准化: 建议 AI 将同一商户的不同写法统一 (如 "瑞幸"/"luckin coffee" -> "瑞幸咖啡")
    但必须在 UserProfile 中记录映射关系，不得静默修改
    """
    
    platform: str | None = None  # 支付平台/渠道
    """
    示例: "微信支付", "支付宝", "招商银行", "现金", "WildCard"
    来源:
    - 账单类型（如微信导出的都是"微信支付"）
    - 用户手工记录的"购物平台"列
    
    区别于 merchant:
    - merchant 是"卖家" (瑞幸咖啡)
    - platform 是"付款工具" (微信支付)
    """
    
    item_name: str | None = None  # 商品/服务名称
    """
    示例: "API充值", "美式咖啡", "猫粮"
    来源: 用户账本的"所购商品"列，或 AI 从备注提取
    """
    
    quantity: float | None = None  # 数量
    unit: str | None = None  # 单位
    """
    示例: 
    - quantity: 10, unit: "袋"
    - quantity: 5, unit: "USD" (充值5美元)
    
    注意: 若原始数据无数量，保持 None，不得自动填 1
    """
    
    # ============ 4. 智能分类系统 ============
    category_main: str | None = None  # 一级分类
    category_sub: str | None = None  # 二级分类
    """
    示例: 
    - category_main: "餐饮", category_sub: "咖啡"
    - category_main: "软件服务", category_sub: "生产力工具"
    
    分类规则:
    1. 互斥性: 一笔消费只能属于一个分类
    2. 标准化: 建议 AI 维护一个分类字典 (如"吃"/"餐饮"/"食物" -> "餐饮")
    3. 可为空: 若 AI 无法判断，保持 None，标记 confidence_score < 0.8
    """
    
    tags: list[str] = []  # 标签列表 (多维度)
    """
    示例: ["女儿", "教育"], ["工作", "报销"], ["猫"]
    
    核心价值: 解决"维度混乱"问题
    - 用户原分类: "女儿费用" -> tags: ["女儿"], category: "餐饮"
    - 用户原分类: "工作花销" -> tags: ["工作"], category: "软件服务"
    
    这样可以既查"我在女儿身上花了多少"，又查"我买了多少餐饮"
    """
    
    # ============ 5. 元数据与溯源 ============
    source_file: str  # 来源文件名
    """
    示例: "家庭账本0713.csv", "wechat_bill_202503.csv"
    用途: 数据追溯、问题定位
    """
    
    original_row: dict  # 原始数据快照 (JSON)
    """
    示例: {
        "所购商品": "瑞幸咖啡",
        "金额（元）": "37.68",
        "购买日期": "2025年3月15日",
        "备注": "WildCard",
        ...
    }
    用途: 
    - 用户质疑数据时，展示原始记录
    - 支持"撤销导入"功能
    - 审计和调试
    """
    
    confidence_score: float = 1.0  # AI 处理的可信度 (0.0-1.0)
    """
    示例: 0.95 (高可信), 0.65 (低可信)
    规则:
    - 用户手工录入的字段: 1.0
    - AI 从备注提取的商户: 0.7-0.9
    - AI 推测的分类: 0.5-0.8
    
    阈值: < 0.8 时在 UI 标红，提示人工复核
    """
    
    notes: str | None = None  # 备注/说明
    """
    示例: "4S店补漆工本费", "原价34.8元"
    来源: 
    - 用户账本的"备注"列（已提取实体后的剩余内容）
    - 用户手工添加的说明
    """
    
    status: Literal["validated", "pending_review", "flagged"] = "validated"
    """
    - validated: 已验证，可用于统计
    - pending_review: 待人工复核（低 confidence_score）
    - flagged: 已标记问题（用户手动标记）
    """
```

---

## 3. 字段设计原则详解

### 3.1 为什么需要 `tags` 而不是多个 `category`？

**问题场景**：用户有一笔 "古茗奶茶 17元，给女儿买的"

* **旧模式**（单一分类）：`category: "女儿费用"` ❌  
    *后果*：无法统计"我这个月在餐饮上花了多少"

* **错误方案**（多分类）：`category: ["餐饮", "女儿费用"]` ❌  
    *后果*：逻辑混乱，一笔钱算了两次

* **正确方案**（分类+标签）：`category: "餐饮", tags: ["女儿"]` ✅  
    *优势*：
  * 查询 `category="餐饮"` 能得到所有吃喝的钱
  * 查询 `tags包含"女儿"` 能得到所有花在女儿身上的钱
  * 两者不冲突

### 3.2 为什么 `transaction_time` 可以是 `date` 或 `datetime`？

**问题场景**：银行账单只有日期 `2025-03-15`，微信账单有精确时间 `2025-03-15 14:30:45`

* **错误做法**：统一补全为 `2025-03-15 00:00:00` ❌  
    *后果*：违反"真实性原则"，用户会误以为所有银行消费都发生在午夜

* **正确做法**：保持原始精度 ✅

    ```python
    # 微信记录
    transaction_time: datetime = datetime(2025, 3, 15, 14, 30, 45)
    
    # 银行记录
    transaction_time: date = date(2025, 3, 15)
    ```

* **查询兼容**：Python 的 `datetime` 继承自 `date`，可以统一比较

    ```python
    # 查询 3 月 15 日所有记录
    records = [r for r in data if r.transaction_time.date() == date(2025, 3, 15)]
    ```

### 3.3 为什么用 `Decimal` 而不是 `float`？

**浮点陷阱**：

```python
# float 的精度问题
>>> 0.1 + 0.2
0.30000000000000004

# Decimal 的精确计算
>>> Decimal("0.1") + Decimal("0.2")
Decimal("0.3")
```

在财务系统中，`37.68 + 25.32` 必须等于 `63.00`，不能是 `62.99999999`。

---

## 4. 扩展性设计

### 4.1 未来可能新增的字段

```python
# 高级分析字段 (v3.0 计划)
price_per_unit: Decimal | None = None  # 单价 (amount / quantity)
is_shared: bool = False  # 是否家庭共享消费
split_ratio: dict[str, float] | None = None  # 成员分摊比例
    # 示例: {"爸爸": 0.5, "妈妈": 0.5}

# 智能提醒字段 (v4.0 计划)
price_trend: Literal["normal", "cheap", "expensive"] | None = None
    # AI 判断: 这次猫粮是买贵了还是便宜了
last_purchase_date: date | None = None  # 上次购买同类商品的日期
repurchase_cycle: int | None = None  # 复购周期 (天)
```

### 4.2 兼容性保证

**原则**：新增字段必须有默认值，旧数据自动补全为 `None` 或默认值，不影响现有功能。

---

## 5. 与其他协议的关系

```text
┌─────────────────────────────────────┐
│  Standard_Data_Model.md (本文档)     │  ← 定义"砖头"的形状
│  规定每条记录必须长什么样              │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  Data_Integrity_Protocol.md         │  ← 规定"砖头"的质量标准
│  规定数据不能编造、精度要匹配          │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  UserProfile.md (待创建)             │  ← 规定如何把各种"石头"变成"砖头"
│  定义 AI 如何生成适配器               │
└─────────────────────────────────────┘
```

---

## 6. 实现检查清单

在编写 Python 代码实现此模型前，必须确认：

* [ ] 所有字段的类型定义明确（包括 Optional 标注）
* [ ] 字段的默认值符合业务逻辑
* [ ] 已考虑字段的扩展性（未来新增字段不影响旧数据）
* [ ] 所有示例数据已验证可行性
* [ ] 与《数据完整性协议》无冲突

---

**下一步**：创建 `src/models/standard_record.py`，使用 `Pydantic` 实现此规范。
