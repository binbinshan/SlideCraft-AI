# SlideCraft AI

🎯 一个基于AI的智能PPT生成Agent系统

## 功能特性

- ✅ 根据主题自动生成PPT大纲
- ✅ AI生成每页内容
- ✅ 多轮对话优化
- 🚧 自动配图(开发中)
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
```

### 4. 运行

```bash
# 运行Web界面
streamlit run app.py

# 或命令行模式
python src/main.py
```

## 项目结构

```
slidecrafter-ai/
├── src/
│   ├── agents/          # Agent逻辑
│   ├── generators/      # PPT生成器
│   ├── prompts/         # Prompt模板
│   └── utils/           # 工具函数
├── tests/               # 测试代码
├── data/                # 数据文件
├── output/              # 生成的PPT
├── app.py              # Streamlit应用
└── requirements.txt    # 依赖列表
```

## 开发计划

- [x] Week 1: 环境搭建
- [x] Week 2-3: 核心功能
- [ ] Week 4: 界面开发
- [ ] Week 5-6: 功能增强
- [ ] Week 7: Agent智能化
- [ ] Week 8: 完善发布

## 技术栈

- **AI**: OpenAI API (DeepSeek-chat)
- **框架**: LangChain
- **PPT生成**: python-pptx
- **UI**: Gradio
- **语言**: Python 3.8+

## License

MIT

## 联系方式

- Issues: GitHub Issues
- Email: sotime94@163.com