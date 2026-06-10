# AI_module.md

# AI 辅助数据分析与结果解释模块设计文档

## 1. 模块定位

本模块用于在“基于 OPNs-SVM/SVR 的 IgAN 病理标签预测与 AI 辅助分析系统”中引入大语言模型能力，使系统不仅能够完成数据上传、模型训练和预测，还能够对数据状态、字段含义、模型训练结果、预测结果和实验报告进行智能化分析。

AI 模块的定位是：

```text
AI 大模型负责辅助理解、分析、解释和生成报告。
OPNs-SVM/SVR 负责核心预测建模。
用户负责最终确认字段处理、模型配置和结果使用。
系统负责隐私保护、脱敏、权限控制和日志审计。
```

AI 模块不得替代医学专业判断，不得输出临床诊断、治疗建议或用药建议。所有 AI 输出均应限定为科研分析、模型验证和结果解释。

---

## 2. 设计边界

### 2.1 允许 AI 完成的任务

AI 可以用于：

```text
1. 数据集状态分析。
2. 数据集来源与字段背景分析。
3. 数据清洗建议。
4. 隐私风险提示。
5. 字段处理建议。
6. 特征工程建议。
7. 模型训练配置建议。
8. OPNs 特征配对解释。
9. 超参数初始范围建议。
10. 模型训练结果分析。
11. 模型失效与错误样本分析。
12. 单病例预测结果说明。
13. 批量预测结果分析。
14. 图表解读。
15. 模型可解释性摘要。
16. 实验报告生成。
17. 数据集问答。
18. 模型结果问答。
19. 系统操作向导。
20. 异常报错解释。
```

### 2.2 禁止 AI 完成的任务

AI 不得用于：

```text
1. 输出临床诊断结论。
2. 输出治疗建议。
3. 输出用药建议。
4. 判断患者是否需要某种临床处置。
5. 直接读取未经脱敏的完整医疗原始数据。
6. 自动删除字段或自动修改训练配置。
7. 自动替用户确认隐私风险。
8. 将统计相关性解释为医学因果关系。
9. 根据单个患者预测结果作出医学结论。
```

所有医学相关输出必须包含以下声明：

```text
本系统预测结果和 AI 分析内容仅用于科研分析和模型验证，不作为临床诊断、治疗决策或用药依据。实际医学判断应由具有资质的临床医生结合完整病史、检查结果和病理资料完成。
```

---

## 3. 总体可行性分析

### 3.1 技术可行性

本系统已经规划了数据集上传、数据预览、字段统计、模型训练、模型评估和预测结果保存等基础能力。AI 模块可以基于这些结构化信息生成自然语言分析，不需要直接读取完整原始数据。

推荐数据流如下：

```text
用户上传数据集
    ↓
后端读取 CSV/XLSX
    ↓
pandas 生成数据摘要
    ↓
隐私扫描模块识别高风险字段
    ↓
脱敏或用户确认
    ↓
构造 AI 输入上下文
    ↓
AI 生成分析文本
    ↓
输出校验模块检查是否包含禁止内容
    ↓
前端展示、保存、导出
```

### 3.2 业务可行性

该模块适合当前系统，原因如下：

```text
1. 医学表格数据字段较多，用户需要理解数据质量和字段含义。
2. IgAN 的 M、E、S、T、C 标签具有明确医学背景，单纯展示指标不足以支撑结果分析。
3. OPNs-SVM/SVR 的性能变化需要结合特征配对、标签分布和数据质量进行解释。
4. AI 可以将模型指标、图表和实验结果转化为可读性更强的分析文本。
5. AI 可以辅助生成专业实践报告和论文实验结果分析初稿。
```

### 3.3 风险可控性

主要风险包括：

```text
1. 医疗隐私数据泄露。
2. AI 生成未经验证的医学结论。
3. 用户误以为系统具备临床诊断能力。
4. AI 对字段作用或模型结果进行过度解释。
```

控制策略：

```text
1. 默认不向 AI 发送完整原始数据。
2. 默认仅发送统计摘要、字段摘要、模型指标和脱敏样本。
3. 对姓名、身份证号、住院号、手机号、精确日期等字段进行识别和屏蔽。
4. 高风险字段必须经过用户确认后才能进入 AI 上下文。
5. AI 输出必须通过安全校验。
6. AI 输出必须包含科研用途声明。
7. AI 建议只能作为参考，最终配置由用户确认。
8. 保存隐私确认记录和 AI 请求记录，便于审计。
```

---

## 4. AI 应用场景总览

| 优先级 | 应用场景         | 功能价值                       | 是否进入 MVP |
| --- | ------------ | -------------------------- | -------- |
| 高   | AI 数据集状态分析   | 上传后自动分析数据规模、缺失值、标签分布、类别不平衡 | 是        |
| 高   | AI 隐私风险扫描    | 识别姓名、住院号、手机号、唯一标识符等敏感字段    | 是        |
| 高   | AI 字段分析      | 判断字段是否建议保留、忽略、脱敏、填补、标准化    | 是        |
| 高   | AI 模型训练配置建议  | 推荐任务类型、目标变量、特征、评价指标、配对方式   | 是        |
| 高   | AI 模型结果分析    | 结合指标、标签分布和背景解释模型表现         | 是        |
| 高   | AI 预测结果说明    | 解释单病例或批量预测结果的不确定性          | 是        |
| 中   | AI OPNs 配对解释 | 解释特征对、配对策略和 OPNs 性能变化      | 建议       |
| 中   | AI 特征工程助手    | 结合字段含义和统计特征给出工程建议          | 建议       |
| 中   | AI 错误样本分析    | 分析误分类样本和模型失效模式             | 建议       |
| 中   | AI 图表解读      | 对 ECharts 图表生成自然语言说明       | 建议       |
| 中   | AI 报告生成      | 生成数据分析报告、模型报告、预测报告         | 建议       |
| 低   | AI 数据集问答     | 用户围绕数据集进行自然语言提问            | 可选       |
| 低   | AI 模型问答      | 用户围绕模型结果进行自然语言提问           | 可选       |
| 低   | AI 操作向导      | 辅助用户理解系统操作                 | 可选       |
| 低   | AI 异常解释      | 将技术错误转换为用户可读说明             | 可选       |

MVP 阶段建议优先实现：

```text
1. AI 数据集状态分析
2. AI 隐私风险扫描
3. AI 字段分析
4. AI 模型训练配置建议
5. AI 模型结果分析
6. AI 预测结果说明
```

增强阶段再实现：

```text
1. AI OPNs 配对解释
2. AI 错误样本分析
3. AI 图表解读
4. AI 报告生成
5. AI 数据集问答
6. AI 模型问答
```

---

## 5. AI 数据集状态分析

### 5.1 功能目标

用户上传数据集后，AI 根据后端生成的数据摘要，对数据集当前状态进行科学分析。

### 5.2 输入信息

AI 不接收完整原始数据，只接收结构化摘要。

示例：

```json
{
  "dataset_name": "IgAN Dataset",
  "task_type": "multi_output_classification",
  "sample_count": 312,
  "feature_count": 18,
  "target_columns": ["M", "E", "S", "T", "C"],
  "numeric_columns": ["age", "scr", "egfr", "proteinuria"],
  "categorical_columns": ["sex"],
  "missing_summary": {
    "albumin": {"missing_count": 26, "missing_rate": 0.083},
    "uric_acid": {"missing_count": 18, "missing_rate": 0.058}
  },
  "label_distribution": {
    "M": {"M0": 180, "M1": 132},
    "E": {"E0": 260, "E1": 52},
    "S": {"S0": 190, "S1": 122},
    "T": {"T0": 220, "T1": 70, "T2": 22},
    "C": {"C0": 210, "C1": 80, "C2": 22}
  },
  "privacy_risk_level": "medium",
  "de_identification_status": "summary_only"
}
```

