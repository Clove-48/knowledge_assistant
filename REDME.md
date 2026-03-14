# AI知识库问答助手

基于RAG（检索增强生成）技术的智能知识库问答系统，支持文档检索、工具调用和多轮对话。

## 功能特性

- 📄 支持多种格式文档上传（PDF、TXT、MD）
- 🔍 智能知识库检索（基于语义相似度）
- 🧮 内置工具（计算器、时间查询、单位转换）
- 💬 多会话管理
- 📤 对话历史导出（Markdown、JSON、Text）
- 🌐 基于Streamlit的Web界面
- 🔐 用户认证系统
- 📊 系统监控中心
- 🔄 自动检测并使用合适的工具

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

### 本地部署

1. 克隆代码库
2. 安装依赖
3. 配置API密钥
4. 运行应用

## 项目结构

- `streamlit_full_ui.py` - 主Web界面
- `conversation_manager.py` - 对话管理
- `document_processor.py` - 文档处理
- `vector_store_manager.py` - 向量存储管理
- `tool_integration.py` - 工具集成
- `user_authentication.py` - 用户认证系统
- `mysql_manager.py` - MySQL数据库管理
- `redis_manager.py` - Redis管理
- `rag_chain.py` - RAG链实现
- `config.py` - 配置文件
- `requirements.txt` - 依赖文件
- `documents/` - 文档存储目录

## 技术栈

- Python
- Streamlit
- LangChain
- ChromaDB
- Sentence Transformers
- DeepSeek API
- MySQL
- Redis

## 使用指南

### 1. 登录/注册

首次使用需要注册账号，或使用已有账号登录。

### 2. 上传文档

在侧边栏的"文件上传"部分，上传PDF、TXT或MD格式的文档。系统会自动处理文档并添加到知识库。

### 3. 提问

在聊天输入框中输入您的问题，系统会：
- 自动从知识库中检索相关信息
- 基于检索结果和自身知识回答问题
- 对于特定问题（如计算、时间查询），自动使用相应工具

### 4. 管理会话

- 创建新对话
- 切换到历史对话
- 导出对话历史

### 5. 监控中心

在侧边栏点击"监控中心"，查看系统性能和使用统计。

## 常见问题

### Q: 为什么AI没有使用文档内容回答问题？
A: 请确保您已经上传了相关文档，并且问题与文档内容相关。系统会自动判断问题与文档的相关性，并决定是否使用文档内容回答。

### Q: 如何提高AI回答的准确性？
A: 上传相关的、高质量的文档，并且提问时尽量具体明确。

### Q: 支持哪些文件格式？
A: 支持PDF、TXT和MD格式的文件。

### Q: 文档大小有限制吗？
A: 建议单个文档不超过10MB，以确保处理速度和质量。

## 许可证

MIT License