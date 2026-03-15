# AI 知识库问答助手

一个基于 RAG (Retrieval-Augmented Generation) 技术的智能知识库问答系统，支持文档检索、工具调用和多轮对话。

## 功能特点

- 📚 **文档处理**：支持 PDF、TXT、MD 等多种格式文档的上传和处理
- 🔍 **智能检索**：基于向量数据库的语义检索，快速找到相关文档内容
- 🤖 **AI 问答**：结合 DeepSeek API 提供智能回答，基于文档内容和自身知识
- 🧮 **工具集成**：内置计算器、时间查询等实用工具
- 👥 **用户认证**：支持用户注册和登录，保护个人对话历史
- 💬 **会话管理**：支持多会话管理，可创建、切换、删除会话
- 📊 **监控中心**：提供登录接口性能监控和系统信息
- 🚀 **多数据库支持**：支持 Supabase (PostgreSQL) 和 MySQL 数据库

## 技术栈

- **前端**：Streamlit
- **后端**：Python
- **向量数据库**：Chroma
- **嵌入模型**：BAAI/bge-small-zh-v1.5
- **AI 模型**：DeepSeek API
- **数据库**：Supabase (PostgreSQL)、MySQL

## 安装步骤

1. **克隆项目**

   ```bash
   git clone https://github.com/yourusername/ai-knowledge-assistant.git
   cd ai-knowledge-assistant
   ```

2. **创建虚拟环境**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

4. **配置 API 密钥**

   在 `config.py` 文件中设置您的 DeepSeek API 密钥：

   ```python
   # 从环境变量获取API密钥
   DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
   if not DEEPSEEK_API_KEY:
       # 提供默认值，仅用于测试
       DEEPSEEK_API_KEY = "您的DeepSeek-API-KEY-在这里"
   ```

5. **配置数据库**

   在 `config.py` 文件中设置您的数据库配置：

   ```python
   # 数据库配置
   DATABASE_SETTINGS = {
       "type": "supabase",  # 数据库类型: sqlite, mysql, supabase
       "supabase_host": os.environ.get("SUPABASE_HOST", "localhost"),  # Supabase主机
       "supabase_port": int(os.environ.get("SUPABASE_PORT", 5432)),  # Supabase端口
       "supabase_user": os.environ.get("SUPABASE_USER", "postgres"),  # Supabase用户名
       "supabase_password": os.environ.get("SUPABASE_PASSWORD", ""),  # Supabase密码
       "supabase_db": os.environ.get("SUPABASE_DB", "postgres"),  # Supabase数据库名
   }
   ```

## 运行应用

```bash
streamlit run streamlit_full_ui.py
```

应用将在 http://localhost:8501 启动。

## 使用方法

1. **注册/登录**：首次使用需要注册一个账户
2. **上传文档**：在左侧栏上传您的文档（支持 PDF、TXT、MD 格式）
3. **提问**：在对话输入框中输入您的问题
4. **查看回答**：AI 将基于文档内容和自身知识提供回答
5. **管理会话**：在左侧栏管理您的对话会话

## 部署到 Streamlit Cloud

1. **创建 Streamlit Cloud 账户**：访问 [Streamlit Cloud](https://streamlit.io/cloud) 并注册
2. **连接 GitHub 仓库**：在 Streamlit Cloud 中连接您的 GitHub 仓库
3. **配置环境变量**：在 Streamlit Cloud 中设置以下环境变量：
   - `DEEPSEEK_API_KEY`：您的 DeepSeek API 密钥
   - `SUPABASE_HOST`：Supabase 主机地址
   - `SUPABASE_PORT`：Supabase 端口
   - `SUPABASE_USER`：Supabase 用户名
   - `SUPABASE_PASSWORD`：Supabase 密码
   - `SUPABASE_DB`：Supabase 数据库名
4. **部署应用**：点击 "Deploy" 按钮部署应用

## 项目结构

```
ai-knowledge-assistant/
├── documents/          # 文档存储目录
├── vector_db/          # 向量数据库存储目录
├── config.py           # 配置文件
├── conversation_manager.py  # 对话管理
├── document_processor.py    # 文档处理
├── mysql_manager.py    # MySQL 数据库管理
├── supabase_manager.py # Supabase 数据库管理
├── tool_integration.py # 工具集成
├── user_authentication.py # 用户认证
├── vector_store_manager.py # 向量数据库管理
├── streamlit_full_ui.py # Streamlit 界面
├── requirements.txt    # 依赖文件
├── .gitignore          # Git 忽略文件
├── LICENSE             # 许可证文件
└── README.md           # 项目说明
```

## 常见问题

### Q: 上传的文档没有被正确处理怎么办？
A: 请确保文档格式正确，并且文件大小不超过 200MB。

### Q: 回答质量不好怎么办？
A: 尝试上传更相关的文档，或者更清晰地表述您的问题。

### Q: 数据库连接失败怎么办？
A: 检查您的数据库配置是否正确，确保数据库服务正在运行。

### Q: API 调用失败怎么办？
A: 检查您的 DeepSeek API 密钥是否正确，以及是否有足够的 API 调用额度。

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！
