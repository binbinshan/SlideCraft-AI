# SlideCraft AI

🎯 一个基于AI的智能PPT生成Agent系统

## 功能特性

- ✅ **智能大纲生成** - 根据主题自动生成结构化PPT大纲
- ✅ **AI内容生成** - 基于DeepSeek-Chat模型生成专业PPT内容
- ✅ **多种内容风格** - 支持专业、创意、学术、创业、教学等风格
- ✅ **Web界面** - 基于Gradio的友好Web交互界面
- ✅ **多轮对话优化** - 支持内容修改和���新生成
- ✅ **实时进度跟踪** - 生成过程可视化进度显示
- ✅ **多种模板** - 商务、创意、学术等视觉模板
- ✅ **命令行支持** - 提供CLI接口供批量处理
- ✅ **自动配图** - 支持Unsplash/Pexels自动搜索和添加配图
- 🚧 图表生成(计划中)

## 快速开始

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装

```bash
# 克隆项目
git clone https://github.com/binbinshan/slidecrafter-ai.git
cd slidecrafter-ai

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env,填入你的API密钥
DEEPSEEK_API_KEY=your_deepseek_api_key_here
OPENAI_MODEL=deepseek-chat

# 如需自动配图功能(可选)
UNSPLASH_ACCESS_KEY=your_unsplash_access_key
# 或
PEXELS_API_KEY=your_pexels_api_key
```

### 4. 运行

```bash
# 运行Web界面 (推荐)
python src/app.py

# 或命令行模式
python src/main.py "你的PPT主题" -n 10 -s professional -t business

# 生成带配图的PPT
python src/main.py "科技创新" -n 12 -s creative --add-images
```

**命令行参数说明:**
- `topic`: PPT主题 (必需)
- `-n, --num-slides`: 页数 (默认10)
- `-s, --style`: 内容风格 (professional/creative/academic/startup/teaching)
- `-t, --template`: 视觉模板 (business/creative/academic)
- `--no-save-intermediate`: 不保存中间过程文件
- `--add-images`: 自动为内容页添加配图
- `-v, --version`: 显示版本信息

**使用示例:**
```bash
# 基础使用
python src/main.py "人工智能的发展趋势"

# 指定页数和风格
python src/main.py "机器学习基础" -n 15 -s academic

# 生成带配图的创意PPT
python src/main.py "科技创新" -s creative -t creative --add-images

# 快速生成(不保存中间文件)
python src/main.py "季度报告" --no-save-intermediate

# 查看帮助
python src/main.py --help
```

## 项目架构

```
slidecrafter-ai/
├── src/
│   ├── agents/              # AI Agent模块
│   │   ├── content_agent.py # ContentAgent - 内容生成核心
│   │   └── __init__.py
│   ├── generators/          # PPT生成模块
│   │   ├── ppt_generator.py # PPTGenerator - PPT文件创建
│   │   └── __init__.py
│   ├── prompts/             # 提示词模板
│   │   ├── templates.py     # PromptTemplates - 专业化提示词
│   │   └── __init__.py
│   ├── utils/               # 工具函数
│   │   ├── helpers.py       # 通用工具函数
│   │   ├── conversation.py  # 对话管理
│   │   ├── intent_detector.py # 意图识别
│   │   └── __init__.py
│   ├── main.py              # 主程序入口和SlideCrafter类
│   ├── app.py               # Gradio Web界面
│   ├── app_advanced.py      # 高级Web界面
│   └── prototype_demo.py    # 原型演示
├── tests/                   # 测试代码
│   ├── test_integration.py  # 集成测试
│   ├── t_content_agent.py   # ContentAgent测试
│   ├── test_templates.py    # 模板测试
│   └── test_intent_detection.py # 意图识别测试
├── data/                    # 数据文件
├── output/                  # 生成的PPT和日志
│   └── logs/               # 中间结果和日志文件
├── .env.example             # 环境变量模板
├── requirements.txt         # 项目依赖
└── README.md               # 项目说明
```

## 实现状态

### ✅ 已完成功能 (Week 1-3)

**核心功能**
- [x] **ContentAgent**: AI内容生成引擎，支持大纲和页面内容生成
- [x] **PPTGenerator**: PPT文件生成器，支持多种视觉模板
- [x] **多轮对话**: 内容修改、页面重新生成等交互功能
- [x] **实时进度跟踪**: 生成过程可视化和时间估算

**Web界面**
- [x] **Gradio界面**: 友好的Web交互界面
- [x] **多标签设计**: 生成PPT、编辑PPT、使用帮助三大功能区
- [x] **实时预览**: 大纲预览和状态显示
- [x] **文件下载**: 直接下载生成的PPT文件

**内容风格**
- [x] **Professional (专业)**: 商务汇报、工作总结
- [x] **Creative (创意)**: 创意展示、产品发布
- [x] **Academic (学术)**: 学术报告、论文展示
- [x] **Startup (创业)**: 融资路演、商业计划
- [x] **Teaching (教学)**: 课程教学、培训演示

