# SlideCraft AI V2 - 基于 LangChain/LangGraph 重构

## 🚀 新架构特性

本次重构使用 LangChain 和 LangGraph 对 SlideCraft AI 进行了全面升级，提供了更强大的功能和更好的可扩展性。

### 核心改进

1. **🔄 工作流管理**
   - 使用 LangGraph 状态图管理整个PPT生成流程
   - 支持条件分支和并行处理
   - 可视化工作流程
   - 检查点支持，可恢复中断的任务

2. **🧠 智能Agent**
   - 基于 LangChain 的新一代 ContentAgent
   - 支持异步批量处理
   - 集成对话记忆
   - 更好的提示词管理

3. **⚡ 性能优化**
   - 异步并行生成内容页
   - 并发搜索配图
   - 流式生成支持
   - 智能参数优化

4. **🎯 质量控制**
   - 自动质量检查
   - 错误恢复机制
   - 多级质量模式（快速/平衡/高质量）
   - 生成报告和统计

## 📁 新增文件结构

```
src/
├── graph/                      # LangGraph 工作流
│   ├── __init__.py
│   ├── ppt_workflow.py         # 基础工作流
│   └── advanced_workflow.py    # 高级工作流（带质量控制）
├── agents/                     # 增强的Agent
│   └── langchain_content_agent.py  # 基于LangChain的ContentAgent
├── utils/                      # 集成工具
│   └── langchain_integration.py    # LangChain集成工具
├── main_langgraph.py           # 新的主程序入口
├── app_langgraph.py            # 新的Web界面
└── test_langgraph.py           # 测试脚本
```

## 🛠️ 安装新依赖

```bash
pip install -r requirements.txt
```

新增的主要依赖：
- `langgraph==0.2.55` - 工作流管理
- `langchain-core==0.3.26` - LangChain核心组件
- `mermaid-py==0.3.0` - 工作流可视化（可选）

## 🚀 快速开始

### 1. 命令行使用（新版）

```bash
# 基础使用
python src/main_langgraph.py "人工智能发展趋势" -n 10 -s professional

# 高质量模式（需要配合高级工作流）
python src/main_langgraph.py "区块链技术" -n 15 -s creative --add-images
```

### 2. Web界面（新版）

```bash
# 启动基于LangGraph的新界面
python src/app_langgraph.py
```

新界面特性：
- 📝 快速生成：基础PPT生成功能
- 🧠 智能分析：主题分析和策略建议
- ✨ 内容优化：基于反馈的内容修改
- 📚 生成历史：查看历史记录

### 3. 编程接口

#### 基础工作流

```python
from src.graph.ppt_workflow import PPTWorkflow

# 创建工作流
workflow = PPTWorkflow({
    "api_key": "your-api-key",
    "model": "deepseek-chat",
    "add_images": True
})

# 运行
result = await workflow.run({
    "topic": "机器学习基础",
    "num_slides": 10,
    "style": "professional",
    "template": "business"
})

print(f"PPT生成: {result['ppt_path']}")
```

#### 高级工作流（带质量控制）

```python
from src.graph.advanced_workflow import AdvancedPPTWorkflow

# 创建高级工作流
workflow = AdvancedPPTWorkflow({
    "api_key": "your-api-key",
    "model": "deepseek-chat"
})

# 运行高质量生成
result = await workflow.run({
    "topic": "深度学习研究",
    "num_slides": 15,
    "style": "academic",
    "quality_mode": "high",
    "auto_approve_outline": False,
    "enable_review": True
})

# 查看质量报告
if result["generation_report"]:
    report = result["generation_report"]
    print(f"质量评分: {report['quality_score']}/100")
    print(f"生成时间: {report['duration_seconds']}秒")
```

### 4. 流式生成

```python
from src.utils.langchain_integration import LangChainIntegration

integration = LangChainIntegration(config)

async for update in integration.stream_generation(
    topic="量子计算",
    num_slides=10,
    style="academic",
    quality_mode="high"
):
    if update["type"] == "progress":
        print(f"进度: {update['progress']*100:.1f}% - {update['step']}")
    elif update["type"] == "complete":
        print(f"完成! PPT路径: {update['ppt_path']}")
```

## 🧪 运行测试

```bash
# 运行完整测试套件
python test_langgraph.py

# 测试包括：
# - LangChain Content Agent
# - 基础工作流
# - 高级工作流
# - 集成工具
# - SlideCrafter V2
```

## 📊 性能对比

| 特性 | 原版本 | LangGraph版本 |
|------|--------|---------------|
| 内容生成 | 串行 | **并行（3倍速度提升）** |
| 错误恢复 | 无 | **自动重试** |
| 进度跟踪 | 基础 | **实时状态管理** |
| 质量检查 | 无 | **自动评分系统** |
| 工作流可视化 | 无 | **Mermaid图表** |
| 对话记忆 | 无 | **上下文保持** |
| 参数优化 | 固定 | **智能调整** |

## 🔄 迁移指南

### 从旧版本迁移

1. **保持向后兼容**
   - 原有的 `src/main.py` 仍然可用
   - API接口保持不变
   - 配置文件无需修改

2. **升级到新版本**
   ```python
   # 旧版本
   from src.main import SlideCrafter

   # 新版本
   from src.main_langgraph import SlideCrafterV2
   ```

3. **利用新特性**
   - 使用异步方法获得更好性能
   - 启用质量控制模式
   - 使用流式生成改善用户体验

## 🎯 最佳实践

### 1. 选择合适的模式

- **快速模式**: 简单演示、草稿生成
- **平衡模式**: 日常使用、标准质量
- **高质量模式**: 重要演示、专业用途

### 2. 性能优化建议

```python
# 对于大批量生成
config = {
    "api_key": "your-key",
    "model": "deepseek-chat",
    # 调整并发数
    "max_concurrent_contents": 3,
    "max_concurrent_images": 5
}

# 对于高质量输出
workflow = AdvancedPPTWorkflow(config)
result = await workflow.run({
    "quality_mode": "high",
    "enable_review": True,
    "auto_approve_outline": False
})
```

### 3. 错误处理

```python
# 检查最终状态
if result.get("errors"):
    print("生成过程中的错误:")
    for error in result["errors"]:
        print(f"- {error}")

# 查看质量报告
if result.get("generation_report"):
    report = result["generation_report"]
    if report["quality_score"] < 80:
        print("建议重新生成以获得更好质量")
```

## 🔮 未来计划

1. **多模态支持** - 集成图像生成模型
2. **模板市场** - 社区贡献模板系统
3. **协作功能** - 多用户实时协作
4. **云部署** - 支持云端批量处理
5. **API服务** - RESTful API接口

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

## 📄 许可证

MIT License