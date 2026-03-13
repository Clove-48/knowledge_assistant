# AI知识库问答助手

基于RAG（检索增强生成）技术的智能知识库问答系统，支持文档检索、工具调用和多轮对话。

## 功能特性

- 📄 支持多种格式文档上传（PDF、TXT、MD）
- 🔍 智能知识库检索
- 🧮 内置工具（计算器、时间查询、单位转换）
- 💬 多会话管理
- 📤 对话历史导出（Markdown、JSON、Text）
- 🌐 基于Streamlit的Web界面

## 快速开始

### 环境要求

- Python 3.8+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置API密钥

1. 创建`.env`文件，添加DeepSeek API密钥：
   ```
   DEEPSEEK_API_KEY=your-api-key-here
   ```

2. 或者在部署时设置环境变量：
   ```bash
   export DEEPSEEK_API_KEY=your-api-key-here
   ```

### 运行应用

```bash
streamlit run streamlit_full_ui.py
```

应用将在 http://localhost:8501 上运行。

## 部署

### Streamlit Community Cloud

1. 上传代码到GitHub
2. 访问 https://share.streamlit.io/
3. 连接GitHub仓库
4. 设置环境变量 `DEEPSEEK_API_KEY`
5. 部署应用

## 项目结构

- `streamlit_full_ui.py` - 主Web界面
- `ai_assistant.py` - AI助手核心逻辑
- `conversation_manager.py` - 对话管理
- `document_processor.py` - 文档处理
- `vector_store_manager.py` - 向量存储管理
- `tool_integration.py` - 工具集成
- `config.py` - 配置文件
- `requirements.txt` - 依赖文件

## 技术栈

- Python
- Streamlit
- LangChain
- ChromaDB
- Sentence Transformers
- DeepSeek API

## 许可证

MIT License