# UserProfile 配置协议 (AI Adapter Configuration Protocol)

> **版本**: v2.0  
> **创建日期**: 2025-12-07  
> **状态**: Draft for Review  
> **依赖**: [Standard_Data_Model.md](./Standard_Data_Model.md)  

---

## 1. 设计目标

### 核心问题

**如何让一个系统适配无限种用户数据格式，而不需要为每个用户写代码？**

### 解决方案

**让 AI 为每个用户生成一份"护照"（UserProfile），这份护照告诉系统：**

1. 这个用户的 Excel 里哪一列是金额、哪一列是日期。
2. 这个用户的"备注"列里混了哪些信息，需要怎么提取。
3. 这个用户的分类习惯是什么，如何映射到标准分类。

### 类比

* **传统软件**：程序员写死 `if column == "金额（元）"`，只能处理这一种格式。
* **AI 适配器**：AI 看到用户的列名是 `Cost`，自动生成 `amount_column: "Cost"`，系统读取配置就知道该用哪一列。

---

## 2. UserProfile 结构定义

### 2.1 完整 JSON Schema

```json
{
  "user_id": "string (UUID)",
  "profile_version": "2.0",
  "created_at": "ISO8601 timestamp",
  "source_files": [
    {
      "file_name": "string",
      "file_hash": "string (MD5)",
      "sample_rows": 50
    }
  ],
  
  "column_mapping": {
    "date_column": "string",
    "amount_column": "string",
    "merchant_column": "string | null",
    "category_column": "string | null",
    "notes_column": "string | null",
    "platform_column": "string | null",
    "item_column": "string | null",
    "quantity_column": "string | null"
  },
  
  "parsing_strategy": {
    "mode": "standard | mixed_notes | full_nlp",
    "date_format": "string (Python strptime format)",
    "currency_default": "string (ISO 4217)",
    "merchant_extraction": {
      "enabled": true | false,
      "source": "column | notes | ai_inference",
      "rules": [
        {
          "pattern": "regex | keyword",
          "action": "extract | map"
        }
      ]
    }
  },
  
  "category_system": {
    "type": "dimensional_split | flat | hierarchical",
    "category_mapping": {
      "原始分类": {
        "category_main": "string",
        "category_sub": "string | null",
        "tags": ["string"]
      }
    },
    "inference_prompt": "string (optional)"
  },
  
  "data_cleaning_rules": {
    "exclude_transactions": [
      "transfer", "repayment", "redpacket"
    ],
    "merchant_normalization": {
      "enabled": true | false,
      "mappings": {
        "瑞幸": "瑞幸咖啡",
        "luckin coffee": "瑞幸咖啡"
      }
    },
    "deduplication": {
      "enabled": true | false,
      "match_fields": ["amount", "date", "merchant"],
      "time_tolerance_seconds": 60
    }
  },
  
  "metadata": {
    "ai_model": "string (e.g., gpt-4, claude-3.5)",
    "confidence_threshold": 0.8,
    "user_confirmed": true | false,
    "notes": "string"
  }
}
```

---

## 3. 三种核心模式 (Parsing Strategy)

### 3.1 Mode: `standard` (标准模式)

**适用场景**：用户的 Excel 结构清晰，每个信息都有独立的列。

**示例**：

```csv
购买日期,金额（元）,商户,类别,备注
2025-03-15,37.68,瑞幸咖啡,餐饮,WildCard
```

**AI 生成的 UserProfile**：

```json
{
  "column_mapping": {
    "date_column": "购买日期",
    "amount_column": "金额（元）",
    "merchant_column": "商户",
    "category_column": "类别",
    "notes_column": "备注"
  },
  "parsing_strategy": {
    "mode": "standard",
    "date_format": "%Y年%m月%d日",
    "merchant_extraction": {
      "enabled": false,
      "source": "column"
    }
  }
}
```

**处理逻辑**：直接读取对应列，无需 AI 介入。

---

### 3.2 Mode: `mixed_notes` (混合备注模式)

**适用场景**：用户的"备注"列里混杂了商户、规格、原价等信息（你的情况）。

**示例**：

```csv
所购商品,金额（元）,购买日期,备注
二硫化硒洗发水,28.31,2025年2月23日,原价34.8
Open AI API充值,37.68,2025年2月23日,海南莱成玖
```

**AI 生成的 UserProfile**：

