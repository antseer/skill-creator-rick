# DualYield — L3 结论生成

## v2: 模板模式 (默认)

结论由模板函数直接生成，不需要 LLM 调用。

### 模板

```
在{risk_label}策略下（到达概率 ≤ {risk_cap}），
**{platform}** 的 <span class="hl-blue">${strike}</span> 档位表现最优：
年化 <span class="hl-green">{apr}%</span>，
{duration}天内触达概率仅 <span class="hl-yellow">{prob}%</span>。
该价位{direction}当前价 {distance}%。
```

### 字段映射

| 占位符 | 来源 | 示例 |
|---|---|---|
| risk_label | UserContext.risk → {"conservative":"保守","balanced":"平衡","aggressive":"激进"} | 平衡 |
| risk_cap | {"conservative":"5%","balanced":"15%","aggressive":"30%"} | 15% |
| platform | top3[0].platform | Binance |
| strike | top3[0].strike (千分位) | 87,100 |
| apr | top3[0].apr | 18.5 |
| duration | top3[0].duration | 1 |
| prob | top3[0].prob * 100 (1位小数) | 2.3 |
| direction | side=="sell" → "高于", side=="buy" → "低于" | 高于 |
| distance | top3[0].distance | 3.0 |

---

## P2: LLM 增强 (可选)

如果后续需要更丰富的结论（加入 TA 解读），可接入 Claude Sonnet 4:

- Model: claude-sonnet-4-20250514
- Temperature: 0.3
- Max tokens: 300

System prompt 要求:
1. 一句话结论，≤60字，包含平台名+APR+概率
2. 可追加一句 TA 信号（RSI/MACD/趋势），≤40字
3. 不使用"我认为""建议您"等主观用语
4. 不使用表情符号
5. 数字必须具体化

Fallback: LLM 超时或报错 → 回退到模板模式