### 5.3 输出内容

AI 应输出：

```text
1. 数据规模说明。
2. 字段类型说明。
3. 缺失值情况说明。
4. 标签分布说明。
5. 类别不平衡风险。
6. 建模前处理建议。
7. 适合的评价指标建议。
8. 科研用途声明。
```

### 5.4 页面入口

```text
/datasets/:id/profile
/ai/dataset-analysis/:datasetId
```

### 5.5 后端接口

```text
POST /api/ai/dataset-analysis/{dataset_id}
GET  /api/ai/dataset-analysis/{dataset_id}
```

---

## 6. AI 数据集来源与字段背景分析

### 6.1 功能目标

用户可以补充数据集来源、采集背景、字段含义、目标标签含义。AI 在后续分析中结合这些背景信息，避免只做机械的指标解释。

### 6.2 用户可填写内容

```text
1. 数据集来源。
2. 数据采集时间范围。
3. 数据采集机构类型。
4. 入组标准。
5. 排除标准。
6. 字段含义。
7. 目标变量含义。
8. 数据使用限制。
```

### 6.3 示例

```json
{
  "dataset_source": "某院 IgA 肾病患者回顾性数据",
  "scenario_description": "用于根据临床指标预测病理 MEST-C 标签",
  "feature_descriptions": {
    "scr": "血肌酐，反映肾功能状态",
    "egfr": "估算肾小球滤过率，反映肾功能水平",
    "proteinuria": "尿蛋白水平，常用于评估疾病活动和预后风险",
    "albumin": "血清白蛋白，可能反映营养状态和蛋白丢失"
  },
  "target_descriptions": {
    "M": "系膜细胞增生",
    "E": "毛细血管内增生",
    "S": "节段硬化",
    "T": "肾小管萎缩或间质纤维化",
    "C": "新月体"
  }
}
```

### 6.4 数据库建议

新增表：

```text
dataset_contexts
- id
- dataset_id
- user_id
- dataset_source
- scenario_description
- inclusion_criteria
- exclusion_criteria
- feature_descriptions
- target_descriptions
- usage_notes
- created_at
- updated_at
```

### 6.5 后端接口

```text
POST /api/datasets/{dataset_id}/context
GET  /api/datasets/{dataset_id}/context
PUT  /api/datasets/{dataset_id}/context
```

---

## 7. AI 数据清洗助手

### 7.1 功能目标

AI 根据缺失值、异常值、字段类型和隐私风险，对数据清洗提出建议。

### 7.2 可分析内容

```text
1. 哪些字段缺失率过高。
2. 哪些字段可能是唯一标识符。
3. 哪些字段需要标准化。
4. 哪些字段需要类别编码。
5. 哪些字段异常值较多。
6. 哪些字段可能存在数据泄漏。
7. 缺失值填补策略建议。
```

### 7.3 示例输出

```text
patient_id 字段唯一值比例为 100%，疑似患者唯一标识符，不建议参与模型训练，也不应发送给外部 AI 模型。albumin 字段缺失率为 8.3%，可考虑使用中位数填补。proteinuria 字段存在极端值，建议检查是否存在录入错误，或在建模前进行截尾处理。
```

---

## 8. AI 字段分析与特征处理建议

### 8.1 功能目标

AI 根据字段统计、字段含义、目标变量、隐私扫描结果和相关性摘要，对每个字段给出处理建议。

### 8.2 建议类型

```text
keep
ignore
remove
de_identify
impute_and_keep
standardize_and_keep
encode_and_keep
check_for_leakage
manual_review
```

### 8.3 输出格式

```json
{
  "feature_recommendations": [
    {
      "field": "patient_id",
      "recommendation": "remove",
      "reason": "该字段疑似患者唯一标识符，不应参与模型训练，也不应发送给外部 AI 模型。",
      "risk_level": "high",
      "requires_user_confirmation": true
    },
    {
      "field": "egfr",
      "recommendation": "standardize_and_keep",
      "reason": "该字段为连续数值型指标，可能对 IgAN 病理标签预测具有建模价值，建议标准化后参与训练。",
      "risk_level": "medium",
      "requires_user_confirmation": false
    },
    {
      "field": "albumin",
      "recommendation": "impute_and_keep",
      "reason": "该字段存在一定缺失，但缺失比例未超过预设阈值，可考虑中位数填补后参与建模。",
      "risk_level": "low",
      "requires_user_confirmation": true
    }
  ],
  "global_recommendations": [
    "建议使用 F1-score 和 Recall 评价类别不平衡标签。",
    "建议训练前对连续变量进行标准化。",
    "建议排除患者编号、姓名、联系方式等身份标识字段。"
  ],
  "disclaimer": "本分析仅用于科研分析和模型验证，不作为临床诊断、治疗决策或用药依据。"
}
```

### 8.4 用户确认要求

AI 只能给出建议，不能自动删除字段、忽略字段或修改训练配置。所有字段处理必须由用户确认。

### 8.5 后端接口

```text
POST /api/ai/field-analysis/{dataset_id}
GET  /api/ai/field-analysis/{dataset_id}
POST /api/datasets/{dataset_id}/feature-config/confirm
```

---

## 9. AI 特征工程助手

### 9.1 功能目标

AI 结合字段含义、数据分布和目标变量，为特征工程提供建议。

### 9.2 可实现内容

```text
1. 根据字段含义建议哪些字段适合保留。
2. 根据字段类型建议编码方式。
3. 根据字段统计建议是否标准化。
4. 根据相关性建议是否存在冗余字段。
5. 根据目标变量建议优先关注哪些特征。
6. 根据 OPNs 配对结果解释特征对的潜在建模意义。
```

### 9.3 示例输出

```text
egfr 与 scr 均与肾功能状态相关，二者可能存在一定冗余，但也可能从不同角度反映肾功能。若使用 OPNs 特征配对，可进一步观察 egfr-scr、egfr*scr 等结构特征是否改善模型表现。该判断仅表示建模层面的可能性，不代表医学因果关系。
```

---

## 10. AI OPNs 配对解释模块

### 10.1 功能目标

该模块用于强化系统与毕业论文的关联。AI 结合 OPNs 配对方式、特征对、模型指标和基线对比，解释 OPNs 特征构造可能带来的影响。

### 10.2 可实现内容

```text
1. 解释当前使用的配对方式。
2. 分析某些特征对为什么可能具有建模意义。
3. 对比 adjacent、random、correlation_greedy 配对结果。
4. 解释 OPNs-SVM 相对标准 SVM 提升或下降的可能原因。
5. 生成适合写入专业实践报告的分析文本。
```

### 10.3 示例输出

```text
当前模型采用相关性贪心配对方式。该方式倾向于将与目标变量关联较强且彼此冗余较低的特征组成特征对，因此可能增强模型对互补信息的利用能力。若 OPNs-SVM 在 T 标签上优于标准 SVM，可能说明结构特征在该标签预测中提供了额外的信息表达。但该结论仍需结合交叉验证和外部数据集验证。
```

### 10.4 后端接口

```text
POST /api/ai/opns-pairing-analysis/{model_id}
GET  /api/ai/opns-pairing-analysis/{model_id}
```

---

## 11. AI 模型训练配置建议

### 11.1 功能目标

AI 根据数据集状态、字段分析结果和目标变量信息，给出训练配置建议。

### 11.2 建议范围

```text
1. 任务类型选择。
2. 目标变量选择。
3. 输入特征选择。
4. 缺失值处理方式。
5. 标准化设置。
6. 编码方式。
7. 训练测试划分比例。
8. 类别不平衡处理方式。
9. OPNs 配对方式。
10. SVM/SVR 核函数选择。
11. 评价指标选择。
```