**视觉模板**
- [x] **Business (商务)**: 深蓝色调，简洁专业
- [x] **Creative (创意)**: 多彩设计，活泼生动
- [x] **Academic (学术)**: 灰蓝色调，严谨规范

**测试和集成**
- [x] **单元测试**: ContentAgent、PromptTemplates等模块测试
- [x] **集成测试**: 完整工作流测试
- [x] **日志系统**: 完善的日志记录和错误处理
- [x] **自动配图**: 基于内容自动生成相关图片

### 🚧 开发中功能
- [] **图表生成**: 数据可视化图表自动创建



### 📋 计划功能 (Week 4-8)

- [ ] **Agent智能化**: 更智能的内容理解和生成
- [ ] **多语言支持**: 英文、日文等多语言PPT生成
- [ ] **模板市场**: 更多专业模板选择
- [ ] **协作功能**: 多用户协作编辑
- [ ] **云同步**: 在线保存和同步

## 使用示例

### Web界面使用

1. **启动应用**: 运行 `python src/app.py`，访问 http://localhost:7860
2. **生成PPT**:
   - 输入主题：如"人工智能在医疗领域的应用"
   - 选择页数：3-20页
   - 选择风格：根据使用场景选择合适风格
   - 选择模板：选择视觉样式
   - 点击"生成PPT"并等待完成
3. **编辑优化**:
   - 在"编辑PPT"标签页查看各页内容
   - 输入页码和修改要求���行内容优化
   - 支持重新生成特定页面

### 命令行使用

```bash
# 基础用法
python src/main.py "机器学习基础入门"

# 完整参数
python src/main.py "创业公司融资路演" \
  -n 15 \
  -s startup \
  -t creative \
  --add-images

# 生成学术报告带配图
python src/main.py "深度学习研究进展" \
  -n 20 \
  -s academic \
  -t academic \
  --add-images

# 查看所有选项
python src/main.py --help
```

### 编程接口使用

```python
from src.main import SlideCrafter

# 创建实例
crafter = SlideCrafter()

# 生成PPT
ppt_path = crafter.generate_ppt(
    topic="Python数据分析实践",
    num_slides=12,
    style="professional",
    template="business",
    add_images=True  # 自动添加配图
)

print(f"PPT已生成: {ppt_path}")

```

## 核心组件

### ContentAgent (AI内容生成器)
- **功能**: 负责PPT大纲和页面内容的智能生成
- **特性**:
  - 结构化大纲生成
  - 多种页面类型支持 (封面/目录/内容/结束)
  - 内容修改和重新生成
  - 错误处理和重试机制

### PPTGenerator (PPT文件生成器)
- **功能**: 将AI生成的内容转换为PPT文件
- **特性**:
  - 多种视觉模板支持
  - 自动版式设计
  - 格式化内容布局
  - 图片和图表占位符

### PromptTemplates (提示词模板)
- **功能**: 专业化提示词管理
- **特性**:
  - 针对不同场景的优化提示词
  - 结构化输出格式控制
  - 多语言支持预留
  - 易于扩展和定制

## 性能特点

- **生成速度**: 平均每页3-5秒
- **成功率**: >95% (依赖网络和API稳定性)
- **并发支持**: 支持多个用户同时使用Web界面
- **内存占用**: <500MB (生成过程中)
- **文件大小**: 生成的PPT通常1-5MB

## 故障排除

### 常见问题

**Q: API调用失败**
A: 检查DEEPSEEK_API_KEY是否正确设置，确保网络连接正常

**Q: 生成内容质量不理想**
A: 尝试更具体的主题描述，选择合适的内容风格

**Q: Web界面无法访问**
A: 检查端口7860是否被占用，确保防火墙设置正确

**Q: PPT文件打不开**
A: 确保python-pptx库版本正确，检查文件权限

### 日志调试

```bash
# 查看应用日志
ls output/logs/
cat output/logs/app_*.log

# 查看生成的大纲和内容
ls output/logs/outline_*.json
ls output/logs/contents_*.json
```

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. **Fork** 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 技术栈

- **AI模型**: DeepSeek-Chat (通过OpenAI兼容API)
- **AI框架**: LangChain + OpenAI SDK
- **PPT生成**: python-pptx
- **Web界面**: Gradio 6.1.0
- **开发工具**: pytest, black, flake8
- **语言**: Python 3.8+

## 更新日志

### v0.3.0 (2024-12-13) - Week 3完成
- ✨ 新增完整的Gradio Web界面
- ✨ 实现多轮对话和内容编辑功能
- ✨ 添加实时进度跟踪和时间估算
- ✨ 完善5种内容风格和3种视觉模板
- ✨ 集成测试和错误处理优化

### v0.2.0 (2024-12-08) - 核心功能完成
- ✨ 实现ContentAgent AI内容生成引擎
- ✨ 完成PPTGenerator文件生成器
- ✨ 添加PromptTemplates提示词管理
- ✨ 基础命令行接口和参数支持

### v0.1.0 (2024-12-06) - 项目初始化
- 🎉 项目框架搭建
- 📦 环境配置和依赖管理
- 🧪 测试框架建立

## License

MIT

## 联系方式

- Issues: GitHub Issues
- Email: sotime94@163.com