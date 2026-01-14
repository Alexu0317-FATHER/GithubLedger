"""
StandardRecord - GithubLedger 标准数据模型

此模块定义了系统唯一的标准记录格式。
所有导入的数据（无论来自微信、银行还是手写 Excel）都必须转换为此格式。

设计原则:
1. 真实性: 不编造任何不存在的数据
2. 精度适配: 输出精度不得高于输入精度
3. 溯源性: 每条记录都能追溯到原始文件
4. 扩展性: 新增字段必须有默认值，保证向后兼容

相关文档: docs/architecture/Standard_Data_Model.md
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Literal, Optional
from uuid import uuid4


@dataclass
class StandardRecord:
    """
    GithubLedger 标准记录格式
    
    所有外部数据经过清洗后都必须转换为此格式才能存储到数据库。
    这是系统内部唯一的"通用语言"。
    
    Attributes:
        id: 唯一标识符 (UUID v4)
        import_timestamp: 导入时间
        transaction_time: 交易发生时间 (可能是 datetime 或 date)
        amount: 金额 (使用 Decimal 保证精度)
        currency: 货币代码 (ISO 4217, 默认 CNY)
        direction: 收支方向 (expense/income)
        merchant: 商户名称
        platform: 支付平台/渠道
        item_name: 商品/服务名称
        quantity: 数量
        unit: 单位
        category_main: 一级分类
        category_sub: 二级分类
        tags: 多维度标签列表
        source_file: 来源文件名
        original_row: 原始数据 JSON 快照
        confidence_score: AI 处理可信度 (0.0-1.0)
        notes: 备注说明
        status: 数据状态 (validated/pending_review/flagged)
    
    Examples:
        >>> record = StandardRecord(
        ...     transaction_time=datetime(2025, 3, 15, 14, 30),
        ...     amount=Decimal("37.68"),
        ...     direction="expense",
        ...     merchant="瑞幸咖啡",
        ...     category_main="餐饮",
        ...     source_file="wechat_bill.csv",
        ...     original_row={"商户": "瑞幸", "金额": "37.68"}
        ... )
    """
    
    # ============ 身份信息 ============
    id: str = field(default_factory=lambda: str(uuid4()))
    """唯一标识符 (自动生成 UUID v4)"""
    
    import_timestamp: datetime = field(default_factory=datetime.now)
    """导入时间 (自动记录当前时间)"""
    
    # ============ 交易核心信息 ============
    transaction_time: datetime | date
    """
    交易发生时间
    
    重要: 必须保持原始精度
    - 如果源数据有时分秒，使用 datetime
    - 如果源数据只有日期，使用 date
    - 禁止将 date 自动补全为 datetime(年, 月, 日, 0, 0, 0)
    """
    
    amount: Decimal
    """
    金额 (使用 Decimal 避免浮点误差)
    
    示例:
        - Decimal("37.68")  # 正确
        - 37.68  # 错误 (会自动转换，但不推荐直接传入 float)
    """
    
    currency: str = "CNY"
    """
    货币代码 (ISO 4217 标准)
    
    常用值:
        - "CNY": 人民币
        - "USD": 美元
        - "EUR": 欧元
    """
    
    direction: Literal["expense", "income"]
    """
    收支方向
    
    - "expense": 支出 (默认)
    - "income": 收入
    
    注意: 退款算 income，转账不计入（除非用户明确要求）
    """
    
    # ============ 消费实体信息 ============
    merchant: Optional[str] = None
    """
    商户名称
    
    来源优先级:
    1. 账单的"商户"列
    2. AI 从备注中提取
    3. 若无法提取，保持 None
    
    标准化: 建议通过 UserProfile.merchant_normalization 统一同一商户的不同写法
    示例: "瑞幸"/"luckin coffee" -> "瑞幸咖啡"
    """
    
    platform: Optional[str] = None
    """
    支付平台/渠道
    
    示例: "微信支付", "支付宝", "招商银行", "现金"
    
    区别于 merchant:
    - merchant 是"卖家" (瑞幸咖啡)
    - platform 是"付款工具" (微信支付)
    """
    
    item_name: Optional[str] = None
    """商品/服务名称 (如 "美式咖啡", "API充值")"""
    
    quantity: Optional[float] = None
    """数量 (如 10 袋, 5 美元)"""
    
    unit: Optional[str] = None
    """单位 (如 "袋", "USD", "个")"""
    
    # ============ 智能分类系统 ============
    category_main: Optional[str] = None
    """
    一级分类
    
    示例: "餐饮", "软件服务", "交通出行"
    
    规则:
    - 互斥性: 一笔消费只能属于一个分类
    - 可为空: 若 AI 无法判断，保持 None
    """
    
    category_sub: Optional[str] = None
    """
    二级分类
    
    示例: "咖啡", "生产力工具"
    """
    
    tags: list[str] = field(default_factory=list)
    """
    多维度标签列表
    
    示例: ["女儿", "教育"], ["工作", "报销"]
    
    核心价值: 解决"维度混乱"问题
    - 原分类 "女儿费用" -> tags: ["女儿"], category: "餐饮"
    - 这样可以既查"餐饮总支出"，又查"女儿相关支出"
    """
    
    # ============ 元数据与溯源 ============
    source_file: str
    """
    来源文件名
    
    示例: "家庭账本0713.csv", "wechat_bill_202503.csv"
    
    用途: 数据追溯、问题定位、撤销导入
    """
    
    original_row: dict = field(default_factory=dict)
    """
    原始数据 JSON 快照
    
    示例: {
        "所购商品": "瑞幸咖啡",
        "金额（元）": "37.68",
        "购买日期": "2025年3月15日"
    }
    
    用途:
    - 用户质疑数据时，展示原始记录
    - 支持"撤销导入"功能
    - 审计和调试
    """
    
    confidence_score: float = 1.0
    """
    AI 处理的可信度 (0.0 - 1.0)
    
    规则:
    - 用户手工录入: 1.0
    - AI 从备注提取的商户: 0.7-0.9
    - AI 推测的分类: 0.5-0.8
    
    阈值: < 0.8 时在 UI 标红，提示人工复核
    """
    
    notes: Optional[str] = None
    """
    备注/说明
    
    示例: "4S店补漆工本费", "原价34.8元"
    
    来源:
    - 用户账本的"备注"列（已提取实体后的剩余内容）
    - 用户手工添加的说明
    """
    
    status: Literal["validated", "pending_review", "flagged"] = "validated"
    """
    数据状态
    
    - validated: 已验证，可用于统计
    - pending_review: 待人工复核 (低 confidence_score)
    - flagged: 已标记问题 (用户手动标记)
    """
    
    def __post_init__(self):
        """
        数据验证（在对象创建后自动执行）
        """
        # 金额必须大于 0
        if self.amount <= 0:
            raise ValueError(f"金额必须大于 0，当前值: {self.amount}")
        
        # confidence_score 必须在 0-1 之间
        if not 0 <= self.confidence_score <= 1:
            raise ValueError(f"confidence_score 必须在 0-1 之间，当前值: {self.confidence_score}")
        
        # 如果是 pending_review 状态，confidence_score 应该 < 0.8
        if self.status == "pending_review" and self.confidence_score >= 0.8:
            raise ValueError("pending_review 状态的记录 confidence_score 应该 < 0.8")
    
    def to_dict(self) -> dict:
        """
        转换为字典格式（用于序列化）
        
        Returns:
            包含所有字段的字典
        """
        return {
            "id": self.id,
            "import_timestamp": self.import_timestamp.isoformat(),
            "transaction_time": self.transaction_time.isoformat() 
                if isinstance(self.transaction_time, datetime) 
                else self.transaction_time.isoformat(),
            "amount": str(self.amount),
            "currency": self.currency,
            "direction": self.direction,
            "merchant": self.merchant,
            "platform": self.platform,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "unit": self.unit,
            "category_main": self.category_main,
            "category_sub": self.category_sub,
            "tags": self.tags,
            "source_file": self.source_file,
            "original_row": self.original_row,
            "confidence_score": self.confidence_score,
            "notes": self.notes,
            "status": self.status,
        }
    
    @property
    def is_high_confidence(self) -> bool:
        """判断是否高可信度记录（>= 0.8）"""
        return self.confidence_score >= 0.8
    
    @property
    def needs_review(self) -> bool:
        """判断是否需要人工复核"""
        return self.status == "pending_review" or not self.is_high_confidence