### 11.3 示例输出

```json
{
  "task_suggestion": {
    "task_type": "multi_output_classification",
    "target_columns": ["M", "E", "S", "T", "C"],
    "reason": "M/E/S/T/C 均为分类标签，应作为多输出分类任务处理。"
  },
  "feature_suggestion": {
    "include": ["age", "scr", "egfr", "proteinuria", "albumin"],
    "exclude": ["patient_id", "name"],
    "manual_review": ["visit_date"]
  },
  "preprocessing_suggestion": {
    "missing_strategy": "median_for_numeric",
    "scaling": true,
    "encoding": "label_encoding_or_one_hot"
  },
  "model_suggestion": {
    "primary_model": "OPNs-SVM",
    "baseline_models": ["standard SVM", "RandomForestClassifier"],
    "kernel": "rbf",
    "pairing_method": "correlation_greedy",
    "metrics": ["accuracy", "precision", "recall", "f1"]
  },
  "warnings": [
    "E1、T2、C2 样本量较少，建议重点观察 Recall 和 F1-score。",
    "不要将患者编号或病理标签派生字段作为输入特征。"
  ],
  "disclaimer": "本分析仅用于科研分析和模型验证，不作为临床诊断、治疗决策或用药依据。"
}
```

### 11.4 后端接口

```text
POST /api/ai/training-config-suggestion/{dataset_id}
GET  /api/ai/training-config-suggestion/{dataset_id}
```

### 11.5 前端交互要求

前端可提供“应用 AI 建议”按钮，但必须满足：

```text
1. 用户点击确认后才应用建议。
2. AI 建议不得直接修改训练配置。
3. 被忽略字段、高风险字段、疑似泄漏字段必须突出显示。
```

---

## 12. AI 超参数建议模块

### 12.1 功能目标

AI 提供 SVM/SVR 初始参数范围建议，但不替代网格搜索或交叉验证。

### 12.2 可建议内容

```text
1. SVM/SVR 核函数选择。
2. C 参数搜索范围。
3. gamma 参数搜索范围。
4. epsilon 参数搜索范围。
5. 是否启用 class_weight。
6. 是否使用交叉验证。
7. 是否需要分层划分。
```

### 12.3 示例输出

```text
当前数据样本量较小，建议优先比较 linear 和 rbf 核函数。对于 rbf 核，可从 C={0.1,1,10,100}，gamma={scale,0.01,0.1,1} 开始搜索。若类别不平衡明显，可启用 class_weight='balanced' 作为对照实验。
```

### 12.4 注意事项

```text
1. AI 只给出初始搜索建议。
2. 最终参数应由验证集、交叉验证或测试集结果决定。
3. AI 不应宣称某组参数必然最优。
```

---

## 13. AI 模型结果分析

### 13.1 功能目标

模型训练完成后，AI 结合数据集背景、字段含义、标签分布、模型指标、基线模型和 OPNs 配置，生成模型结果分析。

### 13.2 输入信息

```json
{
  "dataset_context": {
    "scenario_description": "用于根据临床指标预测 IgAN MEST-C 病理标签",
    "target_descriptions": {
      "M": "系膜细胞增生",
      "E": "毛细血管内增生",
      "S": "节段硬化",
      "T": "肾小管萎缩或间质纤维化",
      "C": "新月体"
    }
  },
  "model_info": {
    "algorithm": "OPNs-SVM",
    "pairing_method": "correlation_greedy",
    "kernel": "rbf",
    "feature_columns": ["age", "scr", "egfr", "proteinuria", "albumin"],
    "target_columns": ["M", "E", "S", "T", "C"]
  },
  "metrics": {
    "M": {"accuracy": 0.82, "precision": 0.80, "recall": 0.78, "f1": 0.79},
    "E": {"accuracy": 0.76, "precision": 0.73, "recall": 0.65, "f1": 0.69},
    "T": {"accuracy": 0.84, "precision": 0.81, "recall": 0.78, "f1": 0.79}
  },
  "baseline_comparison": {
    "standard_svm": {
      "M": {"f1": 0.74},
      "E": {"f1": 0.67},
      "T": {"f1": 0.75}
    }
  },
  "label_distribution": {
    "E": {"E0": 260, "E1": 52},
    "T": {"T0": 220, "T1": 70, "T2": 22}
  }
}
```

### 13.3 输出内容

AI 应输出：

```text
1. 总体模型表现。
2. 不同标签表现差异。
3. 类别不平衡对指标的影响。
4. OPNs 特征构造可能带来的影响。
5. 与标准 SVM 或其他基线模型的差异。
6. 模型局限性。
7. 后续改进建议。
8. 科研用途声明。
```

### 13.4 后端接口

```text
POST /api/ai/model-analysis/{model_id}
GET  /api/ai/model-analysis/{model_id}
```

---

## 14. AI 模型失效与错误样本分析

### 14.1 功能目标

该模块用于分析模型预测错误的样本和错误模式，比普通指标解释更有研究价值。

### 14.2 可分析内容

```text
1. 哪些标签最容易预测错误。
2. 哪些类别之间最容易混淆。
3. 错误样本是否集中在某些特征区间。
4. 少数类是否识别不足。
5. 预测概率是否集中在低置信区间。
6. 是否存在训练集与测试集分布差异。
```

### 14.3 示例输出

```text
当前模型在 C0 与 C1 之间存在较多混淆，且错误样本主要集中在预测概率 0.45-0.60 区间，说明模型对 C 标签边界样本区分能力有限。建议进一步检查 C 标签样本分布，并尝试类别不平衡处理或引入更多与该标签相关的特征。
```

### 14.4 后端接口

```text
POST /api/ai/error-analysis/{model_id}
GET  /api/ai/error-analysis/{model_id}
```

---

## 15. AI 可解释性摘要模块

### 15.1 功能目标

后端可先计算传统可解释性结果，例如特征重要性、置换重要性、SHAP 结果。AI 再基于这些结果生成自然语言摘要。

### 15.2 可使用输入

```text
1. permutation importance。
2. feature importance。
3. SHAP summary，可选。
4. OPNs 特征重要性。
5. 标签级别特征贡献。
```

### 15.3 示例输出

```text
在 M 标签预测中，proteinuria、egfr 和 scr 的置换重要性较高，说明这些字段对当前模型输出影响较大。但该结果仅反映模型在当前数据集中的统计依赖关系，不能解释为这些指标对 M 标签存在因果作用。
```

### 15.4 后端接口

```text
POST /api/ai/explainability-summary/{model_id}
GET  /api/ai/explainability-summary/{model_id}
```

---

## 16. AI 预测结果分析

### 16.1 功能目标

AI 对单病例或批量预测结果进行分析。分析内容不应只复述预测标签，而应结合数据集背景、预测概率、模型整体性能和不确定性进行说明。

### 16.2 单病例输入摘要

```json
{
  "scenario": "IgAN MEST-C 病理标签预测",
  "input_features_summary": {
    "age": 35,
    "scr": 86.2,
    "egfr": 92.5,
    "proteinuria": 1.4,
    "albumin": 39.1
  },
  "prediction": {
    "M": {"label": "M1", "probability": 0.76},
    "E": {"label": "E0", "probability": 0.82},
    "S": {"label": "S1", "probability": 0.69},
    "T": {"label": "T0", "probability": 0.71},
    "C": {"label": "C1", "probability": 0.64}
  },
  "model_metrics_summary": {
    "M": {"f1": 0.79},
    "E": {"f1": 0.69},
    "C": {"f1": 0.68}
  }
}
```

### 16.3 输出内容

AI 应输出：

