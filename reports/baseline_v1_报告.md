# InvoiceGuard AI Baseline v1 报告

**项目名称：** Receipt Extraction and Review Agent  
**核心模型：** Qwen2.5-VL-7B-Instruct  
**GPU 机器：** NVIDIA L40S  
**数据集：** SROIE receipt dataset  
**报告日期：** 2026-06-08

## 1. 项目目标

InvoiceGuard AI 是一个面向发票/小票审核的 Document AI / VLM baseline pipeline。给定一张 receipt image，系统需要完成以下任务：

1. 从图像中提取结构化字段；
2. 与 ground truth 做字段级评估；
3. 使用 rule-based checks 判断提取结果是否可靠；
4. 计算 confidence score；
5. 输出最终审核决策。

当前版本输出三种 decision：

- `approve`
- `need_human_review`
- `reject`

本版本重点是先完成一个可运行、可评估、可复现的 baseline，而不是一开始就做完整的 LangGraph production agent。

## 2. 数据集和输入

当前 baseline 使用 SROIE receipt dataset。每个样本包含：

- receipt image；
- preprocessing 后的 unified JSON；
- ground-truth key fields；
- OCR text / bounding boxes 等辅助信息。

本报告主要评估三个核心字段：

- `vendor_name`
- `invoice_date`
- `total`

模型也会提取：

- `vendor_address`
- `currency`

但 baseline v1 的主要指标集中在 vendor、date 和 total 三个关键字段上。

## 3. 系统 Workflow

```text
receipt image
  -> Qwen2.5-VL extraction
  -> structured JSON prediction
  -> field-level evaluation
  -> rule engine
  -> confidence scoring
  -> approve / need_human_review / reject
```

主要代码文件包括：

- `scripts/run_qwen_baseline.py`
- `scripts/evaluate_baseline.py`
- `scripts/compare_codex_qwen.py`
- `agent/schemas.py`
- `agent/rule_engine.py`
- `agent/confidence.py`
- `agent/decision.py`
- `agent/review_agent.py`

## 4. GPU 环境

Qwen2.5-VL baseline 在 **NVIDIA L40S GPU** 上运行。这个信息很重要，因为 Qwen2.5-VL-7B 在当前项目设置下对显存有较高要求，在较小的 16 GB GPU 上推理会比较困难或容易出现 OOM。

## 5. Prompt Engineering 总结

本阶段测试了三个 prompt 版本：

- `receipt_review_v1.txt`：初始简单 extraction prompt；
- `receipt_review_v2.txt`：稳定的 structured JSON extraction prompt；
- `receipt_review_v3.txt`：加入 uncertainty-aware 逻辑，例如 blurry text、ambiguous vendor、unclear amount 和 human-review signal。

最终选择 `receipt_review_v2.txt` 作为 baseline extraction prompt。原因是 v2 的 JSON 输出稳定性更好，而 v3 虽然加入了不确定性检测逻辑，但没有稳定地产生有用的 document quality labels，并且出现了 JSON parse failure。

| Prompt | Sample | Parse success | Vendor normalized | Date normalized | Total normalized | All-key normalized |
|---|---:|---:|---:|---:|---:|---:|
| v2 | train 100 | 100.0% | 94.0% | 99.0% | 98.0% | 91.0% |
| v3 | train 100 | 99.0% | 93.0% | 98.0% | 98.0% | 91.0% |

结论：v3 的思想可以用于 rule design，但不适合作为当前主 extraction prompt。因此本项目保留 v2 作为稳定提取 prompt，并把模糊、歧义、低置信度等不确定性处理移动到 `rule_engine.py` 和 `confidence.py`。

## 6. Evaluation 定义

本项目使用多种匹配方式评估字段提取结果：

- `vendor_name`：exact match、normalized match 和 fuzzy match；其中 fuzzy threshold = 0.85。
- `invoice_date`：normalized date match。
- `total`：normalized numeric amount match。

字段级 Precision / Recall / F1 使用固定字段抽取任务的定义：

- TP：ground truth 有值，prediction 有值，并且二者匹配；
- FP：prediction 有值，但不匹配 ground truth；
- FN：ground truth 有值，但 prediction 缺失或 prediction 错误。

如果 ground truth 有值，模型也预测了值，但预测值错误，则同时计为 FP 和 FN。这表示模型产生了一个错误字段，同时没有恢复正确字段。

## 7. Train Sample 结果 - Qwen v2