```json
{
  "column_mapping": {
    "date_column": "购买日期",
    "amount_column": "金额（元）",
    "item_column": "所购商品",
    "notes_column": "备注",
    "merchant_column": null
  },
  "parsing_strategy": {
    "mode": "mixed_notes",
    "merchant_extraction": {
      "enabled": true,
      "source": "notes",
      "rules": [
        {
          "pattern": "公司名|店铺名",
          "action": "extract_as_merchant"
        },
        {
          "pattern": "原价\\d+\\.\\d+",
          "action": "extract_as_metadata"
        }
      ]
    }
  }
}
```

**处理逻辑**：

1. 读取"备注"列。
2. AI 检测到"海南莱成玖"像商户名，提取到 `merchant` 字段。
3. AI 检测到"原价34.8"，提取为 `notes` 的一部分（或丢弃）。

---

### 3.3 Mode: `full_nlp` (全文提取模式)

**适用场景**：用户根本没有结构化表格，只有一列"描述"。

**示例**：

```csv
Content
今天在瑞幸花了37.68买咖啡
2月23号买洗发水28.31元
```

**AI 生成的 UserProfile**：

```json
{
  "column_mapping": {
    "date_column": null,
    "amount_column": null,
    "merchant_column": null,
    "notes_column": "Content"
  },
  "parsing_strategy": {
    "mode": "full_nlp",
    "merchant_extraction": {
      "enabled": true,
      "source": "ai_inference"
    }
  }
}
```

**处理逻辑**：

1. 将整行文本扔给 LLM。
2. LLM 提取：`date: 2月23号`, `amount: 28.31`, `merchant: 洗发水商家`, `item: 洗发水`。

---

## 4. 分类系统映射 (Category System)

### 4.1 Type: `dimensional_split` (维度拆解模式)

**问题**：用户的"女儿费用"既是对象，又当成了分类。

**AI 的解决方案**：

```json
{
  "category_system": {
    "type": "dimensional_split",
    "category_mapping": {
      "女儿费用": {
        "category_main": "未分类",
        "tags": ["女儿"]
      },
      "吃": {
        "category_main": "餐饮",
        "category_sub": null,
        "tags": []
      },
      "工作花销": {
        "category_main": "软件服务",
        "tags": ["工作"]
      }
    }
  }
}
```

**结果**：

* 原数据：`古茗奶茶, 17元, 女儿费用`
* 转换后：`category_main: "餐饮", tags: ["女儿"]`（AI 根据"古茗"推断是餐饮）

---

### 4.2 Type: `flat` (平面模式)

**场景**：用户的分类本身就很标准，直接映射即可。

```json
{
  "category_system": {
    "type": "flat",
    "category_mapping": {
      "食物": {
        "category_main": "餐饮",
        "category_sub": null,
        "tags": []
      },
      "交通": {
        "category_main": "交通出行",
        "category_sub": null,
        "tags": []
      }
    }
  }
}
```

---

### 4.3 Type: `hierarchical` (层级模式)

**场景**：用户的分类已经有层级（如"餐饮 > 咖啡"）。

```json
{
  "category_system": {
    "type": "hierarchical",
    "category_mapping": {
      "餐饮.咖啡": {
        "category_main": "餐饮",
        "category_sub": "咖啡",
        "tags": []
      }
    }
  }
}
```

---

## 5. AI 生成 UserProfile 的流程

### 输入

1. 用户上传的 CSV/Excel 文件。
2. 系统读取前 50 行作为样本。

### AI 分析任务

```text
[System Prompt]
你是一个数据结构分析专家。用户上传了一份财务账本，你需要分析其结构并生成 UserProfile JSON 配置。

[User Input]
文件名: 家庭账本0713.csv
样本数据 (前 10 行):
所购商品,数量,购买日期,金额（元）,类别,备注,购物平台
B超,,2025年1月6日,73.3,女儿费用,,卫生院
粉面馆,1份,2025年2月11日,20,吃,削骨肉盖码饭,线下
...

[Tasks]
1. 识别必需字段：日期、金额、商户/商品。
2. 检测"备注"列是否混杂了商户信息。
3. 分析"类别"列，判断是否存在维度混乱（如"女儿费用"）。
4. 生成 UserProfile JSON，包含：
   - column_mapping
   - parsing_strategy (选择 mode)
   - category_system (选择 type，生成 mapping)
5. 标注 confidence_score (0-1)，低于 0.8 的字段标红。

[Output Format]
返回完整的 UserProfile JSON。
```

### 输出示例 (针对你的数据)