```text
1. 各标签预测结果说明。
2. 哪些标签置信度较高。
3. 哪些标签不确定性较大。
4. 结合模型整体性能说明预测可信边界。
5. 结合字段背景说明模型可能依赖的输入信息。
6. 科研用途声明。
```

### 16.4 示例输出风格

```text
模型对该样本的 E 标签预测为 E0，预测概率较高，说明在当前模型和输入特征条件下，该标签输出较稳定。相比之下，C 标签预测为 C1，但预测概率较低，同时模型在 C 标签上的历史 F1-score 也较低，因此该标签应被视为不确定性较高的预测结果。

该分析仅基于当前模型、输入字段和训练数据分布生成，不能作为临床诊断或治疗依据。
```

### 16.5 后端接口

```text
POST /api/ai/prediction-explanation/{prediction_job_id}
GET  /api/ai/prediction-explanation/{prediction_job_id}
```

---

## 17. AI 批量预测结果分析

### 17.1 功能目标

对批量预测结果进行整体分析，辅助用户理解预测分布和模型偏向。

### 17.2 可分析内容

```text
1. 批量预测样本数量。
2. 各标签预测分布。
3. 是否明显偏向某一类别。
4. 低置信度样本比例。
5. 需要人工复核的样本范围。
6. 与模型整体指标的关系。
```

### 17.3 后端接口

```text
POST /api/ai/batch-prediction-analysis/{prediction_job_id}
GET  /api/ai/batch-prediction-analysis/{prediction_job_id}
```

---

## 18. AI 图表解读模块

### 18.1 功能目标

对 ECharts 图表对应的结构化数据进行自然语言解读。

### 18.2 可解读图表

```text
1. 标签分布图。
2. 缺失值柱状图。
3. 相关性热力图。
4. 混淆矩阵。
5. ROC 曲线。
6. 模型指标对比图。
7. 真实值-预测值散点图。
8. 残差图。
```

### 18.3 示例输出

```text
从标签分布图看，E 标签中 E0 样本明显多于 E1，说明该标签存在类别不平衡。若模型在 E1 上 Recall 较低，应避免仅依据 Accuracy 判断模型效果。
```

### 18.4 后端接口

```text
POST /api/ai/chart-interpretation
```

---

## 19. AI OPNs-SVR 回归结果分析

### 19.1 功能目标

对 OPNs-SVR 回归模型的 MAE、RMSE、R2、残差和真实值-预测值分布进行分析。

### 19.2 分析内容

```text
1. MAE、RMSE、R2 的含义。
2. OPNs-SVR 与标准 SVR 的差异。
3. 残差分布是否存在明显偏差。
4. 是否存在极端误差样本。
5. 模型适用和不适用场景。
6. 后续改进方向。
```

### 19.3 后端接口

```text
POST /api/ai/regression-analysis/{model_id}
GET  /api/ai/regression-analysis/{model_id}
```

---

## 20. AI 报告生成模块

### 20.1 功能目标

AI 根据数据集状态、字段处理、模型训练配置、模型指标、图表和预测结果，生成实验报告或专业实践报告片段。

### 20.2 可生成报告类型

```text
1. 数据集分析报告。
2. 字段处理建议报告。
3. 模型训练报告。
4. 模型对比报告。
5. 单病例预测说明。
6. 批量预测结果报告。
7. 专业实践系统运行报告。
```

### 20.3 推荐报告结构

```text
1. 数据集概况
2. 数据预处理
3. 隐私保护与脱敏处理
4. OPNs 特征构造
5. 模型训练配置
6. 模型评估结果
7. 与基线模型对比
8. 预测结果分析
9. 局限性
10. 科研用途声明
```

### 20.4 后端接口

```text
POST /api/ai/report/{model_id}
GET  /api/ai/report/{model_id}
GET  /api/ai/report/{report_id}/download
```

---

## 21. AI 数据集问答模块

### 21.1 功能目标

用户可以围绕当前数据集提问，AI 基于数据摘要、字段说明和隐私处理状态回答。

### 21.2 可支持问题

```text
1. 这个数据集缺失值严重吗？
2. 哪些字段可能不适合训练？
3. M、E、S、T、C 标签是否平衡？
4. 这个数据集适合用 OPNs-SVM 吗？
5. 是否适合做 OPNs-SVR？
6. 哪些字段可能存在隐私风险？
```

### 21.3 实现要求

```text
1. AI 只能访问当前用户有权限的数据摘要。
2. AI 不能访问其他用户数据。
3. AI 默认不访问完整原始数据。
4. AI 回答必须包含不确定性说明。
```

### 21.4 后端接口

```text
POST /api/ai/dataset-chat/{dataset_id}
```

---

## 22. AI 模型问答模块

### 22.1 功能目标

用户可以围绕训练模型和实验结果提问。

### 22.2 可支持问题

```text
1. 为什么 E 标签 F1-score 较低？
2. OPNs-SVM 相比标准 SVM 是否有提升？
3. 哪个标签预测效果最好？
4. 模型是否可能过拟合？
5. 下一步应该怎么改进实验？
6. 为什么 OPNs-SVM 没有明显优于标准 SVM？
```

### 22.3 后端输入上下文

```text
1. 模型参数。
2. 训练测试划分。
3. 标签分布。
4. 模型指标。
5. 基线对比。
6. 混淆矩阵摘要。
7. 错误样本摘要。
8. OPNs 配置。
```

### 22.4 后端接口

```text
POST /api/ai/model-chat/{model_id}
```

---

## 23. AI 操作向导模块

### 23.1 功能目标

AI 引导用户完成系统操作。

### 23.2 可支持问题

```text
1. 如何上传数据集？
2. 如何训练 OPNs-SVM？
3. 如何进行单病例预测？
4. 为什么需要填写字段含义？
5. 为什么不能上传姓名和住院号？
6. 如何查看模型评估结果？
```

### 23.3 优先级

该模块不是 MVP 必须项，可作为增强功能。

---

## 24. AI 异常解释模块

### 24.1 功能目标

当系统出现错误时，AI 将技术错误转换为用户可理解的说明。

### 24.2 示例

原始错误：

```text
Missing required columns: egfr, proteinuria
```

AI 输出：

```text
当前批量预测失败的原因是上传文件缺少模型训练时使用的 egfr 和 proteinuria 字段。请检查文件表头，确保包含模型所需的全部输入字段后重新上传。
```

### 24.3 后端接口

```text
POST /api/ai/error-explanation
```

---

## 25. 医疗隐私数据管理设计

### 25.1 字段隐私分类

系统应将字段分为四类：

```text
1. 直接身份标识符。
2. 准身份标识符。
3. 敏感医学字段。
4. 普通建模字段。
```

### 25.2 直接身份标识符

包括但不限于：

```text
姓名
身份证号
手机号
住院号
门诊号
病案号
医保号
详细地址
邮箱
精确联系方式
医生签名
医院内部编号
```

处理策略：

```text
1. 默认不参与建模。
2. 默认不发送给 AI。
3. 上传后提示用户删除、忽略或脱敏。
```

### 25.3 准身份标识符

包括但不限于：

```text
出生日期
年龄
性别
就诊日期
入院日期
出院日期
医院名称
地区
极端年龄
极端实验室指标组合
```

处理策略：

```text
1. 可参与建模，但发送给 AI 前应优先摘要化。
2. 日期建议转换为年龄、间隔天数或年份区间。
3. 年龄可按区间处理，如 30-39。
4. 地区可降低精度，如省级或市级。
```

### 25.4 敏感医学字段

包括但不限于：

```text
诊断
病理结果
实验室检查
影像结果
用药信息
治疗方案
病程记录
遗传信息
感染状态
生育相关信息
心理精神状态
```

处理策略：

