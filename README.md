<div align="center">

# Mercury · 电商运营 Agent 框架

**ReAct Agent Framework for E-commerce Operations**

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-1.2-green)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.1-orange)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.57-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

</div>

---

## 项目简介

**Mercury** 是一个面向电商运营场景的 ReAct Agent 框架。系统基于 LangGraph 手写 StateGraph 构建，集成 **Context Engineering、Harness Engineering、Agent Runtime、Tool System、Memory** 五大模块，覆盖 **新品上架优化、评价危机管理、大促活动策划、运营日报生成** 四个完整业务闭环。

> 墨丘利（Mercury）—— 罗马神话中的**商业之神**与**众神信使**，象征电商领域与 Agent 消息传递的双重属性。

### 为什么不做通用 Agent

通用 Agent 什么问题都能答，但什么场景都不深。Mercury 聚焦手机配件电商运营，每个工作流都走完 **触发→数据拉取→多维分析→策略生成→结构化输出** 的完整闭环，输出内容直接可用而非泛泛而谈。

---

## 架构

```
app.py (Streamlit)
    │
ReactAgent (薄包装器)
    │
AgentExecutor (中心枢纽)
    │
    ├── Context Engineering   ContextAssembler + Budget + Compressor
    ├── Harness Engineering   LifecycleHooks + TraceCollector
    ├── Agent Runtime         AgentGraph + AgentExecutor + SubAgent
    ├── Tool System           ToolRegistry + 7 tools + Pydantic validation
    └── Memory                WorkingMemory + ShortTermMemory + LongTermMemory
```

---

## 四个业务闭环

| 工作流 | 触发 | 工具链 | 输出 |
|--------|------|--------|------|
| **新品上架优化** | 用户提供 SKU | 商品详情 → 竞品对标 → 评价分析 | 标题 SEO + 定价策略 + 卖点提炼 + 执行优先级 |
| **评价危机管理** | 差评增多预警 | 评价拉取 → 情感归类 → 根因分析 | 差评分类 + 回复模板 + 升级 SOP |
| **大促活动策划** | 活动目标 + 预算 | 历史促销复盘 → 订单趋势 → ROI 测算 | 预算分配方案 + 执行 SOP + 风险预案 |
| **运营日报生成** | 日报请求 | 多维度数据聚合 → 异常检测 | GMV/UV/转化率看板 + 异常预警 + 行动建议 |

---

## 快速开始

### 1. 环境

- Python ≥ 3.10
- [阿里云百炼 API Key](https://bailian.console.aliyun.com/)

### 2. 安装

```bash
git clone https://github.com/aisakataiga1215/Mercury.git
cd Mercury
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY
```

### 3. 启动

```bash
streamlit run app.py
```

浏览器打开 http://localhost:8501，左侧选择工作流模式，输入运营需求即可。

---

## 项目结构

```
Mercury/
├── app.py                     # Streamlit 运营面板（4 工作流）
├── agent/
│   └── react_agent.py         # 兼容包装器
├── src/                       # Agent 框架（5 模块）
│   ├── tools/                 # Tool System — 注册中心 + Pydantic 校验 + 7 工具
│   │   ├── registry.py, base.py
│   │   └── builtin/           # product_tools, analytics_tools, workflow_tools
│   ├── context/               # Context Engineering — 组装管线 + Token 预算 + 压缩
│   ├── harness/               # Harness Engineering — 8 事件钩子 + Span 追踪
│   ├── memory/                # Memory — Working/ShortTerm/LongTerm 三层记忆
│   └── runtime/               # Agent Runtime — StateGraph 构建器 + Executor + SubAgent
├── data/                      # 电商数据集（50 SKU × 599 评价 × 91 天订单 × 42 竞品）
├── prompts/                   # 5 个场景提示词（主提示词 + 4 工作流模板）
├── config/                    # YAML 配置
├── model/                     # ChatTongyi 工厂
└── utils/                     # 工具函数
```

---

## 技术栈

| 层 | 技术 |
|---|------|
| LLM | 通义千问 qwen3-max（DashScope / 阿里云百炼） |
| Agent 框架 | LangChain 1.2 + LangGraph 1.1 |
| 前端 | Streamlit 1.57 |
| 配置 | YAML |
| 数据校验 | Pydantic |
| 数据 | 自建电商结构化 CSV 数据集 |

---

## License

MIT
