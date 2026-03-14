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

### 配置API密钥和数据库

1. 创建`.env`文件，添加DeepSeek API密钥和Supabase配置：
   ```
   # DeepSeek API Key
   DEEPSEEK_API_KEY=your-api-key-here

   # Supabase配置（推荐）
   SUPABASE_HOST=your-supabase-host
   SUPABASE_PORT=5432
   SUPABASE_USER=your-supabase-user
   SUPABASE_PASSWORD=your-supabase-password
   SUPABASE_DB=your-supabase-database

   # 或MySQL配置（可选）
   # MYSQL_HOST=localhost
   # MYSQL_PORT=3306
   # MYSQL_USER=root
   # MYSQL_PASSWORD=
   # MYSQL_DB=ai_assistant
   ```

2. 或者在部署时设置环境变量：
   ```bash
   export DEEPSEEK_API_KEY=your-api-key-here
   export SUPABASE_HOST=your-supabase-host
   export SUPABASE_PORT=5432
   export SUPABASE_USER=your-supabase-user
   export SUPABASE_PASSWORD=your-supabase-password
   export SUPABASE_DB=your-supabase-database
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
4. 设置环境变量：
   - `DEEPSEEK_API_KEY` - 您的DeepSeek API密钥
   - `SUPABASE_HOST` - Supabase数据库主机
   - `SUPABASE_PORT` - Supabase数据库端口
   - `SUPABASE_USER` - Supabase数据库用户名
   - `SUPABASE_PASSWORD` - Supabase数据库密码
   - `SUPABASE_DB` - Supabase数据库名称
5. 部署应用

### 本地部署

1. 克隆代码库
2. 安装依赖：`pip install -r requirements.txt`
3. 配置API密钥和Supabase连接信息（见上文）
4. 运行应用：`streamlit run streamlit_full_ui.py`

### Supabase数据库部署

1. 访问 [Supabase官网](https://supabase.com) 并注册账号
2. 创建一个新的Supabase项目
3. 在项目设置中找到数据库连接信息：
   - 主机地址（Host）
   - 端口（Port）
   - 用户名（User）
   - 密码（Password）
   - 数据库名（Database）
4. 将这些信息添加到`.env`文件中
5. 应用启动时会自动创建必要的数据库表结构

## 项目结构

- `streamlit_full_ui.py` - 主Web界面
- `conversation_manager.py` - 对话管理
- `document_processor.py` - 文档处理
- `vector_store_manager.py` - 向量存储管理
- `tool_integration.py` - 工具集成
- `user_authentication.py` - 用户认证系统
- `mysql_manager.py` - MySQL数据库管理
- `supabase_manager.py` - Supabase数据库管理
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
- MySQL (可选)
- Supabase (推荐)
- Redis
- PostgreSQL (Supabase使用)

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

### Q: 如何获取Supabase连接信息？
A: 登录Supabase控制台，进入您的项目，点击左侧菜单中的"Settings"，然后选择"Database"，在"Connection String"部分可以找到所有连接信息。

### Q: Supabase部署需要付费吗？
A: Supabase提供免费计划，包含500MB数据库存储空间和1GB带宽，对于大多数个人和小型项目来说已经足够。

### Q: 可以使用其他PostgreSQL数据库而不是Supabase吗？
A: 可以，只需要在`.env`文件中配置相应的连接信息即可，系统会自动使用SupabaseManager来连接PostgreSQL数据库。

### Q: 应用启动时出现数据库连接错误怎么办？
A: 请检查您的`.env`文件中的数据库配置是否正确，确保网络连接正常，并且Supabase项目处于活跃状态。

## 许可证

MIT License