```text
1. 可用于科研建模，但必须有明确用途。
2. 发送给 AI 前优先使用统计摘要。
3. 不得将完整患者级敏感信息直接发送给外部模型。
```

### 25.5 普通建模字段

包括：

```text
已脱敏后的数值特征
标准化后的统计特征
聚合后的标签分布
模型评估指标
特征重要性结果
相关性矩阵
```

处理策略：

```text
1. 可用于 AI 分析。
2. 仍需避免反推出单个患者。
```

---

## 26. 脱敏策略

系统应支持以下脱敏方式：

```text
1. 删除字段。
2. 字段忽略。
3. 标识符哈希化。
4. 日期泛化。
5. 年龄分箱。
6. 地区泛化。
7. 极端值截尾。
8. 仅传输统计摘要。
9. 仅传输脱敏样本。
10. 用户手动确认后传输。
```

推荐默认策略：

```text
1. AI 数据集分析只发送统计摘要，不发送原始行数据。
2. AI 字段分析发送字段名、字段类型、缺失率、唯一值数量、统计量和字段说明。
3. AI 模型结果分析发送模型指标、目标变量分布、特征列表和数据背景。
4. AI 单病例预测说明默认只发送输入字段摘要和预测结果。
5. 姓名、住院号、身份证号、手机号等字段永不默认发送给 AI。
```

---

## 27. 隐私扫描与用户确认机制

### 27.1 高风险触发条件

```text
1. 字段名包含 name、姓名、id、身份证、phone、mobile、tel、住院号、门诊号、病案号、address、地址、email、医保号 等。
2. 字段唯一值比例过高，疑似唯一标识符。
3. 字段为详细日期，且与医疗事件相关。
4. 字段包含长文本病程记录。
5. 字段包含自由文本备注。
```

### 27.2 确认弹窗内容

```text
系统检测到当前数据集中可能包含身份标识或敏感医疗信息。为降低隐私泄露风险，建议在调用 AI 分析前进行脱敏或仅发送统计摘要。

请选择处理方式：
1. 仅发送统计摘要，推荐。
2. 自动脱敏后发送字段摘要。
3. 手动选择可发送字段。
4. 取消 AI 分析。
```

### 27.3 用户确认记录

新增表：

```text
ai_privacy_confirmations
- id
- user_id
- dataset_id
- action_type
- risk_fields
- selected_strategy
- confirmed_at
```

`selected_strategy` 可选值：

```text
summary_only
auto_deidentify
manual_field_selection
cancel
```

---

## 28. AI 请求日志与审计

### 28.1 设计目标

保存 AI 分析过程的必要记录，便于复现实验、问题追踪和专业实践展示。

### 28.2 数据库表

```text
ai_request_logs
- id
- user_id
- dataset_id
- model_id
- prediction_job_id
- prompt_type
- privacy_level
- de_identification_strategy
- input_summary_hash
- output_text
- created_at
```

说明：

```text
1. input_summary_hash 用于记录输入摘要版本，不保存完整敏感输入。
2. output_text 保存 AI 输出文本。
3. 不保存未经脱敏的患者级原始数据。
```

---

## 29. 后端架构设计

### 29.1 新增目录

```text
backend/app/ai/
├── __init__.py
├── ai_client.py
├── mock_ai_client.py
├── prompt_templates.py
├── privacy_guard.py
├── context_builder.py
├── response_validator.py
└── output_parser.py
```

### 29.2 文件职责

```text
ai_client.py
- 调用外部大模型 API。

mock_ai_client.py
- 在无 API Key 情况下使用模板生成分析文本。

prompt_templates.py
- 存放所有提示词模板。

privacy_guard.py
- 负责敏感字段检测、脱敏、用户确认状态检查。

context_builder.py
- 从数据库、数据集统计、模型指标中构造 AI 输入上下文。

response_validator.py
- 检查 AI 输出是否包含禁止内容。

output_parser.py
- 解析 AI 返回的 JSON 或 Markdown 文本。
```

### 29.3 AI 服务类

```python
class AIAnalysisService:
    def analyze_dataset(self, dataset_id: int, user_id: int) -> str:
        pass

    def analyze_fields(self, dataset_id: int, user_id: int) -> dict:
        pass

    def suggest_training_config(self, dataset_id: int, user_id: int) -> dict:
        pass

    def analyze_opns_pairing(self, model_id: int, user_id: int) -> str:
        pass

    def analyze_model_result(self, model_id: int, user_id: int) -> str:
        pass

    def analyze_errors(self, model_id: int, user_id: int) -> str:
        pass

    def explain_prediction(self, prediction_job_id: int, user_id: int) -> str:
        pass

    def generate_report(self, model_id: int, user_id: int) -> str:
        pass
```

---

## 30. AI 模式设计

系统支持两种 AI 模式：

```text
mock 模式：不调用外部大模型，使用模板生成分析文本。
llm 模式：调用外部大模型 API 生成分析文本。
```

环境变量：

```env
AI_MODE=mock
OPENAI_API_KEY=
AI_PROVIDER=openai
AI_MODEL=
```

MVP 阶段优先实现 mock 模式。这样即使没有 API Key，系统仍然可以运行和展示。

---

## 31. 数据库扩展设计

### 31.1 dataset_contexts

```text
id                    Integer primary key
dataset_id            Integer foreign key
user_id               Integer foreign key
dataset_source        Text nullable
scenario_description  Text nullable
inclusion_criteria    Text nullable
exclusion_criteria    Text nullable
feature_descriptions  JSON nullable
target_descriptions   JSON nullable
usage_notes           Text nullable
created_at            DateTime
updated_at            DateTime
```

### 31.2 ai_field_recommendations

```text
id                            Integer primary key
dataset_id                    Integer foreign key
user_id                       Integer foreign key
field_name                    String
recommendation                String
reason                        Text
risk_level                    String
requires_user_confirmation    Boolean
user_decision                 String nullable
created_at                    DateTime
updated_at                    DateTime
```

### 31.3 ai_privacy_confirmations

```text
id                       Integer primary key
user_id                  Integer foreign key
dataset_id               Integer foreign key
action_type              String
risk_fields              JSON
selected_strategy        String
confirmed_at             DateTime
```

### 31.4 ai_request_logs

```text
id                          Integer primary key
user_id                     Integer foreign key
dataset_id                  Integer nullable
model_id                    Integer nullable
prediction_job_id           Integer nullable
prompt_type                 String
privacy_level               String
de_identification_strategy  String
input_summary_hash          String nullable
output_text                 Text
created_at                  DateTime
```

### 31.5 ai_analysis_reports

```text
id                  Integer primary key
user_id             Integer foreign key
dataset_id          Integer nullable
model_id            Integer nullable
prediction_job_id   Integer nullable
analysis_type       String
input_summary_json  JSON
generated_text      Text
created_at          DateTime
```

---

## 32. API 设计汇总

### 32.1 数据集上下文接口

```text
POST /api/datasets/{dataset_id}/context
GET  /api/datasets/{dataset_id}/context
PUT  /api/datasets/{dataset_id}/context
```

### 32.2 隐私检测接口

```text
POST /api/ai/privacy-scan/{dataset_id}
GET  /api/ai/privacy-scan/{dataset_id}
POST /api/ai/privacy-confirm/{dataset_id}
```

### 32.3 AI 数据分析接口

```text
POST /api/ai/dataset-analysis/{dataset_id}
GET  /api/ai/dataset-analysis/{dataset_id}

POST /api/ai/field-analysis/{dataset_id}
GET  /api/ai/field-analysis/{dataset_id}

POST /api/ai/training-config-suggestion/{dataset_id}
GET  /api/ai/training-config-suggestion/{dataset_id}
```