| Metric | Value |
|---|---:|
| Total records | 100 |
| Parse success rate | 100.0% |
| Vendor exact accuracy | 80.0% |
| Vendor normalized accuracy | 94.0% |
| Vendor fuzzy accuracy | 97.0% |
| Date normalized accuracy | 99.0% |
| Total normalized accuracy | 98.0% |
| All key fields normalized accuracy | 91.0% |
| All key fields fuzzy accuracy | 94.0% |
| Vendor P/R/F1 | 0.970 / 0.970 / 0.970 |
| Date P/R/F1 | 0.990 / 0.990 / 0.990 |
| Total P/R/F1 | 0.980 / 0.980 / 0.980 |
| Macro P/R/F1 | 0.980 / 0.980 / 0.980 |
| Decision counts | {'need_human_review': 10, 'approve': 90} |

主要观察：

- Train sample 上 parse success 为 100%。
- Vendor fuzzy accuracy 高于 vendor normalized accuracy，因为很多 vendor mismatch 来自大小写、标点、拼写差异或 legal name 变体。
- Total normalized accuracy 较高，但 exact total accuracy 会受到 currency formatting 影响，例如 `RM 5.00` vs `5.00`。
- Review agent 在 train sample 中 approve 了 90 张 receipts，并将 10 张送入 human review。

## 8. Held-out Test Sample 结果 - Qwen v2

| Metric | Value |
|---|---:|
| Total records | 100 |
| Parse success rate | 100.0% |
| Vendor exact accuracy | 79.0% |
| Vendor normalized accuracy | 89.0% |
| Vendor fuzzy accuracy | 95.0% |
| Date normalized accuracy | 97.0% |
| Total normalized accuracy | 98.0% |
| All key fields normalized accuracy | 84.0% |
| All key fields fuzzy accuracy | 90.0% |
| Vendor P/R/F1 | 0.950 / 0.950 / 0.950 |
| Date P/R/F1 | 0.970 / 0.970 / 0.970 |
| Total P/R/F1 | 0.980 / 0.980 / 0.980 |
| Macro P/R/F1 | 0.967 / 0.967 / 0.967 |
| Decision counts | {'approve': 95, 'need_human_review': 5} |

主要观察：

- Held-out test sample 上 parse success 仍为 100%。
- Test sample 上 all-key-field fuzzy accuracy 为 90.0%，低于 train sample 的 94.0%。
- Test sample 上 macro F1 为 0.967。
- Review agent 在 test sample 中 approve 了 95 张 receipts，并将 5 张送入 human review。

## 9. Rule Engine

Baseline rule engine 包含以下检查：

1. parse success check；
2. required critical fields check；
3. field-level confidence check；
4. numeric total validity check；
5. subtotal / tax / discount 存在时的 total math consistency check；
6. date validity check；
7. optional vendor fuzzy check；
8. document quality issue check；
9. high amount risk check。

对于 SROIE receipts，critical required fields 是：

- `vendor_name`
- `invoice_date`
- `total`

`invoice_number` 不作为 required field，因为很多小票本身不包含 invoice number。

## 10. Confidence Scoring 和 Decision Logic

Confidence score 综合以下部分：

- parse score；
- VLM self confidence；
- schema score；
- rule score；
- required-field completeness；
- field-level confidence。

系统同时输出两个分数：

- `confidence_score`：0-1；
- `confidence_score_0_10`：0-10。

Decision thresholds：

| Score range | Decision |
|---:|---|
| 0-2 | reject |
| 3-7 | need_human_review |
| 8-10 | approve |

Rule overrides：

- parse failure -> reject；
- critical rule failure -> reject；
- high severity warning/failure -> need_human_review；
- any warning -> need_human_review。

平均 confidence score：

| Split | Average confidence 0-10 | Decision counts |
|---|---:|---|
| Train 100 | 9.790 | {'need_human_review': 10, 'approve': 90} |
| Test 100 | 9.733 | {'approve': 95, 'need_human_review': 5} |

## 11. ChatGPT vs Qwen 对比

本项目额外选取了 10 张 receipt image，由 ChatGPT 进行字段抽取，并与 Qwen2.5-VL 的输出进行对比。比较字段包括：

- `vendor_name`
- `invoice_date`
- `total`

| Model | Vendor F1 | Date F1 | Total F1 | Macro F1 |
|---|---:|---:|---:|---:|
| Qwen2.5-VL | 1.000 | 1.000 | 1.000 | 1.000 |
| ChatGPT | 1.000 | 1.000 | 1.000 | 1.000 |

Case outcome counts: `{'tie': 10}`。

这个对比只是一个小规模 qualitative reference，不是完整 benchmark。它说明在相对干净、简单的样本上，Qwen2.5-VL 可以达到和 ChatGPT 相同的字段抽取结果。但后续仍需要扩大样本范围，覆盖更多模糊、污损、歧义和失败案例。

## 12. Examples 和 Failure Cases

### 案例 1 - 正确抽取并自动 approve

