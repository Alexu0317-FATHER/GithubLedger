"""
UserProfile - AI 适配器配置模型

此模块定义了 AI 如何为每个用户生成"护照"（配置文件）。
这个配置告诉系统如何将用户的千奇百怪的 Excel/CSV 转换为 StandardRecord。

设计原则:
1. 配置驱动: 不写死任何用户特定的逻辑
2. AI 生成: 由 LLM 分析用户数据后自动生成
3. 用户确认: AI 生成后必须经过用户确认
4. 可复用: 一次生成，后续导入都复用

相关文档: docs/architecture/UserProfile_Protocol.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional


@dataclass
class ColumnMapping:
    """
    列映射配置
    
    告诉系统用户的 Excel 里哪一列对应哪个标准字段
    """
    date_column: str
    """日期列名 (必需)"""
    
    amount_column: str
    """金额列名 (必需)"""
    
    merchant_column: Optional[str] = None
    """商户列名 (可选，若为 None 则从备注提取)"""
    
    category_column: Optional[str] = None
    """分类列名 (可选)"""
    
    notes_column: Optional[str] = None
    """备注列名 (可选)"""
    
    platform_column: Optional[str] = None
    """平台列名 (可选)"""
    
    item_column: Optional[str] = None
    """商品/服务列名 (可选)"""
    
    quantity_column: Optional[str] = None
    """数量列名 (可选)"""


@dataclass
class MerchantExtraction:
    """
    商户提取规则
    
    定义如何从"备注"或其他列中提取商户信息
    """
    enabled: bool = False
    """是否启用商户提取"""
    
    source: Literal["column", "notes", "ai_inference"] = "column"
    """
    提取来源
    - column: 直接从 merchant_column 读取
    - notes: 从 notes_column 通过规则提取
    - ai_inference: 通过 AI 全文理解提取
    """
    
    rules: list[dict] = field(default_factory=list)
    """
    提取规则列表
    
    示例: [
        {"pattern": ".*学校|.*医院|.*店", "action": "extract"},
        {"pattern": "原价\\d+\\.\\d+", "action": "ignore"}
    ]
    """


@dataclass
class ParsingStrategy:
    """
    解析策略配置
    
    定义如何解析用户的数据文件
    """
    mode: Literal["standard", "mixed_notes", "full_nlp"] = "standard"
    """
    解析模式
    - standard: 标准模式，每个字段都有独立的列
    - mixed_notes: 混合备注模式，备注列包含多种信息
    - full_nlp: 全文提取模式，所有信息都在一个字段里
    """
    
    date_format: str = "%Y-%m-%d"
    """
    日期格式 (Python strptime 格式)
    
    示例:
    - "%Y年%m月%d日" -> 2025年3月15日
    - "%Y-%m-%d" -> 2025-03-15
    - "%Y/%m/%d" -> 2025/03/15
    """
    
    currency_default: str = "CNY"
    """默认货币 (ISO 4217)"""
    
    merchant_extraction: MerchantExtraction = field(default_factory=MerchantExtraction)
    """商户提取配置"""


@dataclass
class CategoryMapping:
    """
    单个分类的映射规则
    """
    category_main: str
    """映射到的一级分类"""
    
    category_sub: Optional[str] = None
    """映射到的二级分类"""
    
    tags: list[str] = field(default_factory=list)
    """附加的标签"""


@dataclass
class CategorySystem:
    """
    分类系统配置
    
    定义如何将用户的原始分类转换为标准分类
    """
    type: Literal["dimensional_split", "flat", "hierarchical"] = "flat"
    """
    分类系统类型
    - dimensional_split: 维度拆解（将"女儿费用"拆为分类+标签）
    - flat: 平面映射（直接一对一映射）
    - hierarchical: 层级映射（"餐饮.咖啡" -> main: 餐饮, sub: 咖啡）
    """
    
    category_mapping: dict[str, CategoryMapping] = field(default_factory=dict)
    """
    分类映射表
    
    示例: {
        "吃": CategoryMapping(category_main="餐饮", tags=[]),
        "女儿费用": CategoryMapping(category_main="未分类", tags=["女儿"]),
        "工作花销": CategoryMapping(category_main="软件服务", tags=["工作"])
    }
    """
    
    inference_prompt: Optional[str] = None
    """
    AI 推断提示词（当分类为空时使用）
    
    示例: "根据商户名和商品名推断分类，如'瑞幸咖啡'归为'餐饮'"
    """


@dataclass
class DataCleaningRules:
    """
    数据清洗规则
    """
    exclude_transactions: list[str] = field(default_factory=lambda: ["transfer", "repayment", "redpacket"])
    """
    排除的交易类型
    
    默认排除:
    - transfer: 转账
    - repayment: 还款
    - redpacket: 红包
    """
    
    merchant_normalization_enabled: bool = False
    """是否启用商户名称标准化"""
    
    merchant_mappings: dict[str, str] = field(default_factory=dict)
    """
    商户名称映射表
    
    示例: {
        "瑞幸": "瑞幸咖啡",
        "luckin coffee": "瑞幸咖啡",
        "元元": "元元早餐店"
    }
    """
    
    deduplication_enabled: bool = False
    """是否启用去重"""
    
    deduplication_match_fields: list[str] = field(default_factory=lambda: ["amount", "transaction_time", "merchant"])
    """去重匹配字段"""
    
    time_tolerance_seconds: int = 0
    """时间容差（秒），用于判断两笔交易是否重复"""


@dataclass
class SourceFileInfo:
    """
    源文件信息
    """
    file_name: str
    """文件名"""
    
    file_hash: str
    """文件哈希值 (MD5)"""
    
    sample_rows: int = 50
    """AI 分析时使用的样本行数"""


@dataclass
class UserProfile:
    """
    用户配置文件（AI 生成的"护照"）
    
    这是连接"用户数据"与"标准模型"的桥梁。
    AI 分析用户上传的文件后生成此配置，经用户确认后保存。
    
    Examples:
        >>> profile = UserProfile(
        ...     user_id="user_a",
        ...     column_mapping=ColumnMapping(
        ...         date_column="购买日期",
        ...         amount_column="金额（元）"
        ...     ),
        ...     parsing_strategy=ParsingStrategy(
        ...         mode="mixed_notes",
        ...         date_format="%Y年%m月%d日"
        ...     )
        ... )
    """
    
    user_id: str
    """用户 ID (UUID)"""
    
    profile_version: str = "2.0"
    """配置版本"""
    
    created_at: datetime = field(default_factory=datetime.now)
    """创建时间"""
    
    source_files: list[SourceFileInfo] = field(default_factory=list)
    """源文件列表（用于生成此配置的文件）"""
    
    column_mapping: ColumnMapping = field(default_factory=lambda: ColumnMapping(
        date_column="date",
        amount_column="amount"
    ))
    """列映射配置"""
    
    parsing_strategy: ParsingStrategy = field(default_factory=ParsingStrategy)
    """解析策略"""
    
    category_system: CategorySystem = field(default_factory=CategorySystem)
    """分类系统配置"""
    
    data_cleaning_rules: DataCleaningRules = field(default_factory=DataCleaningRules)
    """数据清洗规则"""
    
    # ============ 元数据 ============
    ai_model: str = "gpt-4o"
    """生成此配置的 AI 模型"""
    
    confidence_threshold: float = 0.8
    """可信度阈值（低于此值需要人工复核）"""
    
    user_confirmed: bool = False
    """用户是否已确认此配置"""
    
    notes: Optional[str] = None
    """配置说明/备注"""
    
    def __post_init__(self):
        """数据验证"""
        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError(f"confidence_threshold 必须在 0-1 之间，当前值: {self.confidence_threshold}")
    
    def to_dict(self) -> dict:
        """
        转换为字典格式（用于 JSON 序列化）
        
        Returns:
            包含所有字段的字典
        """
        return {
            "user_id": self.user_id,
            "profile_version": self.profile_version,
            "created_at": self.created_at.isoformat(),
            "source_files": [
                {
                    "file_name": sf.file_name,
                    "file_hash": sf.file_hash,
                    "sample_rows": sf.sample_rows
                }
                for sf in self.source_files
            ],
            "column_mapping": {
                "date_column": self.column_mapping.date_column,
                "amount_column": self.column_mapping.amount_column,
                "merchant_column": self.column_mapping.merchant_column,
                "category_column": self.column_mapping.category_column,
                "notes_column": self.column_mapping.notes_column,
                "platform_column": self.column_mapping.platform_column,
                "item_column": self.column_mapping.item_column,
                "quantity_column": self.column_mapping.quantity_column,
            },
            "parsing_strategy": {
                "mode": self.parsing_strategy.mode,
                "date_format": self.parsing_strategy.date_format,
                "currency_default": self.parsing_strategy.currency_default,
                "merchant_extraction": {
                    "enabled": self.parsing_strategy.merchant_extraction.enabled,
                    "source": self.parsing_strategy.merchant_extraction.source,
                    "rules": self.parsing_strategy.merchant_extraction.rules,
                }
            },
            "category_system": {
                "type": self.category_system.type,
                "category_mapping": {
                    k: {
                        "category_main": v.category_main,
                        "category_sub": v.category_sub,
                        "tags": v.tags
                    }
                    for k, v in self.category_system.category_mapping.items()
                },
                "inference_prompt": self.category_system.inference_prompt
            },
            "data_cleaning_rules": {
                "exclude_transactions": self.data_cleaning_rules.exclude_transactions,
                "merchant_normalization": {
                    "enabled": self.data_cleaning_rules.merchant_normalization_enabled,
                    "mappings": self.data_cleaning_rules.merchant_mappings
                },
                "deduplication": {
                    "enabled": self.data_cleaning_rules.deduplication_enabled,
                    "match_fields": self.data_cleaning_rules.deduplication_match_fields,
                    "time_tolerance_seconds": self.data_cleaning_rules.time_tolerance_seconds
                }
            },
            "metadata": {
                "ai_model": self.ai_model,
                "confidence_threshold": self.confidence_threshold,
                "user_confirmed": self.user_confirmed,
                "notes": self.notes
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """
        从字典创建 UserProfile 对象（用于 JSON 反序列化）
        
        Args:
            data: 包含配置数据的字典
            
        Returns:
            UserProfile 对象
        """
        # 解析 source_files
        source_files = [
            SourceFileInfo(
                file_name=sf["file_name"],
                file_hash=sf["file_hash"],
                sample_rows=sf.get("sample_rows", 50)
            )
            for sf in data.get("source_files", [])
        ]
        
        # 解析 column_mapping
        cm_data = data.get("column_mapping", {})
        column_mapping = ColumnMapping(
            date_column=cm_data["date_column"],
            amount_column=cm_data["amount_column"],
            merchant_column=cm_data.get("merchant_column"),
            category_column=cm_data.get("category_column"),
            notes_column=cm_data.get("notes_column"),
            platform_column=cm_data.get("platform_column"),
            item_column=cm_data.get("item_column"),
            quantity_column=cm_data.get("quantity_column")
        )
        
        # 解析 parsing_strategy
        ps_data = data.get("parsing_strategy", {})
        me_data = ps_data.get("merchant_extraction", {})
        parsing_strategy = ParsingStrategy(
            mode=ps_data.get("mode", "standard"),
            date_format=ps_data.get("date_format", "%Y-%m-%d"),
            currency_default=ps_data.get("currency_default", "CNY"),
            merchant_extraction=MerchantExtraction(
                enabled=me_data.get("enabled", False),
                source=me_data.get("source", "column"),
                rules=me_data.get("rules", [])
            )
        )
        
        # 解析 category_system
        cs_data = data.get("category_system", {})
        category_mapping = {
            k: CategoryMapping(
                category_main=v["category_main"],
                category_sub=v.get("category_sub"),
                tags=v.get("tags", [])
            )
            for k, v in cs_data.get("category_mapping", {}).items()
        }
        category_system = CategorySystem(
            type=cs_data.get("type", "flat"),
            category_mapping=category_mapping,
            inference_prompt=cs_data.get("inference_prompt")
        )
        
        # 解析 data_cleaning_rules
        dcr_data = data.get("data_cleaning_rules", {})
        mn_data = dcr_data.get("merchant_normalization", {})
        dd_data = dcr_data.get("deduplication", {})
        data_cleaning_rules = DataCleaningRules(
            exclude_transactions=dcr_data.get("exclude_transactions", ["transfer", "repayment", "redpacket"]),
            merchant_normalization_enabled=mn_data.get("enabled", False),
            merchant_mappings=mn_data.get("mappings", {}),
            deduplication_enabled=dd_data.get("enabled", False),
            deduplication_match_fields=dd_data.get("match_fields", ["amount", "transaction_time", "merchant"]),
            time_tolerance_seconds=dd_data.get("time_tolerance_seconds", 0)
        )
        
        # 解析元数据
        metadata = data.get("metadata", {})
        
        return cls(
            user_id=data["user_id"],
            profile_version=data.get("profile_version", "2.0"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            source_files=source_files,
            column_mapping=column_mapping,
            parsing_strategy=parsing_strategy,
            category_system=category_system,
            data_cleaning_rules=data_cleaning_rules,
            ai_model=metadata.get("ai_model", "gpt-4o"),
            confidence_threshold=metadata.get("confidence_threshold", 0.8),
            user_confirmed=metadata.get("user_confirmed", False),
            notes=metadata.get("notes")
        )