### 32.4 AI 模型分析接口

```text
POST /api/ai/model-analysis/{model_id}
GET  /api/ai/model-analysis/{model_id}

POST /api/ai/opns-pairing-analysis/{model_id}
GET  /api/ai/opns-pairing-analysis/{model_id}

POST /api/ai/error-analysis/{model_id}
GET  /api/ai/error-analysis/{model_id}

POST /api/ai/explainability-summary/{model_id}
GET  /api/ai/explainability-summary/{model_id}

POST /api/ai/regression-analysis/{model_id}
GET  /api/ai/regression-analysis/{model_id}
```

### 32.5 AI 预测分析接口

```text
POST /api/ai/prediction-explanation/{prediction_job_id}
GET  /api/ai/prediction-explanation/{prediction_job_id}

POST /api/ai/batch-prediction-analysis/{prediction_job_id}
GET  /api/ai/batch-prediction-analysis/{prediction_job_id}
```

### 32.6 AI 问答与报告接口

```text
POST /api/ai/dataset-chat/{dataset_id}
POST /api/ai/model-chat/{model_id}
POST /api/ai/chart-interpretation
POST /api/ai/error-explanation

POST /api/ai/report/{model_id}
GET  /api/ai/report/{model_id}
GET  /api/ai/reports
GET  /api/ai/reports/{report_id}
DELETE /api/ai/reports/{report_id}
```

---

## 33. 前端页面设计

### 33.1 数据集上下文页

路径：

```text
/datasets/:id/context
```

页面内容：

```text
1. 数据集来源。
2. 数据采集背景。
3. 应用场景说明。
4. 入组标准。
5. 排除标准。
6. 字段含义编辑表格。
7. 目标变量含义编辑表格。
8. 保存按钮。
```

### 33.2 AI 数据集分析页

路径：

```text
/ai/dataset-analysis/:datasetId
```

页面内容：

```text
1. 数据集摘要卡片。
2. 隐私风险提示。
3. AI 分析按钮。
4. AI 分析结果。
5. 重新生成按钮。
6. 导出按钮。
```

### 33.3 AI 字段分析页

路径：

```text
/ai/field-analysis/:datasetId
```

页面内容：

```text
1. 字段名。
2. 数据类型。
3. 缺失率。
4. 唯一值数量。
5. 字段说明。
6. AI 建议。
7. 风险等级。
8. 用户决策。
9. 保存配置按钮。
```

### 33.4 AI 模型结果分析页

路径：

```text
/ai/model-analysis/:modelId
```

页面内容：

```text
1. 模型指标表。
2. 模型对比图。
3. AI 分析按钮。
4. AI 分析结果。
5. 局限性说明。
6. 报告导出。
```

### 33.5 AI 预测结果说明页

路径：

```text
/ai/prediction-explanation/:predictionJobId
```

页面内容：

```text
1. 预测结果表格。
2. 预测概率图。
3. AI 解释按钮。
4. AI 解释文本。
5. 科研用途声明。
```

---

## 34. 提示词设计原则

所有提示词必须满足：

```text
1. 明确系统角色：科研数据分析助手。
2. 明确任务边界：只做数据分析、模型解释、科研辅助。
3. 明确禁止内容：不做临床诊断、治疗建议、用药建议。
4. 明确隐私边界：不要尝试识别个人身份。
5. 明确证据来源：只基于输入摘要，不编造数据。
6. 明确输出格式：结构化小标题或 JSON。
7. 明确不确定性：无法判断时说明需要更多信息。
8. 明确医学表达边界：使用“模型预测”“可能提示”“需进一步验证”等表述。
```

---

## 35. 通用系统提示词

```text
你是一个医学表格数据科研分析助手，服务于机器学习建模和实验结果解释。你只能基于用户提供的数据摘要、字段说明、模型指标和预测结果进行分析。

你必须遵守以下规则：
1. 不输出临床诊断结论。
2. 不输出治疗建议。
3. 不输出用药建议。
4. 不尝试识别任何个人身份。
5. 不编造输入中不存在的数据。
6. 对不确定内容必须明确说明不确定性。
7. 对医疗相关内容必须使用“科研分析”“模型输出”“可能提示”等谨慎表述。
8. 不将统计相关性解释为医学因果关系。
9. 输出结尾必须包含：本分析仅用于科研分析和模型验证，不作为临床诊断、治疗决策或用药依据。
```

---

## 36. 提示词模板

### 36.1 数据集状态分析提示词

```text
任务：请根据以下医学表格数据集摘要，生成数据集状态分析报告。

分析目标：
1. 概述数据规模。
2. 分析字段类型构成。
3. 分析缺失值情况。
4. 分析目标标签分布。
5. 判断是否存在类别不平衡。
6. 给出建模前的数据处理建议。
7. 给出适合的评价指标建议。
8. 不输出临床诊断或治疗建议。

数据集背景：
{dataset_context}

数据集统计摘要：
{dataset_profile}

标签分布：
{label_distribution}

缺失值摘要：
{missing_summary}

隐私处理状态：
{privacy_status}

输出格式：
一、数据集总体情况
二、字段与缺失值情况
三、目标变量与类别分布
四、建模前处理建议
五、评价指标建议
六、注意事项与局限性
七、科研用途声明
```

### 36.2 字段分析提示词

```text
任务：请根据字段统计摘要、字段含义和目标变量信息，对每个字段给出建模处理建议。

字段统计摘要：
{field_statistics}

字段含义说明：
{feature_descriptions}

目标变量：
{target_columns}

目标变量含义：
{target_descriptions}

相关性摘要：
{correlation_summary}

隐私风险扫描结果：
{privacy_scan_result}

要求：
1. 对每个字段给出建议：keep、ignore、remove、de_identify、impute_and_keep、standardize_and_keep、encode_and_keep、check_for_leakage、manual_review。
2. 对疑似身份标识符给出 remove 或 de_identify 建议。
3. 对高缺失字段给出 ignore 或 impute_and_keep 建议。
4. 对疑似目标泄漏字段给出 check_for_leakage 建议。
5. 对医学字段只说明其可能的建模价值，不输出临床结论。
6. 建议只能作为参考，最终由用户确认。

请输出 JSON，格式如下：
{
  "feature_recommendations": [
    {
      "field": "字段名",
      "recommendation": "建议类型",
      "reason": "建议原因",
      "risk_level": "low/medium/high",
      "requires_user_confirmation": true
    }
  ],
  "global_recommendations": [
    "总体建议1",
    "总体建议2"
  ],
  "disclaimer": "本分析仅用于科研分析和模型验证，不作为临床诊断、治疗决策或用药依据。"
}
```

### 36.3 模型训练设置建议提示词

```text
任务：请根据数据集状态、字段分析结果和目标变量信息，给出机器学习模型训练配置建议。

数据集摘要：
{dataset_profile}

字段分析结果：
{field_recommendations}

目标变量：
{target_columns}

标签分布：
{label_distribution}

用户场景说明：
{dataset_context}

可选模型：
{available_models}

可选 OPNs 配对方式：
{available_pairing_methods}

要求：
1. 给出任务类型建议。
2. 给出目标变量设置建议。
3. 给出输入特征选择建议。
4. 给出缺失值处理建议。
5. 给出标准化和编码建议。
6. 给出 OPNs 配对方式建议。
7. 给出 SVM/SVR 参数初始建议。
8. 给出评价指标建议。
9. 对所有建议说明原因。
10. 所有建议都必须由用户最终确认。

请输出 JSON：
{
  "task_suggestion": {
    "task_type": "",
    "target_columns": [],
    "reason": ""
  },
  "feature_suggestion": {
    "include": [],
    "exclude": [],
    "manual_review": []
  },
  "preprocessing_suggestion": {
    "missing_strategy": "",
    "scaling": true,
    "encoding": ""
  },
  "model_suggestion": {
    "primary_model": "",
    "baseline_models": [],
    "kernel": "",
    "pairing_method": "",
    "metrics": []
  },
  "warnings": [],
  "disclaimer": "本分析仅用于科研分析和模型验证，不作为临床诊断、治疗决策或用药依据。"
}
```

