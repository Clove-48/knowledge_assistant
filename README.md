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
- 📱 **响应式设计**：优化的单页布局，在不同设备上均保持良好的显示效果
- 🔒 **安全认证**：实现了JWT令牌认证和密码安全存储

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

4. **配置环境变量**

   创建 `.env` 文件并设置以下环境变量：

   ```env
   # DeepSeek API Key
   DEEPSEEK_API_KEY=your_deepseek_api_key

   # Supabase 配置
   SUPABASE_HOST=your_supabase_host
   SUPABASE_PORT=5432
   SUPABASE_USER=your_supabase_user
   SUPABASE_PASSWORD=your_supabase_password
   SUPABASE_DB=your_supabase_database
   
   # JWT 密钥
   JWT_SECRET_KEY=your_jwt_secret_key
   ```

5. **配置数据库**

   在 `config.py` 文件中设置您的数据库类型：

   ```python
   # 数据库配置
   DATABASE_SETTINGS = {
       "type": "supabase",  # 数据库类型: mysql, supabase
       # 其他配置将从环境变量读取
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
6. **监控中心**：点击左侧栏的"监控中心"查看系统信息和登录统计

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
   - `JWT_SECRET_KEY`：JWT 密钥
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

## 性能优化

- **内存管理**：采用延迟初始化机制，只在需要时创建组件
- **数据库连接**：实现了连接池和错误重试机制

## 安全与隐私

- **用户认证**：实现了基于 JWT 的认证机制
- **密码安全**：密码使用 SHA-256 哈希存储
- **数据保护**：用户文档内容安全存储与处理
- **会话管理**：实现了会话过期机制，增强安全性

## 常见问题

### Q: 上传的文档没有被正确处理怎么办？
A: 请确保文档格式正确，并且文件大小不超过 200MB。

### Q: 回答质量不好怎么办？
A: 尝试上传更相关的文档，或者更清晰地表述您的问题。

### Q: 数据库连接失败怎么办？
A: 检查您的数据库配置是否正确，确保数据库服务正在运行。对于 Supabase 连接，确保网络连接正常。

### Q: API 调用失败怎么办？
A: 检查您的 DeepSeek API 密钥是否正确，以及是否有足够的 API 调用额度。

### Q: 登录失败怎么办？
A: 检查您的用户名和密码是否正确，确保数据库连接正常。如果问题持续存在，请查看应用日志获取详细错误信息。

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！