```json
{
  "user_id": "user_a_20251207",
  "profile_version": "2.0",
  "created_at": "2025-12-07T15:00:00+08:00",
  
  "column_mapping": {
    "date_column": "购买日期",
    "amount_column": "金额（元）",
    "merchant_column": null,
    "category_column": "类别",
    "notes_column": "备注",
    "platform_column": "购物平台",
    "item_column": "所购商品",
    "quantity_column": "数量"
  },
  
  "parsing_strategy": {
    "mode": "mixed_notes",
    "date_format": "%Y年%m月%d日",
    "currency_default": "CNY",
    "merchant_extraction": {
      "enabled": true,
      "source": "notes",
      "rules": [
        {
          "pattern": ".*学校|.*医院|.*店",
          "action": "extract"
        }
      ]
    }
  },
  
  "category_system": {
    "type": "dimensional_split",
    "category_mapping": {
      "吃": {"category_main": "餐饮", "tags": []},
      "喝": {"category_main": "餐饮", "category_sub": "饮品", "tags": []},
      "女儿费用": {"category_main": "未分类", "tags": ["女儿"]},
      "工作花销": {"category_main": "软件服务", "tags": ["工作"]},
      "抽": {"category_main": "烟酒", "tags": []},
      "车": {"category_main": "交通出行", "tags": []},
      "猫": {"category_main": "宠物", "tags": []},
      "保险/医疗": {"category_main": "医疗健康", "tags": []},
      "水电气话费": {"category_main": "生活缴费", "tags": []},
      "生活用品": {"category_main": "日用品", "tags": []}
    },
    "inference_prompt": "根据 item_name 和 merchant 推断分类（如果 category 为空）"
  },
  
  "data_cleaning_rules": {
    "exclude_transactions": ["transfer", "repayment"],
    "merchant_normalization": {
      "enabled": true,
      "mappings": {
        "瑞幸": "瑞幸咖啡",
        "luckin coffee": "瑞幸咖啡",
        "元元": "元元早餐店"
      }
    },
    "deduplication": {
      "enabled": true,
      "match_fields": ["amount", "transaction_time", "merchant"],
      "time_tolerance_seconds": 0
    }
  },
  
  "metadata": {
    "ai_model": "gpt-4o",
    "confidence_threshold": 0.8,
    "user_confirmed": false,
    "notes": "检测到备注列混杂商户信息，已启用提取规则。分类存在维度混乱，已拆分为 category + tags。"
  }
}
```

---

## 6. 用户确认流程

### 6.1 AI 生成后，前端展示

```text
✅ 已识别您的账本结构：
  - 日期列: "购买日期"
  - 金额列: "金额（元）"
  - 商户信息: 从"备注"列提取

⚠️ 检测到以下问题：
  1. 您的"女儿费用"分类可能导致统计混乱
     建议: 拆分为"餐饮/教育"分类 + "女儿"标签
     [接受] [保持原样]
  
  2. 检测到商户名称不一致（如"瑞幸"/"luckin coffee"）
     建议: 统一为"瑞幸咖啡"
     [接受] [自定义]

[确认无误，开始导入] [手动调整配置]
```

### 6.2 用户调整

用户可以点击"手动调整配置"，修改 AI 生成的 JSON（通过 UI 表单，而非直接编辑 JSON）。

---

## 7. 与代码的对接

### Python 代码示例

```python
def process_user_data(file_path: str, user_profile: UserProfile):
    """
    根据 UserProfile 处理用户数据
    """
    df = pd.read_csv(file_path)
    
    # 1. 列映射
    date_col = user_profile.column_mapping.date_column
    amount_col = user_profile.column_mapping.amount_column
    
    # 2. 逐行转换
    records = []
    for _, row in df.iterrows():
        record = StandardRecord(
            id=str(uuid4()),
            transaction_time=parse_date(row[date_col], user_profile.parsing_strategy.date_format),
            amount=Decimal(row[amount_col]),
            ...
        )
        
        # 3. 应用清洗规则
        if user_profile.parsing_strategy.merchant_extraction.enabled:
            record.merchant = extract_merchant(row, user_profile.parsing_strategy.merchant_extraction.rules)
        
        # 4. 映射分类
        original_category = row.get(user_profile.column_mapping.category_column)
        mapped = user_profile.category_system.category_mapping.get(original_category)
        if mapped:
            record.category_main = mapped.category_main
            record.tags = mapped.tags
        
        records.append(record)
    
    return records
```

---

## 8. 总结

**UserProfile 是连接"用户数据"与"标准模型"的桥梁。**

* **输入**：用户的千奇百怪的 Excel/CSV。
* **输出**：统一的 `StandardRecord` 列表。
* **核心**：AI 自动生成配置，用户确认后保存，后续导入都复用这份配置。

**下一步**：实现 Python 类来解析和应用 UserProfile。