### 36.4 OPNs 配对解释提示词

```text
任务：请根据 OPNs 特征配对信息、模型指标和基线模型对比，解释当前 OPNs 特征构造可能对模型表现产生的影响。

数据集背景：
{dataset_context}

OPNs 配置：
{opns_config}

特征配对列表：
{pairing_summary}

模型指标：
{model_metrics}

基线模型对比：
{baseline_comparison}

要求：
1. 解释当前配对方式的基本含义。
2. 说明该配对方式可能如何影响结构特征表达。
3. 结合模型指标分析 OPNs-SVM/SVR 相比基线模型的变化。
4. 对提升或下降给出谨慎分析。
5. 不得将模型提升解释为医学因果关系。
6. 不得输出临床诊断或治疗建议。

输出格式：
一、OPNs 配对方式说明
二、结构特征表达分析
三、与基线模型对比
四、可能原因与局限性
五、后续实验建议
六、科研用途声明
```

### 36.5 模型结果分析提示词

```text
任务：请根据模型训练结果、数据集背景和目标变量含义，对模型表现进行科研分析。

数据集背景：
{dataset_context}

目标变量含义：
{target_descriptions}

模型信息：
{model_info}

模型评估指标：
{model_metrics}

基线模型对比：
{baseline_comparison}

标签分布：
{label_distribution}

特征设置信息：
{feature_config}

OPNs 特征构造信息：
{opns_config}

要求：
1. 分析总体模型表现。
2. 分析不同目标标签之间的表现差异。
3. 结合类别分布解释 Precision、Recall、F1 的变化。
4. 结合 OPNs 特征构造说明可能的性能变化原因。
5. 与基线模型进行谨慎比较。
6. 指出模型局限性。
7. 给出后续改进建议。
8. 不得输出医学诊断、治疗建议或用药建议。
9. 不得将模型相关性解释为医学因果关系。

输出格式：
一、总体模型表现
二、不同标签表现差异
三、与基线模型对比
四、OPNs 特征构造的可能影响
五、局限性分析
六、后续改进建议
七、科研用途声明
```

### 36.6 单病例预测结果分析提示词

```text
任务：请根据单病例预测结果、模型整体表现和数据集背景，生成预测结果说明。

数据集背景：
{dataset_context}

目标变量含义：
{target_descriptions}

输入特征摘要：
{input_feature_summary}

模型预测结果：
{prediction_result}

模型整体指标：
{model_metrics_summary}

要求：
1. 说明每个目标标签的预测结果。
2. 说明预测概率较高和较低的标签。
3. 结合模型整体指标说明预测可信边界。
4. 对不确定性较高的结果进行提示。
5. 不输出临床诊断。
6. 不输出治疗建议。
7. 不输出用药建议。
8. 不使用“患者确诊为”等表述。
9. 使用“模型预测为”“当前模型输出提示”“该结果存在不确定性”等表述。

输出格式：
一、预测结果概述
二、各标签预测说明
三、预测置信度与不确定性
四、结合模型性能的解释
五、注意事项
六、科研用途声明
```

### 36.7 批量预测结果分析提示词

```text
任务：请根据批量预测结果摘要，生成批量预测结果分析。

数据集背景：
{dataset_context}

批量预测摘要：
{batch_prediction_summary}

预测标签分布：
{predicted_label_distribution}

模型整体指标：
{model_metrics_summary}

要求：
1. 总结批量预测样本数量。
2. 分析预测标签分布。
3. 判断是否出现明显偏向某一类别的情况。
4. 结合模型性能说明结果可信边界。
5. 指出需要进一步人工复核的部分。
6. 不输出临床诊断、治疗建议或用药建议。

输出格式：
一、批量预测总体情况
二、预测标签分布
三、可能的模型偏向
四、需要关注的不确定性
五、后续复核建议
六、科研用途声明
```

### 36.8 OPNs-SVR 回归结果分析提示词

```text
任务：请根据 OPNs-SVR 回归模型结果，生成回归实验分析。

数据集背景：
{dataset_context}

目标变量说明：
{target_description}

模型信息：
{model_info}

回归指标：
{regression_metrics}

基线模型对比：
{baseline_comparison}

残差摘要：
{residual_summary}

真实值与预测值摘要：
{predicted_vs_actual_summary}

要求：
1. 分析 MAE、RMSE、R2 的含义。
2. 分析 OPNs-SVR 与标准 SVR 的差异。
3. 分析残差分布是否存在明显偏差。
4. 指出模型可能适用和不适用的场景。
5. 不夸大模型性能。
6. 不输出临床诊断或治疗建议。

输出格式：
一、回归模型总体表现
二、误差指标分析
三、与基线模型对比
四、残差与拟合情况
五、局限性与改进方向
六、科研用途声明
```

### 36.9 图表解读提示词

```text
任务：请根据图表对应的结构化数据，对该图表进行科研分析说明。

图表类型：
{chart_type}

图表标题：
{chart_title}

图表数据摘要：
{chart_data_summary}

数据集背景：
{dataset_context}

要求：
1. 说明图表展示的核心现象。
2. 说明该现象对数据分析或模型训练的影响。
3. 指出需要注意的局限性。
4. 不输出临床诊断、治疗建议或用药建议。

输出格式：
一、图表主要信息
二、可能影响
三、注意事项
四、科研用途声明
```

### 36.10 报告生成提示词

```text
任务：请根据系统提供的数据集信息、模型训练结果和预测结果，生成科研分析报告。

数据集信息：
{dataset_summary}

隐私处理信息：
{privacy_summary}

字段处理配置：
{feature_config}

OPNs 配置：
{opns_config}

模型训练配置：
{training_config}

模型评估结果：
{model_metrics}

预测结果摘要：
{prediction_summary}

要求：
1. 报告语言应正式、客观、适合专业实践报告。
2. 不得夸大模型性能。
3. 不得输出临床诊断、治疗建议或用药建议。
4. 不得将相关性解释为因果关系。
5. 必须包含局限性和科研用途声明。

输出结构：
1. 数据集概况
2. 隐私保护与数据预处理
3. OPNs 特征构造
4. 模型训练配置
5. 模型评估结果
6. 与基线模型对比
7. 预测结果分析
8. 局限性
9. 科研用途声明
```

---

## 37. AI 输出校验机制

### 37.1 禁止词检测

系统应检测 AI 输出中是否包含以下内容：

```text
确诊
诊断为
建议用药
治疗方案
必须治疗
立即治疗
临床处置
药物剂量
替代医生判断
可以排除疾病
可以确认病变
```

若检测到禁止内容，系统应：

```text
1. 拒绝展示原始输出。
2. 重新调用模型并加强约束。
3. 或提示用户 AI 输出不符合医学安全边界。
```

### 37.2 输出完整性检查

系统应检查 AI 输出是否包含：

```text
1. 科研用途声明。
2. 不确定性说明。
3. 局限性说明。
```

如果缺失，应自动补充固定声明。

### 37.3 JSON 输出校验

对字段建议、训练配置建议等 JSON 输出，应进行 schema 校验：

```text
1. 字段是否完整。
2. recommendation 是否属于允许枚举值。
3. risk_level 是否属于 low、medium、high。
4. requires_user_confirmation 是否为布尔值。
5. 不允许包含未定义的高风险操作。
```

---