- `doc_id`: `sroie_test_X51005711444`
- 图片： `outputs/examples/SROIE2019_test_X51005711444.jpg`
- Ground truth vendor： `RESTORAN WAN SHENG`
- Qwen vendor： `RESTORAN WAN SHENG`
- Ground truth date： `21-03-2018`
- Qwen date： `21-03-2018`
- Ground truth total： `4.80`
- Qwen total： `4.80`
- Decision： `approve`
- 原因：vendor、date 和 total 都在 normalization 后正确匹配。

### 案例 2 - 字段正确，但因为 document quality 被送入 human review

- `doc_id`: `sroie_test_X51007846355`
- 图片： `outputs/examples/SROIE2019_test_X51007846355.jpg`
- Ground truth vendor： `AEON CO. (M) BHD`
- Qwen vendor： `AEON CO. (M) BHD`
- Ground truth date： `17/06/2018`
- Qwen date： `17/06/2018`
- Ground truth total： `8.95`
- Qwen total： `8.95`
- Error type： `document_quality_issue`
- Decision： `need_human_review`
- 原因：虽然关键字段抽取正确，但 rule engine 将存在 document quality issue 的样本送入人工复核。

### 案例 3 - Total mismatch，但当前 decision logic 仍然 approve

- `doc_id`: `sroie_test_X51005745244`
- 图片： `outputs/examples/SROIE2019_test_X51005745244.jpg`
- Ground truth vendor： `URBAN IDEA SDN BHD`
- Qwen vendor： `URBAN IDEA SDN BHD`
- Ground truth date： `14/02/2018`
- Qwen date： `14/02/2018`
- Ground truth total： `RM11.90`
- Qwen total： `11.23`
- Error type： `total_mismatch`
- Decision： `approve`
- 局限性：review agent 在生产推理时看不到 ground truth。
  如果模型高置信度输出错误 total，且内部规则没有发现异常，就可能错误 approve。
  后续版本需要对 total 风险设置更保守的规则。

### 案例 4 - Vendor fuzzy match 处理拼写差异

- `doc_id`: `sroie_test_X51006329183`
- 图片： `outputs/examples/SROIE2019_test_X51006329183.jpg`
- Ground truth vendor： `SEMBOYAN TEGAS SDN BHD`
- Qwen vendor： `SEMOYAN TEGAS SDN BHD`
- Vendor fuzzy score： `0.9767`
- Date 和 total：正确
- Error type： `vendor_fuzzy_only_match`
- Decision： `approve`
- 原因：vendor 字符串有轻微拼写差异，但 fuzzy score 很高，因此 evaluation 认为这是 near-equivalent extraction。

### 案例 5 - Legal name / display name ambiguity

- `doc_id`: `sroie_test_X51005230616`
- 图片： `outputs/examples/SROIE2019_test_X51005230616.jpg`
- Ground truth vendor： `GERBANG ALAF RESTAURANTS SDN BHD`
- Qwen vendor： `Gerbang Alaf Restaurants Sdn Bhd (65351-M) formerly known as Golden Arches Restaurants Sdn Bhd Licensee of McDonald's`
- Vendor fuzzy score： `0.4354`
- Date 和 total：正确
- Error type： `vendor_mismatch`
- Decision： `approve`
- 局限性：模型抽取了更长的 legal/company description，而不是 ground truth 中的 canonical vendor string。后续需要更强的 vendor canonicalization。

### 案例 6 - Prompt v3 JSON parse failure

- `doc_id`: `sroie_train_X51008123450`
- 图片： `outputs/examples/SROIE2019_train_X51008123450.jpg`
- Ground truth vendor： `SANJUNG REALITI SDN. BHD.`
- Ground truth date： `27/06/18`
- Ground truth total： `1.50`
- Prompt version：v3
- Error type： `parse_failed;vendor_mismatch;date_mismatch;total_mismatch`
- 原因：v3 加入了较多 uncertainty instructions，但这个样本生成了 invalid/incomplete JSON。
- 结论：保留 v2 作为稳定 extraction prompt，将 uncertainty handling 移动到 rules 和 confidence scoring。

## 13. 当前局限性

1. Review agent 在 inference 阶段不能访问 ground truth，因此一些错误抽取结果仍可能因为模型高置信度而被 approve。
2. ChatGPT 对比目前只有 10 张样本，更适合作为 qualitative comparison，而不是完整 benchmark。
3. Document quality labels 还不够稳定，不能作为完整风险检测器。
4. Duplicate detection 和 vendor database checks 目前仍是 placeholder。
5. Pipeline 还没有封装成 LangGraph workflow。

## 14. 下一步工作

1. 让 total mismatch / amount risk handling 更保守。
2. 加强 vendor canonicalization，处理 legal name 和 display name 差异。
3. 扩大 ChatGPT vs Qwen 对比样本数量。
4. 在 VLM extraction 前加入 OCR-assisted features 或 image quality checks。
5. 增加 PostgreSQL duplicate detection。
6. 在 baseline 稳定后，将 pipeline 封装成 LangGraph state-machine workflow。