## 38. 推荐 Codex 开发任务

### 38.1 任务一：数据集上下文模块

```text
请在现有项目中实现数据集上下文模块。

要求：
1. 新增 dataset_contexts 数据库表。
2. 后端实现 POST、GET、PUT /api/datasets/{dataset_id}/context。
3. 支持保存数据集来源、场景说明、入组标准、排除标准、字段含义、目标变量含义。
4. 前端新增 DatasetContextPage。
5. 用户只能访问和修改自己的数据集上下文。
```

### 38.2 任务二：隐私扫描模块

```text
请在现有项目中实现 AI 隐私扫描模块。

要求：
1. 新增 backend/app/ai/privacy_guard.py。
2. 检测字段名中可能包含身份标识的信息，如姓名、身份证、手机号、住院号、门诊号、病案号、地址、email。
3. 检测唯一值比例过高的字段，并标记为疑似唯一标识符。
4. 后端实现 POST /api/ai/privacy-scan/{dataset_id}。
5. 前端在调用 AI 分析前展示隐私风险提示。
6. 高风险字段默认不发送给 AI。
```

### 38.3 任务三：AI 字段分析模块

```text
请在现有项目中实现 AI 字段分析模块。

要求：
1. 新增 ai_field_recommendations 表。
2. 实现 POST /api/ai/field-analysis/{dataset_id}。
3. AI 输入只能包含字段统计摘要、字段含义、目标变量信息和隐私扫描结果。
4. 输出每个字段的 keep、ignore、de_identify、impute_and_keep、standardize_and_keep、check_for_leakage 等建议。
5. 前端实现字段分析表格，允许用户确认保留、忽略或脱敏字段。
6. AI 建议不得自动修改训练配置，必须由用户确认。
```

### 38.4 任务四：AI 训练配置建议模块

```text
请在现有项目中实现 AI 训练配置建议模块。

要求：
1. 实现 POST /api/ai/training-config-suggestion/{dataset_id}。
2. 根据数据集摘要、字段分析结果、标签分布、任务类型生成训练配置建议。
3. 返回建议目标变量、输入特征、缺失值处理方式、标准化方式、模型类型、OPNs 配对方式和评价指标。
4. 前端在模型训练页面提供“应用 AI 建议”按钮。
5. 用户点击确认后才应用建议。
```

### 38.5 任务五：AI 模型结果分析模块

```text
请增强 AI 模型结果分析模块。

要求：
1. 模型结果分析时读取 dataset_contexts 中的数据集背景和字段含义。
2. 结合模型指标、标签分布、基线模型对比、OPNs 配置进行分析。
3. 输出必须包含总体表现、标签差异、OPNs 影响、局限性和后续建议。
4. 禁止输出诊断建议、治疗建议和用药建议。
5. 对 AI 输出进行禁止词检测。
```

### 38.6 任务六：AI 预测结果说明模块

```text
请增强 AI 预测结果说明模块。

要求：
1. 单病例预测说明应结合数据集背景、目标变量含义、输入特征摘要、预测概率和模型整体指标。
2. 批量预测说明应结合预测标签分布、模型整体指标和不确定性。
3. 不得输出临床诊断、治疗建议或用药建议。
4. 输出必须包含科研用途声明。
```

### 38.7 任务七：AI OPNs 配对解释模块

```text
请实现 AI OPNs 配对解释模块。

要求：
1. 后端实现 POST /api/ai/opns-pairing-analysis/{model_id}。
2. 读取模型 metadata 中的 pairing_method、mapping_config、feature_columns、target_columns。
3. 读取模型指标和基线模型对比结果。
4. 生成 OPNs 配对方式、结构特征表达和模型性能变化的分析文本。
5. 不得将性能变化解释为医学因果关系。
```

### 38.8 任务八：AI 报告生成模块

```text
请实现 AI 报告生成模块。

要求：
1. 后端实现 POST /api/ai/report/{model_id}。
2. 报告内容包括数据集概况、隐私处理、字段配置、OPNs 特征构造、模型训练配置、模型评估结果、预测结果分析、局限性和科研用途声明。
3. 前端提供报告预览页面。
4. 支持导出 Markdown。
5. 不得输出临床诊断、治疗建议或用药建议。
```

---

## 39. Git 提交建议

每完成一个 AI 子模块后单独提交：

```bash
git add .
git commit -m "feat: add dataset context module"

git add .
git commit -m "feat: implement AI privacy scan"

git add .
git commit -m "feat: implement AI field analysis"

git add .
git commit -m "feat: implement AI training config suggestion"

git add .
git commit -m "feat: enhance AI model result analysis"

git add .
git commit -m "feat: implement AI prediction explanation"

git add .
git commit -m "feat: implement AI OPNs pairing analysis"

git add .
git commit -m "feat: implement AI report generation"
```

每次 Codex 修改后应检查：

```bash
git status
git diff --stat
```

后端检查：

```bash
cd backend
source .venv/bin/activate
python -m compileall app
```

前端检查：

```bash
cd frontend
npm run build
```

---

## 40. 验收标准

AI 模块最终应满足：

```text
1. 用户可以填写数据集来源和字段含义。
2. 系统可以对上传数据集进行隐私风险扫描。
3. 系统默认不将完整原始医疗数据发送给 AI。
4. 系统可以生成数据集状态分析。
5. 系统可以生成字段处理建议。
6. 系统可以生成训练配置建议。
7. 系统可以结合字段背景分析模型训练结果。
8. 系统可以解释 OPNs 特征配对与模型表现的关系。
9. 系统可以结合数据集场景解释预测结果。
10. 用户可以确认或拒绝 AI 给出的字段处理建议。
11. AI 输出不得包含临床诊断、治疗建议或用药建议。
12. AI 输出必须包含科研用途声明。
13. 系统保存 AI 分析记录和隐私确认记录。
14. AI 模块支持 mock 模式。
15. 真实大模型 API Key 不得硬编码到代码中。
```

---

## 41. 推荐实现优先级

### 41.1 第一优先级

```text
1. 数据集上下文填写。
2. 隐私扫描。
3. AI 数据集状态分析。
4. AI 字段分析。
5. AI 模型训练配置建议。
6. AI 模型结果分析。
```

### 41.2 第二优先级

```text
1. AI 单病例预测结果说明。
2. AI 批量预测结果分析。
3. AI OPNs 配对解释。
4. AI 图表解读。
5. AI 报告生成。
```

### 41.3 第三优先级

```text
1. AI 错误样本分析。
2. AI 可解释性摘要。
3. AI 数据集问答。
4. AI 模型问答。
5. AI 操作向导。
6. AI 异常解释。
```

---

## 42. 总体结论

在本系统中加入 AI 大模型是可行的，并且可以显著增强专业实践系统的完整性和展示价值。推荐形成如下系统分工：

```text
OPNs-SVM/SVR：负责核心预测建模。
ECharts：负责可视化展示。
AI 大模型：负责数据理解、字段建议、结果解释和报告生成。
隐私模块：负责脱敏、确认和审计。
用户：负责最终确认字段处理、模型配置和结果使用。
```

系统设计必须坚持以下原则：

```text
1. 以结构化摘要替代完整原始数据。
2. 以脱敏样本替代可识别患者信息。
3. 以用户确认替代自动决策。
4. 以科研辅助分析替代临床诊断。
5. 以日志审计保证过程可追踪。
6. 以 OPNs-SVM/SVR 作为核心预测方法，AI 作为辅助解释模块。
```

该模块应作为系统的重要增强部分，但不应喧宾夺主。毕业论文和专业实践的核心仍然是 OPNs-SVM/SVR 在医学表格数据分类与回归任务中的应用，AI 模块用于提高系统的可解释性、可用性和报告生成能力。
